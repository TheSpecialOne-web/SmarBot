FROM postgres:16

RUN apt update && apt install -y curl jq postgresql-client-16

COPY . .
RUN chmod +x ./copy-db.sh

CMD ["./copy-db.sh"]
