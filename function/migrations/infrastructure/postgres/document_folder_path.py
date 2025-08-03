import uuid

from psycopg2.extensions import connection as Connection

DOCUMENT_FOLDER_PATHS = "document_folder_paths"


def create_root_document_folder_path(conn: Connection, folder_id: str) -> None:
    cur = conn.cursor()

    try:
        cur.execute(
            f"""
            INSERT INTO {DOCUMENT_FOLDER_PATHS} (id, ancestor_document_folder_id, descendant_document_folder_id, path_length) VALUES (%s, %s, %s, %s)
        """,
            (str(uuid.uuid4()), folder_id, folder_id, 0),
        )
        conn.commit()
    except Exception as e:
        raise e
    finally:
        cur.close()
