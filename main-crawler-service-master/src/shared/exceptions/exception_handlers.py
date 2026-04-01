"""
Global Exception Handlers - Shared Layer
Centralizes all global exception handlers for FastAPI
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.shared.exceptions.custom_exceptions import (
    ValidationError,
    BusinessRuleError,
    DatabaseError,
    ExternalServiceError,
    IQAirError,
    BrowserError
)
from src.shared.messages.general.general_error_messages import GeneralErrorMessages
from src.shared.messages.iqair.iqair_error_messages import IQAirErrorMessages

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """
    Register all global exception handlers with the FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """Handler para erros de validação"""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": GeneralErrorMessages.VALIDATION_ERROR.format(detail=str(exc))}
        )

    @app.exception_handler(BusinessRuleError)
    async def business_error_handler(request: Request, exc: BusinessRuleError):
        """Handler para erros de regra de negócio"""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": GeneralErrorMessages.BUSINESS_RULE_ERROR.format(detail=str(exc))}
        )

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        """Handler para erros de banco de dados"""
        logger.error(f"Erro de banco de dados: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": GeneralErrorMessages.DATABASE_ERROR}
        )

    @app.exception_handler(ExternalServiceError)
    async def external_service_error_handler(request: Request, exc: ExternalServiceError):
        """Handler para erros de serviços externos"""
        logger.error(f"Erro de serviço externo: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": GeneralErrorMessages.EXTERNAL_SERVICE_ERROR}
        )

    @app.exception_handler(IQAirError)
    async def iqair_error_handler(request: Request, exc: IQAirError):
        """Handler para erros do IQAir"""
        logger.error(f"Erro no IQAir: {exc}")
        detail = str(exc) if str(exc) else IQAirErrorMessages.DEFAULT_DETAIL
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": IQAirErrorMessages.SERVICE_UNAVAILABLE.format(detail=detail)}
        )

    @app.exception_handler(BrowserError)
    async def browser_error_handler(request: Request, exc: BrowserError):
        """Handler para erros de automação do navegador"""
        logger.error(f"Erro no navegador: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": GeneralErrorMessages.BROWSER_ERROR.format(detail=str(exc))}
        )

