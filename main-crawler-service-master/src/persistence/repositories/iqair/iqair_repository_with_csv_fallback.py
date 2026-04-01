"""
Wrapper do repositório IQAir com suporte a fallback CSV
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
import re
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.infrastructure.config.config import config
from src.persistence.entities.iqair.iqair_entity import IQAirEntity
from src.shared.utils.csv_utils import CSVManager


class IQAirRepositoryWithCSVFallback:
    """
    Repositório IQAir que implementa fallback para CSV quando o banco de dados não está disponível
    """
    
    def __init__(self, db: Session = None, csv_manager: CSVManager = None, database_available: bool = True):
        """
        Inicializa o repositório
        
        Args:
            db: Sessão do banco de dados
            csv_manager: Gerenciador de CSV para fallback
            database_available: Indica se o banco de dados está disponível
        """
        self.db = db
        self.csv_manager = csv_manager or CSVManager(output_dir=config.CSV_OUTPUT_DIR)
        self.database_available = database_available
        self.logger = logging.getLogger(__name__)
        self.csv_filename = "iqair_data.csv"

    def _extract_numeric_value(self, text: str) -> str:
        if not text:
            return ""
        match = re.search(r"\d+(?:[\.,]\d+)?", str(text))
        return match.group(0).replace(',', '.') if match else ""

    def _resolve_timestamp(self, value) -> str:
        if value is None:
            return datetime.utcnow().isoformat()
        if isinstance(value, datetime):
            return value.isoformat()
        value_as_str = str(value).strip()
        return value_as_str if value_as_str and value_as_str.lower() != "none" else datetime.utcnow().isoformat()

    def _next_csv_id(self) -> int:
        data = self.csv_manager.read_csv(self.csv_filename)
        if not data:
            return 1

        max_id = 0
        for row in data:
            try:
                max_id = max(max_id, int(row.get('id', 0)))
            except (TypeError, ValueError):
                continue
        return max_id + 1

    def _entity_to_dict(self, entity: IQAirEntity) -> Dict[str, Any]:
        """Converte uma entidade para dicionário"""
        sensor_location = str(
            getattr(entity, 'sensor_location', '') or getattr(entity, 'collection_unit', '') or ''
        ).strip() or 'Brasília'
        main_pollutant = str(getattr(entity, 'main_pollutant', '') or '')
        pollutant_concentration = str(getattr(entity, 'pollutant_concentration', '') or '')

        pm25 = ""
        pm10 = ""
        concentration_value = self._extract_numeric_value(pollutant_concentration)
        pollutant_lower = main_pollutant.lower()
        if 'pm2.5' in pollutant_lower or 'pm25' in pollutant_lower:
            pm25 = concentration_value
        if 'pm10' in pollutant_lower:
            pm10 = concentration_value

        created_at = self._resolve_timestamp(getattr(entity, 'created_at', None))
        updated_at = self._resolve_timestamp(getattr(entity, 'updated_at', None))

        return {
            'id': str(getattr(entity, 'id', '')),
            'created_at': created_at,
            'updated_at': updated_at,
            'sensor_location': sensor_location,
            'city': 'Brasília',
            'country': 'Brasil',
            'aqi': str(getattr(entity, 'aqi_score', '')),
            'pm25': pm25,
            'pm10': pm10,
            'aqi_score': str(getattr(entity, 'aqi_score', '')),
            'aqi_category': str(getattr(entity, 'aqi_category', '')),
            'local_time': str(getattr(entity, 'local_time', '')),
            'main_pollutant': main_pollutant,
            'pollutant_concentration': pollutant_concentration,
            'temperature': str(getattr(entity, 'temperature', '')),
            'wind_speed': str(getattr(entity, 'wind_speed', '')),
            'wind_direction': str(getattr(entity, 'wind_direction', '')),
            'wind_direction_degree': str(getattr(entity, 'wind_direction_degree', '')),
            'humidity': str(getattr(entity, 'humidity', '')),
        }
    
    def create(self, iqair_data: IQAirEntity) -> IQAirEntity:
        """Create a new IQAir data record"""
        if self.database_available:
            self.db.add(iqair_data)
            self.db.commit()
            self.db.refresh(iqair_data)
            return iqair_data
        else:
            # Fallback para CSV
            if not getattr(iqair_data, 'id', None):
                iqair_data.id = self._next_csv_id()

            data_dict = self._entity_to_dict(iqair_data)
            csv_path = self.csv_manager.append_to_csv(data_dict, self.csv_filename)
            self.logger.info(f"Dados salvos em CSV (modo fallback) em: {csv_path}")
            return iqair_data
    
    def get_by_id(self, iqair_id: int) -> Optional[IQAirEntity]:
        """Get IQAir data by ID"""
        if self.database_available:
            return self.db.query(IQAirEntity).filter(IQAirEntity.id == iqair_id).first()
        else:
            # Fallback para CSV
            data = self.csv_manager.read_csv(self.csv_filename)
            for row in data:
                if str(row.get('id')) == str(iqair_id):
                    self.logger.info(f"Registro encontrado no CSV: {row}")
                    return row
            return None
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[IQAirEntity]:
        """Get all IQAir data records, ordered by most recent"""
        if self.database_available:
            query = self.db.query(IQAirEntity).order_by(desc(IQAirEntity.created_at))
            if limit:
                query = query.limit(limit).offset(offset)
            return query.all()
        else:
            # Fallback para CSV
            data = self.csv_manager.read_csv(self.csv_filename)
            # Ordena por created_at (mais recente primeiro)
            try:
                data.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            except Exception as e:
                self.logger.warning(f"Erro ao ordenar dados do CSV: {e}")
            
            # Aplica limit e offset
            if offset:
                data = data[offset:]
            if limit:
                data = data[:limit]
            
            return data
    
    def get_latest(self) -> Optional[IQAirEntity]:
        """Get the most recent IQAir data record"""
        if self.database_available:
            return self.db.query(IQAirEntity).order_by(desc(IQAirEntity.created_at)).first()
        else:
            # Fallback para CSV
            data = self.csv_manager.read_csv(self.csv_filename)
            if not data:
                return None
            
            try:
                data.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                self.logger.info(f"Registro mais recente do CSV: {data[0]}")
                return data[0]
            except Exception as e:
                self.logger.warning(f"Erro ao obter registro mais recente do CSV: {e}")
                return None
    
    def count(self) -> int:
        """Get total count of IQAir data records"""
        if self.database_available:
            return self.db.query(IQAirEntity).count()
        else:
            # Fallback para CSV
            data = self.csv_manager.read_csv(self.csv_filename)
            count = len(data)
            self.logger.info(f"Total de registros no CSV: {count}")
            return count
