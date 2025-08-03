drop table if exists conversation_turn_model;

create table conversation_turn_model (
    tenant_id int not null
    , tenant_name text
    , conversation_id uuid
    , conversation_turn_id uuid
    , conversation_title text
    , turn_number int
    , token_count int
    , user_id int
    , user_name text
    , bot_id int
    , bot_name text
    , bot_approach text
    , response_generator_model_family text
    , group_id int
    , group_name text
    , is_general_group boolean
    , queries text[]
    , evaluation text
    , created_date date
    , conversation_turn_created_at timestamp
    , conversation_created_at timestamp
    , conversation_deleted_at timestamp
);
