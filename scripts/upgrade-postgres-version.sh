#!/bin/bash
DB_CONTAINER_NAME="db"
POSTGRES_USER="postgres"
POSTGRES_DB="neosmartchat"

# Dump
docker compose exec $DB_CONTAINER_NAME pg_dumpall -c -U $POSTGRES_USER > dump.sql 2>dump_error.log
if [ -s dump_error.log ]; then
    echo "Error during dump:"
    cat dump_error.log
    exit 1
fi

# Modify dump file
sed '/DROP DATABASE/d; /CREATE DATABASE/d; /DROP ROLE/d; /CREATE ROLE/d; /ALTER ROLE/d' dump.sql > dump_modified.sql

docker compose down --volumes --remove-orphans

mv data/ data_backup/

docker compose pull
docker compose up -d $DB_CONTAINER_NAME

sleep 15

# Restore
cat dump_modified.sql | docker compose exec -i $DB_CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB -v ON_ERROR_STOP=1 > restore.log 2>&1

if grep -qi "error" restore.log; then
    echo "Error during restore:"
    cat restore.log
    exit 1
fi

docker compose exec $DB_CONTAINER_NAME cp /var/lib/postgresql/data/pg_hba.conf /var/lib/postgresql/data/pg_hba.conf.bak

docker compose exec $DB_CONTAINER_NAME sed -i 's/scram-sha-256/trust/g' /var/lib/postgresql/data/pg_hba.conf

docker compose restart $DB_CONTAINER_NAME

sleep 15

docker compose exec $DB_CONTAINER_NAME psql -U $POSTGRES_USER -c "ALTER USER $POSTGRES_USER WITH PASSWORD 'postgres';"

docker compose exec $DB_CONTAINER_NAME mv /var/lib/postgresql/data/pg_hba.conf.bak /var/lib/postgresql/data/pg_hba.conf

docker compose restart $DB_CONTAINER_NAME

sleep 15

docker compose exec $DB_CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"

# Cleanup
rm dump.sql
rm dump_modified.sql

echo "🎉 Completed."
