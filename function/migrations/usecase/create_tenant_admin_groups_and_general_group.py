from libs.logging import get_logger
from libs.session import session_scope
from migrations.infrastructure.postgres import Tenant
from migrations.infrastructure.postgres.bot import (
    add_bots_to_group,
    find_basic_ais,
    find_bots_without_basic_ai,
)
from migrations.infrastructure.postgres.group import (
    add_users_to_group,
    create_general_group,
    create_tenant_admin_group,
    find_general_group_by_tenant_id,
)
from migrations.infrastructure.postgres.postgres import get_tenants
from migrations.infrastructure.postgres.user import (
    find_admin_users,
    find_users_without_admin_by_tenant_id,
)

logger = get_logger(__name__)
logger.setLevel("INFO")


def create_tenant_admin_groups_and_general_group():
    try:
        tenants = get_tenants()
    except Exception as e:
        raise Exception(f"Failed to get tenants: {e}")

    successed_tenants: list[Tenant] = []

    for tenant in tenants:
        # すでにAllグループがある場合はスキップ
        general_group = find_general_group_by_tenant_id(tenant.id)
        if general_group is not None:
            continue

        with session_scope() as session:
            try:
                # テナント管理者グループ作成
                tenant_admin_group_id = create_tenant_admin_group(session, tenant.id)

                # テナント管理者グループにテナント管理者をGroup Adminとして追加
                admin_users = find_admin_users(session, tenant.id, include_deleted=True)
                add_users_to_group(
                    session,
                    group_id=tenant_admin_group_id,
                    user_ids=[user.id for user in admin_users],
                    group_role="group_admin",
                )

                # テナント内の 基盤モデル以外のbotを全てテナント管理者グループに追加
                bots = find_bots_without_basic_ai(session, tenant.id, include_deleted=True)
                add_bots_to_group(session, group_id=tenant_admin_group_id, bots=bots)

                # Allグループ作成
                general_group_id = create_general_group(session, tenant.id, tenant.name)

                # Allグループにテナント管理者をGroup Adminとして追加
                add_users_to_group(
                    session,
                    group_id=general_group_id,
                    user_ids=[user.id for user in admin_users],
                    group_role="group_admin",
                )

                # Allグループにテナント内の管理者ではないユーザをGroup Viewerとして追加
                users = find_users_without_admin_by_tenant_id(session, tenant.id, include_deleted=True)
                add_users_to_group(
                    session, group_id=general_group_id, user_ids=[user.id for user in users], group_role="group_viewer"
                )

                # Allグループに基盤モデルを追加
                basic_ais = find_basic_ais(session, tenant.id, include_deleted=True)
                add_bots_to_group(session, group_id=general_group_id, bots=basic_ais)
                successed_tenants.append(tenant)
                logger.info(f"successed_tenants: {[(tenant.id, tenant.name) for tenant in successed_tenants]}")
            except Exception as e:
                logger.error(f"Failed to create tenant ID:{tenant.id} name:{tenant.name} error: {e}")
                raise e
