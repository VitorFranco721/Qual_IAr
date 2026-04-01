"""
IQAir Error Messages - Shared Layer
Centralizes all error messages for IQAir module
"""


class IQAirErrorMessages:
    """Error messages for IQAir exceptions"""
    
    SERVICE_UNAVAILABLE = "Erro ao acessar IQAir: {detail}"
    DEFAULT_DETAIL = "Serviço IQAir temporariamente indisponível"
    BROWSER_AUTOMATION_ERROR = "Erro na automação do navegador: {detail}"
    INTERNAL_COLLECT_ERROR = "Erro interno ao coletar dados: {detail}"
    INTERNAL_HISTORY_ERROR = "Erro interno ao buscar histórico: {detail}"

