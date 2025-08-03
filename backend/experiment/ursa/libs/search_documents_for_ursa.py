import os
import re

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from neollm import MyLLM
from neollm.utils.postprocess import json2dict
from neollm.utils.preprocess import dict2json
from openai import AzureOpenAI

load_dotenv()
LLM_PLATFORM = os.getenv("LLM_PLATFORM")
AZURE_ENGINE_GPT35_0613 = os.getenv("AZURE_ENGINE_GPT35_0613")
AZURE_SEARCH_SERVICE_ENDPOINT = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT")
AZURE_SEARCH_SERVICE_ENDPOINT_1 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_1")
AZURE_SEARCH_SERVICE_ENDPOINT_2 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_2")
AZURE_SEARCH_SERVICE_ENDPOINT_3 = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT_3")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")
EMBEDDINGS_MODEL = os.environ.get("AZURE_ENGINE_EMBEDDING")


INDEX_NAME = "ursa-major-hybrid-phase1"
EXPERIMENT_SEMANTIC_CONFIG = "experiment-semantic-config"
EXPERIMENT_SCORING_PROFILE = "experimentScoringProfile"
azure_credential = DefaultAzureCredential()


class HistoricalCustomQueryLLM(MyLLM):
    """
    クエリを生成するクラス。
    copy from pj-ursa-major
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _preprocess(self, inputs):
        system_prompt = self.get_system_prompt()

        self.inputs = inputs["input"].strip()
        user_prompt = f"<input>\n'''{inputs['input'].strip()}'''"

        # 履歴を含むメッセージリストを作成
        if inputs.get("chat_history") is None:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        else:
            messages = [
                *inputs.get("chat_history"),
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        return messages

    def get_system_prompt(self) -> str:
        output_format = dict2json(
            {
                "search_text": "Array[String] 検索クエリ(空白区切り)。助詞や動詞や拡張子に関する単語や「ファイル」や年度は含めない。使用機材はあいまいな名称でなく詳細な名称を含めよ。",
                "author_name": "String 作成者の名前(さんなど敬称をつけない)。",
                "extention": "String 拡張子 ex) .xxx, null",
                "year": "Integer 年号",
                "branch": "String 支社という部分を除いた支社名",
            }
        )
        return (
            "ユーザーの入力から<OUTPUT_FORMAT>に従ったJSON形式で、検索クエリパラメータを作成してください\n"
            "注意点\n"
            "- 「Docuworks」、「docu」、「ドキュ」、「ドキュワークス」は、「.xdw」の拡張子である。"
            "- 具体的な資料名が与えられた場合にはsearch_textに必ず含めてください\n"
            "- 会話の履歴がある場合は、ユーザーからの入力は、以前作成したクエリに対する変更を意味する\n"
            "- 珍しい単語を先頭に、珍しくない単語を後ろにくるようにしてください\n"
            "- 存在しない場合nullとせよ."
            "\n"
            "<OUTPUT_FORMAT>"
            f"{output_format}\n"
            "\n"
            "<OUTPUT>"
        )

    # search_textとfilterに重複している要素をsearch_textから削除
    def process_search_text(self, key, search_text, search_text_list):
        match = re.search(rf"\S*{key}\S*", search_text)
        word = match.group(0) if match else None
        search_text_list.remove(word)

    def _postprocess(self, response):
        # JSON形式のresponseになっているかチェック
        try:
            response_dict = json2dict(response["choices"][0]["message"]["content"])
        except Exception as e:
            raise ValueError(f"Failed to parse response as JSON: {e}")

        search_text = response_dict.get("search_text")
        filters = self._create_filters(response_dict, search_text)

        # ノイズワードの消去
        noize_words = ["資料", "作成", "作成者", "支社", "年", "年度", "年号", "年度"]
        search_text_list = [word for word in search_text.split() if word not in noize_words]
        search_text = " ".join(search_text_list)

        param_dict = {"search_text": search_text, "filter": " and ".join(filters) if filters else None}

        return response_dict, param_dict

    def _create_filters(self, response_dict, search_text):
        filters = []
        self._add_author_filter(response_dict, filters)
        self._add_extension_filter(response_dict, search_text, filters)
        self._add_year_filter(response_dict, filters)
        self._add_branch_filter(response_dict, filters)
        return filters

    # 各filterのユーザー入力部分にエスケープ操作を行う
    def _escape_single_quotes(self, value: str) -> str:
        return value.replace("'", "''") if isinstance(value, str) else value

    def _add_author_filter(self, response_dict, filters):
        author_name = response_dict.get("author_name")
        escaped_author_name = self._escape_single_quotes(author_name)
        if author_name:
            filters.append(f"search.ismatch('{escaped_author_name}', 'author', 'simple', 'all')")

    def _add_extension_filter(self, response_dict, search_text, filters):
        input_extension = response_dict.get("extention")
        if input_extension:
            input_extension = input_extension.replace(".", "")
            extensions = self._get_extensions_for(input_extension)
            extension_filters = []
            for ext in extensions:
                if ext in search_text:
                    escaped_ext = self._escape_single_quotes(ext)
                    extension_filters.append(f"extention eq '{escaped_ext}'")
            if extension_filters:
                filters.append(" or ".join(extension_filters))

    def _add_year_filter(self, response_dict, filters):
        year = response_dict.get("year")
        if year and isinstance(year, int) and 2010 <= year <= 2023:
            escaped_year = self._escape_single_quotes(year)
            filters.append(f"year eq {escaped_year}")

    def _add_branch_filter(self, response_dict, filters):
        branch = response_dict.get("branch")
        valid_branches = ["福岡", "北九州", "宮崎", "鹿児島", "熊本", "長崎", "大分", "佐賀"]
        if branch and branch in valid_branches:
            escaped_branch = self._escape_single_quotes(branch)
            filters.append(f"branch eq '{escaped_branch}'")

    def _get_extensions_for(self, input_extension):
        extension_mapper = {
            "パワポ": [".ppt", ".pptx"],
            "パワーポイント": [".ppt", ".pptx"],
            "powerpoint": [".ppt", ".pptx"],
            "ppt": [".ppt"],
            "pptx": [".pptx"],
            "ワード": [".doc", ".docx"],
            "word": [".doc", ".docx"],
            "doc": [".doc"],
            "docx": [".docx"],
            "ドキュワークス": [".xdw"],
            "Docuworks": [".xdw"],
            "docu": [".xdw"],
            "ドキュ": [".xdw"],
            "xdw": [".xdw"],
            "エクセル": [".xls", ".xlsx"],
            "excel": [".xls", ".xlsx"],
            "xls": [".xls"],
            "xlsx": [".xlsx"],
            "pdf": [".pdf"],
        }
        return extension_mapper.get(input_extension, [])

    def clear_history(self):
        self.chat_history.clear()


def get_search_client(endpoint: str, index_name: str) -> SearchClient:
    if endpoint not in [
        AZURE_SEARCH_SERVICE_ENDPOINT,
        AZURE_SEARCH_SERVICE_ENDPOINT_1,
        AZURE_SEARCH_SERVICE_ENDPOINT_2,
        AZURE_SEARCH_SERVICE_ENDPOINT_3,
    ]:
        raise ValueError(f"Invalid endpoint: {endpoint}")
    return SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=azure_credential,
    )


def query_generator(input: str) -> dict:
    """
    クエリを生成する。
    Args:
        input: ユーザーの入力
    Returns:
        {"search_text": 検索クエリ, "filter": フィルター条件}
    例:
        {'search_text': '熊本 管内 社内 電話 システム 整備 工事 仕様書', 'filter': "branch eq '熊本'"}
    """
    query_llm = HistoricalCustomQueryLLM(
        platform=LLM_PLATFORM,
        model=AZURE_ENGINE_GPT35_0613,
        verbose=False,
        llm_settings={"temperature": 0, "max_tokens": 300},
    )
    input_text = {"input": input}
    _, query = query_llm(input_text)
    return query


def generate_embeddings(text: str) -> list[float]:
    """
    Azure OpenAIを使って、指定されたテキストのEmbeddingを生成する。
    Args:
        text: Embeddingを生成するテキスト
    Returns:
        Embeddingのリスト
    """
    if AZURE_OPENAI_ENDPOINT is None:
        raise ValueError("AZURE_OPENAI_ENDPOINTが設定されていません。")
    azure_openai_client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY, api_version=AZURE_OPENAI_API_VERSION, azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    try:
        response = azure_openai_client.embeddings.create(input=text, model=EMBEDDINGS_MODEL)  # type: ignore
        embeddings = response.data[0].embedding
        return embeddings
    except Exception as e:
        raise Exception(f"Embedding作成でエラーが発生しました: {e!s}")


def search_documents_for_ursa(
    input: str,
    document_limit: int,
    params: dict | None = None,
    vector_search: bool = False,
    select: list | None = None,
) -> list[dict]:
    """
    Azure AI Searchを使って、指定された条件に合致するドキュメントを検索する。
    Args:
        input: 検索条件を含む文字列 eg) "ダム放流警報システム用のGPS装置の購入仕様書が欲しい。"
        document_limit: 検索結果の上限数
        params: 検索条件に関するパラメータ
        vector_search: ベクトル検索を行うかどうか
        select: 検索結果のフィールドを指定する
    Returns:
        検索結果のリスト
    """
    # クエリを生成
    query = query_generator(input)
    filter = query["filter"]

    # Azure AI Searchに渡す際に、空白区切りのクエリにする
    filters = ["document_id ne null"]
    if filter:
        filters.append(filter)
    filter_ = " and ".join(filters)
    search_text = " ".join(query["search_text"].split())

    # ベクトル検索のパラメータを設定
    if vector_search:
        vector_search_params = params.get("vector_search", params) if params else None
        path_weight = vector_search_params.get("path_weight", 1) if vector_search_params else 1
        content_weight = vector_search_params.get("content_weight", 1) if vector_search_params else 1
        embeddings = generate_embeddings(search_text)
        path_vector = VectorizedQuery(
            vector=embeddings, k_nearest_neighbors=3, fields="path_vector", weight=path_weight
        )
        content_vector = VectorizedQuery(
            vector=embeddings, k_nearest_neighbors=3, fields="content_vector", weight=content_weight
        )

    if not AZURE_SEARCH_SERVICE_ENDPOINT_1:
        raise ValueError("AZURE_SEARCH_SERVICE_ENDPOINT_1 is not set.")
    search_client = get_search_client(AZURE_SEARCH_SERVICE_ENDPOINT_1, INDEX_NAME)

    raw_document = search_client.search(
        search_text=search_text,
        query_type="semantic",
        semantic_configuration_name=EXPERIMENT_SEMANTIC_CONFIG,
        query_caption="extractive",
        query_answer="extractive",
        query_answer_count=3,
        vector_queries=[path_vector, content_vector] if vector_search else None,
        top=document_limit,
        filter=filter_,
        select=select if select else ["full_path"],
        scoring_profile=EXPERIMENT_SCORING_PROFILE,
    )

    return list(raw_document) if raw_document else []
