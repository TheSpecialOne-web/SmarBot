import ast
import random
import re

from api.domain.models.conversation.follow_up_question import FollowUpQuestion
from api.domain.services.llm import UrsaQuestionGeneratorInput
from api.libs.logging import get_logger

from ..base_myllm import BaseMyLLM

MAX_RESPONSE_TOKENS = 1024


class UrsaQuestionGenerator(BaseMyLLM[UrsaQuestionGeneratorInput, list[FollowUpQuestion]]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger()

    def get_system_prompt(self) -> str:
        output_format = "['質問1', '質問2', '質問3']"

        return (
            "### 互いに異なる資料検索の質問を、各queryのリストから生成せよ。\n"
            f"- {output_format}の形式で質問はシングルクウォートで囲み、出力は必ずlist型にすること。\n"
            "- 3つの質問を含んだlistを1つだけ返すこと。これ以外の出力はしてはならない。\n"
            "### 注意点\n"
            "- inputはユーザー入力の資料検索の質問例である。\n"
            "- inputの質問では、検索クエリの要素が多く資料が見つからなかったため、検索クエリの要素を減らす必要がある。\n"
            "- queryは検索クエリのリストである。\n"
            "- 各リストの要素とinputの単語だけで質問を生成せよ。\n"
            "- inputと同様の単語の順番で生成せよ。ただし、inputにある単語は、いくつか省いて生成すること。\n"
            "- queryの単語は必ず1つ以上含めること。queryがない場合は、必ずinputの単語を1つ以上含んだ質問を生成せよ。\n"
            "- 以下にある出力例では、「北九州支社のエクセルの伺書をください」というinputの質問に対し、単語数を1つ減らすことで簡略化した例を示している。\n"
            "### 出力の例\n"
            "-['北九州支社のエクセルの資料を検索してください', 'エクセルの伺書を検索してください', '北九州支社の伺書を検索してください']\n"
        )

    def extract_filter_values(self, filter_string) -> list[str]:
        values = []
        search_matches = re.findall(r"search\.ismatch\('([^']*)'", filter_string)
        values.extend(search_matches)
        eq_values = re.findall(r"eq\s+'?([^'\s]*)'?", filter_string)
        values.extend(eq_values)
        return values

    def _preprocess(self, inputs: UrsaQuestionGeneratorInput):
        system_prompt = self.get_system_prompt()
        user_input = inputs.messages[-1].content.root
        query = inputs.queries.to_string_list()
        filter = inputs.additional_kwargs.get("filter")
        if filter:
            filter_list = self.extract_filter_values(inputs.additional_kwargs.get("filter"))
        else:
            filter_list = []
        query_list = query + filter_list

        base_queries = []
        for i in range(0, len(query_list)):
            combination_list = query_list[:i] + query_list[i + 1 :]
            base_queries.append(combination_list)

        user_prompt = "<input>\n" + f"{user_input}\n" + "<query>\n" + f"{base_queries}\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        trimmed_messages = self.trim_message(
            messages, max_response_tokens=MAX_RESPONSE_TOKENS, context_window=self.llm.context_window
        )
        return trimmed_messages

    def _postprocess(self, response) -> list[FollowUpQuestion]:
        response_for_return = response.choices[0].message.content
        if response_for_return is None:
            raise Exception("Failed to generate question")

        DEFAULT_QUESTION = "この工事に関係する安全関連の事例を教えてください"

        lists_str = response_for_return.split("\n")
        combined_list = []
        for list_str in lists_str:
            try:
                list_obj = ast.literal_eval(list_str)
                combined_list.extend([item.replace("\\", "") for item in list_obj])
            except SyntaxError as e:
                self.logger.warning(f"Invalid list format: {list_str}, error: {e}")
                return [FollowUpQuestion(root=DEFAULT_QUESTION)]

        generated_combination_question = []
        generated_combination_question.append(DEFAULT_QUESTION)
        following_query = []
        if len(combined_list) == 1:
            following_query = combined_list
        else:
            following_query = random.sample(combined_list, 2)
        generated_combination_question.extend(following_query)

        return [FollowUpQuestion(root=question) for question in generated_combination_question]
