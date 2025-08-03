init:
	docker compose up db azurite -d
	sleep 10
	make setup-azurite
	docker compose up --build -d
	cd backend && make seed
	cd frontend && npm install

up:
	docker compose up -d
	make oapigen
	cd frontend && npm install && npm run dev

stop:
	docker compose stop

reset:
	docker compose down
	rm -rf ./data
	rm -rf ./azurite
	make init

format: format/backend format/frontend format/function

format/backend:
	cd backend && make format

format/frontend:
	cd frontend && npm run format

format/function:
	cd function && make format

lint: lint/backend lint/frontend lint/function

lint/backend:
	cd backend && make lint

lint/frontend:
	cd frontend && npm run lint:fix

lint/function:
	cd function && make lint

test: test/backend

test/backend:
	cd backend && make test

oapigen: oapigen/server oapigen/client

oapigen/server:
	cd backend && make oapigen

oapigen/client:	oapigen/client/api oapigen/client/backend-api oapigen/client/administrator-api

oapigen/client/api:
	cd frontend && npm run orval:api

oapigen/client/backend-api:
	cd frontend && npm run orval:backend-api

oapigen/client/administrator-api:
	cd frontend && npm run orval:administrator-api

setup-azurite:
	sh ./scripts/setup-azurite.sh

decrypt-env:
	sh ./scripts/decrypt-env.sh

encrypt-env:
	sh ./scripts/encrypt-env.sh $(packages)

# Usage: make send-message message='{"tenant_id": 1, "bot_id": 1, "document_id": 1}' queue='documents-process-queue'
.PHONY: send-message
send-message:
	$(eval ENCODED_TEXT := $(shell printf '%s' '${message}' | base64))
	@az storage message put --content '$(ENCODED_TEXT)' --queue-name '${queue}' --connection-string 'DefaultEndpointsProtocol=http;AccountName=stbatchlocal;AccountKey=c3RiYXRjaGxvY2Fsa2V5;QueueEndpoint=http://localhost:10001/stbatchlocal;'
