from migrations.infrastructure.postgres.postgres import (
    get_tenants,
    get_users_tenants_by_tenant_id,
    update_roles_in_users_table,
    update_tenant_id_in_users_table,
)


def make_tenant_user_relationship_many_to_one() -> None:
    tenants = get_tenants()
    for tenant in tenants:
        users_tenants = get_users_tenants_by_tenant_id(tenant.id)
        for user_tenant in users_tenants:
            # usersのtenant_idを更新する
            update_tenant_id_in_users_table(user_tenant.tenant_id, user_tenant.user_id)
            # usersのrolesを更新する
            update_roles_in_users_table(user_tenant.user_id, user_tenant.roles)
