"""
SpeedyFoodBot - API FastAPI + Bot Telegram
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import categorias, productos, clientes, conductores, pedidos
from app.bot.bot import create_bot_application


# Variable global para la aplicación del bot
bot_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    Inicia el bot de Telegram cuando arranca FastAPI.
    """
    global bot_app
    
    print("🚀 Iniciando SpeedyFoodBot...")
    
    # Crear e iniciar el bot de Telegram
    bot_app = create_bot_application()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    
    print("✅ Bot de Telegram iniciado")
    print("📡 API FastAPI lista en http://localhost:8000")
    print("📖 Documentación en http://localhost:8000/docs")
    
    yield  # La aplicación se ejecuta aquí
    
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


# Para ejecutar directamente: python -m app.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
