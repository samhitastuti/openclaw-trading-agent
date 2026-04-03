"""
FastAPI Server - Main HTTP API for OpenClaw Trading Agent
"""

import logging
import os

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import components
from backend.integrations.alpaca_client import AlpacaClient
from backend.security.file_access_controller import get_file_access_controller

# Import shared Pydantic schemas
from backend.api.schemas import (  # noqa: F401 - re-exported for convenience
    AccountInfo,
    AnalysisRequest,
    AnalysisResponse,
    AuditEntry,
    PolicyConstraint,
    PolicyResponse,
    Position,
    TradeRequest,
    TradeResponse,
)

# Import route factories
from backend.api.routes import (
    account_routes,
    audit_routes,
    demo_routes,
    health_routes,
    market_routes,
    policy_routes,
    trading_routes,
)


# ===============================================
# INITIALIZE APP & COMPONENTS
# ===============================================

app = FastAPI(
    title="OpenClaw Trading Agent",
    description="Autonomous trading with ArmorClaw enforcement",
    version="1.0.0",
)

logger.info("🚀 Initializing FastAPI server...")

# Initialize Alpaca client
try:
    alpaca_client = AlpacaClient()
    logger.info("✅ AlpacaClient initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize AlpacaClient: {e}")
    alpaca_client = None

# Initialize file access controller
file_controller = get_file_access_controller(
    allowed_output_dir=os.getenv("ALLOWED_OUTPUT_DIR", "outputs/")
)
logger.info("✅ FileAccessController initialized")

# ===============================================
# INCLUDE ROUTE MODULES
# ===============================================

app.include_router(health_routes(alpaca_client=alpaca_client))
app.include_router(trading_routes())
app.include_router(market_routes(alpaca_client=alpaca_client))
app.include_router(account_routes(alpaca_client=alpaca_client))
app.include_router(policy_routes())
app.include_router(audit_routes())
app.include_router(demo_routes())


# ===============================================
# FILE ACCESS TEST ENDPOINT
# ===============================================

@app.get("/api/test/file-access/{operation}/{file_path:path}")
async def test_file_access(operation: str, file_path: str):
    """Test file access control"""

    if operation == "read":
        allowed, reason = file_controller.is_read_allowed(file_path)
        return {
            "operation": "read",
            "file_path": file_path,
            "allowed": allowed,
            "reason": reason,
        }
    elif operation == "write":
        allowed, reason = file_controller.is_write_allowed(file_path)
        return {
            "operation": "write",
            "file_path": file_path,
            "allowed": allowed,
            "reason": reason,
        }
    else:
        raise HTTPException(status_code=400, detail="Unknown operation. Use 'read' or 'write'.")


# ===============================================
# ROOT ENDPOINT
# ===============================================

@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "OpenClaw Trading Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "trading": "/api/trade",
            "market_data": "/api/market-data/{ticker}",
            "account": "/api/account",
            "positions": "/api/positions",
            "policy": "/api/policy",
            "audit": "/api/audit/decisions",
            "demos": [
                "/api/demo/allowed-scenario",
                "/api/demo/blocked-scenario-size",
                "/api/demo/blocked-scenario-ticker",
                "/api/demo/blocked-scenario-credential",
            ]
        }
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))

    logger.info(f"🚀 Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

