"""
Dependency Injection System - Shared Layer
Centralizes creation and injection of dependencies

Pattern:
1. Repositories (depend on db: Session)
2. Services without dependencies
3. Services with dependencies (inject via Depends)
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from src.infrastructure.config.database import get_db

# Repositories
from src.persistence.repositories.iqair.iqair_repository import IQAirRepository

# Services
from src.business.services.iqair.iqair_controller import IQAirController
from src.business.services.health.health_service import HealthService
from src.business.services.health.infrastructure_service import InfrastructureService

# ======================================
# REPOSITORIES (depend on db: Session)
# ======================================

def get_iqair_repository(db: Session = Depends(get_db)) -> IQAirRepository:
    """
    Creates and returns an instance of IQAirRepository

    Args:
        db: Database session

    Returns:
        IQAirRepository: Instance of the repository
    """
    return IQAirRepository(db)


# ======================================
# SERVICES WITHOUT DEPENDENCIES
# ======================================

def get_infrastructure_service() -> InfrastructureService:
    """
    Creates and returns an instance of InfrastructureService

    Returns:
        InfrastructureService: Instance of the infrastructure service
    """
    return InfrastructureService()


# ======================================
# SERVICES WITH DEPENDENCIES
# ======================================

def get_iqair_controller(
    iqair_repository: IQAirRepository = Depends(get_iqair_repository)
) -> IQAirController:
    """
    Creates and returns an instance of IQAirController

    Args:
        iqair_repository: Repository for IQAir data

    Returns:
        IQAirController: Instance of the IQAir controller
    """
    return IQAirController(iqair_repository)


def get_health_service(
    infrastructure_service: InfrastructureService = Depends(get_infrastructure_service)
) -> HealthService:
    """
    Creates and returns an instance of HealthService

    Args:
        infrastructure_service: Infrastructure service

    Returns:
        HealthService: Instance of the health service
    """
    return HealthService(infrastructure_service)
