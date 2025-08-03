import uuid

from psycopg2.extensions import connection as Connection

DOCUMENT_FOLDERS = "document_folders"


def create_root_document_folder(conn: Connection, bot_id: int) -> str:
    id = str(uuid.uuid4())
    cur = conn.cursor()

    try:
        cur.execute(
            f"""
            INSERT INTO {DOCUMENT_FOLDERS} (id, bot_id, name) VALUES (%s, %s, %s)
        """,
            (
                id,
                bot_id,
                None,
            ),
        )
        conn.commit()
    except Exception as e:
        raise e
    finally:
        cur.close()

    return id
