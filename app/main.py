"""
SpeedyFoodBot - API FastAPI + Bot Telegram
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import categorias, productos, clientes, conductores, pedidos
from app.bot.bot import create_bot_application
from app.database import SessionLocal
from app.models import Pedido, Conductor
from app.services.conductor_service import asignar_conductor_a_pedido


# Variable global para la aplicación del bot
bot_app = None
# Variable para controlar el task de asignación automática
asignacion_task = None

# Configuración de asignación automática
INTERVALO_ASIGNACION_SEGUNDOS = 30  # Cada 30 segundos


async def asignar_pedidos_automaticamente():
    """
    Task que se ejecuta periódicamente para asignar pedidos SOLICITADOS
    a conductores disponibles automáticamente.
    """
    while True:
        try:
            db = SessionLocal()
            
            # Buscar pedidos en estado SOLICITADO sin conductor
            pedidos_pendientes = db.query(Pedido).filter(
                Pedido.estado == "SOLICITADO",
                Pedido.conductor_codigo.is_(None)
            ).order_by(Pedido.fecha.asc()).all()  # Ordenar por antigüedad
            
            if pedidos_pendientes:
                print(f"🔄 Asignación automática: {len(pedidos_pendientes)} pedidos pendientes")
                
                for pedido in pedidos_pendientes:
                    # Verificar si hay conductores disponibles
                    conductor_disponible = db.query(Conductor).filter(
                        Conductor.is_disponible == True,
                        Conductor.latitud.isnot(None),
                        Conductor.longitud.isnot(None)
                    ).first()
                    
                    if not conductor_disponible:
                        print("⚠️ No hay conductores disponibles")
                        break
                    
                    # Asignar conductor más cercano
                    resultado = asignar_conductor_a_pedido(db, pedido.codigo_pedido)
                    
                    if resultado["exito"]:
                        print(f"✅ Pedido {pedido.codigo_pedido} asignado a {resultado.get('conductor', 'N/A')}")
                    else:
                        print(f"⚠️ No se pudo asignar {pedido.codigo_pedido}: {resultado['mensaje']}")
            
            db.close()
            
        except Exception as e:
            print(f"❌ Error en asignación automática: {e}")
        
        # Esperar antes de la siguiente verificación
        await asyncio.sleep(INTERVALO_ASIGNACION_SEGUNDOS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    Inicia el bot de Telegram y el sistema de asignación automática.
    """
    global bot_app, asignacion_task
    
    print("🚀 Iniciando SpeedyFoodBot...")
    
    # Crear e iniciar el bot de Telegram
    bot_app = create_bot_application()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    print("✅ Bot de Telegram iniciado")
    
    # Iniciar task de asignación automática
    asignacion_task = asyncio.create_task(asignar_pedidos_automaticamente())
    print(f"🔄 Asignación automática iniciada (cada {INTERVALO_ASIGNACION_SEGUNDOS} segundos)")
    
    print("📡 API FastAPI lista en http://localhost:8000")
    print("📖 Documentación en http://localhost:8000/docs")
    
    yield  # La aplicación se ejecuta aquí
    
    # Apagar el task de asignación
    print("🛑 Deteniendo asignación automática...")
    if asignacion_task:
        asignacion_task.cancel()
        try:
            await asignacion_task
        except asyncio.CancelledError:
            pass
    
    # Apagar el bot cuando se cierra FastAPI
    print("🛑 Deteniendo bot de Telegram...")
    await bot_app.updater.stop()
    await bot_app.stop()
    await bot_app.shutdown()


# Crear instancia de FastAPI con lifespan
app = FastAPI(
    title="SpeedyFoodBot API",
    description="API para el sistema de delivery de comida rápida",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS (permite peticiones desde cualquier origen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(categorias.router)
app.include_router(productos.router)
app.include_router(clientes.router)
app.include_router(conductores.router)
app.include_router(pedidos.router)


@app.get("/", tags=["Root"])
def root():
    """Endpoint raíz - Info de la API"""
    return {
        "nombre": "SpeedyFoodBot API",
        "version": "1.0.0",
        "docs": "/docs",
        "estado": "🚀 En línea"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check para verificar que la API está funcionando"""
    settings = get_settings()
    return {
        "status": "healthy",
        "database": settings.postgres_db,
        "host": settings.postgres_host
    }


@app.get("/asignacion/estado", tags=["Asignación Automática"])
def estado_asignacion():
    """Ver estado del sistema de asignación automática"""
    db = SessionLocal()
    try:
        # Contar pedidos pendientes
        pedidos_solicitados = db.query(Pedido).filter(
            Pedido.estado == "SOLICITADO",
            Pedido.conductor_codigo.is_(None)
        ).count()
        
        # Contar conductores disponibles
        conductores_disponibles = db.query(Conductor).filter(
            Conductor.is_disponible == True,
            Conductor.latitud.isnot(None),
            Conductor.longitud.isnot(None)
        ).count()
        
        return {
            "asignacion_automatica": "activa",
            "intervalo_segundos": INTERVALO_ASIGNACION_SEGUNDOS,
            "pedidos_pendientes": pedidos_solicitados,
            "conductores_disponibles": conductores_disponibles
        }
    finally:
        db.close()


# Para ejecutar directamente: python -m app.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
