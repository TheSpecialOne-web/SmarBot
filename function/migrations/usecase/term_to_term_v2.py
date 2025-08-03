from collections import defaultdict

from migrations.infrastructure.postgres import (
    create_term_v2,
    get_bots_by_tenant_id,
    get_tenants,
    get_terms_by_bot_id,
)


def migrate_term_to_term_v2():
    print("start migrate term to term v2")
    for tenant in get_tenants():
        bots = get_bots_by_tenant_id(tenant_id=tenant.id)
        for bot in bots:
            terms = get_terms_by_bot_id(bot_id=bot.id)
            # 同じdescriptionのtermをグループ化
            grouped_terms = defaultdict(list)
            for term in terms:
                grouped_terms[term.description].append(term.name)
            # グループ化したtermから term_v2を作成
            for description, names in grouped_terms.items():
                create_term_v2(bot_id=bot.id, names=names, description=description)
    print("finish migrate term to term v2")
