insert into conversation_turn_model
select
    tenants.id as tenant_id
    , tenants.name as tenant_name
    , conversations.id as conversation_id
    , conversation_turns.id as conversation_turn_id
    , title as conversation_title
    , row_number() over (partition by conversations.id order by conversation_turns.created_at) as turn_number
    , token_count
    , users.id as user_id
    , users.name as user_name
    , bots.id as bot_id
    , bots.name as bot_name
    , approach as bot_approach
    , response_generator_model_family
    , groups.id as group_id
    , groups.name as group_name
    , groups.is_general as is_general_group
    , queries
    , evaluation
    , conversation_turns.created_at::date as created_date
    , conversation_turns.created_at
    , conversations.created_at as conversation_created_at
    , conversations.deleted_at as conversation_deleted_at
from conversations
join conversation_turns
    on conversation_turns.conversation_id = conversations.id
left join bots
    on bots.id = conversations.bot_id
left join groups
    on groups.id = bots.group_id
left join users
    on users.id = conversations.user_id
left join tenants
    on users.tenant_id = tenants.id
        and groups.tenant_id = tenants.id
where tenants.id is not null
order by created_date desc
