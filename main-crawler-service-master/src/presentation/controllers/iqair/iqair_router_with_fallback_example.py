"""
Exemplo de como usar o fallback CSV em rotas/controladores
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime

from src.infrastructure.config.database import get_db
from src.persistence.repositories.iqair.iqair_repository_with_csv_fallback import IQAirRepositoryWithCSVFallback
from src.presentation.schemas.iqair.iqair_schema import IQAirSchema
from src.shared.utils.csv_utils import CSVManager

router = APIRouter()


def get_iqair_repository(
    request: Request,
    db: Session = Depends(get_db)
) -> IQAirRepositoryWithCSVFallback:
    """
    Dependency injection do repositório IQAir com suporte a CSV fallback
    """
    # Obtém o estado da aplicação
    csv_manager = getattr(request.app.state, 'csv_manager', None)
    database_available = getattr(request.app.state, 'database_available', True)
    
    # Se não houver csv_manager, cria um novo
    if csv_manager is None:
        csv_manager = CSVManager(output_dir="output")
    
    return IQAirRepositoryWithCSVFallback(
        db=db,
        csv_manager=csv_manager,
        database_available=database_available
    )


@router.post("/data")
def create_iqair_data(
    data: IQAirSchema,
    repository: IQAirRepositoryWithCSVFallback = Depends(get_iqair_repository)
):
    """
    Cria um novo registro de dados IQAir
    
    - Se banco de dados está disponível: salva no banco
    - Se banco de dados está indisponível: salva em CSV
    """
    try:
        # Aqui você pode criar uma entidade e salvar
        # entity = IQAirEntity(**data.dict())
        # saved = repository.create(entity)
        
        # Para este exemplo, salvamos o dicionário direto
        data_dict = {
            'city': data.city,
            'country': data.country,
            'aqi': data.aqi,
            'pm25': data.pm25,
            'pm10': data.pm10,
            'created_at': datetime.utcnow().isoformat()
        }
        
        repository.create(data_dict)
        
        return {
            "status": "success",
            "message": "Dados salvos com sucesso",
            "data": data_dict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar dados: {str(e)}")


@router.get("/data/latest")
def get_latest_iqair_data(
    repository: IQAirRepositoryWithCSVFallback = Depends(get_iqair_repository)
):
    """
    Obtém o registro mais recente de dados IQAir
    
    - Se banco de dados está disponível: obtém do banco
    - Se banco de dados está indisponível: obtém do CSV
    """
    try:
        data = repository.get_latest()
        
        if not data:
            raise HTTPException(status_code=404, detail="Nenhum registro encontrado")
        
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados: {str(e)}")


@router.get("/data")
def get_all_iqair_data(
    limit: int = 10,
    offset: int = 0,
    repository: IQAirRepositoryWithCSVFallback = Depends(get_iqair_repository)
):
    """
    Obtém todos os registros de dados IQAir com paginação
    
    - Se banco de dados está disponível: obtém do banco
    - Se banco de dados está indisponível: obtém do CSV
    """
    try:
        data = repository.get_all(limit=limit, offset=offset)
        
        return {
            "status": "success",
            "total": len(data),
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados: {str(e)}")


@router.get("/data/count")
def count_iqair_data(
    repository: IQAirRepositoryWithCSVFallback = Depends(get_iqair_repository)
):
    """
    Obtém o total de registros de dados IQAir
    
    - Se banco de dados está disponível: obtém do banco
    - Se banco de dados está indisponível: obtém do CSV
    """
    try:
        count = repository.count()
        
        return {
            "status": "success",
            "total": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao contar dados: {str(e)}")


@router.get("/status/database")
def get_database_status(request: Request):
    """
    Verifica o status da conexão com o banco de dados
    """
    database_available = getattr(request.app.state, 'database_available', True)
    
    status = "online" if database_available else "offline (usando CSV)"
    mode = "banco de dados" if database_available else "CSV fallback"
    
    return {
        "status": status,
        "mode": mode,
        "csv_enabled": not database_available,
        "csv_path": "./output/" if not database_available else None
    }
