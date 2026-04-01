"""
General Error Messages - Shared Layer
Centralizes general error messages used across the application
"""


class GeneralErrorMessages:
    """General error messages"""
    
    VALIDATION_ERROR = "Erro de validação: {detail}"
    BUSINESS_RULE_ERROR = "Erro de regra de negócio: {detail}"
    DATABASE_ERROR = "Erro interno do servidor"
    EXTERNAL_SERVICE_ERROR = "Serviço temporariamente indisponível"
    BROWSER_ERROR = "Erro na automação do navegador: {detail}"

