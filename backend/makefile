EXEC := docker compose exec api poetry run

.PHONY: install
install:
	docker compose exec api poetry install --no-root

.PHONY: lint
lint:
	$(EXEC) ruff format --check
	$(EXEC) ruff check
	$(EXEC) mypy -p api
	$(EXEC) mypy -p tests

.PHONY: format
format:
	$(EXEC) ruff format
	$(EXEC) ruff check --select I --fix

.PHONY: test
test:
	$(EXEC) pytest $(args)

.PHONY: revision
revision:
	$(EXEC) alembic revision -m "$(m)"

.PHONY: migrate
migrate:
	$(EXEC) alembic upgrade head

.PHONY: migrate/rollback
migrate/rollback:
	$(EXEC) alembic downgrade -1

.PHONY: seed
seed:
	sh scripts/seed.sh

.PHONY: oapigen
oapigen:
	$(EXEC) python -m api.commands.create_openapi_schema

.PHONY: validate-openapi
validate-openapi:
	$(EXEC) openapi-spec-validator api/controllers/api/openapi/openapi.yml
	$(EXEC) openapi-spec-validator api/controllers/backend_api/openapi/openapi.yml
	$(EXEC) openapi-spec-validator api/controllers/administrator_api/openapi/openapi.yml
