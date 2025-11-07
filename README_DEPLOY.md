# Gerador de Comandos - Guia de Deploy

**Deploy em Docker Swarm + Traefik**

---

## 📋 Sumário

- [Pré-requisitos](#pré-requisitos)
- [Desenvolvimento Local](#desenvolvimento-local)
- [Deploy em Produção](#deploy-em-produção)
  - [1. Preparação DNS](#1-preparação-dns)
  - [2. Configurar Secrets e Volumes](#2-configurar-secrets-e-volumes)
  - [3. Build das Imagens](#3-build-das-imagens)
  - [4. Deploy da Stack](#4-deploy-da-stack)
  - [5. Executar Migrações](#5-executar-migrações)
  - [6. Carregar Seeds](#6-carregar-seeds)
  - [7. Validar Deploy](#7-validar-deploy)
- [Uso da CLI](#uso-da-cli)
- [Manutenção](#manutenção)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Pré-requisitos

### Desenvolvimento
- Python 3.11+
- Docker + Docker Compose
- Git

### Produção
- VPS com Docker instalado
- Docker Swarm inicializado (`docker swarm init`)
- Traefik configurado e rodando
- Rede externa `minha_rede` criada: `docker network create --driver overlay minha_rede`
- DNS configurado apontando para seu servidor

---

## 💻 Desenvolvimento Local

### 1. Clone o repositório

```bash
git clone <seu-repo>
cd Arquivos
```

### 2. Configure ambiente de desenvolvimento

```bash
# Copie .env de exemplo
cp deploy/.env.example .env

# Edite .env com valores locais (já tem defaults para dev)
```

### 3. Suba ambiente local

```bash
docker-compose -f docker-compose.dev.yml up -d

# Aguarde os healthchecks ficarem healthy
docker-compose -f docker-compose.dev.yml ps
```

### 4. Execute migrações

```bash
# Instale dependências localmente (opcional, para Alembic)
pip install -r api/requirements.txt

# Execute migração
alembic upgrade head
```

### 5. Carregue seeds

```bash
# Instale PyYAML se necessário
pip install pyyaml httpx

# Carregue comandos de exemplo
python seeds/load_seeds.py --api-url http://localhost:8000
```

### 6. Acesse a API

- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/healthz
- **Meilisearch**: http://localhost:7700 (master key: `dev_master_key_123`)

### 7. Teste a CLI

```bash
# Instale CLI
pip install -r cli/requirements.txt

# Teste
python cli/cmdgen.py --help
python cli/cmdgen.py search docker
python cli/cmdgen.py show 1
```

---

## 🚀 Deploy em Produção

### 1. Preparação DNS

Aponte seu domínio para o IP do servidor:

```
A    api.comandos.seudominio.com  →  IP_DO_SERVIDOR
```

*(Opcional: aponte `meili.comandos.seudominio.com` se quiser expor Meilisearch - não recomendado)*

### 2. Configurar Secrets e Volumes

SSH no servidor:

```bash
ssh root@SEU_SERVIDOR

# Crie diretório de deploy
mkdir -p /root/stacks/cmdgen/deploy
cd /root/stacks/cmdgen/deploy

# Crie .env com valores de produção
cat > .env << 'EOF'
DOMAIN=api.comandos.seudominio.com
DB_PASS=SuaSenhaForteAqui123!
MEILI_MASTER_KEY=SuaChaveMestreMeiliForte456!
LOG_LEVEL=info
EOF

# Proteja o arquivo
chmod 600 .env

# Crie volumes
docker volume create cmdgen-db
docker volume create meili-data

# Diretório de backups
mkdir -p /var/backups/cmdgen
```

### 3. Build das Imagens

**Opção A: Build no servidor (mais simples)**

```bash
# Clone repositório no servidor
cd /root/stacks/cmdgen
git clone <seu-repo> .

# Build API
docker build -t cmdgen-api:latest -f Dockerfile .

# Build CLI
docker build -t cmdgen-cli:latest -f cli/Dockerfile ./cli
```

**Opção B: Build local + push para registry (recomendado)**

```bash
# Local
docker build -t ghcr.io/suaorg/cmdgen-api:latest -f Dockerfile .
docker build -t ghcr.io/suaorg/cmdgen-cli:latest -f cli/Dockerfile ./cli

docker push ghcr.io/suaorg/cmdgen-api:latest
docker push ghcr.io/suaorg/cmdgen-cli:latest

# Atualize deploy/stack.yml com as imagens do registry
# Substitua:
#   image: cmdgen-api:latest
# Por:
#   image: ghcr.io/suaorg/cmdgen-api:latest
```

### 4. Deploy da Stack

```bash
cd /root/stacks/cmdgen/deploy

# Carregue variáveis do .env
source .env

# Deploy
docker stack deploy -c stack.yml cmdgen

# Verifique serviços
docker service ls | grep cmdgen

# Aguarde ~1-2 min até todos ficarem 'ready'
watch docker service ls
```

### 5. Executar Migrações

```bash
# Entre em um container da API
docker exec -it $(docker ps --filter "name=cmdgen_api" -q | head -1) bash

# Dentro do container, execute:
alembic upgrade head

# Saia do container
exit
```

**Ou execute direto:**

```bash
docker exec $(docker ps --filter "name=cmdgen_api" -q | head -1) alembic upgrade head
```

### 6. Carregar Seeds

```bash
# Copie seeds para o servidor (se necessário)
scp -r seeds/ root@SEU_SERVIDOR:/root/stacks/cmdgen/

# No servidor
cd /root/stacks/cmdgen

# Instale dependências localmente (temporário)
pip3 install pyyaml httpx

# Carregue seeds
python3 seeds/load_seeds.py --api-url https://api.comandos.seudominio.com
```

**Ou via CLI container:**

```bash
# Ajuste replicas da CLI para 1 temporariamente
docker service scale cmdgen_cli=1

# Execute load
docker exec $(docker ps --filter "name=cmdgen_cli" -q) python /app/load_seeds.py
```

### 7. Validar Deploy

#### 7.1 Health Check

```bash
# Via curl
curl -fsS https://api.comandos.seudominio.com/healthz

# Resposta esperada:
# {
#   "status": "healthy",
#   "database": "healthy",
#   "meilisearch": "healthy",
#   "timestamp": "..."
# }
```

#### 7.2 Listar comandos

```bash
curl -fsS https://api.comandos.seudominio.com/commands | jq
```

#### 7.3 Buscar com Meilisearch

```bash
curl -X POST https://api.comandos.seudominio.com/commands/search \
  -H "Content-Type: application/json" \
  -d '{"q": "docker exec", "limit": 5}' | jq
```

#### 7.4 Renderizar comando

```bash
curl -X POST https://api.comandos.seudominio.com/commands/render \
  -H "Content-Type: application/json" \
  -d '{
    "command_id": 1,
    "variables": {
      "SERVICE": "postgres_postgres",
      "SHELL": "bash"
    }
  }' | jq
```

---

## 🖥️ Uso da CLI

### Instalação Local

```bash
pip install -r cli/requirements.txt

# Configure API URL
export CMDGEN_API_URL=https://api.comandos.seudominio.com

# Teste
python cli/cmdgen.py --help
```

### Instalação via Docker

```bash
# Executar CLI via container
docker run --rm --network minha_rede \
  -e CMDGEN_API_URL=http://api:8000 \
  cmdgen-cli:latest search "docker exec"
```

### Comandos Principais

```bash
# Buscar comandos
cmdgen search "postgres"

# Mostrar detalhes
cmdgen show 5

# Renderizar comando
cmdgen render 1 --set SERVICE=postgres_postgres --set SHELL=bash

# Dry-run (valida sem executar)
cmdgen dry-run 1 --set SERVICE=postgres_postgres

# Listar serviços Docker
cmdgen services

# Health check
cmdgen health
```

---

## 🔧 Manutenção

### Backup do Banco

```bash
# Copie script de backup para servidor
scp deploy/scripts/backup.sh root@SEU_SERVIDOR:/root/stacks/cmdgen/

# Execute backup manualmente
bash /root/stacks/cmdgen/backup.sh

# Agendar backup diário (crontab)
crontab -e

# Adicione:
0 2 * * * /root/stacks/cmdgen/backup.sh >> /var/log/cmdgen-backup.log 2>&1
```

### Reindexar Meilisearch

```bash
# Via script
bash deploy/scripts/reindex_meili.sh https://api.comandos.seudominio.com

# Ou via curl
curl -X POST https://api.comandos.seudominio.com/commands/reindex
```

### Atualizar Aplicação

```bash
# Pull nova versão
git pull origin main

# Rebuild imagens
docker build -t cmdgen-api:latest -f Dockerfile .

# Atualizar stack (rolling update)
docker stack deploy -c deploy/stack.yml cmdgen

# Ou atualizar apenas API
docker service update --image cmdgen-api:latest cmdgen_api
```

### Escalar Réplicas

```bash
# Aumentar réplicas da API
docker service scale cmdgen_api=3

# Ver status
docker service ps cmdgen_api
```

### Logs

```bash
# Logs da API
docker service logs -f --tail=100 cmdgen_api

# Logs do Postgres
docker service logs -f --tail=50 cmdgen_postgres

# Logs do Meilisearch
docker service logs -f --tail=50 cmdgen_meili
```

---

## 🐛 Troubleshooting

### 1. API não responde / 502 Bad Gateway

**Verificar:**

```bash
# Status dos serviços
docker service ls | grep cmdgen

# Tarefas da API
docker service ps cmdgen_api

# Logs detalhados
docker service logs cmdgen_api --tail=200
```

**Possíveis causas:**
- Migração não executada → Execute `alembic upgrade head`
- Banco não conecta → Verifique `DATABASE_URL` e senha
- Porta 8000 não acessível → Verifique healthcheck

### 2. Meilisearch não indexa

**Verificar:**

```bash
# Health do Meili
docker exec $(docker ps --filter "name=cmdgen_meili" -q) \
  curl -fsS http://localhost:7700/health

# Logs
docker service logs cmdgen_meili
```

**Solução:**
```bash
# Reindexar manualmente
curl -X POST https://api.comandos.seudominio.com/commands/reindex
```

### 3. Migrações Alembic falham

**Verificar versão atual:**

```bash
docker exec $(docker ps --filter "name=cmdgen_api" -q) alembic current
```

**Resetar (apenas DEV - NUNCA em produção!):**

```bash
# Apague banco e recrie
docker exec $(docker ps --filter "name=cmdgen_postgres" -q) \
  psql -U cmdgen -d cmdgen -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Execute migração
docker exec $(docker ps --filter "name=cmdgen_api" -q) alembic upgrade head
```

### 4. Traefik não roteia corretamente

**Verificar labels:**

```bash
# Inspecione serviço
docker service inspect cmdgen_api --format='{{json .Spec.Labels}}' | jq

# Certifique-se de que:
# - traefik.enable=true
# - Rede está correta (minha_rede)
# - DOMAIN está correto no .env
```

**Logs do Traefik:**

```bash
docker service logs traefik | grep cmdgen
```

### 5. CLI não conecta à API

**Verificar:**

```bash
# Teste conectividade
curl -fsS https://api.comandos.seudominio.com/healthz

# Verifique variável de ambiente
echo $CMDGEN_API_URL

# Tente com --api explícito
cmdgen --api https://api.comandos.seudominio.com health
```

### 6. Backup falha

**Verificar:**

```bash
# Container do Postgres rodando?
docker ps --filter "name=cmdgen_postgres"

# Permissões do diretório
ls -la /var/backups/cmdgen

# Testar pg_dump manualmente
docker exec cmdgen_postgres_postgres pg_dump -U cmdgen -d cmdgen > test.sql
```

### 7. Performance lenta

**Otimizações:**

```bash
# Indexar banco (já criado na migração)
# Aumentar replicas da API
docker service scale cmdgen_api=3

# Aumentar recursos no stack.yml:
# resources:
#   limits:
#     cpus: '1.0'
#     memory: 1G
```

---

## 📊 Checklist de Sucesso (Aceite)

Marque cada item após validação:

- [ ] `GET /healthz` → 200 OK (database + meilisearch healthy)
- [ ] `GET /commands` → Lista comandos (vazio ou com seeds)
- [ ] `POST /commands/search` → Retorna resultados (typo-tolerant)
- [ ] `POST /commands/render` → Substitui `${VAR}` corretamente
- [ ] `CLI: cmdgen search` → Busca funciona
- [ ] `CLI: cmdgen dry-run` → Valida sem executar DDL
- [ ] `backup.sh` → Gera arquivo `.sql.gz` em `/var/backups/cmdgen`
- [ ] `reindex_meili.sh` → Reindexação funciona
- [ ] Traefik → HTTPS funciona com certificado Let's Encrypt
- [ ] Logs → Sem erros críticos

---

## 📚 Recursos Adicionais

- **API Docs (Swagger)**: https://api.comandos.seudominio.com/docs
- **Alembic Docs**: https://alembic.sqlalchemy.org/
- **Meilisearch Docs**: https://www.meilisearch.com/docs
- **Docker Swarm**: https://docs.docker.com/engine/swarm/
- **Traefik**: https://doc.traefik.io/traefik/

---

## 🤝 Suporte

Para problemas:
1. Verifique logs: `docker service logs <service>`
2. Consulte [Troubleshooting](#troubleshooting)
3. Abra issue no repositório

---

**Desenvolvido com ❤️ usando FastAPI + Meilisearch + Docker Swarm**
