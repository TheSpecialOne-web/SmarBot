drop table if exists bot_model;

create table bot_model (
    tenant_id int not null
    , tenant_name text
    , bot_id int
    , name text
    , description text
    , approach text
    , enable_web_browsing boolean
    , enable_follow_up_questions boolean
    , max_conversation_turns int
    , response_generator_model_family text
    , image_generator_model_family text
    , icon_url text
    , icon_color text
    , status text
    , created_at timestamp
    , updated_at timestamp
    , archived_at timestamp
    , deleted_at timestamp
    , liked_count int
    , tenant_created_at timestamp
    , tenant_deleted_at timestamp
    , group_id int
    , group_name text
    , is_general_group boolean
    , group_created_at timestamp
    , group_deleted_at timestamp
);
