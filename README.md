# 🚀 Gerador de Comandos

**API FastAPI + CLI Python + Postgres + Meilisearch para gerenciar comandos reutilizáveis**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Swarm-2496ED?logo=docker)](https://www.docker.com/)
[![Meilisearch](https://img.shields.io/badge/Meilisearch-v1.12-FF5CAA)](https://www.meilisearch.com/)

---

## 📖 Visão Geral

Sistema completo para **armazenar, buscar e executar comandos** de forma inteligente. Ideal para DevOps, SRE e desenvolvedores que precisam gerenciar bibliotecas de comandos complexos.

### ✨ Funcionalidades

- 🔍 **Busca Fuzzy**: Meilisearch com tolerância a erros de digitação
- 📝 **Templates Dinâmicos**: Substitui variáveis `${VAR}` com validação
- 🛡️ **Dry-Run**: Valida comandos sem executar (Docker/Postgres)
- 📦 **CRUD Completo**: API REST para gerenciar comandos
- 🖥️ **CLI Interativa**: Busca e renderiza via linha de comando
- 🐳 **Deploy Swarm**: Produção com Traefik + SSL automático
- 💾 **Backup Automatizado**: Scripts prontos para cron
- 🔄 **Migrações**: Alembic para evolução de schema

---

## 🏗️ Arquitetura

```
┌─────────────┐
│   CLI       │  (Typer)
│  cmdgen.py  │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────┐
│  FastAPI API                    │
│  ┌─────────┐  ┌──────────────┐ │
│  │ CRUD    │  │ Render       │ │
│  │ /search │  │ /dry-run     │ │
│  └─────────┘  └──────────────┘ │
└────┬──────────────┬─────────────┘
     │              │
     ▼              ▼
┌─────────┐   ┌────────────┐
│Postgres │   │Meilisearch │
│(Dados)  │   │  (Busca)   │
└─────────┘   └────────────┘
```

---

## 🚀 Quick Start

### Desenvolvimento Local

```bash
# 1. Clone
git clone <repo>
cd Arquivos

# 2. Suba ambiente
docker-compose -f docker-compose.dev.yml up -d

# 3. Execute migrações
pip install -r api/requirements.txt
alembic upgrade head

# 4. Carregue seeds
pip install pyyaml httpx
python seeds/load_seeds.py

# 5. Teste API
curl http://localhost:8000/healthz

# 6. Teste CLI
pip install -r cli/requirements.txt
python cli/cmdgen.py search docker
```

**Acesse:**
- API Docs: http://localhost:8000/docs
- Meilisearch: http://localhost:7700

---

## 📂 Estrutura do Projeto

```
.
├── api/                     # API FastAPI
│   ├── app.py              # Aplicação principal
│   ├── models.py           # SQLModel (Pydantic + SQLAlchemy)
│   ├── database.py         # Conexão PostgreSQL
│   ├── config.py           # Configurações
│   ├── routes/             # Endpoints
│   │   ├── commands.py     # CRUD + search + render
│   │   └── health.py       # /healthz
│   └── services/           # Lógica de negócio
│       ├── meilisearch_service.py
│       └── render_service.py
├── cli/                    # CLI Typer
│   ├── cmdgen.py           # Interface de linha de comando
│   └── Dockerfile          # Container da CLI
├── alembic/                # Migrações de banco
│   ├── versions/           # Scripts de migração
│   └── env.py              # Config Alembic
├── seeds/                  # Dados iniciais
│   ├── commands.yaml       # ~20 comandos úteis
│   └── load_seeds.py       # Script de carga
├── deploy/                 # Produção
│   ├── stack.yml           # Docker Swarm + Traefik
│   ├── .env.example        # Variáveis de ambiente
│   └── scripts/
│       ├── backup.sh       # Backup PostgreSQL
│       └── reindex_meili.sh
├── Dockerfile              # Imagem multi-stage da API
├── docker-compose.dev.yml  # Desenvolvimento local
└── README_DEPLOY.md        # Guia completo de deploy
```

---

## 🎯 Exemplos de Uso

### API REST

#### Criar comando

```bash
curl -X POST http://localhost:8000/commands/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "git-status",
    "description": "Mostra status do Git",
    "command_template": "git status",
    "category": "git",
    "tags": ["git", "status"],
    "variables": {}
  }'
```

#### Buscar comandos (fuzzy search)

```bash
# Tolera typos: "dokcer" encontra "docker"
curl -X POST http://localhost:8000/commands/search \
  -H "Content-Type: application/json" \
  -d '{"q": "dokcer exec", "limit": 5}'
```

#### Renderizar comando

```bash
curl -X POST http://localhost:8000/commands/render \
  -H "Content-Type: application/json" \
  -d '{
    "command_id": 1,
    "variables": {
      "SERVICE": "postgres_postgres",
      "SHELL": "bash"
    }
  }'
```

### CLI

```bash
# Buscar
cmdgen search "postgres backup"

# Ver detalhes
cmdgen show 8

# Renderizar
cmdgen render 1 --set SERVICE=my-container --set SHELL=zsh

# Dry-run (valida sem executar)
cmdgen dry-run 1 --set SERVICE=postgres_postgres

# Listar containers Docker
cmdgen services

# Health check
cmdgen health
```

---

## 🐳 Deploy em Produção

Veja **[README_DEPLOY.md](README_DEPLOY.md)** para guia completo.

**Resumo:**

1. Configure DNS apontando para seu servidor
2. Crie `.env` com senhas fortes
3. Build imagens: `docker build -t cmdgen-api:latest .`
4. Deploy: `docker stack deploy -c deploy/stack.yml cmdgen`
5. Migre: `alembic upgrade head`
6. Carregue seeds: `python seeds/load_seeds.py --api-url https://api.seudominio.com`

---

## 🔐 Segurança

### Implementado (MVP)

- ✅ Healthchecks em todos os serviços
- ✅ Migrações versionadas (Alembic)
- ✅ Validação de entrada (Pydantic)
- ✅ Containers non-root
- ✅ Multi-stage builds (imagens otimizadas)
- ✅ Timeouts em dry-run

### Fase 2 (Futuro)

- 🔲 Autenticação (OAuth2/JWT)
- 🔲 Rate limiting
- 🔲 Auditoria de comandos executados
- 🔲 RBAC (permissões por categoria)

---

## 🧪 Testes

```bash
# Instale dependências de teste
pip install pytest httpx

# Execute testes (quando implementados)
pytest tests/ -v
```

---

## 🛠️ Tecnologias

| Componente       | Tecnologia               | Versão    |
|------------------|--------------------------|-----------|
| API Framework    | FastAPI                  | 0.115     |
| ORM              | SQLModel                 | 0.0.22    |
| Banco de Dados   | PostgreSQL               | 15        |
| Busca            | Meilisearch              | v1.12     |
| Migrações        | Alembic                  | 1.13      |
| CLI              | Typer                    | 0.15      |
| Containerização  | Docker + Docker Swarm    | -         |
| Proxy Reverso    | Traefik                  | 2.x/3.x   |

---

## 📝 Variáveis de Ambiente

| Variável              | Descrição                     | Padrão                                    |
|-----------------------|-------------------------------|-------------------------------------------|
| `DATABASE_URL`        | Connection string Postgres    | `postgresql+psycopg2://...`              |
| `MEILI_URL`           | URL do Meilisearch            | `http://localhost:7700`                  |
| `MEILI_MASTER_KEY`    | Chave mestra Meili            | (vazio em dev)                           |
| `LOG_LEVEL`           | Nível de log                  | `info`                                   |
| `CMDGEN_API_URL`      | URL da API (para CLI)         | `http://localhost:8000`                  |

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'feat: adiciona nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra Pull Request

---

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

## 🙏 Agradecimentos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web incrível
- [Meilisearch](https://www.meilisearch.com/) - Busca rápida e fuzzy
- [Typer](https://typer.tiangolo.com/) - CLI moderna

---

**Desenvolvido com ❤️ para simplificar a vida de DevOps/SRE**

⭐ Se este projeto foi útil, considere dar uma estrela!
