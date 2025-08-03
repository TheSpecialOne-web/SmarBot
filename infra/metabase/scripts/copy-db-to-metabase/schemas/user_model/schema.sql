drop table if exists user_model;

create table user_model (
    tenant_id int not null
    , tenant_name text
    , user_id int
    , name text
    , email text
    , roles text[]
    , group_count int
    , liked_bot_count int
    , created_at timestamp
    , updated_at timestamp
    , deleted_at timestamp
    , tenant_deleted_at timestamp
);
