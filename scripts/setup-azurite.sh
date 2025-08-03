#!/bin/bash

# 共通の接続文字列を変数に格納
BATCH_STORAGE_QUEUE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=stbatchlocal;AccountKey=c3RiYXRjaGxvY2Fsa2V5;QueueEndpoint=http://localhost:10001/stbatchlocal;"
BATCH_STORAGE_BLOB_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=stbatchlocal;AccountKey=c3RiYXRjaGxvY2Fsa2V5;BlobEndpoint=http://localhost:10000/stbatchlocal;"
PUBLIC_STORAGE_BLOB_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=stpubliclocal;AccountKey=c3RwdWJsaWNsb2NhbGtleQ==;BlobEndpoint=http://localhost:10000/stpubliclocal;"

# キューのリスト
queues=(
    "alert-capacity-queue"
    "backup-index-queue"
    "calculate-storage-usage-queue"
    "sync-document-name-queue"
    "convert-and-upload-pdf-document-queue"
    "create-chat-completion-export-queue"
    "create-conversation-export-queue"
    "create-embeddings-queue"
    "delete-attachments-queue"
    "delete-bot-queue"
    "delete-document-folders-queue"
    "delete-multiple-documents-queue"
    "delete-tenant-queue"
    "documents-process-queue"
    "migration-queue"
    "restore-index-queue"
    "upload-question-answers-queue"
    "users-import-queue"
    "sync-document-path-queue"
    "sync-document-location-queue"
    "start-external-data-connection-queue"
    "upload-external-documents-queue"
)

# コンテナのリスト
containers=(
    "users-import-container"
)

# キューの作成
for queue in "${queues[@]}"; do
    echo "Creating queue: $queue"
    az storage queue create --name "$queue" --connection-string "$BATCH_STORAGE_QUEUE_CONNECTION_STRING"
done

# コンテナの作成
for container in "${containers[@]}"; do
    echo "Creating container: $container"
    az storage container create --name "$container" --connection-string "$BATCH_STORAGE_BLOB_CONNECTION_STRING"
done

# 共通のコンテナを作成
echo "Creating container: common-container"
az storage container create --name "common-container" --connection-string "$PUBLIC_STORAGE_BLOB_CONNECTION_STRING" --public-access blob
