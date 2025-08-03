drop table if exists tenant_model;

create table tenant_model (
    tenant_id int not null
    , name text
    , user_count int
    , group_count int
    , bot_count int
    , alias text
    , enable_document_intelligence boolean
    , enable_llm_document_reader boolean
    , enable_url_scraping boolean
    , enable_api_integrations boolean
    , enable_basic_ai_web_browsing boolean
    , free_token_limit bigint
    , additional_token_limit bigint
    , free_storage_limit bigint
    , additional_storage_limit bigint
    , free_user_seat_limit int
    , additional_user_seat_limit int
    , document_intelligence_page_limit int
    , max_attachment_token int
    , allowed_model_families text[]
    , basic_ai_max_conversation_turns int
    , basic_ai_pdf_parser text
    , allow_foreign_region boolean
    , additional_platforms text[]
    , status text
    , created_at timestamp
    , updated_at timestamp
    , deleted_at timestamp
);
