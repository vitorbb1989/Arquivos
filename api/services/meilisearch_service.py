"""
Serviço de integração com Meilisearch para busca de comandos
"""
import meilisearch
from typing import List, Optional, Dict, Any
from api.config import settings
from api.models import Command
import logging

logger = logging.getLogger(__name__)


class MeilisearchService:
    """Serviço para sincronizar e buscar comandos no Meilisearch"""

    def __init__(self):
        """Inicializa cliente Meilisearch"""
        self.client = meilisearch.Client(
            settings.MEILI_URL,
            settings.MEILI_MASTER_KEY
        )
        self.index_name = settings.MEILI_INDEX_NAME
        self._init_index()

    def _init_index(self):
        """Inicializa o índice com configurações"""
        try:
            # Cria índice se não existir
            try:
                self.client.get_index(self.index_name)
            except Exception:
                self.client.create_index(self.index_name, {"primaryKey": "id"})

            # Configurações do índice
            index = self.client.index(self.index_name)

            # Campos pesquisáveis
            index.update_searchable_attributes([
                "name",
                "description",
                "category",
                "tags",
                "command_template",
                "notes"
            ])

            # Campos filtráveis
            index.update_filterable_attributes(["category", "tags"])

            # Campos para ranking
            index.update_ranking_rules([
                "words",
                "typo",
                "proximity",
                "attribute",
                "sort",
                "exactness"
            ])

            # Typo tolerance (tolerância a erros de digitação)
            index.update_typo_tolerance({
                "enabled": True,
                "minWordSizeForTypos": {
                    "oneTypo": 4,
                    "twoTypos": 8
                }
            })

            logger.info(f"Índice {self.index_name} configurado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar índice Meilisearch: {e}")

    def add_command(self, command: Command) -> bool:
        """
        Adiciona/atualiza comando no índice.

        Args:
            command: Comando a ser indexado

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            index = self.client.index(self.index_name)
            document = {
                "id": command.id,
                "name": command.name,
                "description": command.description,
                "command_template": command.command_template,
                "category": command.category,
                "tags": command.tags,
                "notes": command.notes or ""
            }
            index.add_documents([document])
            logger.debug(f"Comando {command.id} adicionado ao Meilisearch")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar comando ao Meilisearch: {e}")
            return False

    def update_command(self, command: Command) -> bool:
        """
        Atualiza comando no índice (mesma implementação que add).

        Args:
            command: Comando a ser atualizado

        Returns:
            True se sucesso
        """
        return self.add_command(command)

    def delete_command(self, command_id: int) -> bool:
        """
        Remove comando do índice.

        Args:
            command_id: ID do comando

        Returns:
            True se sucesso
        """
        try:
            index = self.client.index(self.index_name)
            index.delete_document(command_id)
            logger.debug(f"Comando {command_id} removido do Meilisearch")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover comando do Meilisearch: {e}")
            return False

    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Busca comandos no índice.

        Args:
            query: Texto de busca
            limit: Número máximo de resultados
            offset: Offset para paginação
            category: Filtro por categoria (opcional)

        Returns:
            Dicionário com hits e metadata
        """
        try:
            index = self.client.index(self.index_name)

            search_params = {
                "limit": limit,
                "offset": offset,
                "attributesToRetrieve": ["*"]
            }

            # Filtro por categoria
            if category:
                search_params["filter"] = f"category = '{category}'"

            results = index.search(query, search_params)
            return results

        except Exception as e:
            logger.error(f"Erro ao buscar no Meilisearch: {e}")
            return {"hits": [], "estimatedTotalHits": 0}

    def reindex_all(self, commands: List[Command]) -> bool:
        """
        Reindexar todos os comandos (limpa índice e adiciona tudo).

        Args:
            commands: Lista de comandos do banco

        Returns:
            True se sucesso
        """
        try:
            index = self.client.index(self.index_name)

            # Limpa índice
            index.delete_all_documents()

            # Adiciona todos os comandos
            documents = [
                {
                    "id": cmd.id,
                    "name": cmd.name,
                    "description": cmd.description,
                    "command_template": cmd.command_template,
                    "category": cmd.category,
                    "tags": cmd.tags,
                    "notes": cmd.notes or ""
                }
                for cmd in commands
            ]

            if documents:
                index.add_documents(documents)

            logger.info(f"Reindexados {len(documents)} comandos")
            return True

        except Exception as e:
            logger.error(f"Erro ao reindexar comandos: {e}")
            return False

    def health_check(self) -> bool:
        """
        Verifica se Meilisearch está acessível.

        Returns:
            True se saudável
        """
        try:
            self.client.health()
            return True
        except Exception:
            return False


# Singleton
meili_service = MeilisearchService()
