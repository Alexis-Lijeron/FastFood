"""
Bot de Telegram - Configuración y ejecución principal
"""
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from app.config import get_settings
from app.bot.handlers import (
    start_command,
    menu_command,
    carrito_command,
    cancelar_command,
    mispedidos_command,
    rastrear_command,
    handle_callbacks,
    handle_location,
    handle_text,
    handle_contact,
    handle_omitir_telefono
)


def create_bot_application() -> Application:
    """
    Crea y configura la aplicación del bot
    """
    settings = get_settings()
    
    # Crear la aplicación
    application = Application.builder().token(settings.token_telegram).build()
    
    # Registrar handlers de comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("carrito", carrito_command))
    application.add_handler(CommandHandler("cancelar", cancelar_command))
    application.add_handler(CommandHandler("mispedidos", mispedidos_command))
    application.add_handler(CommandHandler("rastrear", rastrear_command))
    application.add_handler(CommandHandler("help", start_command))
    
    # Handler para callbacks (botones inline) - PRINCIPAL
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    
    # Handler para contacto (teléfono)
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # Handler para ubicación
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    
    # Handler para omitir teléfono y volver al menú
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex("^(❌ Omitir por ahora|🔙 Volver al menú)$"), handle_omitir_telefono)
    )
    
    # Handler para texto general (debe ir al final)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    return application


def run_bot():
    """
    Ejecuta el bot en modo polling
    """
    print("🤖 Iniciando SpeedyFoodBot...")
    application = create_bot_application()
    
    print("✅ Bot configurado correctamente")
    print("📡 Escuchando mensajes...")
    
    # Ejecutar el bot
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
