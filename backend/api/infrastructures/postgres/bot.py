from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session, joinedload

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.bot import approach_variable as approach_variable_domain
from api.domain.models.bot.prompt_template import (
    Id as BotPromptTemplateId,
    PromptTemplate,
)
from api.domain.models.llm.model import ModelFamily
from api.domain.models.text_2_image_model.model import Text2ImageModelFamily
from api.libs.exceptions import NotFound

from .models.approach_variable import ApproachVariable
from .models.bot import Bot
from .models.bot_prompt_template import BotPromptTemplate
from .models.group import Group
from .models.user_liked_bots import UserLikedBot


class BotRepository(bot_domain.IBotRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, id: bot_domain.Id, include_deleted: bool = False) -> bot_domain.Bot:
        bot = (
            self.session.execute(
                select(Bot)
                .where(Bot.id == id.value)
                .options(joinedload(Bot.approach_variables))
                .execution_options(include_deleted=include_deleted)
            )
            .scalars()
            .first()
        )
        if not bot:
            raise NotFound("基盤モデルまたはアシスタントが見つかりませんでした")
        return bot.to_domain(bot.approach_variables)

    def find_with_tenant_by_id(self, id: bot_domain.Id) -> bot_domain.BotWithTenant:
        bot = (
            self.session.execute(
                select(Bot)
                .where(Bot.id == id.value)
                .options(joinedload(Bot.approach_variables))
                .options(joinedload(Bot.tenant))
            )
            .scalars()
            .first()
        )
        if not bot:
            raise NotFound("基盤モデルまたはアシスタントが見つかりませんでした")
        return bot.to_domain_with_tenant(bot.approach_variables, bot.tenant)

    def find_by_id_and_group_id(self, id: bot_domain.Id, group_id: group_domain.Id) -> bot_domain.Bot:
        try:
            bot = self.session.execute(
                select(Bot).where(Bot.id == id.value).where(Bot.group_id == group_id.value)
            ).scalar_one_or_none()
            if not bot:
                raise NotFound("基盤モデルまたはアシスタントが見つかりませんでした")
            return bot.to_domain(bot.approach_variables)
        except NoResultFound:
            raise NotFound("基盤モデルまたはアシスタントが見つかりませんでした")

    def find_by_tenant_id(
        self,
        tenant_id: tenant_domain.Id,
        statuses: list[bot_domain.Status] | None = None,
    ) -> list[bot_domain.Bot]:
        bots = (
            self.session.execute(
                select(Bot)
                .where(Bot.tenant_id == tenant_id.value)
                .where(Bot.status.in_(statuses if statuses is not None else [bot_domain.Status.ACTIVE]))
                .options(joinedload(Bot.approach_variables))
            )
            .unique()
            .scalars()
            .all()
        )
        return [bot.to_domain(bot.approach_variables) for bot in bots]

    def find_all_by_tenant_id(
        self, tenant_id: tenant_domain.Id, include_deleted: bool = False
    ) -> list[bot_domain.Bot]:
        bots = (
            self.session.execute(
                select(Bot)
                .where(Bot.tenant_id == tenant_id.value)
                .options(joinedload(Bot.approach_variables))
                .execution_options(include_deleted=include_deleted)
            )
            .unique()
            .scalars()
            .all()
        )
        return [bot.to_domain(bot.approach_variables) for bot in bots]

    def find_by_id_and_tenant_id(self, id: bot_domain.Id, tenant_id: tenant_domain.Id) -> bot_domain.Bot:
        bot = (
            self.session.execute(
                select(Bot)
                .where(Bot.id == id.value)
                .where(Bot.tenant_id == tenant_id.value)
                .options(joinedload(Bot.approach_variables))
            )
            .scalars()
            .first()
        )
        if not bot:
            raise NotFound("基盤モデルまたはアシスタントが見つかりませんでした")
        return bot.to_domain(bot.approach_variables)

    def find_by_ids_and_tenant_id(
        self,
        ids: list[bot_domain.Id],
        tenant_id: tenant_domain.Id,
        statuses: list[bot_domain.Status] | None = None,
    ) -> list[bot_domain.Bot]:
        bots = (
            self.session.execute(
                select(Bot)
                .where(Bot.id.in_([bot_id.value for bot_id in ids]))
                .where(Bot.tenant_id == tenant_id.value)
                .where(Bot.status.in_(statuses if statuses is not None else [bot_domain.Status.ACTIVE]))
                .options(joinedload(Bot.approach_variables))
            )
            .unique()
            .scalars()
            .all()
        )
        return [bot.to_domain(bot.approach_variables) for bot in bots]

    def find_by_ids_and_group_id(
        self,
        bot_ids: list[bot_domain.Id],
        group_id: group_domain.Id,
        statuses: list[bot_domain.Status] | None = None,
    ):
        select_stmt = (
            select(Bot)
            .where(Bot.group_id == group_id.value)
            .where(Bot.id.in_([bot_id.value for bot_id in bot_ids]))
            .where(Bot.status.in_(statuses if statuses is not None else [bot_domain.Status.ACTIVE]))
            .options(joinedload(Bot.approach_variables))
        )
        bots = self.session.execute(select_stmt).unique().scalars().all()
        return [bot.to_domain(bot.approach_variables) for bot in bots]

    def find_by_tenant_id_and_approaches(
        self,
        tenant_id: tenant_domain.Id,
        approaches: list[bot_domain.Approach],
        exclude_ids: list[bot_domain.Id],
        statuses: list[bot_domain.Status] | None = None,
    ) -> list[bot_domain.Bot]:
        select_stmt = (
            select(Bot)
            .where(Bot.tenant_id == tenant_id.value)
            .where(Bot.id.notin_([exclude_id.value for exclude_id in exclude_ids]))
            .where(Bot.approach.in_([approach.value for approach in approaches]))
            .where(Bot.status.in_(statuses if statuses is not None else [bot_domain.Status.ACTIVE]))
            .options(joinedload(Bot.approach_variables))
        )
        bots = self.session.execute(select_stmt).unique().scalars().all()
        return [bot.to_domain(bot.approach_variables) for bot in bots]

    def find_by_group_id_and_name(self, group_id: group_domain.Id, name: bot_domain.Name) -> bot_domain.Bot:
        bot = (
            self.session.execute(
                select(Bot)
                .where(Bot.group_id == group_id.value)
                .where(Bot.name == name.value)
                .options(joinedload(Bot.approach_variables))
            )
            .scalars()
            .first()
        )
        if not bot:
            raise NotFound("基盤モデルまたはアシスタントが見つかりませんでした")

        return bot.to_domain(bot.approach_variables)

    def find_basic_ai_by_response_generator_model_family(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        model_family: ModelFamily,
        statuses: list[bot_domain.Status],
    ) -> bot_domain.Bot:
        bot = (
            self.session.execute(
                select(Bot)
                .where(Bot.approach == bot_domain.Approach.CHAT_GPT_DEFAULT.value)
                .where(Bot.tenant_id == tenant_id.value)
                .where(Bot.group_id == group_id.value)
                .where(Bot.response_generator_model_family == model_family.value)
                .where(Bot.status.in_(statuses if statuses is not None else [bot_domain.Status.ACTIVE]))
                .options(joinedload(Bot.approach_variables))
            )
            .scalars()
            .first()
        )
        if not bot:
            raise NotFound("基盤モデルが見つかりませんでした")

        return bot.to_domain(bot.approach_variables)

    def find_basic_ai_by_image_generator_model_family(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        model_family: Text2ImageModelFamily,
        statuses: list[bot_domain.Status],
    ) -> bot_domain.Bot:
        bot = (
            self.session.execute(
                select(Bot)
                .where(Bot.approach == bot_domain.Approach.TEXT_2_IMAGE.value)
                .where(Bot.tenant_id == tenant_id.value)
                .where(Bot.group_id == group_id.value)
                .where(Bot.image_generator_model_family == model_family.value)
                .where(Bot.status.in_(statuses if statuses is not None else [bot_domain.Status.ACTIVE]))
                .options(joinedload(Bot.approach_variables))
            )
            .scalars()
            .first()
        )
        if not bot:
            raise NotFound("基盤モデルが見つかりませんでした")

        return bot.to_domain(bot.approach_variables)

    def find_with_groups_by_tenant_id(
        self, tenant_id: tenant_domain.Id, statuses: list[bot_domain.Status] | None = None
    ) -> list[bot_domain.BotWithGroupName]:
        stmt = (
            select(Bot)
            .join(Group, Group.id == Bot.group_id)
            .where(Group.tenant_id == tenant_id.value)
            .where(Bot.status.in_(statuses if statuses is not None else [bot_domain.Status.ACTIVE]))
            .options(joinedload(Bot.approach_variables))
            .options(joinedload(Bot.group))
        )
        bots = self.session.execute(stmt).unique().scalars().all()
        return [bot.to_domain_with_group_name() for bot in bots]

    def find_with_groups_by_ids_and_tenant_id(
        self, ids: list[bot_domain.Id], tenant_id: tenant_domain.Id, statuses: list[bot_domain.Status] | None = None
    ) -> list[bot_domain.BotWithGroupName]:
        stmt = (
            select(Bot)
            .join(Group, Group.id == Bot.group_id)
            .where(Group.tenant_id == tenant_id.value)
            .where(Bot.id.in_([bot_id.value for bot_id in ids]))
            .where(Bot.status.in_(statuses if statuses is not None else [bot_domain.Status.ACTIVE]))
            .options(joinedload(Bot.approach_variables))
            .options(joinedload(Bot.group))
        )
        bots = self.session.execute(stmt).unique().scalars().all()
        return [bot.to_domain_with_group_name() for bot in bots]

    def create(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        bot: bot_domain.BotForCreate,
    ) -> bot_domain.Bot:
        new_bot = Bot.from_domain(tenant_id=tenant_id, group_id=group_id, bot=bot)

        try:
            self.session.add(new_bot)
            self.session.flush()

            for var in bot.approach_variables:
                self._create_approach_variable(
                    session=self.session,
                    bot_id=bot_domain.Id(value=new_bot.id),
                    var=var,
                )
            self.session.commit()

            return new_bot.to_domain(new_bot.approach_variables)
        except Exception as e:
            self.session.rollback()
            raise e

    def update(self, bot: bot_domain.Bot) -> None:
        update_stmt = (
            update(Bot)
            .where(Bot.id == bot.id.value)
            .values(
                name=bot.name.value,
                description=bot.description.value,
                approach=bot.approach.value,
                example_questions=[example_question.value for example_question in bot.example_questions],
                search_method=bot.search_method.value if bot.search_method else None,
                response_generator_model_family=bot.response_generator_model_family.value,
                image_generator_model_family=(
                    bot.image_generator_model_family.value if bot.image_generator_model_family else None
                ),
                pdf_parser=bot.pdf_parser.value if bot.pdf_parser else None,
                enable_web_browsing=bot.enable_web_browsing.root,
                enable_follow_up_questions=bot.enable_follow_up_questions.root,
                status=bot.status.value,
                icon_url=bot.icon_url.root if bot.icon_url else None,
                icon_color=bot.icon_color.root,
                max_conversation_turns=bot.max_conversation_turns.root if bot.max_conversation_turns else None,
            )
        )

        current_approach_variables = (
            self.session.execute(select(ApproachVariable).filter_by(bot_id=bot.id.value)).scalars().all()
        )

        # 既存の変数名のリストを作成
        existing_var_names = [var.name for var in current_approach_variables]

        # 新しい変数を追加または更新
        for new_var in bot.approach_variables:
            # 既存の変数を更新
            if new_var.name.value in existing_var_names:
                for existing_variable in current_approach_variables:
                    if existing_variable.name == new_var.name.value:
                        existing_variable.value = new_var.value.value
                        break
            else:
                # 新しい変数を追加
                self._create_approach_variable(
                    session=self.session,
                    bot_id=bot.id,
                    var=new_var,
                )

        # 不要な変数を削除
        for existing_var in current_approach_variables:
            if existing_var.name not in [var.name.value for var in bot.approach_variables]:
                self._delete_approach_variable(
                    session=self.session,
                    bot_id=bot.id,
                    var_name=approach_variable_domain.Name(value=existing_var.name),
                )

        try:
            self.session.execute(update_stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def _create_approach_variable(
        self,
        session: Session,
        bot_id: bot_domain.Id,
        var: approach_variable_domain.ApproachVariable,
    ) -> None:
        approach_variable = ApproachVariable.from_domain(bot_id=bot_id, approach_variable=var)
        session.add(approach_variable)

    def _delete_approach_variable(
        self,
        session: Session,
        bot_id: bot_domain.Id,
        var_name: approach_variable_domain.Name,
    ) -> None:
        approach_variable = (
            self.session.execute(
                select(ApproachVariable).filter_by(bot_id=bot_id.value).filter_by(name=var_name.value)
            )
            .scalars()
            .first()
        )
        if not approach_variable:
            raise NotFound("アプローチ変数が見つかりませんでした")
        session.delete(approach_variable)

    def delete(self, bot_id: bot_domain.Id) -> None:
        now = datetime.now(timezone.utc)
        bot = self.session.execute(select(Bot).where(Bot.id == bot_id.value)).scalars().first()
        if not bot:
            raise NotFound("基盤モデルまたはアシスタントが見つかりませんでした")
        bot.deleted_at = now

        approach_variables = (
            self.session.execute(select(ApproachVariable).filter_by(bot_id=bot_id.value)).scalars().all()
        )
        for approach_variable in approach_variables:
            approach_variable.deleted_at = now

        try:
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise e
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_tenant_id(self, tenant_id: tenant_domain.Id) -> None:
        try:
            self.session.execute(delete(Bot).where(Bot.tenant_id == tenant_id.value).where(Bot.deleted_at.isnot(None)))
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_prompt_template_by_id_and_bot_id(
        self,
        bot_id: bot_domain.Id,
        bot_prompt_template_id: BotPromptTemplateId,
    ) -> bot_domain.PromptTemplate:
        prompt_template = (
            self.session.execute(
                select(BotPromptTemplate).filter_by(id=bot_prompt_template_id.root).filter_by(bot_id=bot_id.value)
            )
            .scalars()
            .first()
        )
        if not prompt_template:
            raise NotFound("質問例が見つかりませんでした")

        return prompt_template.to_domain()

    def find_prompt_templates_by_bot_id(
        self,
        bot_id: bot_domain.Id,
    ) -> list[bot_domain.PromptTemplate]:
        prompt_templates = (
            self.session.execute(select(BotPromptTemplate).filter_by(bot_id=bot_id.value)).scalars().all()
        )
        return [prompt_template.to_domain() for prompt_template in prompt_templates]

    def create_prompt_template(
        self,
        bot_id: bot_domain.Id,
        prompt_template: bot_domain.PromptTemplateForCreate,
    ) -> PromptTemplate:
        new_prompt_template = BotPromptTemplate.from_domain(
            domain_model=prompt_template,
            bot_id=bot_id,
        )

        try:
            self.session.add(new_prompt_template)
            self.session.commit()
            return new_prompt_template.to_domain()
        except Exception as e:
            self.session.rollback()
            raise e

    def update_prompt_template(self, bot_id: bot_domain.Id, prompt_template: bot_domain.PromptTemplate) -> None:
        try:
            update_stmt = (
                update(BotPromptTemplate)
                .where(BotPromptTemplate.id == prompt_template.id.root)
                .where(BotPromptTemplate.bot_id == bot_id.value)
                .values(
                    title=prompt_template.title.root,
                    description=prompt_template.description.root if prompt_template.description else "",
                    prompt=prompt_template.prompt.root,
                )
            )
            self.session.execute(update_stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_prompt_templates(
        self,
        bot_id: bot_domain.Id,
        bot_prompt_template_ids: list[BotPromptTemplateId],
    ) -> None:
        try:
            # 質問例IDのリストを取得
            prompt_template_ids = [bot_prompt_template_id.root for bot_prompt_template_id in bot_prompt_template_ids]
            # 一括で削除対象の質問例を取得
            prompt_templates = (
                self.session.execute(
                    select(BotPromptTemplate)
                    .filter_by(bot_id=bot_id.value)
                    .where(BotPromptTemplate.id.in_(prompt_template_ids))
                )
                .scalars()
                .all()
            )

            # 取得した質問例を一括で削除
            for prompt_template in prompt_templates:
                self.session.delete(prompt_template)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_prompt_templates_by_bot_id(self, bot_id: bot_domain.Id) -> None:
        prompt_templates = (
            self.session.execute(select(BotPromptTemplate).where(BotPromptTemplate.bot_id == bot_id.value))
            .scalars()
            .all()
        )

        now = datetime.now(timezone.utc)
        for prompt_template in prompt_templates:
            prompt_template.deleted_at = now

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def add_liked_bot(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        user_id: user_domain.Id,
    ) -> None:
        bot = (
            self.session.execute(select(Bot).where(Bot.id == bot_id.value).where(Bot.tenant_id == tenant_id.value))
            .scalars()
            .first()
        )
        if not bot:
            raise NotFound("基盤モデルまたはアシスタントが見つかりませんでした")

        new_user_liked_bot = UserLikedBot.from_domain(user_id=user_id, bot_id=bot_id)
        try:
            self.session.add(new_user_liked_bot)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def remove_liked_bot(self, bot_id: bot_domain.Id, user_id: user_domain.Id) -> None:
        user_liked_bot = (
            self.session.execute(
                select(UserLikedBot).where(
                    UserLikedBot.user_id == user_id.value,
                    UserLikedBot.bot_id == bot_id.value,
                )
            )
            .scalars()
            .first()
        )
        if not user_liked_bot:
            raise NotFound("基盤モデルまたはアシスタントが見つかりませんでした")

        try:
            self.session.delete(user_liked_bot)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_liked_bot_ids_by_user_id(self, user_id: user_domain.Id) -> list[bot_domain.Id]:
        liked_bots = (
            self.session.execute(select(UserLikedBot).where(UserLikedBot.user_id == user_id.value)).scalars().all()
        )
        return [bot_domain.Id(value=user_liked_bot.bot_id) for user_liked_bot in liked_bots]

    def find_by_group_id(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        statuses: list[bot_domain.Status] | None = None,
    ) -> list[bot_domain.Bot]:
        stmt = self.session.execute(
            select(Bot)
            .join(Group, Group.id == Bot.group_id)
            .where(Group.tenant_id == tenant_id.value)
            .where(Bot.group_id == group_id.value)
            .where(Bot.status.in_(statuses if statuses is not None else [bot_domain.Status.ACTIVE]))
            .options(joinedload(Bot.approach_variables))
        )
        bots = stmt.unique().scalars().all()
        return [bot.to_domain(bot.approach_variables) for bot in bots]

    def update_bot_group(self, bot_id: bot_domain.Id, group_id: group_domain.Id):
        try:
            stmt = update(Bot).where(Bot.id == bot_id.value).values(group_id=group_id.value)
            self.session.execute(stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
