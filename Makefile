.PHONY: help dev dev-down build test lint format clean migrate seed deploy

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Sobe ambiente de desenvolvimento
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Ambiente dev iniciado!"
	@echo "📖 API Docs: http://localhost:8000/docs"
	@echo "🔍 Meilisearch: http://localhost:7700"

dev-down: ## Para ambiente de desenvolvimento
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## Mostra logs do ambiente dev
	docker-compose -f docker-compose.dev.yml logs -f

build: ## Build das imagens Docker
	docker build -t cmdgen-api:latest -f Dockerfile .
	docker build -t cmdgen-cli:latest -f cli/Dockerfile ./cli

migrate: ## Executa migrações Alembic
	alembic upgrade head

migrate-create: ## Cria nova migração
	@read -p "Nome da migração: " name; \
	alembic revision --autogenerate -m "$$name"

seed: ## Carrega seeds no banco
	python seeds/load_seeds.py

install: ## Instala dependências localmente
	pip install -r api/requirements.txt
	pip install -r cli/requirements.txt

lint: ## Verifica código com flake8
	flake8 api/ cli/ --max-line-length=120 --exclude=__pycache__,venv,env

format: ## Formata código com black
	black api/ cli/ --line-length=120

test: ## Executa testes
	pytest tests/ -v

clean: ## Remove arquivos temporários
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov

deploy: ## Deploy em produção (Docker Swarm)
	@echo "🚀 Deploying to Swarm..."
	docker stack deploy -c deploy/stack.yml cmdgen
	@echo "✅ Deploy concluído!"
	@echo "📊 Verifique: docker service ls | grep cmdgen"

status: ## Status dos serviços
	docker service ls | grep cmdgen

logs: ## Logs da API em produção
	docker service logs -f --tail=100 cmdgen_api

backup: ## Executa backup do banco
	bash deploy/scripts/backup.sh

reindex: ## Reindexar Meilisearch
	bash deploy/scripts/reindex_meili.sh

# Comandos CLI
cli-search: ## Busca via CLI (ex: make cli-search Q="docker")
	python cli/cmdgen.py search "${Q}"

cli-health: ## Health check via CLI
	python cli/cmdgen.py health
