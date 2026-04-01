from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.persistence.entities.iqair.iqair_entity import IQAirEntity


class IQAirRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, iqair_data: IQAirEntity) -> IQAirEntity:
        """Create a new IQAir data record"""
        self.db.add(iqair_data)
        self.db.commit()
        self.db.refresh(iqair_data)
        return iqair_data

    def get_by_id(self, iqair_id: int) -> Optional[IQAirEntity]:
        """Get IQAir data by ID"""
        return self.db.query(IQAirEntity).filter(IQAirEntity.id == iqair_id).first()

    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[IQAirEntity]:
        """Get all IQAir data records, ordered by most recent"""
        query = self.db.query(IQAirEntity).order_by(desc(IQAirEntity.created_at))
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()

    def get_latest(self) -> Optional[IQAirEntity]:
        """Get the most recent IQAir data record"""
        return self.db.query(IQAirEntity).order_by(desc(IQAirEntity.created_at)).first()

    def update(self, iqair_data: IQAirEntity) -> IQAirEntity:
        """Update an existing IQAir data record"""
        iqair_data.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(iqair_data)
        return iqair_data

    def delete(self, iqair_data: IQAirEntity):
        """Delete an IQAir data record"""
        self.db.delete(iqair_data)
        self.db.commit()

    def count(self) -> int:
        """Get total count of IQAir data records"""
        return self.db.query(IQAirEntity).count()

