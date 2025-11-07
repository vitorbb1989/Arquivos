"""
Serviço de renderização de templates de comandos
Substitui ${VAR} ou $VAR pelos valores fornecidos
"""
import re
from typing import Dict, Tuple, List


class RenderService:
    """Serviço para renderizar comandos com substituição de variáveis"""

    @staticmethod
    def extract_variables(template: str) -> List[str]:
        """
        Extrai todas as variáveis do template.
        Suporta: ${VAR} e $VAR
        """
        # Padrão para ${VAR} ou $VAR (word characters)
        pattern = r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
        matches = re.findall(pattern, template)
        # Flatten: cada match retorna (grupo1, grupo2), pegamos o não-vazio
        variables = [m[0] if m[0] else m[1] for m in matches]
        return list(set(variables))  # Remove duplicatas

    @staticmethod
    def render(template: str, variables: Dict[str, str]) -> Tuple[str, List[str]]:
        """
        Renderiza o template substituindo variáveis.

        Args:
            template: Template com ${VAR} ou $VAR
            variables: Dicionário com valores {VAR: valor}

        Returns:
            (comando_renderizado, lista_de_variaveis_faltantes)
        """
        rendered = template
        required_vars = RenderService.extract_variables(template)
        missing = []

        for var in required_vars:
            if var in variables:
                # Substitui ${VAR} e $VAR
                rendered = rendered.replace(f"${{{var}}}", variables[var])
                rendered = rendered.replace(f"${var}", variables[var])
            else:
                missing.append(var)

        return rendered, missing

    @staticmethod
    def validate_required_variables(
        variables_schema: Dict,
        provided_vars: Dict[str, str]
    ) -> List[str]:
        """
        Valida se todas as variáveis obrigatórias foram fornecidas.

        Args:
            variables_schema: Schema das variáveis do comando
                Formato: {VAR: {type, default, required, description}}
            provided_vars: Variáveis fornecidas pelo usuário

        Returns:
            Lista de variáveis obrigatórias faltantes
        """
        missing = []
        for var_name, var_info in variables_schema.items():
            is_required = var_info.get("required", True)
            has_default = "default" in var_info
            is_provided = var_name in provided_vars

            if is_required and not has_default and not is_provided:
                missing.append(var_name)

        return missing

    @staticmethod
    def apply_defaults(
        variables_schema: Dict,
        provided_vars: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Aplica valores padrão para variáveis não fornecidas.

        Args:
            variables_schema: Schema das variáveis
            provided_vars: Variáveis fornecidas

        Returns:
            Dicionário com valores fornecidos + defaults
        """
        result = provided_vars.copy()

        for var_name, var_info in variables_schema.items():
            if var_name not in result and "default" in var_info:
                result[var_name] = str(var_info["default"])

        return result
