# Dockerfile para CLI
# Imagem leve para executar cmdgen em containers

FROM python:3.11-slim

WORKDIR /app

# Instala Docker CLI e psql (para validações no dry-run)
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia CLI
COPY cmdgen.py /app/cmdgen.py

# Torna executável
RUN chmod +x /app/cmdgen.py

# Cria usuário não-root
RUN useradd -m -u 1000 cliuser && chown -R cliuser:cliuser /app
USER cliuser

ENV PYTHONPATH=/app

# Entrypoint para CLI
ENTRYPOINT ["python", "/app/cmdgen.py"]
CMD ["--help"]
