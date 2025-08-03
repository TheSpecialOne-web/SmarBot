from datetime import datetime, timedelta

from api.database import SessionFactory
from api.domain.models.api_key.api_key import ApiKey
from api.domain.models.bot.bot import Id as BotId
from api.domain.models.chat_completion.chat_completion import ChatCompletion
from api.domain.models.conversation.conversation import Conversation
from api.domain.models.conversation.conversation_turn import ConversationTurn
from api.domain.models.statistics import (
    ApiKeyTokenCount,
    ApiKeyTokenCountSummary,
    UserTokenCount,
    UserTokenCountSummary,
)
from api.domain.models.token import TokenCount
from api.infrastructures.postgres.statistics import StatisticsRepository


class TestStatisticsRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.statistics_repo = StatisticsRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_get_conversation_token_count(
        self,
        conversation_with_turns_seed: tuple[Conversation, list[ConversationTurn]],
        user_seed,
    ):
        """Test get_token_count"""
        # Given
        conversation, conversation_turns = conversation_with_turns_seed
        bot_ids = [conversation.bot_id]
        start_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
        end_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2)

        _, user, _, _, _ = user_seed
        want = UserTokenCountSummary(
            total_count=TokenCount(root=conversation_turns[0].token_count.root),
            users_tokens=[
                UserTokenCount(
                    user_id=conversation.user_id,
                    user_name=user.name,
                    token_count=TokenCount(root=conversation_turns[0].token_count.root),
                ),
            ],
        )

        # When
        got = self.statistics_repo.get_conversation_token_count(
            bot_ids=bot_ids,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )
        # Then
        assert got == want

    def test_get_chat_completion_token_count_by_api_key_ids(
        self,
        chat_completions_seed: tuple[
            BotId,
            list[tuple[ApiKey, ChatCompletion]],
        ],
    ):
        # Given
        _, chat_completions_with_api_key = chat_completions_seed
        start_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
        end_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2)

        target_api_key = chat_completions_with_api_key[0][0]
        target_chat_completions = [
            chat_completion for _, chat_completion in chat_completions_with_api_key if _.id == target_api_key.id
        ]

        want = ApiKeyTokenCountSummary(
            total_count=TokenCount(
                root=sum(chat_completion.token_count.root for chat_completion in target_chat_completions)
            ),
            api_keys_tokens=[
                ApiKeyTokenCount(
                    api_key_id=target_api_key.id,
                    name=target_api_key.name,
                    token_count=TokenCount(
                        root=sum(chat_completion.token_count.root for chat_completion in target_chat_completions)
                    ),
                ),
            ],
        )

        # When
        got = self.statistics_repo.get_chat_completion_token_count_by_api_key_ids(
            api_key_ids=[target_api_key.id],
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )
        # Then
        assert got == want
