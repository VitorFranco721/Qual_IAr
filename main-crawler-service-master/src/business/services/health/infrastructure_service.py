"""
Infrastructure Service - Infrastructure Layer
Contains technical checks for infrastructure components
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.config.database import engine, get_db

logger = logging.getLogger(__name__)


class InfrastructureService:
    """Service responsible for technical infrastructure checks"""

    def __init__(self):
        self.engine = engine

    async def check_database_health(self) -> Dict[str, Any]:
        """
        Checks database technical health

        Returns:
            Dict[str, Any]: Database technical status
        """
        try:
            start_time = time.time()

            # Basic connection test
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as health_check"))
                result.fetchone()

            # Connection pool test
            pool_status = {
                "pool_size": self.engine.pool.size(),
                "checked_in": self.engine.pool.checkedin(),
                "checked_out": self.engine.pool.checkedout(),
                "overflow": self.engine.pool.overflow()
            }

            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "pool_status": pool_status,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Falha no health check do banco de dados: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def check_system_resources(self) -> Dict[str, Any]:
        """
        Checks system technical resources

        Returns:
            Dict[str, Any]: System resources technical status
        """
        if not PSUTIL_AVAILABLE:
            return {
                "status": "warning",
                "message": "psutil not available - system metrics disabled",
                "timestamp": datetime.utcnow().isoformat()
            }

        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory
            memory = psutil.virtual_memory()
            memory_available_gb = round(memory.available / (1024**3), 2)
            memory_percent = memory.percent

            # Disk
            disk = psutil.disk_usage('/')
            disk_free_gb = round(disk.free / (1024**3), 2)
            disk_percent = round((disk.used / disk.total) * 100, 2)

            # Current process
            process = psutil.Process()
            process_memory_mb = round(process.memory_info().rss / (1024**2), 2)
            process_cpu_percent = process.cpu_percent()

            # Determine status based on technical thresholds
            status = "healthy"
            if cpu_percent > 80 or memory_percent > 85 or disk_percent > 90:
                status = "warning"
            if cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
                status = "critical"

            return {
                "status": status,
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "usage_percent": memory_percent,
                    "available_gb": memory_available_gb
                },
                "disk": {
                    "usage_percent": disk_percent,
                    "free_gb": disk_free_gb
                },
                "process": {
                    "memory_mb": process_memory_mb,
                    "cpu_percent": process_cpu_percent
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Falha no health check de recursos do sistema: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def check_external_services(self) -> Dict[str, Any]:
        """
        Checks external services (IQAir)

        Returns:
            Dict[str, Any]: External services status
        """
        services_status = {}

        # Check IQAir
        services_status['iqair'] = await self._check_iqair_health()

        # Determine overall status
        all_healthy = all(s.get("status") == "healthy" for s in services_status.values())
        any_unhealthy = any(s.get("status") == "unhealthy" for s in services_status.values())

        overall_status = "healthy" if all_healthy else ("unhealthy" if any_unhealthy else "warning")

        return {
            "status": overall_status,
            "services": services_status,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _check_iqair_health(self) -> Dict[str, Any]:
        """
        Checks IQAir technical health

        Returns:
            Dict[str, Any]: IQAir technical status
        """
        try:
            import requests

            start_time = time.time()

            # Test connectivity to IQAir
            response = requests.get(
                "https://www.iqair.com",
                timeout=5,
                allow_redirects=True
            )
            response.raise_for_status()

            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "url": "https://www.iqair.com"
            }

        except Exception as e:
            logger.error(f"Falha no health check do IQAir: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "url": "https://www.iqair.com"
            }

