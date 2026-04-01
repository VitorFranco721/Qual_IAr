"""
Health Check Routes - Presentation Layer
Endpoints for system health verification
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.business.services.health.health_service import HealthService
from src.shared.dependency_injection import get_health_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Simple health check",
    description="""
    Verificação básica de saúde do sistema.
    
    **Retorno:**
    - Status básico do sistema
    - Timestamp da verificação
    - Versão da aplicação
    
    **Códigos de resposta:**
    - **200**: Sistema está funcionando (healthy ou unhealthy)
    - **503**: Sistema indisponível (se houver erro crítico)
    
    **Exemplo de resposta:**
    ```json
    {
        "status": "healthy",
        "timestamp": "2025-12-17T20:00:00.000000",
        "version": "0.1.0"
    }
    ```
    """,
)
async def simple_health_check(
    health_service: HealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """
    Simple system health check

    Returns:
        Dict[str, Any]: Simple health status
    """
    return await health_service.get_simple_health()


@router.get(
    "/health/detailed",
    status_code=status.HTTP_200_OK,
    summary="Detailed health check",
    description="""
    Verificação completa de saúde de todos os componentes do sistema.
    
    **Retorno:**
    - Status geral do sistema (healthy, warning, unhealthy)
    - Status detalhado de cada componente:
      - **database**: Status do banco de dados PostgreSQL
      - **system**: Recursos do sistema (CPU, memória, disco)
      - **external_services**: Status dos serviços externos (IQAir)
    - Tempo de resposta total
    - Timestamp da verificação
    - Versão da aplicação
    
    **Códigos de resposta:**
    - **200**: Verificação concluída (status pode ser healthy, warning ou unhealthy)
    
    **Exemplo de resposta:**
    ```json
    {
        "status": "healthy",
        "timestamp": "2025-12-17T20:00:00.000000",
        "response_time_ms": 125.50,
        "version": "0.1.0",
        "components": {
            "database": {
                "status": "healthy",
                "response_time_ms": 5.23,
                "pool_status": {...}
            },
            "system": {
                "status": "healthy",
                "cpu": {...},
                "memory": {...},
                "disk": {...}
            },
            "external_services": {
                "status": "healthy",
                "services": {
                    "iqair": {...}
                }
            }
        }
    }
    ```
    """,
)
async def detailed_health_check(
    health_service: HealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """
    Detailed system health check

    Returns:
        Dict[str, Any]: Complete system status
    """
    return await health_service.get_comprehensive_health()
