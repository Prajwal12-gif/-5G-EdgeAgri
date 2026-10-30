import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.cloud_sync import cloud_sync
from backend.app.mqtt_service import mqtt_service
from backend.app.virtual_sensors import virtual_sensors
from backend.app.edge_engine import edge_engine

from backend.app.routes import telemetry, alerts, edge, actuators, network, benchmark

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("5G-EdgeAgri-Main")

# Connected WebSocket clients manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_json(self, message: dict):
        dead_connections = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self.active_connections.discard(dead)

ws_manager = ConnectionManager()

# Background telemetry generator & edge processing loop
telemetry_task = None

async def run_telemetry_loop():
    logger.info("Starting Autonomous 5G Virtual Sensor & Edge Processing Loop...")
    tick_count = 0
    while True:
        try:
            readings = virtual_sensors.generate_step()
            tick_count += 1
            
            # Evaluate edge engine for each zone reading
            evaluations = []
            for r in readings:
                eval_res = edge_engine.evaluate_reading(r)
                evaluations.append(eval_res)
                
                # Check for generated alerts
                for alert in eval_res.get("alerts", []):
                    alert_record = await asyncio.to_thread(cloud_sync.save_alert, alert)
                    # Broadcast alert immediately via WebSocket
                    await ws_manager.broadcast_json({
                        "event": "NEW_ALERT",
                        "data": {
                            "id": alert_record.id,
                            "timestamp": alert_record.timestamp.isoformat(),
                            "zone_id": alert_record.zone_id,
                            "zone_name": alert_record.zone_name,
                            "alert_type": alert_record.alert_type,
                            "severity": alert_record.severity,
                            "message": alert_record.message,
                            "suggested_action": alert_record.suggested_action,
                            "response_latency_ms": alert_record.response_latency_ms,
                            "source": "EDGE"
                        }
                    })

                # Log actuation if triggered autonomously
                actuation = eval_res.get("actuation_trigger")
                if actuation:
                    virtual_sensors.trigger_water_replenishment(actuation["zone_id"], actuation.get("dosage_liters", 150.0))
                    await asyncio.to_thread(cloud_sync.log_actuation, actuation)

                # Persist readings to SQLite via thread pool
                await asyncio.to_thread(cloud_sync.save_reading, r)

            # Broadcast live state to all connected React clients
            await ws_manager.broadcast_json({
                "event": "TELEMETRY_UPDATE",
                "tick": tick_count,
                "readings": readings,
                "evaluations": evaluations,
                "actuators": edge_engine.active_actuators
            })

        except Exception as e:
            logger.error(f"Error in telemetry loop: {e}", exc_info=True)

        await asyncio.sleep(settings.TELEMETRY_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global telemetry_task
    logger.info(f"Initializing {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}...")
    
    # 1. Initialize SQLite Database
    init_db()
    cloud_sync.seed_default_edge_configs()
    
    # 2. Start MQTT Service (Mosquitto with auto-fallback)
    mqtt_service.start()
    
    # 3. Start background sensor generator if enabled
    if settings.SIMULATION_ENABLED:
        telemetry_task = asyncio.create_task(run_telemetry_loop())
    
    yield
    
    # Shutdown
    if telemetry_task:
        telemetry_task.cancel()
    mqtt_service.stop()
    logger.info("5G-EdgeAgri backend shut down cleanly.")

app = FastAPI(
    title="5G-EdgeAgri: Intelligent Smart Agriculture Using 5G & Edge Computing",
    description="Backend API and Edge Processing Engine for 5G Smart Agriculture with Virtual Sensors and Mosquitto MQTT",
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# CORS Middleware (permits React dev server and production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(telemetry.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(edge.router, prefix=settings.API_V1_PREFIX)
app.include_router(actuators.router, prefix=settings.API_V1_PREFIX)
app.include_router(network.router, prefix=settings.API_V1_PREFIX)
app.include_router(benchmark.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "project": "5G-EdgeAgri",
        "title": "A Software-Based 5G-Enabled Edge Computing Framework for Real-Time Smart Agriculture",
        "authors": [
            "1NT24CS202 - Prajwal Karadi",
            "1NT24CS190 - Padavala Rishi"
        ],
        "department": "B.E Computer Science and Engineering",
        "status": "ONLINE",
        "docs_url": "/docs",
        "mqtt_status": mqtt_service.broker_mode,
        "is_simulated": True
    }

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send immediate initial state
        await websocket.send_json({
            "event": "INITIAL_STATE",
            "readings": list(virtual_sensors.latest_telemetry.values()),
            "actuators": edge_engine.active_actuators,
            "broker_mode": mqtt_service.broker_mode
        })
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
