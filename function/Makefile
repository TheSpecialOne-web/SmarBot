EXEC := docker compose exec function poetry run

.PHONY: lint
lint:
	$(EXEC) ruff format --check
	$(EXEC) ruff check
	$(EXEC) mypy .

.PHONY: format
format:
	$(EXEC) ruff format
	$(EXEC) ruff check --select I --fix

