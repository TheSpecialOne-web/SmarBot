from api.domain.models.bot.max_conversation_turns import MaxConversationTurns
from api.domain.models.conversation.conversation_turn.turn import Message, Turn, Turns


class TestConversationTurnTurns:
    def test_cut_by_max_ceonversartion_turns(self):
        turns = Turns(root=[Turn(user=Message(root="user"), bot=Message(root="bot")) for _ in range(10)])

        # 3ターンに制限
        max_conversation_turns = MaxConversationTurns(root=3)
        result = turns.cut_by_max_ceonversartion_turns(max_conversation_turns=max_conversation_turns)
        assert len(result.root) == 3, f"期待値: 3, 実際: {len(result.root)}"

        # 最大ターン数を超える場合のテスト
        max_conversation_turns = MaxConversationTurns(root=6)  # 6ターンに制限
        result = turns.cut_by_max_ceonversartion_turns(max_conversation_turns=max_conversation_turns)
        assert len(result.root) == 6, f"期待値: 6, 実際: {len(result.root)}"

        # max_conversation_turnsがNoneの場合のテスト
        result = turns.cut_by_max_ceonversartion_turns(max_conversation_turns=None)
        assert len(result.root) == 10, f"期待値: 10, 実際: {len(result.root)}"
