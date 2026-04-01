"""
Health Service - Business Layer
Contains business logic for system health checks
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any

from src.business.services.health.infrastructure_service import InfrastructureService

logger = logging.getLogger(__name__)


class HealthService:
    """Service responsible for business logic of health checks"""

    def __init__(self, infrastructure_service: InfrastructureService):
        self.infrastructure_service = infrastructure_service

    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """
        Returns comprehensive system health check

        Returns:
            Dict[str, Any]: Complete system status
        """
        start_time = time.time()

        # Execute all checks in parallel
        tasks = [
            self.infrastructure_service.check_database_health(),
            self.infrastructure_service.check_system_resources(),
            self.infrastructure_service.check_external_services()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Organize results
        health_data = {
            "database": results[0] if not isinstance(results[0], Exception) else {
                "status": "unhealthy",
                "error": str(results[0])
            },
            "system": results[1] if not isinstance(results[1], Exception) else {
                "status": "unhealthy",
                "error": str(results[1])
            },
            "external_services": results[2] if not isinstance(results[2], Exception) else {
                "status": "unhealthy",
                "error": str(results[2])
            }
        }

        # Determine overall status based on business logic
        overall_status = self._determine_overall_status(health_data)

        total_time = time.time() - start_time

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(total_time * 1000, 2),
            "version": "0.1.0",
            "components": health_data
        }

    def _determine_overall_status(self, health_data: Dict[str, Any]) -> str:
        """
        Determines overall status based on business logic

        Args:
            health_data: Health data from components

        Returns:
            str: Overall status (healthy, warning, unhealthy)
        """
        # Business logic to determine status
        critical_components = ["database", "system"]
        warning_components = ["external_services"]

        # Check critical components
        for component in critical_components:
            if component in health_data:
                status = health_data[component].get("status", "unknown")
                if status not in ["healthy", "warning"]:
                    return "unhealthy"

        # Check warning components
        warning_count = 0
        for component in warning_components:
            if component in health_data:
                status = health_data[component].get("status", "unknown")
                if status == "warning":
                    warning_count += 1
                elif status not in ["healthy", "warning"]:
                    # External services are not critical, so we don't fail if they're down
                    pass

        # If many components in warning, consider warning
        if warning_count >= 1:
            return "warning"

        return "healthy"

    async def get_simple_health(self) -> Dict[str, Any]:
        """
        Returns simple health check (basic status only)

        Returns:
            Dict[str, Any]: Simple status
        """
        try:
            # Quick check only of database
            db_health = await self.infrastructure_service.check_database_health()

            return {
                "status": "healthy" if db_health.get("status") == "healthy" else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "0.1.0"
            }
        except Exception as e:
            logger.error(f"Erro no health check simples: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "version": "0.1.0"
            }

