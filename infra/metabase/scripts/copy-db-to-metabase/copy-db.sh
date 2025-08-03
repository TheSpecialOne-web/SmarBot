#!/bin/bash

# MSI Endpoint
URL="$IDENTITY_ENDPOINT?resource=https%3A%2F%2Fossrdbms-aad.database.windows.net&api-version=2019-08-01&client_id=$IDENTITY"

# Get Access Token
export PGPASSWORD=$(curl -s $URL -H "x-identity-header: $IDENTITY_HEADER" | jq -r .access_token)
if [ $? -ne 0 ] || [ -z "$PGPASSWORD" ]; then
    echo "ERROR: Failed to obtain access token"
    exit 1
fi
echo "INFO: Access Token is obtained"

# Backup
pg_dump "host=$SOURCE_SERVER.postgres.database.azure.com \
    port=5432 \
    dbname=$SOURCE_DATABASE \
    user=$SOURCE_USERNAME \
    sslmode=require" \
    -F c -f backup.dump
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create backup"
    exit 1
fi
echo "INFO: Backup is created"

# Restore
export PGPASSWORD=$TARGET_PASSWORD
pg_restore -h $TARGET_SERVER.postgres.database.azure.com \
    -U $TARGET_USERNAME \
    -d $TARGET_DATABASE \
    backup.dump \
    --no-acl --no-owner --clean
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to restore backup"
    exit 1
fi
echo "INFO: Restore is completed"

# Delete backup file
rm backup.dump
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to delete backup file"
    exit 1
fi
echo "INFO: Backup file deleted"

# Apply schema.sql and transform.sql
SCHEMAS_DIR="./schemas"
KEEP_TABLES=()
for DIR in "$SCHEMAS_DIR"/*/; do
    if [ -d "$DIR" ]; then
        for FILE in "$DIR"schema.sql "$DIR"transform.sql; do
            if [ -f "$FILE" ]; then
                FILE_BASENAME=$(basename "$FILE")
                DIRECTORY_NAME=$(basename "$DIR")
                KEEP_TABLES+=("$DIRECTORY_NAME")

                echo "INFO: Applying $FILE_BASENAME in $DIRECTORY_NAME..."
                psql -h "$TARGET_SERVER.postgres.database.azure.com" \
                    -U "$TARGET_USERNAME" \
                    -d "$TARGET_DATABASE" \
                    -f "$FILE"

                if [ $? -ne 0 ]; then
                    echo "ERROR: Failed to apply $FILE_BASENAME in $DIRECTORY_NAME."
                    exit 1
                fi
            fi
        done
    fi
done
echo "INFO: Data transformation is completed"

# Delete tables not in schemas
echo "INFO: Deleting tables not defined in schemas directory..."

# Get list of all tables in the target database
ALL_TABLES=$(psql -h "$TARGET_SERVER.postgres.database.azure.com" \
    -U "$TARGET_USERNAME" \
    -d "$TARGET_DATABASE" \
    -t -c "SELECT tablename FROM pg_tables WHERE schemaname='public';")

# Drop tables not in the keep list
for TABLE in $ALL_TABLES; do
    if [[ ! " ${KEEP_TABLES[@]} " =~ " ${TABLE} " ]]; then
        echo "INFO: Dropping table $TABLE..."
        psql -h "$TARGET_SERVER.postgres.database.azure.com" \
            -U "$TARGET_USERNAME" \
            -d "$TARGET_DATABASE" \
            -c "DROP TABLE IF EXISTS $TABLE CASCADE;"
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to drop table $TABLE."
            exit 1
        fi
    fi
done

echo "INFO: Tables not in schemas directory have been deleted"
