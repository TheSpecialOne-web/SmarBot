from migrations.infrastructure.postgres.postgres import (
    get_user_tenant_by_tenant_id_and_user_id,
    update_roles_in_users_table,
    update_tenant_id_in_users_table,
)


def update_user_tenant_info_by_tenant_id_and_user_id(tenant_id: int, user_id: int) -> None:
    user_tenant = get_user_tenant_by_tenant_id_and_user_id(tenant_id, user_id)
    if user_tenant is None:
        raise Exception("user tenant not found")

    # userのtenant_idを更新する
    update_tenant_id_in_users_table(user_tenant.tenant_id, user_tenant.user_id)
    # userのrolesを更新する
    update_roles_in_users_table(user_tenant.user_id, user_tenant.roles)
