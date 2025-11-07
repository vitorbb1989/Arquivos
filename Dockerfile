# Dockerfile multi-stage para API FastAPI
# Imagem otimizada para produção

# ==================== STAGE 1: Builder ====================
FROM python:3.11-slim as builder

WORKDIR /build

# Instala dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY api/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==================== STAGE 2: Runtime ====================
FROM python:3.11-slim

WORKDIR /app

# Instala dependências de runtime + curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências do builder
COPY --from=builder /root/.local /root/.local

# Copia código da aplicação
COPY api/ /app/api/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/

# Cria usuário não-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Path para encontrar pacotes instalados
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Porta da aplicação
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

# Comando padrão
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
