#!/usr/bin/env python3
"""
CLI do Gerador de Comandos - Typer
Comandos: search, show, render, dry-run, services
"""
import typer
import httpx
import json
import subprocess
import sys
from typing import Optional, Dict, List
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich import print as rprint

app = typer.Typer(
    name="cmdgen",
    help="Gerador de Comandos - CLI para buscar e executar comandos reutilizáveis"
)
console = Console()

# Configurações
API_URL = typer.Option(
    "http://localhost:8000",
    envvar="CMDGEN_API_URL",
    help="URL da API"
)
TIMEOUT = 10  # segundos
DRY_RUN_DOCKER_TIMEOUT = 5
DRY_RUN_PSQL_TIMEOUT = 3


def get_client(api_url: str) -> httpx.Client:
    """Cria cliente HTTP com timeout"""
    return httpx.Client(base_url=api_url, timeout=TIMEOUT)


@app.command()
def search(
    q: str = typer.Argument(..., help="Texto de busca"),
    limit: int = typer.Option(10, "--limit", "-l", help="Número de resultados"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filtrar por categoria"),
    api: str = API_URL
):
    """
    Busca comandos via Meilisearch (fuzzy, typo-tolerant).

    Exemplos:
        cmdgen search "docker exec"
        cmdgen search postgres --category=postgres
    """
    try:
        client = get_client(api)
        response = client.post(
            "/commands/search",
            json={
                "q": q,
                "limit": limit,
                "offset": 0,
                "category": category
            }
        )
        response.raise_for_status()
        data = response.json()

        hits = data.get("hits", [])
        total = data.get("total", 0)

        if not hits:
            console.print(f"[yellow]Nenhum comando encontrado para '{q}'[/yellow]")
            return

        # Tabela de resultados
        table = Table(title=f"Resultados: {total} comando(s) encontrado(s)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Nome", style="magenta")
        table.add_column("Categoria", style="green")
        table.add_column("Descrição", style="white")

        for hit in hits:
            table.add_row(
                str(hit["id"]),
                hit["name"],
                hit["category"],
                hit["description"][:60] + "..." if len(hit["description"]) > 60 else hit["description"]
            )

        console.print(table)
        console.print(f"\n[dim]Use 'cmdgen show <ID>' para ver detalhes[/dim]")

    except httpx.HTTPStatusError as e:
        console.print(f"[red]Erro HTTP {e.response.status_code}: {e.response.text}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)


@app.command()
def show(
    command_id: int = typer.Argument(..., help="ID do comando"),
    api: str = API_URL
):
    """
    Mostra detalhes de um comando.

    Exemplo:
        cmdgen show 5
    """
    try:
        client = get_client(api)
        response = client.get(f"/commands/{command_id}")
        response.raise_for_status()
        cmd = response.json()

        console.print(f"\n[bold cyan]Comando #{cmd['id']}: {cmd['name']}[/bold cyan]")
        console.print(f"[bold]Categoria:[/bold] {cmd['category']}")
        console.print(f"[bold]Descrição:[/bold] {cmd['description']}\n")

        # Template
        console.print("[bold]Template:[/bold]")
        syntax = Syntax(cmd['command_template'], "bash", theme="monokai", line_numbers=False)
        console.print(syntax)

        # Variáveis
        if cmd.get('variables'):
            console.print("\n[bold]Variáveis:[/bold]")
            for var_name, var_info in cmd['variables'].items():
                required = var_info.get('required', True)
                default = var_info.get('default', 'N/A')
                desc = var_info.get('description', '')
                req_label = "[red]obrigatória[/red]" if required else "[green]opcional[/green]"
                console.print(f"  • {var_name} ({req_label}) - {desc}")
                if default != 'N/A':
                    console.print(f"    [dim]default: {default}[/dim]")

        # Tags
        if cmd.get('tags'):
            console.print(f"\n[bold]Tags:[/bold] {', '.join(cmd['tags'])}")

        # Notes
        if cmd.get('notes'):
            console.print(f"\n[bold]Observações:[/bold]\n{cmd['notes']}")

        console.print(f"\n[dim]Use 'cmdgen render {command_id} --set VAR=valor' para renderizar[/dim]")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Comando {command_id} não encontrado[/red]")
        else:
            console.print(f"[red]Erro HTTP {e.response.status_code}: {e.response.text}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)


@app.command()
def render(
    command_id: int = typer.Argument(..., help="ID do comando"),
    set: List[str] = typer.Option([], "--set", help="Variável no formato VAR=valor"),
    api: str = API_URL
):
    """
    Renderiza comando substituindo variáveis.

    Exemplo:
        cmdgen render 1 --set SERVICE=postgres_postgres --set SHELL=bash
    """
    try:
        # Parse variáveis
        variables = {}
        for var_assignment in set:
            if "=" not in var_assignment:
                console.print(f"[red]Formato inválido: {var_assignment}. Use VAR=valor[/red]")
                sys.exit(1)
            key, value = var_assignment.split("=", 1)
            variables[key.strip()] = value.strip()

        # Chamar API
        client = get_client(api)
        response = client.post(
            "/commands/render",
            json={
                "command_id": command_id,
                "variables": variables
            }
        )
        response.raise_for_status()
        data = response.json()

        # Exibir resultado
        console.print(f"\n[bold cyan]Comando #{data['command_id']}: {data['name']}[/bold cyan]")

        if data.get('missing_variables'):
            console.print(f"[yellow]Aviso: Variáveis faltantes: {', '.join(data['missing_variables'])}[/yellow]\n")

        console.print("[bold]Comando renderizado:[/bold]")
        syntax = Syntax(data['rendered_command'], "bash", theme="monokai")
        console.print(syntax)

    except httpx.HTTPStatusError as e:
        console.print(f"[red]Erro HTTP {e.response.status_code}: {e.response.text}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)


@app.command()
def dry_run(
    command_id: int = typer.Argument(..., help="ID do comando"),
    set: List[str] = typer.Option([], "--set", help="Variável no formato VAR=valor"),
    api: str = API_URL
):
    """
    Dry-run: renderiza comando + valida (Docker/Postgres) SEM executar DDL.

    Validações:
    - Docker: verifica se serviço existe (timeout 5s)
    - Postgres: tenta conectar (timeout 3s)
    - Exibe comando final + warnings

    Exemplo:
        cmdgen dry-run 1 --set SERVICE=postgres_postgres --set SHELL=bash
    """
    try:
        # Parse variáveis
        variables = {}
        for var_assignment in set:
            if "=" not in var_assignment:
                console.print(f"[red]Formato inválido: {var_assignment}. Use VAR=valor[/red]")
                sys.exit(1)
            key, value = var_assignment.split("=", 1)
            variables[key.strip()] = value.strip()

        # Renderizar via API
        client = get_client(api)
        response = client.post(
            "/commands/render",
            json={
                "command_id": command_id,
                "variables": variables
            }
        )
        response.raise_for_status()
        data = response.json()

        console.print(f"\n[bold cyan]DRY-RUN - Comando #{data['command_id']}: {data['name']}[/bold cyan]")

        # Warnings de variáveis faltantes
        if data.get('missing_variables'):
            console.print(f"[yellow]⚠ Variáveis obrigatórias faltantes: {', '.join(data['missing_variables'])}[/yellow]")

        rendered_cmd = data['rendered_command']
        console.print("\n[bold]Comando renderizado:[/bold]")
        syntax = Syntax(rendered_cmd, "bash", theme="monokai")
        console.print(syntax)

        # Validações específicas
        console.print("\n[bold]Validações:[/bold]")

        # Validação Docker
        if "docker exec" in rendered_cmd.lower() or "docker-compose" in rendered_cmd.lower():
            console.print("[cyan]• Detectado comando Docker...[/cyan]")
            service_name = variables.get("SERVICE")
            if service_name:
                try:
                    result = subprocess.run(
                        ["docker", "ps", "--filter", f"name={service_name}", "--format", "{{.Names}}"],
                        capture_output=True,
                        text=True,
                        timeout=DRY_RUN_DOCKER_TIMEOUT
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        console.print(f"  [green]✓ Serviço '{service_name}' encontrado[/green]")
                    else:
                        console.print(f"  [yellow]⚠ Serviço '{service_name}' não encontrado[/yellow]")
                except subprocess.TimeoutExpired:
                    console.print(f"  [yellow]⚠ Timeout ao verificar Docker (>{DRY_RUN_DOCKER_TIMEOUT}s)[/yellow]")
                except FileNotFoundError:
                    console.print("  [yellow]⚠ Docker CLI não encontrado[/yellow]")

        # Validação Postgres (básica - apenas verifica se psql existe)
        if "psql" in rendered_cmd.lower():
            console.print("[cyan]• Detectado comando Postgres...[/cyan]")
            try:
                result = subprocess.run(
                    ["which", "psql"],
                    capture_output=True,
                    timeout=DRY_RUN_PSQL_TIMEOUT
                )
                if result.returncode == 0:
                    console.print("  [green]✓ psql CLI disponível[/green]")
                else:
                    console.print("  [yellow]⚠ psql CLI não encontrado no PATH[/yellow]")
            except subprocess.TimeoutExpired:
                console.print(f"  [yellow]⚠ Timeout ao verificar psql (>{DRY_RUN_PSQL_TIMEOUT}s)[/yellow]")

        console.print("\n[green]✓ Dry-run concluído (comando NÃO foi executado)[/green]")
        console.print("[dim]Para executar, copie o comando acima ou use ferramentas apropriadas[/dim]")

    except httpx.HTTPStatusError as e:
        console.print(f"[red]Erro HTTP {e.response.status_code}: {e.response.text}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)


@app.command()
def services(api: str = API_URL):
    """
    Lista serviços Docker em execução (helper para preencher variável SERVICE).

    Exemplo:
        cmdgen services
    """
    try:
        console.print("[cyan]Listando serviços Docker...[/cyan]\n")

        # Lista containers
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Image}}"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            console.print(f"[red]Erro ao listar containers: {result.stderr}[/red]")
            sys.exit(1)

        console.print(result.stdout)
        console.print("\n[dim]Use os nomes da coluna 'NAMES' na variável SERVICE[/dim]")

    except subprocess.TimeoutExpired:
        console.print("[yellow]Timeout ao listar serviços Docker[/yellow]")
        sys.exit(1)
    except FileNotFoundError:
        console.print("[red]Docker CLI não encontrado. Instale Docker.[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)


@app.command()
def health(api: str = API_URL):
    """
    Verifica saúde da API.

    Exemplo:
        cmdgen health
    """
    try:
        client = get_client(api)
        response = client.get("/healthz")
        response.raise_for_status()
        data = response.json()

        console.print(f"\n[bold]Status da API:[/bold] [{'green' if data['status'] == 'healthy' else 'yellow'}]{data['status']}[/]")
        console.print(f"[bold]Database:[/bold] {data['database']}")
        console.print(f"[bold]Meilisearch:[/bold] {data['meilisearch']}")
        console.print(f"[bold]Timestamp:[/bold] {data['timestamp']}\n")

    except httpx.HTTPStatusError as e:
        console.print(f"[red]API indisponível (HTTP {e.response.status_code})[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print(f"[red]Não foi possível conectar à API em {api}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    app()
