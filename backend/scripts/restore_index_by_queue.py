import base64
import os

from azure.storage.queue import QueueServiceClient
import click
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from pydantic import BaseModel

load_dotenv()

db_host = os.environ.get("DB_HOST", "")
db_name = os.environ.get("DB_NAME", "")
db_user = os.environ.get("DB_USER", "")
password = os.environ.get("DB_PASSWORD")

dsn = f"postgresql://{db_user}:{password}@{db_host}/{db_name}?client_encoding=utf8"

sql = """
SELECT d.id document_id, b.id bot_id, t.id tenant_id
FROM documents d
JOIN document_folders df ON d.document_folder_id = df.id
JOIN bots b ON df.bot_id = b.id
JOIN groups g ON b.group_id = g.id
JOIN tenants t ON g.tenant_id = t.id
WHERE t.id = %s AND t.deleted_at IS NULL AND g.deleted_at IS NULL AND b.deleted_at IS NULL AND df.deleted_at IS NULL AND d.deleted_at IS NULL
"""


class DocumentProcessQueueMessage(BaseModel):
    tenant_id: int
    bot_id: int
    document_id: int


QUEUE_CONNECTION_STRING = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;QueueEndpoint=http://azurite:10001/devstoreaccount1;"


@click.command()
@click.option("--tenant-id", type=int, required=True)
def main(tenant_id: int):
    """
    インデックスを再構築するためのキューを送信する関数
    ストレージにドキュメントが残っている場合に使用できる
    """
    queue_messages: list[DocumentProcessQueueMessage] = []
    conn = psycopg2.connect(dsn)
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute(sql, (tenant_id,))
        rows = cur.fetchall()
        for row in rows:
            queue_messages.append(DocumentProcessQueueMessage(**row))
    queue_client = QueueServiceClient.from_connection_string(QUEUE_CONNECTION_STRING).get_queue_client(
        "documents-process-queue"
    )
    for message in queue_messages:
        base64_message = base64.b64encode(message.model_dump_json().encode("utf-8")).decode("utf-8")
        queue_client.send_message(base64_message)
    print(f"Send {len(queue_messages)} messages")


if __name__ == "__main__":
    main()
