from app.routers.health import router as health_router
from app.routers.datasets import router as datasets_router
from app.routers.models import router as models_router
from app.routers.predictions import router as predictions_router

__all__ = ["health_router", "datasets_router", "models_router", "predictions_router"]
