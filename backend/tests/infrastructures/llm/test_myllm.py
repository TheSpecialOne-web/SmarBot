from unittest.mock import MagicMock

import pytest

from api.infrastructures.llm.libs.base_myllm import BaseMyLLM


class TestMyLLM:
    @pytest.fixture
    def myllm(self) -> BaseMyLLM:
        myllm: BaseMyLLM = BaseMyLLM(model="gpt-3.5-turbo")
        myllm.llm = MagicMock()
        return myllm

    def test_trim_message(self, myllm: BaseMyLLM):
        """システムプロンプト + 履歴 + 最新のユーザー入力がLLMの最大トークン数以内に収まる場合"""
        max_response_tokens = 1024
        max_tokens = 4096

        messages = [
            {"role": "system", "content": "system message"},  # 2トークン
            {"role": "user", "content": "ユーザ1"},  # 2トークン
            {"role": "assistant", "content": "アシスタント1"},  # 2トークン
            {"role": "user", "content": "ユーザ2"},  # 2トークン
            {"role": "assistant", "content": "アシスタント2"},  # 2トークン
            {"role": "user", "content": "last message"},  # 2トークン
        ]
        myllm.llm.count_tokens.side_effect = [2, 2, 8, 2]
        trimmed_message = myllm.trim_message(messages, max_response_tokens, max_tokens)
        assert len(trimmed_message) == 6
        assert trimmed_message == messages
        myllm.llm.count_tokens.assert_any_call([{"role": "system", "content": "system message"}])
        myllm.llm.count_tokens.assert_any_call([{"role": "user", "content": "last message"}])
        myllm.llm.count_tokens.assert_any_call(
            [
                {"role": "user", "content": "ユーザ1"},
                {"role": "assistant", "content": "アシスタント1"},
                {"role": "user", "content": "ユーザ2"},
                {"role": "assistant", "content": "アシスタント2"},
            ]
        )

    def test_trim_message_when_too_long_user_input(self, myllm: BaseMyLLM):
        """1ターン目のチャットで、ユーザー入力がLLMの最大入力トークン数を超える場合"""
        max_response_tokens = 1024
        max_tokens = 4096
        max_chat_history_tokens = 12000

        user_input = "テスト1" * 10000
        messages = [
            {"role": "system", "content": "system message"},  # 2トークン
            {"role": "user", "content": user_input},  # 30,000トークン
        ]
        myllm.llm.count_tokens.side_effect = [
            2,
            20000,
        ]
        trimmed_message = myllm.trim_message(messages, max_response_tokens, max_tokens)
        assert len(trimmed_message) == 2
        assert trimmed_message == [
            {"role": "system", "content": "system message"},
            {"role": "user", "content": myllm.llm.slice_text(user_input, 0, max_chat_history_tokens)},
        ]
        myllm.llm.count_tokens.assert_any_call([{"role": "system", "content": "system message"}])
        myllm.llm.count_tokens.assert_any_call([{"role": "user", "content": user_input}])

    def test_trim_message_when_huge_history(self, myllm: BaseMyLLM):
        """履歴が大きく、システム入力 + 履歴 + 最新のユーザー入力で、LLMの最大入力トークン数を超える場合"""
        max_response_tokens = 1024
        max_tokens = 4096

        user1 = "ユーザ1" * 300
        assistant1 = "アシスタント1" * 250
        user2 = "ユーザ2" * 300
        assistant2 = "アシスタント2" * 250
        messages = [
            {"role": "system", "content": "system message"},  # 2トークン
            {"role": "user", "content": user1},  # 1,500トークン
            {"role": "assistant", "content": assistant1},  # 1,500トークン
            {"role": "user", "content": user2},  # 1,500トークン
            {"role": "assistant", "content": assistant2},  # 1,500トークン
            {"role": "user", "content": "last message"},  # 2トークン
        ]
        myllm.llm.count_tokens.side_effect = [2, 2, 6000, 2]
        trimmed_message = myllm.trim_message(messages, max_response_tokens, max_tokens)
        assert len(trimmed_message) == 4
        assert trimmed_message == [
            {"role": "system", "content": "system message"},
            {"role": "user", "content": user2},
            {"role": "assistant", "content": assistant2},
            {"role": "user", "content": "last message"},
        ]
        myllm.llm.count_tokens.assert_any_call([{"role": "system", "content": "system message"}])
        myllm.llm.count_tokens.assert_any_call([{"role": "user", "content": "last message"}])
        myllm.llm.count_tokens.assert_any_call(
            [
                {"role": "user", "content": user2},
                {"role": "assistant", "content": assistant2},
            ]
        )

    def test_trim_message_when_user_message_content_empty(self, myllm: BaseMyLLM):
        """ユーザーのメッセージが空の場合は、"ファイルの添付"とする"""
        max_response_tokens = 1024
        max_tokens = 4096

        messages = [
            {"role": "system", "content": "system message"},  # 2トークン
            {"role": "user", "content": ""},  # 0トークン
            {"role": "assistant", "content": "アシスタント1"},  # 2トークン
            {"role": "user", "content": "last message"},  # 2トークン
        ]
        myllm.llm.count_tokens.side_effect = [2, 0, 2, 2]
        trimmed_message = myllm.trim_message(messages, max_response_tokens, max_tokens)
        assert len(trimmed_message) == 4
        assert trimmed_message == [
            {"role": "system", "content": "system message"},
            {"role": "user", "content": "ファイルの添付"},
            {"role": "assistant", "content": "アシスタント1"},
            {"role": "user", "content": "last message"},
        ]
        myllm.llm.count_tokens.assert_any_call([{"role": "system", "content": "system message"}])
        myllm.llm.count_tokens.assert_any_call([{"role": "user", "content": "last message"}])
        myllm.llm.count_tokens.assert_any_call(
            [
                {"role": "user", "content": ""},
                {"role": "assistant", "content": "アシスタント1"},
            ]
        )
