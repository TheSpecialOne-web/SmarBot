from typing import TypedDict
from uuid import UUID

from fastapi import Request

from api.database import get_db_session_from_request
from api.domain.models.bot import Id as BotId
from api.domain.models.group import (
    GroupRole,
    Id as GroupId,
)
from api.domain.models.policy import Action, ActionEnum
from api.domain.models.tenant import Id as TenantId
from api.domain.models.workflow import Id as WorkflowId
from api.infrastructures.postgres.bot import BotRepository
from api.infrastructures.postgres.group import GroupRepository
from api.infrastructures.postgres.user import UserRepository
from api.infrastructures.postgres.workflow import WorkflowRepository
from api.libs.ctx import get_user_from_request
from api.libs.exceptions import BadRequest, Forbidden, NotFound
from api.libs.url_rule import get_url_rule_from_request


def validate_tenant_id(request: Request):
    tenant_id = request.path_params.get("tenant_id", None)
    if tenant_id is None:
        raise BadRequest("テナントIDが指定されていません。")

    tid = TenantId(value=int(tenant_id))

    user = get_user_from_request(request)
    if tid != user.tenant.id:
        raise Forbidden("指定されたテナントにアクセスする権限がありません。")

    return user.tenant


def requires_admin(request: Request):
    user = get_user_from_request(request)
    if not user.is_admin():
        raise Forbidden("組織管理者権限が必要です")
    return user


def requires_user(request: Request):
    user = get_user_from_request(request)
    if not user.is_user():
        raise Forbidden("一般ユーザー権限が必要です")
    return user


# NOTE: リクエストしたユーザーがパスパラメーターの groupId の管理者かどうかを確認する
def requires_group_admin(request: Request):
    user = get_user_from_request(request)

    if user.is_admin():
        return user

    if "group_id" not in request.path_params:
        raise Forbidden("group_id is required in url")

    try:
        group_id = GroupId(value=int(request.path_params["group_id"]))
    except Exception:
        raise BadRequest("group_id is invalid")

    session = get_db_session_from_request(request)
    group_repo = GroupRepository(session)
    group_role = group_repo.get_group_role_by_user_id_and_group_id_and_tenant_id(user.id, group_id, user.tenant.id)

    if group_role != GroupRole.GROUP_ADMIN:
        raise Forbidden("グループ管理者権限が必要です")

    return user


# NOTE: リクエストしたユーザーがどこかのグループが管理者がどうかを確認する
def requires_any_group_admin(request: Request):
    user = get_user_from_request(request)

    if user.is_admin():
        return user

    session = get_db_session_from_request(request)
    group_repo = GroupRepository(session)
    has_any_group_admin = group_repo.get_has_any_group_admin_by_user_id_and_tenant_id(user.id, user.tenant.id)

    if not has_any_group_admin:
        raise Forbidden("グループ管理者権限が必要です")

    return user


def requires_group_role(request: Request):
    user = get_user_from_request(request)

    if user.is_admin():
        return user

    if "group_id" not in request.path_params:
        raise Forbidden("group_id is required in url")

    try:
        group_id = GroupId(value=int(request.path_params["group_id"]))
    except Exception:
        raise BadRequest("group_id is invalid")

    try:
        session = get_db_session_from_request(request)
        group_repo = GroupRepository(session)
        group_repo.get_group_role_by_user_id_and_group_id_and_tenant_id(user.id, group_id, user.tenant.id)
    except Exception:
        raise Forbidden("権限がありません。")

    return user


def validate_bot_policy(request: Request):
    url_rule = get_url_rule_from_request(request)

    # ポリシーの取得
    operation_policy = _check_operation_policy(request, OPERATION_POLICIES)

    # ユーザーの取得
    user = get_user_from_request(request)

    # ボットの取得
    # 最初にテナント内にボットが存在するかチェック (他テナントのボットにアクセスできないように)
    if "bot_id" not in request.path_params:
        raise BadRequest("bot_id is required in url")
    try:
        bot_id = BotId(value=int(request.path_params["bot_id"]))
    except Exception:
        raise BadRequest("bot_id is invalid")

    session = get_db_session_from_request(request)
    bot_repo = BotRepository(session)
    bot = bot_repo.find_by_id_and_tenant_id(bot_id, user.tenant.id)

    # admin は全ての操作を許可
    if user.is_admin():
        return user

    # chat_gpt_default に関するエンドポイントはユーザー権限を持っていれば許可
    if (
        bot.is_basic_ai()
        and (user.is_user() or user.is_admin())
        and any(
            endpoint["url_path"] == url_rule and endpoint["method"] == request.method for endpoint in DEFAULT_ENDPOINTS
        )
    ):
        return user

    # ポリシーベースの認可
    user_repo = UserRepository(session)
    try:
        policy = user_repo.find_policy(user.id, user.tenant.id, bot_id)
        if policy.action.priority < operation_policy["action"].priority:
            raise Forbidden("権限がありません。")
        return user
    except NotFound:
        raise Forbidden("権限がありません。")


