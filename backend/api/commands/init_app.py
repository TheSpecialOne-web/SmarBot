from dotenv import load_dotenv

load_dotenv(".env")

import click
from injector import Injector

from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import (
    bot as bot_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.llm import AllowForeignRegion, ModelFamily, Platform
from api.infrastructures.postgres.models.administrator import Administrator
from api.usecase.bot import BotUseCase
from api.usecase.tenant import TenantUseCase
from api.usecase.tenant.tenant import CreateTenantOutput


@click.command("init-app")
@click.option("--tenant-name", type=str, required=True)
@click.option("--tenant-alias", type=str, required=True)
@click.option("--allow-foreign-region", type=bool, required=True)
@click.option("--use-gcp", type=bool, required=True)
@click.option("--enable-document-intelligence", type=bool, required=True)
@click.option("--admin-name", type=str, required=True)
@click.option("--admin-email", type=str, required=True)
def init_app(
    tenant_name: str,
    tenant_alias: str,
    allow_foreign_region: bool,
    use_gcp: bool,
    enable_document_intelligence: bool,
    admin_name: str,
    admin_email: str,
):
    with SessionFactory() as session:
        injector = get_injector(session)
        output = init_app_impl(
            injector,
            tenant_name,
            tenant_alias,
            allow_foreign_region,
            use_gcp,
            enable_document_intelligence,
            admin_name,
            admin_email,
        )
        if output.tenant.id != tenant_domain.NEOAI_TENANT_ID:
            return

        administrator = Administrator(
            user_id=output.admin.id.value,
        )
        try:
            session.add(administrator)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error creating administrator: {e}")
            raise e

        print(f"administrator.id: {administrator.id}")


def init_app_impl(
    injector: Injector,
    tenant_name: str,
    tenant_alias: str,
    allow_foreign_region: bool,
    use_gcp: bool,
    enable_document_intelligence: bool,
    admin_name: str,
    admin_email: str,
) -> CreateTenantOutput:
    tenant_use_case = injector.get(TenantUseCase)
    output = tenant_use_case.create_tenant(
        tenant_for_create=tenant_domain.TenantForCreate(
            name=tenant_domain.Name(value=tenant_name),
            alias=tenant_domain.Alias(root=tenant_alias),
            allow_foreign_region=AllowForeignRegion(root=allow_foreign_region),
            additional_platforms=tenant_domain.AdditionalPlatformList.from_values(
                [Platform.GCP.value] if use_gcp else []
            ),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=enable_document_intelligence),
        ),
        admin=user_domain.UserForCreate(
            name=user_domain.Name(value=admin_name),
            email=user_domain.Email(value=admin_email),
            roles=[user_domain.Role.ADMIN],
        ),
    )
    tenant = output.tenant

    print(f"tenant: {tenant.model_dump_json(indent=2)}")

    bot_use_case = injector.get(BotUseCase)
    system_prompt = (
        "あなたは優秀な「neoAI Chat」のカスタマーサポートAIです。\n"
        "「neoAI Chat」は社内ドキュメントと生成AIの連携により、従業員の様々な業務効率化を可能にするサービスです。\n"
        "以下の{要件}を満たすため、{制約条件}に気をつけながら、{ユーザーからの入力}と{学習済みドキュメント}を元に回答を生成してください。\n\n"
        "# 要件\n"
        "neoAI Chat利用ユーザーからのneoAI Chatの使い方に関する質問に答えてください。\n\n"
        "# 制約条件\n"
        "neoAI Chatを初めて使うユーザーにもわかるようなわかりやすい表現で答えてください\n"
        "200字で答えて\n\n"
        "# ユーザーからの入力\n"
        "neoAI Chatの使い方に関する質問\n\n"
        "# 学習済みドキュメント\n"
        "neoAI Chatご利用マニュアル"
    )
    bot = bot_use_case.create_bot(
        tenant_id=tenant.id,
        group_id=output.group_id,
        bot_for_create=bot_domain.BotForCreate.create_neollm(
            tenant_alias=tenant.alias,
            name=bot_domain.Name(value="neoAI Chat AIサポート"),
            description=bot_domain.Description(
                value="neoAI Chatの使い方に関する質問に答えられるAIカスタマーサポートです。neoAI Chat利用方法でわからないことがあればなんでも聞いてください。"
            ),
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            example_questions=[],
            response_generator_model_family=ModelFamily.GPT_4O,
            response_system_prompt=bot_domain.ResponseSystemPrompt(root=system_prompt),
            document_limit=bot_domain.DocumentLimit(root=10),
            pdf_parser=llm_domain.PdfParser.PYPDF,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=True),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=True),
            icon_color=bot_domain.IconColor(root="#BDBDBD"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        ),
        bot_template_id=None,
        creator_id=None,
    )

    print(f"bot: {bot.model_dump_json(indent=2)}")

    return output


if __name__ == "__main__":
    init_app()
