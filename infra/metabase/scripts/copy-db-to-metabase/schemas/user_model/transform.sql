with
    group_count as (
        select
            users_groups.user_id
            , count(groups.id) as count
        from users_groups
        join groups
            on groups.id = users_groups.group_id
        where users_groups.deleted_at is null
            and groups.deleted_at is null
        group by users_groups.user_id
    )
    , liked_bot_count as (
        select
            users_liked_bots.user_id
            , count(bots.id) as count
        from users_liked_bots
        join bots
            on bots.id = users_liked_bots.bot_id
        where bots.deleted_at is null
        group by users_liked_bots.user_id
    )
insert into user_model
select
    tenants.id as tenant_id
    , tenants.name as tenant_name
    , users.id as user_id
    , users.name
    , users.email
    , users.roles
    , coalesce(group_count.count, 0) as group_count
    , coalesce(liked_bot_count.count, 0) as liked_bot_count
    , users.created_at
    , users.updated_at
    , users.deleted_at
    , tenants.deleted_at as tenant_deleted_at
from users
join tenants
    on tenants.id = users.tenant_id
left join group_count
    on group_count.user_id = users.id
left join liked_bot_count
    on liked_bot_count.user_id = users.id
where tenants.id is not null
