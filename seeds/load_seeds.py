#!/usr/bin/env python3
"""
Script para carregar seeds de comandos no banco de dados
Uso: python load_seeds.py [--api-url http://localhost:8000]
"""
import yaml
import httpx
import sys
from pathlib import Path


def load_seeds(api_url: str, seeds_file: str = "commands.yaml"):
    """Carrega seeds via API"""
    seeds_path = Path(__file__).parent / seeds_file

    if not seeds_path.exists():
        print(f"[ERROR] Arquivo de seeds não encontrado: {seeds_path}")
        sys.exit(1)

    # Carrega YAML
    with open(seeds_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    commands = data.get('commands', [])
    print(f"[INFO] Carregando {len(commands)} comandos...")

    # Envia para API
    client = httpx.Client(base_url=api_url, timeout=30)
    created = 0
    failed = 0

    for cmd in commands:
        try:
            response = client.post("/commands/", json=cmd)
            response.raise_for_status()
            created += 1
            print(f"  [OK] {cmd['name']}")
        except httpx.HTTPStatusError as e:
            failed += 1
            print(f"  [FAIL] {cmd['name']}: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {cmd['name']}: {e}")

    print(f"\n[SUMMARY] Criados: {created}, Falhas: {failed}")

    # Reindexar Meilisearch
    try:
        print("\n[INFO] Reindexando Meilisearch...")
        response = client.post("/commands/reindex")
        response.raise_for_status()
        print("[OK] Reindex concluído")
    except Exception as e:
        print(f"[WARN] Falha ao reindexar: {e}")

    return created, failed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Carrega seeds de comandos")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="URL da API (padrão: http://localhost:8000)"
    )
    args = parser.parse_args()

    created, failed = load_seeds(args.api_url)
    sys.exit(0 if failed == 0 else 1)
