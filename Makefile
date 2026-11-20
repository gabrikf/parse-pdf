# Root commands. `make bootstrap` takes a fresh clone to a running app; see scripts/bootstrap.sh.
.DEFAULT_GOAL := help
.PHONY: help bootstrap up down logs ps

help: ## List the commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

bootstrap: ## Check Docker, prepare .env, pull, build, start everything and wait until healthy
	@bash scripts/bootstrap.sh $(ARGS)

up: bootstrap ## Same as bootstrap

down: ## Stop every service (data stays in the Docker volumes)
	docker compose down

logs: ## Follow the logs of every service
	docker compose logs -f --tail=100

ps: ## Show each service and its health
	docker compose ps