def validate_workflow_policy(request: Request):
    operation_policy = _check_operation_policy(request, WORKFLOW_OPERATION_POLICIES)

    current_user = get_user_from_request(request)

    if "workflow_id" not in request.path_params:
        raise BadRequest("workflow_id is required in url")
    workflow_id = WorkflowId(root=UUID(request.path_params["workflow_id"]))

    session = get_db_session_from_request(request)
    workflow_repo = WorkflowRepository(session)
    group_repo = GroupRepository(session)

    # 先にワークフローを取得することで adminでもテナント外のワークフローにアクセスできないようにする
    workflow = workflow_repo.find_with_group_by_id_and_tenant_id(current_user.tenant.id, workflow_id)

    # admin は全ての操作を許可
    if current_user.is_admin():
        return current_user

    group_id = workflow.group.id

    try:
        group_role = group_repo.get_group_role_by_user_id_and_group_id_and_tenant_id(
            current_user.id, group_id, current_user.tenant.id
        )
    except NotFound:
        raise Forbidden("権限がありません。")

    if group_role.to_policy_action().priority < operation_policy["action"].priority:
        raise Forbidden("権限がありません。")

    return current_user


class Endpoint(TypedDict):
    url_path: str
    method: str


DEFAULT_ENDPOINTS: list[Endpoint] = [
    {
        "url_path": "/bots/{bot_id}/conversations",
        "method": "POST",
    },
    {
        "url_path": "/bots/{bot_id}/conversations/validate",
        "method": "POST",
    },
    {
        "url_path": "/bots/{bot_id}/attachments",
        "method": "POST",
    },
    {
        "url_path": "/bots/{bot_id}/conversations/{conversation_id}/gen-title",
        "method": "POST",
    },
    {
        "url_path": "/conversations/{conversation_id}/turns/{turn_id}",
        "method": "PATCH",
    },
    {
        "url_path": "/conversations/{conversation_id}/turns/{turn_id}/data-points",
        "method": "GET",
    },
    {
        "url_path": "/users/{user_id}/conversations/{conversation_id}",
        "method": "GET",
    },
    {
        "url_path": "/users/{user_id}/conversations/{conversation_id}",
        "method": "PATCH",
    },
]


class OperationPolicy(TypedDict):
    url_path: str
    method: str
    action: Action


def _check_operation_policy(
    request: Request,
    operation_policies: list[OperationPolicy],
) -> OperationPolicy:
    url_rule = get_url_rule_from_request(request)
    for op in operation_policies:
        if op["url_path"] == url_rule and op["method"] == str(request.method):
            return op
    raise Forbidden("権限がありません。")


WORKFLOW_OPERATION_POLICIES: list[OperationPolicy] = [
    {
        "url_path": "/workflows/{workflow_id}/run",
        "method": "POST",
        "action": Action(root=ActionEnum.READ),
    },
]


# エンドポイントとポリシーの対応
OPERATION_POLICIES: list[OperationPolicy] = [
    {
        "url_path": "/bots/{bot_id}",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}",
        "method": "PUT",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}",
        "method": "DELETE",
        "action": Action(root=ActionEnum.ALL),
    },
    {
        "url_path": "/bots/{bot_id}/archive",
        "method": "PATCH",
        "action": Action(root=ActionEnum.ALL),
    },
    {
        "url_path": "/bots/{bot_id}/attachments",
        "method": "POST",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/attachments/{attachment_id}/signed-url",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/restore",
        "method": "PATCH",
        "action": Action(root=ActionEnum.ALL),
    },
    {
        "url_path": "/bots/{bot_id}/conversations",
        "method": "POST",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/document-folders",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/document-folders",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/document-folders/root",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/document-folders/{document_folder_id}",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/document-folders/{document_folder_id}",
        "method": "PUT",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/document-folders/{document_folder_id}",
        "method": "DELETE",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/document-folders/{document_folder_id}/move",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/external-document-folders/{external_document_folder_id}",
        "method": "DELETE",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/external-document-folders/{external_document_folder_id}/external-url",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/documents",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/documents",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/documents/all",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/documents/delete",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/documents/{document_id}",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/documents/{document_id}",
        "method": "PUT",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/documents/{document_id}",
        "method": "DELETE",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/documents/{document_id}/feedback",
        "method": "PATCH",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/documents/{document_id}/signed-url",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/documents/{document_id}/chunks/bulk",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/documents/{document_id}/move",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/terms",
        "method": "PUT",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/terms",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/terms/bulk",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/terms/delete",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/terms/sample/download",
        "method": "GET",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/terms_v2",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/terms_v2",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/terms_v2/{term_v2_id}",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/terms_v2/{term_v2_id}",
        "method": "PUT",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/terms_v2/delete",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/conversations/{conversation_id}/gen-title",
        "method": "POST",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/conversations/validate",
        "method": "POST",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/icon",
        "method": "PUT",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/icon",
        "method": "DELETE",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/conversations/{conversation_id}/turns/{turn_id}",
        "method": "PATCH",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/conversations/{conversation_id}/turns/{turn_id}/data-points",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/prompt-templates",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/prompt-templates",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/prompt-templates/{bot_prompt_template_id}",
        "method": "PUT",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/prompt-templates/delete",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/question-answers",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/question-answers",
        "method": "POST",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/question-answers/{question_answer_id}",
        "method": "GET",
        "action": Action(root=ActionEnum.READ),
    },
    {
        "url_path": "/bots/{bot_id}/question-answers/{question_answer_id}",
        "method": "PUT",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/question-answers/{question_answer_id}",
        "method": "DELETE",
        "action": Action(root=ActionEnum.WRITE),
    },
    {
        "url_path": "/bots/{bot_id}/question-answers/bulk",
        "method": "PUT",
        "action": Action(root=ActionEnum.WRITE),
    },
]
