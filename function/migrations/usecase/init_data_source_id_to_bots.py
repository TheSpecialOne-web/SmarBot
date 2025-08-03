from migrations.infrastructure.postgres import (
    get_custom_bots,
    update_bot_data_source_id,
)


def insert_data_source_id_to_bots():
    # botsを取得
    try:
        bots = get_custom_bots()
    except Exception as e:
        raise Exception(f"failed to get custom bots: {e}")

    # 各botにデータを入れる
    for bot in bots:
        if bot.data_source_id is not None:
            continue
        try:
            update_bot_data_source_id(bot.id)
        except Exception as e:
            raise Exception(f"failed to update bot data_source_id: {e}")
