from psycopg2.extensions import connection as Connection


def set_document_folder_id_to_documents(conn: Connection, bot_id: int, folder_id: str):
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE documents
            SET document_folder_id = %s
            WHERE bot_id = %s AND deleted_at IS NULL
        """,
            (folder_id, bot_id),
        )
        conn.commit()
    except Exception as e:
        raise e
    finally:
        cur.close()
