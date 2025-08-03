import re
from typing import Any

from neollm import MyLLM
from neollm.exceptions import ContentFilterError
from neollm.types import Messages
from neollm.utils.postprocess import json2dict
from neollm.utils.preprocess import dict2json, optimize_token

from api.domain.models.chat_completion.role import Role
from api.domain.models.query import Queries
from api.domain.services.llm import QueryGeneratorInput, QueryGeneratorOutput
from api.libs.app_env import app_env
from api.libs.exceptions import BadRequest

from ..constants import CONTENT_FILTER_NOTION


class UrsaQueryGenerator(MyLLM[QueryGeneratorInput, QueryGeneratorOutput]):
    def system_prompt(self) -> str:
        output_format = dict2json(
            {
                "search_text": "Array[String] 検索クエリ(空白区切り)。助詞や動詞や拡張子名や「ファイル」と、以下に示されている、author_name、extension、year、branchに該当するものは除外せよ。使用機材、施設名はあいまいな名称でなく詳細な名称を含めよ。",
                "author_name": "String 作成者の名前(さんなど敬称をつけない)。",
                "extension": "String 拡張子。「Docuworks」、「docu」、「ドキュ」、「ドキュワークス」は、「.xdw」の拡張子です。「エクセル」は、「.xls」と「.xlsx」の二つの拡張子である。 ex) .xxx, null ",
                "year": "Integer 年号または年度。",
                "branch": "String 支社という部分を除いた支社名。",
            }
        )
        return (
            "ユーザーの入力から<OUTPUT_FORMAT>に従ったJSON形式で、検索クエリパラメータを作成せよ。\n"
            "注意点\n"
            "- 「Docuworks」、「docu」、「ドキュ」、「ドキュワークス」という単語が出た場合では、「.xdw」の拡張子である。extensionに入れて下さい\n"
            "- 「エクセル」、「excel」という単語が出た場合では、「.xls」と「.xlsx」の拡張子である。extensionに入れて下さい\n"
            "- 具体的な資料名、施設名が与えられた場合、search_textに必ず含めること。\n"
            "- botの入力は前回の会話で作成したクエリ、フィルターである。追加でユーザーからの入力があった場合には、フィルターを変更すること。\n"
            "- 会話の履歴がある場合は、ユーザーからの入力は、以前作成した検索クエリに対する変更を意味する。会話履歴は末尾が直近の会話である。指示と対応するクエリのみを変更し、それ以外のクエリの内容は保持すること。\n"
            "- author_name、extension、year、branchに関しては、入力で指示のあった項目のみを変更する。入力で指示がない項目に関しては、1つ前の内容をそのまま用いること。\n"
            "- ただし、入力内容が全く新しいものの場合や、前の入力内容を補足する場合でなければ、会話履歴は考慮しなくてよい。これらの場合、クエリとフィルターは入力内容のみを用いて新規作成すること。\n"
            "- 珍しい単語を先頭に、珍しくない単語を後ろにくるようにせよ。\n"
            "- 存在しない場合や考慮しない項目はnullとせよ。\n"
            "\n"
            "<OUTPUT_FORMAT>\n"
            f"{output_format}\n"
            "\n"
            "<OUTPUT>\n"
        )

    # ユーザー表示用のフィルタ文字列をQueryGeneratorOutputの辞書形式に変換する関数
    def parse_filters_to_dict(self, filter_string):
        output_dict = {
            "author_name": None,
            "extension": None,
            "year": None,
            "branch": None,
        }
        author_match = re.search(r"作成者:\s*(\w+)", filter_string)
        if author_match:
            output_dict["author_name"] = author_match.group(1)
        extension_match = re.search(r"拡張子:\s*(\.\w+|null)", filter_string)
        if extension_match:
            output_dict["extension"] = extension_match.group(1)
        year_match = re.search(r"年度:\s*(\d{4})", filter_string)
        if year_match:
            output_dict["year"] = int(year_match.group(1))
        branch_match = re.search(r"支店:\s*(\w+)", filter_string)
        if branch_match:
            output_dict["branch"] = branch_match.group(1)
        return output_dict

    # ユーザー表示用の文字列からprefixで指定した部分の文字列を抽出する関数
    def extract_query(self, prefix, f_string):
        suffix = "\n\n"

        # prefixとsuffixの間にある部分を抽出
        start = f_string.find(prefix) + len(prefix)
        end = f_string.find(suffix, start)

        target_string = f_string[start:end]
        return target_string

    # botのメッセージを解析して、QueryGeneratorOutputの辞書形式に変換する関数
    def _parse_bot_history(self, bot_message: str):
        if "フィルタ:" in bot_message:
            search_text = self.extract_query("検索語句:", bot_message)
            filter_text = self.extract_query("フィルタ:", bot_message)
            bot_dict = self.parse_filters_to_dict(filter_text)
        else:
            search_text = self.extract_query("検索語句:", bot_message)
            bot_dict = {}
        search_text = search_text.replace("「", "").replace("」", "").replace("\n", "")
        search_text_list = search_text.split("、")
        search_text = " ".join(search_text_list)
        bot_dict["search_text"] = search_text
        bot_message = dict2json(bot_dict)
        return bot_message

    def _preprocess(self, inputs: QueryGeneratorInput) -> Messages:
        if inputs.query_system_prompt is None:
            system_prompt = self.system_prompt()
        else:
            system_prompt = inputs.query_system_prompt.root
        self.query_type = "その他"
        messages: Messages = [{"role": "system", "content": optimize_token(system_prompt)}]
        for message in inputs.messages:
            if message.role == Role.USER:
                messages.append({"role": "user", "content": optimize_token(message.content.root)})
            elif message.role == Role.ASSISTANT:
                try:
                    bot_message = self._parse_bot_history(message.content.root)
                except Exception:
                    bot_message = ""
                messages.append({"role": "assistant", "content": optimize_token(bot_message)})
        return messages

    def _ruleprocess(self, inputs: QueryGeneratorInput):
        question = inputs.messages[-1].content.root
        if question == "この工事に関係する安全関連の事例を教えてください":
            self.query_type = "安全関連"
            if len(inputs.messages) < 2:
                return None
            bot_message = inputs.messages[-2].content.root
            parsed_bot_message = self._parse_bot_history(bot_message)
            rulebase_response_dict = {}
            rulebase_response_dict["choices"] = [{"message": {"content": parsed_bot_message}}]
            return self._postprocess(rulebase_response_dict)
        return None

    def _extensions_replacer(self, list_extensions, search_text_list):
        search_text_list = [q for q in search_text_list if q not in list_extensions]
        return search_text_list

    def _postprocess(self, response) -> QueryGeneratorOutput:
        response_dict = json2dict(response["choices"][0]["message"]["content"])
        # 検索のノイズになるワードをsearch_textから削除
        noize_words = ["資料", "作成", "作成者", "支社", "年", "年度", "年号", "年度"]
        search_text: Any = response_dict.get("search_text", "")
        search_text_list: list[str] = (
            str(search_text).split() if not isinstance(search_text, list) else [str(query) for query in search_text]
        )
        search_text_list = [query for query in search_text_list if query not in noize_words]
        # filterが存在するとき、search_textの重複を削除
        # search_text, author_nameともに作成者の名前は「さん」を削除された状態にGPTがしてくれているので、removeにしている
        author_name = response_dict.get("author_name", "")
        input_extension = (
            response_dict.get("extension", "").replace(".", "") if response_dict.get("extension") else None
        )
        year = response_dict.get("year", "")
        branch = response_dict.get("branch", "")
        search_text = str(search_text)
        if author_name and author_name in search_text_list:
            search_text_list.remove(author_name)
        if input_extension:
            if input_extension in ["xlsx", "xls"]:
                search_text_list = self._extensions_replacer(["エクセル", "xlsx", "xls", "excel"], search_text_list)
            elif input_extension in ["pptx", "ppt"]:
                search_text_list = self._extensions_replacer(
                    ["パワポ", "パワーポイント", "pptx", "ppt"],
                    search_text_list,
                )
            elif input_extension in ["doc", "docx"]:
                search_text_list = self._extensions_replacer(["ワード", "word", "doc", "docx"], search_text_list)
            elif input_extension == "pdf":
                search_text_list = self._extensions_replacer(["pdf"], search_text_list)
            # PoCではxdwファイルがないので、xdwの処理はコメントアウト
            # elif input_extension == "xdw":
            #     search_text_list = self._extensions_replacer(
            #         ["Docuworks", "docu", "どきゅ", "ドキュ", "xdw", "ドキュワークス"], search_text_list
            #     )
        if year and str(year) in search_text_list:
            search_text_list.remove(str(year))
        if (
            branch
            and branch in search_text_list
            and branch
            in [
                "福岡",
                "北九州",
                "宮崎",
                "鹿児島",
                "熊本",
                "長崎",
                "大分",
                "佐賀",
            ]
        ):  # add branch vaildation
            search_text_list.remove(branch)

        # 安全管理事例に関する質問の時はfilterを無しで検索
        query_type = self.query_type
        if query_type == "安全関連":
            author_name = None
            input_extension = None
            if year:
                search_text += f" {year}"
                year = None
            if branch:
                search_text += f" {branch}"
                branch = None
        filters = self._create_filters(search_text, author_name, input_extension, year, branch, query_type)
        query_generator_output = QueryGeneratorOutput(
            # セマンティック検索の精度を向上させるため、クエリでなく、質問文でそのまま検索する
            queries=(
                Queries.from_list([self.inputs.messages[-1].content.root])
                if app_env.is_localhost() or app_env.is_development()
                else Queries.from_list(search_text_list)
            ),
            input_token=self.token["input"],
            output_token=self.token["output"],
            # フィルターと表示用のクエリを作成
            additional_kwargs={
                "filter": " and ".join(filters) if filters else None,
                "query_for_display": search_text_list,
            },
        )
        return query_generator_output

    def _create_filters(self, search_text, author_name, input_extension, year, branch, query_type) -> list:
        """

        Args:
            response_dict: dict
            search_text: str

        Returns:
            filters: 検索時のフィルター list
        """
        filters: list = []
        self._add_author_filter(author_name, filters)
        self._add_year_filter(year, filters)
        self._add_branch_filter(branch, filters)
        self._add_extension_filter(search_text, input_extension, filters)
        self._add_query_type_filter(query_type, filters)
        return filters

    # 各filterのユーザー入力部分にエスケープ操作を行う
    def _escape_single_quotes(self, value: str) -> str:
        return value.replace("'", "''") if isinstance(value, str) else value

    def _add_author_filter(self, author_name, filters):
        if author_name:
            escaped_name = self._escape_single_quotes(author_name)
            filters.append(f"search.ismatch('{escaped_name}', 'author', 'simple', 'all')")

    def _add_extension_filter(self, search_text, input_extension, filters):
        search_text = " ".join(search_text)
        if input_extension:
            extensions = self._get_extensions_for_ursa(input_extension)
            extension_filters = []
            for ext in extensions:
                # xdwをvalid_extensionからも除外
                is_valid_extension = ext in [
                    ".ppt",
                    ".pptx",
                    ".doc",
                    ".docx",
                    ".xls",
                    ".xlsx",
                    ".pdf",
                ]  # PoCではxdwは対象外 #
                if is_valid_extension:
                    ext = ext.replace(".", "")
                    escaped_ext = self._escape_single_quotes(ext)
                    extension_filters.append(f"extention eq '{escaped_ext}'")
            if extension_filters:
                filters.append(" or ".join(extension_filters))

    def _add_year_filter(self, year, filters):
        if year and isinstance(year, int) and 2010 <= year <= 2023:
            escaped_year = self._escape_single_quotes(year)
            filters.append(f"year eq {escaped_year}")

    def _add_branch_filter(self, branch, filters):
        valid_branches = ["福岡", "北九州", "宮崎", "鹿児島", "熊本", "長崎", "大分", "佐賀"]
        if branch and branch in valid_branches:
            escaped_branch = self._escape_single_quotes(branch)
            filters.append(f"branch eq '{escaped_branch}'")

    def _add_query_type_filter(self, query_type, filters):
        if query_type == "安全関連":
            filters.append("document_type eq '安全関連'")
        else:
            filters.append("document_type ne '安全関連'")

    def _get_extensions_for_ursa(self, input_extension: str):
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
        input_extensions = input_extension.split()
        results = []
        for ext in input_extensions:
            results.extend(extension_mapper.get(ext.lower(), []))
        return results

    def __call__(self, inputs: QueryGeneratorInput) -> QueryGeneratorOutput:
        """_summary_

        Args:
            inputs (QueryGeneratorInput): クエリ生成の入力(question, tenant_name, search_method)

        Raises:
            e: _description_

        Returns:
            QueryGeneratorOutput: クエリ生成の出力(query, is_vector_query)
        """
        try:
            return super().__call__(inputs)
        except ContentFilterError:
            raise BadRequest(CONTENT_FILTER_NOTION)
