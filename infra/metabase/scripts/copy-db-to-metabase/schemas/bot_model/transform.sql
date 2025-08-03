with
    liked_count as (
        select
            bot_id
            , count(user_id) as count
        from users_liked_bots
        group by bot_id
    )
insert into bot_model
select
    tenants.id as tenant_id
    , tenants.name as tenant_name
    , bots.id as bot_id
    , bots.name
    , description
    , approach
    , enable_web_browsing
    , enable_follow_up_questions
    , max_conversation_turns
    , response_generator_model_family
    , image_generator_model_family
    , icon_url
    , icon_color
    , bots.status
    , bots.created_at
    , bots.updated_at
    , bots.archived_at
    , bots.deleted_at
    , liked_count.count as liked_count
    , tenants.created_at as tenant_created_at
    , tenants.deleted_at as tenant_deleted_at
    , groups.id as group_id
    , groups.name as group_name
    , groups.is_general as is_general_group
    , groups.created_at as group_created_at
    , groups.deleted_at as group_deleted_at
from tenants
left join groups
    on groups.tenant_id = tenants.id
left join bots
    on bots.group_id = groups.id
left join liked_count
    on bots.id = liked_count.bot_id
where tenants.id is not null
