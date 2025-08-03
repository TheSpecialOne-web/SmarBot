with
    user_count as (
        select
            tenant_id
            , count(id) as user_count
        from users
        where deleted_at is null
        group by tenant_id
    )
    , group_count as (
        select
            tenant_id
            , count(id) as group_count
        from groups
        where deleted_at is null
        group by tenant_id
    )
    , bot_count as (
        select
            groups.tenant_id
            , count(bots.id) as bot_count
        from groups
        join bots
            on groups.id = bots.group_id
        where groups.deleted_at is null
            and bots.deleted_at is null
            and bots.archived_at is null
        group by groups.tenant_id
    )
insert into tenant_model
select
    tenants.id as tenant_id
    , name
    , user_count
    , group_count
    , bot_count
    , alias
    , enable_document_intelligence
    , enable_llm_document_reader
    , enable_url_scraping
    , enable_api_integrations
    , enable_basic_ai_web_browsing
    , free_token_limit
    , additional_token_limit
    , free_storage_limit
    , additional_storage_limit
    , free_user_seat_limit
    , additional_user_seat_limit
    , document_intelligence_page_limit
    , max_attachment_token
    , allowed_model_families
    , basic_ai_max_conversation_turns
    , basic_ai_pdf_parser
    , allow_foreign_region
    , additional_platforms
    , status
    , created_at
    , updated_at
    , deleted_at
from tenants
left join user_count
    on tenants.id = user_count.tenant_id
left join group_count
    on tenants.id = group_count.tenant_id
left join bot_count
    on tenants.id = bot_count.tenant_id
where tenants.id is not null
