from migrations.infrastructure.postgres.postgres import (
    get_user_and_group_actions,
    insert_user_policy,
    update_user_policy,
)


def set_either_user_policy_or_group_policy_to_user_policy():
    user_and_group_actions = get_user_and_group_actions()

    for action in user_and_group_actions:
        if action.user_action is None:
            insert_user_policy(action.user_id, action.bot_id, action.group_action)
        else:
            update_user_policy(action.user_id, action.bot_id, action.group_action)
