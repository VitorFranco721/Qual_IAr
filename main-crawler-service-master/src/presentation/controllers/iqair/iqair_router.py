"""
Router for IQAir operations
"""
import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.business.mappers.iqair_mapper import iqair_entity_to_response_schema
from src.business.services.iqair.iqair_controller import IQAirController
from src.persistence.repositories.iqair.iqair_repository import IQAirRepository
from src.presentation.schemas.iqair.iqair_schema import IQAirDataSchema, IQAirDataResponseSchema
from src.shared.exceptions.custom_exceptions import IQAirError, BrowserError
from src.shared.dependency_injection import get_iqair_controller
from src.shared.dependency_injection import get_iqair_repository
from src.shared.messages.iqair.iqair_error_messages import IQAirErrorMessages
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/coletar-aqi",
    response_model=IQAirDataSchema,
    status_code=status.HTTP_200_OK,
    summary="Collect AQI data from IQAir",
    description="""
    Acessa o site IQAir e coleta os dados do campo .aqi-box-shadow-green.
    
    **Retorno:**
    - AQI Score: Pontuação do índice de qualidade do ar
    - AQI Category: Categoria da qualidade do ar
    - Main Pollutant: Poluente principal
    - Pollutant Concentration: Concentração do poluente
    - Temperature: Temperatura atual
    - Wind Speed: Velocidade do vento
    - Wind Direction: Direção do vento
    - Humidity: Umidade relativa
    - Pressure: Pressão atmosférica
    - Feels Like: Sensação térmica
    - Visibility: Visibilidade
    - Dew Point: Ponto de orvalho
    
    **Códigos de resposta:**
    - **200**: Dados coletados com sucesso
    - **500**: Erro interno ao coletar dados
    - **503**: Erro ao acessar IQAir ou automação do navegador
    
    **Exemplo de uso:**
    ```python
    import requests
    
    response = requests.get("http://localhost:8080/api/v1/iqair/coletar-aqi")
    data = response.json()
    
    print(f"AQI Score: {data['aqi_score']}")
    print(f"Category: {data['aqi_category']}")
    print(f"Temperature: {data['temperature']}")
    ```
    """,
)
def coletar_dados_aqi(
    iqair_controller: Annotated[IQAirController, Depends(get_iqair_controller)] = None
) -> IQAirDataSchema:
    """
    Endpoint para coletar dados AQI do IQAir.
    
    Args:
        db: Sessão do banco de dados (injetada)
        
    Returns:
        IQAirDataSchema: Dados coletados do IQAir
        
    Raises:
        HTTPException 500: Erro interno ao coletar dados
        HTTPException 503: Erro ao acessar IQAir ou automação do navegador
    """
    try:
        logger.info("Iniciando coleta de dados do IQAir")
        
        dados = iqair_controller.collect_aqi_data()
        
        logger.info(f"Dados IQAir coletados com sucesso - AQI: {dados.aqi_score}")
        return dados
        
    except IQAirError as e:
        logger.error(f"Erro no IQAir: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=IQAirErrorMessages.SERVICE_UNAVAILABLE.format(detail=str(e))
        )
    except BrowserError as e:
        logger.error(f"Erro na automação do navegador: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=IQAirErrorMessages.BROWSER_AUTOMATION_ERROR.format(detail=str(e))
        )
    except Exception as e:
        logger.error(f"Erro ao coletar dados do IQAir: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=IQAirErrorMessages.INTERNAL_COLLECT_ERROR.format(detail=str(e))
        )


@router.get(
    "/historico",
    response_model=List[IQAirDataResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="Get IQAir data history",
    description="""
    Retorna o histórico de dados coletados do IQAir.
    
    **Parâmetros:**
    - **limit**: Número máximo de registros a retornar (padrão: 100)
    - **offset**: Número de registros a pular (padrão: 0)
    
    **Retorno:**
    - Lista de registros históricos com ID e timestamps
    
    **Códigos de resposta:**
    - **200**: Histórico retornado com sucesso
    - **500**: Erro interno ao buscar histórico
    """,
)
def obter_historico_aqi(
    limit: Annotated[int, Query(ge=1, le=1000, description="Número máximo de registros")] = 100,
    offset: Annotated[int, Query(ge=0, description="Número de registros a pular")] = 0,
    iqair_repository: Annotated[IQAirRepository, Depends(get_iqair_repository)] = None
) -> List[IQAirDataResponseSchema]:
    """
    Endpoint para obter histórico de dados AQI do IQAir.
    
    Args:
        limit: Número máximo de registros a retornar
        offset: Número de registros a pular
        iqair_repository: Repository for IQAir data (injected)
        
    Returns:
        List[IQAirDataResponseSchema]: Lista de registros históricos
    """
    try:
        logger.info(f"Buscando histórico IQAir - limit: {limit}, offset: {offset}")
        
        entities = iqair_repository.get_all(limit=limit, offset=offset)
        
        logger.info(f"Histórico IQAir retornado - {len(entities)} registro(s)")
        
        return [iqair_entity_to_response_schema(entity) for entity in entities]
        
    except Exception as e:
        logger.error(f"Erro ao buscar histórico IQAir: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=IQAirErrorMessages.INTERNAL_HISTORY_ERROR.format(detail=str(e))
        )
