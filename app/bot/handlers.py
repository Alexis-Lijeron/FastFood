"""
Handlers para el bot de Telegram - Maneja los comandos y mensajes
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from app.bot.keyboards import (
    get_main_menu_keyboard,
    get_categorias_keyboard,
    get_productos_keyboard,
    get_cantidad_keyboard,
    get_confirmar_pedido_keyboard,
    get_ubicacion_keyboard,
    get_metodo_pago_keyboard,
    get_solicitar_telefono_keyboard,
    get_mis_pedidos_keyboard,
    get_detalle_pedido_keyboard,
    get_rastrear_keyboard,
    get_tracking_keyboard
)
from app.database import SessionLocal
from app.models import Categoria, Producto, ClienteBot, Pedido, ItemPedido, Conductor
from decimal import Decimal
import random
import string


def get_db():
    """Obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Se cierra manualmente después


def generar_codigo_pedido() -> str:
    """Genera un código único para el pedido"""
    chars = string.ascii_uppercase + string.digits
    return f"PED-{''.join(random.choices(chars, k=6))}"


# ============ COMANDO /start ============
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Inicia el bot y muestra el menú principal"""
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    
    # Registrar o actualizar cliente en la BD
    db = get_db()
    try:
        cliente = db.query(ClienteBot).filter(ClienteBot.chat_id == chat_id).first()
        if not cliente:
            # Cliente nuevo - solicitar teléfono
            context.user_data['carrito'] = []
            context.user_data['nuevo_usuario'] = True
            
            mensaje = f"""
🍔 *¡Bienvenido a SpeedyFood, {user.first_name}!* 🍔

Soy tu asistente de delivery de comida rápida.

Para brindarte un mejor servicio, por favor comparte tu número de teléfono 📱
"""
            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=get_solicitar_telefono_keyboard()
            )
            return
        else:
            # Cliente existente
            context.user_data['carrito'] = []
    finally:
        db.close()
    
    # Mostrar menú principal
    mensaje = f"""
🍔 *¡Hola de nuevo, {user.first_name}!* 🍔

¿Qué deseas hacer hoy?

Usa los botones del menú 👇
"""
    await update.message.reply_text(
        mensaje,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )


# ============ COMANDO /menu ============
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /menu - Muestra las categorías"""
    await mostrar_categorias(update, context)


async def mostrar_categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las categorías disponibles"""
    db = get_db()
    try:
        categorias = db.query(Categoria).all()
        
        if not categorias:
            await update.message.reply_text("😢 No hay categorías disponibles por el momento.")
            return
        
        mensaje = "🍽️ *NUESTRO MENÚ*\n\nSelecciona una categoría:"
        await update.message.reply_text(
            mensaje,
            parse_mode='Markdown',
            reply_markup=get_categorias_keyboard(categorias)
        )
    finally:
        db.close()


# ============ MANEJADOR DE BOTONES DEL MENÚ PRINCIPAL ============
async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los botones del menú principal (ReplyKeyboard)"""
    text = update.message.text
    
    if text == "🍔 Ver Menú":
        await mostrar_categorias(update, context)
    
    elif text == "🛒 Iniciar Pedido":
        context.user_data['carrito'] = []
        await update.message.reply_text(
            "🛒 *Nuevo pedido iniciado*\n\nSelecciona productos del menú para agregar.",
            parse_mode='Markdown'
        )
        await mostrar_categorias(update, context)
    
    elif text == "➕ Agregar Producto":
        await mostrar_categorias(update, context)
    
    elif text == "📝 Agregar Detalles":
        context.user_data['esperando_detalles'] = True
        await update.message.reply_text(
            "📝 *Escribe los detalles adicionales para tu pedido:*\n\n"
            "Ejemplo: Sin cebolla, extra salsa, etc.",
            parse_mode='Markdown'
        )
    
    elif text == "📋 Ver Resumen":
        await mostrar_resumen(update, context)
    
    elif text == "✅ Pagar Pedido":
        await procesar_pago(update, context)
    
    elif text == "📞 Contacto":
        await update.message.reply_text(
            "📞 *CONTACTO*\n\n"
            "📱 WhatsApp: +591 70000000\n"
            "☎️ Teléfono: 3-123456\n"
            "📧 Email: contacto@speedyfood.com\n\n"
            "¡Estamos para servirte! 😊",
            parse_mode='Markdown'
        )
    
    elif text == "🕐 Horarios":
        await update.message.reply_text(
            "🕐 *HORARIOS DE ATENCIÓN*\n\n"
            "🗓️ Lunes a Viernes:\n"
            "   11:00 AM - 10:00 PM\n\n"
            "🗓️ Sábados y Domingos:\n"
            "   12:00 PM - 11:00 PM\n\n"
            "🎉 ¡Abierto todos los días!",
            parse_mode='Markdown'
        )
    
    elif text == "🚚 Delivery":
        await update.message.reply_text(
            "🚚 *INFORMACIÓN DE DELIVERY*\n\n"
            "📍 Zona de cobertura: 5 km a la redonda\n"
            "💰 Costo de envío: Bs. 10\n"
            "⏱️ Tiempo estimado: 30-45 min\n\n"
            "📍 Para hacer tu pedido, necesitaremos tu ubicación.",
            parse_mode='Markdown',
            reply_markup=get_ubicacion_keyboard()
        )
    
    elif text == "❓ Ayuda":
        await update.message.reply_text(
            "❓ *AYUDA*\n\n"
            "*Comandos disponibles:*\n"
            "/start - Iniciar el bot\n"
            "/menu - Ver el menú\n"
            "/carrito - Ver tu carrito\n"
            "/cancelar - Cancelar pedido actual\n\n"
            "*¿Cómo hacer un pedido?*\n"
            "1️⃣ Presiona 'Ver Menú'\n"
            "2️⃣ Selecciona una categoría\n"
            "3️⃣ Elige tus productos\n"
            "4️⃣ Revisa el resumen\n"
            "5️⃣ Confirma y paga\n\n"
            "¿Dudas? Contáctanos 📞",
            parse_mode='Markdown'
        )
    
    elif text == "🔙 Volver al menú":
        await update.message.reply_text(
            "📋 *Menú Principal*",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )


# ============ MANEJADOR DE CALLBACKS (Botones Inline) ============
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks de los botones inline"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Función helper para enviar mensaje (maneja fotos y texto)
    async def enviar_mensaje(texto: str, reply_markup=None):
        """Envía o edita mensaje, manejando fotos y texto"""
        try:
            if query.message.photo:
                # Es una foto, eliminar y enviar nuevo mensaje
                await query.message.delete()
                await query.message.chat.send_message(
                    texto,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                # Es texto, editar
                await query.edit_message_text(
                    texto,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        except Exception:
            # Fallback: enviar nuevo mensaje
            await query.message.chat.send_message(
                texto,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    # ============ MENÚ PRINCIPAL ============
    if data == "menu_ver" or data == "ver_categorias" or data == "producto_agregar":
        db = get_db()
        try:
            categorias = db.query(Categoria).all()
            await enviar_mensaje(
                "🍽️ *NUESTRO MENÚ*\n\nSelecciona una categoría:",
                reply_markup=get_categorias_keyboard(categorias)
            )
        finally:
            db.close()
    
    elif data == "pedido_iniciar":
        context.user_data['carrito'] = []
        db = get_db()
        try:
            categorias = db.query(Categoria).all()
            await enviar_mensaje(
                "🛒 *NUEVO PEDIDO INICIADO*\n\n"
                "Tu carrito está vacío.\n"
                "Selecciona productos del menú:\n",
                reply_markup=get_categorias_keyboard(categorias)
            )
        finally:
            db.close()
    
    elif data == "detalles_agregar":
        context.user_data['esperando_detalles'] = True
        keyboard = [[InlineKeyboardButton("🔙 Cancelar", callback_data="volver_menu")]]
        await enviar_mensaje(
            "📝 *AGREGAR DETALLES*\n\n"
            "Escribe los detalles adicionales para tu pedido:\n\n"
            "_Ejemplo: Sin cebolla, extra salsa, etc._",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "resumen_ver":
        await mostrar_resumen_callback(query, context)
    
    elif data == "pagar_pedido":
        carrito = context.user_data.get('carrito', [])
        if not carrito:
            keyboard = [[InlineKeyboardButton("🔙 Volver al menú", callback_data="volver_menu")]]
            await enviar_mensaje(
                "🛒 *Tu carrito está vacío*\n\nAgrega productos para hacer un pedido.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        await enviar_mensaje(
            "💳 *MÉTODO DE PAGO*\n\nSelecciona cómo deseas pagar:",
            reply_markup=get_metodo_pago_keyboard()
        )
    
    elif data == "info_contacto":
        keyboard = [[InlineKeyboardButton("🔙 Volver al menú", callback_data="volver_menu")]]
        await enviar_mensaje(
            "📞 *CONTACTO*\n\n"
            "📱 WhatsApp: +591 70000000\n"
            "☎️ Teléfono: 3-123456\n"
            "📧 Email: contacto@speedyfood.com\n\n"
            "¡Estamos para servirte! 😊",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "info_horarios":
        keyboard = [[InlineKeyboardButton("🔙 Volver al menú", callback_data="volver_menu")]]
        await enviar_mensaje(
            "🕐 *HORARIOS DE ATENCIÓN*\n\n"
            "🗓️ Lunes a Viernes:\n"
            "   11:00 AM - 10:00 PM\n\n"
            "🗓️ Sábados y Domingos:\n"
            "   12:00 PM - 11:00 PM\n\n"
            "🎉 ¡Abierto todos los días!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "info_delivery":
        keyboard = [
            [InlineKeyboardButton("📍 Enviar Ubicación", callback_data="solicitar_ubicacion")],
            [InlineKeyboardButton("🔙 Volver al menú", callback_data="volver_menu")]
        ]
        await enviar_mensaje(
            "🚚 *INFORMACIÓN DE DELIVERY*\n\n"
            "📍 Zona de cobertura: 5 km a la redonda\n"
            "💰 Costo de envío: Bs. 10\n"
            "⏱️ Tiempo estimado: 30-45 min\n\n"
            "📍 Para hacer tu pedido, necesitaremos tu ubicación.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "info_ayuda":
        keyboard = [[InlineKeyboardButton("🔙 Volver al menú", callback_data="volver_menu")]]
        await enviar_mensaje(
            "❓ *AYUDA*\n\n"
            "*¿Cómo hacer un pedido?*\n"
            "1️⃣ Presiona 'Ver Menú'\n"
            "2️⃣ Selecciona una categoría\n"
            "3️⃣ Elige tus productos\n"
            "4️⃣ Revisa el resumen\n"
            "5️⃣ Confirma y paga\n\n"
            "*Comandos útiles:*\n"
            "/start - Reiniciar bot\n"
            "/menu - Ver menú\n"
            "/carrito - Ver carrito\n"
            "/mispedidos - Ver mis pedidos\n\n"
            "¿Dudas? Contáctanos 📞",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # ============ MIS PEDIDOS Y RASTREO ============
    elif data == "mis_pedidos":
        # Limpiar mensajes de ubicación al volver a la lista
        await limpiar_mensajes_ubicacion(query, context)
        await mostrar_mis_pedidos(query, context)
    
    elif data == "rastrear_pedido":
        await enviar_mensaje(
            "🔍 *RASTREAR PEDIDO*\n\n"
            "Puedes ver el estado de tus pedidos y la ubicación del repartidor.\n\n"
            "Selecciona 'Ver Mis Pedidos' para ver todos tus pedidos activos:",
            reply_markup=get_rastrear_keyboard()
        )
    
    elif data.startswith("ver_pedido_"):
        codigo_pedido = data.replace("ver_pedido_", "")
        await mostrar_detalle_pedido(query, context, codigo_pedido)
    
    elif data.startswith("ubicacion_conductor_"):
        codigo_pedido = data.replace("ubicacion_conductor_", "")
        await mostrar_ubicacion_conductor(query, context, codigo_pedido)
    
    elif data.startswith("tracking_live_"):
        codigo_pedido = data.replace("tracking_live_", "")
        await iniciar_tracking_live(query, context, codigo_pedido)
    
    elif data.startswith("stop_tracking_"):
        codigo_pedido = data.replace("stop_tracking_", "")
        await detener_tracking_live(query, context, codigo_pedido)
    
    elif data.startswith("actualizar_pedido_"):
        codigo_pedido = data.replace("actualizar_pedido_", "")
        await mostrar_detalle_pedido(query, context, codigo_pedido)
    
    elif data == "volver_menu":
        # Limpiar mensajes de ubicación pendientes
        await limpiar_mensajes_ubicacion(query, context)
        await enviar_mensaje(
            "🍔 *MENÚ PRINCIPAL*\n\n¿Qué deseas hacer?",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif data == "solicitar_ubicacion":
        await query.message.reply_text(
            "📍 Por favor, envía tu ubicación:",
            reply_markup=get_ubicacion_keyboard()
        )
    
    # Seleccionar categoría - MOSTRAR PRODUCTOS CON IMÁGENES
    elif data.startswith("categoria_"):
        codigo_cat = data.replace("categoria_", "")
        db = get_db()
        try:
            categoria = db.query(Categoria).filter(Categoria.codigo_categoria == codigo_cat).first()
            productos = db.query(Producto).filter(Producto.codigo_categoria == codigo_cat).all()
            
            if not productos:
                await enviar_mensaje(
                    f"😢 No hay productos en {categoria.nombre}",
                    reply_markup=get_categorias_keyboard(db.query(Categoria).all())
                )
                return
            
            # Guardar la categoría actual en el contexto
            context.user_data['categoria_actual'] = codigo_cat
            
            # Eliminar mensaje anterior
            try:
                await query.message.delete()
            except:
                pass
            
            # Enviar cada producto con su imagen
            for prod in productos:
                caption = f"🍽️ *{prod.nombre}*\n\n📝 {prod.descripcion or 'Delicioso!'}\n💰 *Bs. {prod.precio}*"
                
                # Botones para este producto
                keyboard = [
                    [
                        InlineKeyboardButton("1️⃣", callback_data=f"cantidad_{prod.codigo_producto}_1"),
                        InlineKeyboardButton("2️⃣", callback_data=f"cantidad_{prod.codigo_producto}_2"),
                        InlineKeyboardButton("3️⃣", callback_data=f"cantidad_{prod.codigo_producto}_3"),
                    ],
                    [
                        InlineKeyboardButton("4️⃣", callback_data=f"cantidad_{prod.codigo_producto}_4"),
                        InlineKeyboardButton("5️⃣", callback_data=f"cantidad_{prod.codigo_producto}_5"),
                        InlineKeyboardButton("6️⃣", callback_data=f"cantidad_{prod.codigo_producto}_6"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if prod.img_url:
                    try:
                        await query.message.chat.send_photo(
                            photo=prod.img_url,
                            caption=caption,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                    except:
                        # Si falla la imagen, enviar sin ella
                        await query.message.chat.send_message(
                            caption,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                else:
                    await query.message.chat.send_message(
                        caption,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
            
            # Enviar mensaje con opciones de navegación
            nav_keyboard = [
                [
                    InlineKeyboardButton("📋 Ver Resumen", callback_data="resumen_ver"),
                    InlineKeyboardButton("🔙 Categorías", callback_data="menu_ver")
                ],
                [InlineKeyboardButton("🏠 Volver al Inicio", callback_data="volver_menu")]
            ]
            await query.message.chat.send_message(
                f"👆 *{categoria.nombre}* - Selecciona la cantidad que deseas",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(nav_keyboard)
            )
        finally:
            db.close()
    
    # Seleccionar cantidad (desde imagen de producto)
    elif data.startswith("cantidad_"):
        parts = data.split("_")
        codigo_prod = parts[1]
        cantidad = int(parts[2])
        
        db = get_db()
        try:
            producto = db.query(Producto).filter(Producto.codigo_producto == codigo_prod).first()
            
            # Agregar al carrito
            if 'carrito' not in context.user_data:
                context.user_data['carrito'] = []
            
            # Verificar si ya está en el carrito
            encontrado = False
            for item in context.user_data['carrito']:
                if item['codigo'] == codigo_prod:
                    item['cantidad'] += cantidad
                    encontrado = True
                    break
            
            if not encontrado:
                context.user_data['carrito'].append({
                    'codigo': codigo_prod,
                    'nombre': producto.nombre,
                    'precio': float(producto.precio),
                    'cantidad': cantidad
                })
            
            # Calcular total del carrito
            total_items = sum(item['cantidad'] for item in context.user_data['carrito'])
            total_precio = sum(item['cantidad'] * item['precio'] for item in context.user_data['carrito'])
            
            mensaje_exito = (
                f"✅ *{cantidad}x {producto.nombre}* agregado!\n\n"
                f"🛒 Carrito: {total_items} items - Bs. {total_precio:.2f}"
            )
            
            # Verificar si el mensaje tiene foto (caption) o es texto
            if query.message.photo:
                # Es una foto, actualizar el caption
                await query.edit_message_caption(
                    caption=mensaje_exito,
                    parse_mode='Markdown',
                    reply_markup=get_confirmar_pedido_keyboard()
                )
            else:
                # Es un mensaje de texto
                await query.edit_message_text(
                    mensaje_exito,
                    parse_mode='Markdown',
                    reply_markup=get_confirmar_pedido_keyboard()
                )
        except Exception as e:
            # Si hay error, enviar mensaje nuevo
            await query.message.reply_text(
                f"✅ *{cantidad}x {producto.nombre}* agregado!\n\n"
                f"🛒 Carrito actualizado",
                parse_mode='Markdown',
                reply_markup=get_confirmar_pedido_keyboard()
            )
        finally:
            db.close()
    
    # Confirmar pedido
    elif data == "confirmar_pedido":
        # Eliminar mensaje anterior si es foto
        try:
            if query.message.photo:
                await query.message.delete()
        except:
            pass
        await query.message.chat.send_message(
            "📍 *Envía tu ubicación para el delivery*\n\nPresiona el botón para compartir tu ubicación:",
            parse_mode='Markdown',
            reply_markup=get_ubicacion_keyboard()
        )
    
    # Cancelar pedido
    elif data == "cancelar_pedido":
        context.user_data['carrito'] = []
        db = get_db()
        try:
            categorias = db.query(Categoria).all()
            await enviar_mensaje(
                "❌ *Pedido cancelado*\n\n¿Deseas empezar de nuevo?",
                reply_markup=get_categorias_keyboard(categorias)
            )
        finally:
            db.close()
    
    # Ver resumen desde callback
    elif data == "ver_resumen":
        carrito = context.user_data.get('carrito', [])
        if not carrito:
            await enviar_mensaje(
                "🛒 *Tu carrito está vacío*",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        mensaje = "📋 *RESUMEN DE TU PEDIDO*\n\n"
        total = 0
        for item in carrito:
            subtotal = item['precio'] * item['cantidad']
            total += subtotal
            mensaje += f"• {item['cantidad']}x {item['nombre']} - Bs. {subtotal:.2f}\n"
        
        mensaje += f"\n💰 *TOTAL: Bs. {total:.2f}*"
        
        await enviar_mensaje(
            mensaje,
            reply_markup=get_confirmar_pedido_keyboard()
        )
    
    # Método de pago
    elif data.startswith("pago_"):
        metodo = data.replace("pago_", "")
        await finalizar_pedido(query, context, metodo)


# ============ MOSTRAR RESUMEN ============
async def mostrar_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el resumen del carrito"""
    carrito = context.user_data.get('carrito', [])
    
    if not carrito:
        await update.message.reply_text(
            "🛒 *Tu carrito está vacío*\n\nAgrega productos desde el menú.",
            parse_mode='Markdown'
        )
        return
    
    mensaje = "📋 *RESUMEN DE TU PEDIDO*\n\n"
    total = 0
    for item in carrito:
        subtotal = item['precio'] * item['cantidad']
        total += subtotal
        mensaje += f"• {item['cantidad']}x {item['nombre']} - Bs. {subtotal:.2f}\n"
    
    detalles = context.user_data.get('detalles', '')
    if detalles:
        mensaje += f"\n📝 *Notas:* {detalles}\n"
    
    mensaje += f"\n💰 *TOTAL: Bs. {total:.2f}*"
    
    await update.message.reply_text(
        mensaje,
        parse_mode='Markdown',
        reply_markup=get_confirmar_pedido_keyboard()
    )


# ============ MOSTRAR RESUMEN CALLBACK ============
async def mostrar_resumen_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el resumen del carrito (desde callback)"""
    carrito = context.user_data.get('carrito', [])
    
    if not carrito:
        keyboard = [[InlineKeyboardButton("🔙 Volver al menú", callback_data="volver_menu")]]
        await query.edit_message_text(
            "🛒 *Tu carrito está vacío*\n\nAgrega productos desde el menú.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    mensaje = "📋 *RESUMEN DE TU PEDIDO*\n\n"
    total = 0
    for item in carrito:
        subtotal = item['precio'] * item['cantidad']
        total += subtotal
        mensaje += f"• {item['cantidad']}x {item['nombre']} - Bs. {subtotal:.2f}\n"
    
    detalles = context.user_data.get('detalles', '')
    if detalles:
        mensaje += f"\n📝 *Notas:* {detalles}\n"
    
    mensaje += f"\n💰 *TOTAL: Bs. {total:.2f}*"
    
    await query.edit_message_text(
        mensaje,
        parse_mode='Markdown',
        reply_markup=get_confirmar_pedido_keyboard()
    )


# ============ PROCESAR PAGO ============
async def procesar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de pago"""
    carrito = context.user_data.get('carrito', [])
    
    if not carrito:
        await update.message.reply_text(
            "🛒 *Tu carrito está vacío*\n\nAgrega productos para hacer un pedido.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        "💳 *MÉTODO DE PAGO*\n\nSelecciona cómo deseas pagar:",
        parse_mode='Markdown',
        reply_markup=get_metodo_pago_keyboard()
    )


# ============ FINALIZAR PEDIDO ============
async def finalizar_pedido(query, context: ContextTypes.DEFAULT_TYPE, metodo_pago: str):
    """Finaliza y guarda el pedido en la BD con asignación automática de conductor"""
    from app.services.conductor_service import asignar_conductor_a_pedido, calcular_distancia_conductor_cliente
    
    carrito = context.user_data.get('carrito', [])
    chat_id = str(query.message.chat_id)
    
    db = get_db()
    try:
        # Obtener cliente
        cliente = db.query(ClienteBot).filter(ClienteBot.chat_id == chat_id).first()
        
        if not cliente:
            await query.edit_message_text("❌ Error: Cliente no encontrado. Usa /start")
            return
        
        # Calcular total
        total = sum(item['precio'] * item['cantidad'] for item in carrito)
        
        # Obtener detalles/observaciones del pedido
        observaciones = context.user_data.get('detalles', '')
        
        # Crear pedido
        codigo_pedido = generar_codigo_pedido()
        pedido = Pedido(
            codigo_pedido=codigo_pedido,
            cliente_telefono=cliente.telefono,
            total=Decimal(str(total)),
            estado="SOLICITADO",
            observaciones=observaciones if observaciones else None,
            latitud_destino=cliente.latitud_ultima,
            longitud_destino=cliente.longitud_ultima
        )
        db.add(pedido)
        
        # Crear items del pedido
        for item in carrito:
            item_pedido = ItemPedido(
                codigo_pedido=codigo_pedido,
                codigo_producto=item['codigo'],
                cantidad=item['cantidad'],
                precio_unitario=Decimal(str(item['precio']))
            )
            db.add(item_pedido)
        
        db.commit()
        
        # ============ ASIGNAR CONDUCTOR MÁS CERCANO ============
        resultado_asignacion = asignar_conductor_a_pedido(db, codigo_pedido)
        
        if resultado_asignacion["exito"]:
            conductor_info = resultado_asignacion["conductor"]
            
            # Calcular distancia y tiempo al cliente
            dist_cliente = None
            tiempo_estimado = None
            if cliente.latitud_ultima and cliente.longitud_ultima:
                info_entrega = calcular_distancia_conductor_cliente(
                    db, 
                    conductor_info["codigo_conductor"],
                    float(cliente.latitud_ultima),
                    float(cliente.longitud_ultima)
                )
                dist_cliente = info_entrega.get("distancia_km")
                tiempo_estimado = info_entrega.get("tiempo_estimado_min")
            
            mensaje = f"""
✅ *¡PEDIDO CONFIRMADO!*

🎫 Código: `{codigo_pedido}`
💰 Total: Bs. {total:.2f}
💳 Pago: {metodo_pago}

🚴 *CONDUCTOR ASIGNADO:*
👤 {conductor_info['nombre']}
📞 {conductor_info['telefono']}
🏍️ {conductor_info['tipo_vehiculo']} - {conductor_info['vehiculo']}
📍 A {conductor_info['distancia_km']} km del restaurante

⏱️ *Tiempo estimado de entrega:* ~{tiempo_estimado or 15} min

¡Tu pedido está en camino! 🎉
"""
        else:
            # No hay conductores disponibles
            mensaje = f"""
✅ *¡PEDIDO CONFIRMADO!*

🎫 Código: `{codigo_pedido}`
💰 Total: Bs. {total:.2f}
💳 Pago: {metodo_pago}

📍 Estamos preparando tu pedido...
⚠️ Buscando repartidor disponible...

Te notificaremos cuando un conductor sea asignado.

¡Gracias por tu compra! 🙏
"""
        
        # Limpiar carrito
        context.user_data['carrito'] = []
        context.user_data['detalles'] = ''
        
        await query.edit_message_text(mensaje, parse_mode='Markdown')
        
    except Exception as e:
        db.rollback()
        await query.edit_message_text(f"❌ Error al procesar el pedido: {str(e)}")
    finally:
        db.close()


# ============ FUNCIONES DE SEGUIMIENTO DE PEDIDOS ============
async def mostrar_mis_pedidos(query, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los pedidos del cliente"""
    chat_id = str(query.message.chat_id)
    
    db = get_db()
    try:
        # Obtener cliente
        cliente = db.query(ClienteBot).filter(ClienteBot.chat_id == chat_id).first()
        
        if not cliente or not cliente.telefono:
            keyboard = [[InlineKeyboardButton("🏠 Volver al Inicio", callback_data="volver_menu")]]
            await query.edit_message_text(
                "❌ No tienes un teléfono registrado.\n"
                "Usa /start para registrarte primero.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Obtener pedidos del cliente
        pedidos = db.query(Pedido).filter(
            Pedido.cliente_telefono == cliente.telefono
        ).order_by(Pedido.fecha.desc()).limit(10).all()
        
        if not pedidos:
            keyboard = [[InlineKeyboardButton("🏠 Volver al Inicio", callback_data="volver_menu")]]
            await query.edit_message_text(
                "📦 *MIS PEDIDOS*\n\n"
                "No tienes pedidos registrados aún.\n"
                "¡Haz tu primer pedido! 🍔",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        await query.edit_message_text(
            "📦 *MIS PEDIDOS*\n\n"
            "Selecciona un pedido para ver los detalles:\n\n"
            "🟡 Solicitado | 🟠 Asignado | 🔵 Aceptado\n"
            "🚴 En Camino | ✅ Entregado | ❌ Cancelado",
            parse_mode='Markdown',
            reply_markup=get_mis_pedidos_keyboard(pedidos)
        )
        
    finally:
        db.close()


async def mostrar_detalle_pedido(query, context: ContextTypes.DEFAULT_TYPE, codigo_pedido: str):
    """Muestra el detalle de un pedido específico"""
    from app.services.conductor_service import calcular_distancia_conductor_cliente
    
    db = get_db()
    try:
        pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo_pedido).first()
        
        if not pedido:
            await query.edit_message_text("❌ Pedido no encontrado")
            return
        
        # Estado con emoji
        estado_emoji = {
            "SOLICITADO": "🟡 Solicitado",
            "ASIGNADO": "🟠 Asignado",
            "ACEPTADO": "🔵 Aceptado",
            "EN_CAMINO": "🚴 En Camino",
            "ENTREGADO": "✅ Entregado",
            "CANCELADO": "❌ Cancelado"
        }
        estado_texto = estado_emoji.get(pedido.estado, pedido.estado)
        
        # Obtener items del pedido
        items = db.query(ItemPedido).filter(ItemPedido.codigo_pedido == codigo_pedido).all()
        
        items_texto = ""
        for item in items:
            producto = db.query(Producto).filter(Producto.codigo_producto == item.codigo_producto).first()
            nombre = producto.nombre if producto else item.codigo_producto
            items_texto += f"  • {item.cantidad}x {nombre} - Bs.{item.precio_unitario}\n"
        
        # Info del conductor si está asignado
        conductor_texto = ""
        tiene_conductor = False
        if pedido.conductor_codigo:
            tiene_conductor = True
            conductor = db.query(Conductor).filter(
                Conductor.codigo_conductor == pedido.conductor_codigo
            ).first()
            
            if conductor:
                conductor_texto = f"\n🚴 *REPARTIDOR:*\n"
                conductor_texto += f"👤 {conductor.nombre}\n"
                conductor_texto += f"📞 {conductor.telefono}\n"
                conductor_texto += f"🏍️ {conductor.tipo_vehiculo} - {conductor.vehiculo}\n"
                
                # Calcular distancia al cliente si tiene ubicación
                if conductor.latitud and conductor.longitud and pedido.latitud_destino and pedido.longitud_destino:
                    info_distancia = calcular_distancia_conductor_cliente(
                        db,
                        conductor.codigo_conductor,
                        float(pedido.latitud_destino),
                        float(pedido.longitud_destino)
                    )
                    if info_distancia.get("distancia_km"):
                        conductor_texto += f"📍 A {info_distancia['distancia_km']} km de ti\n"
                        conductor_texto += f"⏱️ ~{info_distancia['tiempo_estimado_min']} min\n"
        
        # Formatear fecha
        fecha_str = pedido.fecha.strftime("%d/%m/%Y %H:%M") if pedido.fecha else "N/A"
        
        mensaje = f"""
📦 *DETALLE DEL PEDIDO*

🎫 Código: `{pedido.codigo_pedido}`
📅 Fecha: {fecha_str}
💰 Total: *Bs. {pedido.total}*

📊 Estado: *{estado_texto}*

🛒 *Productos:*
{items_texto}"""
        
        # Agregar observaciones si existen
        if pedido.observaciones:
            mensaje += f"\n📝 *Observaciones:*\n_{pedido.observaciones}_\n"
        
        mensaje += conductor_texto
        
        await query.edit_message_text(
            mensaje,
            parse_mode='Markdown',
            reply_markup=get_detalle_pedido_keyboard(codigo_pedido, pedido.estado, tiene_conductor)
        )
        
    finally:
        db.close()


async def mostrar_ubicacion_conductor(query, context: ContextTypes.DEFAULT_TYPE, codigo_pedido: str):
    """Muestra la ubicación del conductor asignado al pedido con live location"""
    from app.services.conductor_service import calcular_distancia_conductor_cliente
    from datetime import datetime
    
    db = get_db()
    try:
        pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo_pedido).first()
        
        if not pedido or not pedido.conductor_codigo:
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data=f"ver_pedido_{codigo_pedido}")]]
            await query.edit_message_text(
                "❌ No hay conductor asignado a este pedido.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        conductor = db.query(Conductor).filter(
            Conductor.codigo_conductor == pedido.conductor_codigo
        ).first()
        
        if not conductor:
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data=f"ver_pedido_{codigo_pedido}")]]
            await query.edit_message_text(
                "❌ Conductor no encontrado.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Verificar si tiene ubicación
        if not conductor.latitud or not conductor.longitud:
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data=f"ver_pedido_{codigo_pedido}")]]
            await query.edit_message_text(
                "📍 *UBICACIÓN DEL CONDUCTOR*\n\n"
                f"👤 {conductor.nombre}\n"
                f"📞 {conductor.telefono}\n\n"
                "⚠️ El conductor aún no ha compartido su ubicación.\n"
                "Intenta más tarde.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Calcular distancias
        distancia_cliente = None
        tiempo_estimado = None
        
        if pedido.latitud_destino and pedido.longitud_destino:
            info = calcular_distancia_conductor_cliente(
                db,
                conductor.codigo_conductor,
                float(pedido.latitud_destino),
                float(pedido.longitud_destino)
            )
            distancia_cliente = info.get("distancia_km")
            tiempo_estimado = info.get("tiempo_estimado_min")
        
        # Última actualización
        ultima_actualizacion = ""
        if conductor.ultima_actualizacion:
            ultima_actualizacion = conductor.ultima_actualizacion.strftime("%H:%M:%S")
        
        # Timestamp actual
        ahora = datetime.now().strftime("%H:%M:%S")
        
        # Generar link de Google Maps
        maps_link = f"https://www.google.com/maps?q={conductor.latitud},{conductor.longitud}"
        
        keyboard = [
            [InlineKeyboardButton("🗺️ Ver en Google Maps", url=maps_link)],
            [InlineKeyboardButton("🔄 Actualizar", callback_data=f"ubicacion_conductor_{codigo_pedido}")],
            [InlineKeyboardButton("🔙 Volver al Pedido", callback_data=f"ver_pedido_{codigo_pedido}")]
        ]
        
        mensaje = f"""
📍 *UBICACIÓN DEL CONDUCTOR*

👤 *{conductor.nombre}*
📞 {conductor.telefono}
🏍️ {conductor.tipo_vehiculo} - {conductor.vehiculo}

📊 *Estado del pedido:* {pedido.estado}
"""
        
        if distancia_cliente:
            mensaje += f"""
📏 *Distancia a tu ubicación:* {distancia_cliente} km
⏱️ *Tiempo estimado:* ~{tiempo_estimado} minutos
"""
        
        if ultima_actualizacion:
            mensaje += f"\n🕐 *Ubicación del conductor:* {ultima_actualizacion}"
        
        mensaje += f"\n🔄 *Consultado a las:* {ahora}"
        
        # Eliminar mensaje de ubicación anterior si existe
        last_location_msg = context.user_data.get(f'location_msg_{codigo_pedido}')
        if last_location_msg:
            try:
                await context.bot.delete_message(
                    chat_id=query.message.chat_id,
                    message_id=last_location_msg
                )
            except:
                pass  # Si no se puede eliminar, continuar
        
        try:
            await query.edit_message_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception:
            await query.answer("📍 Ubicación actualizada")
        
        # Enviar nueva ubicación y guardar el message_id
        try:
            location_msg = await query.message.reply_location(
                latitude=float(conductor.latitud),
                longitude=float(conductor.longitud)
            )
            # Guardar el ID del mensaje de ubicación para eliminarlo después
            context.user_data[f'location_msg_{codigo_pedido}'] = location_msg.message_id
        except:
            pass
        
    finally:
        db.close()


# ============ TRACKING EN VIVO ============
async def iniciar_tracking_live(query, context: ContextTypes.DEFAULT_TYPE, codigo_pedido: str):
    """Inicia el tracking en vivo del conductor"""
    from datetime import datetime
    
    chat_id = query.message.chat_id
    
    # Verificar si ya hay un tracking activo
    if context.user_data.get(f'tracking_active_{codigo_pedido}'):
        await query.answer("⚠️ El tracking ya está activo")
        return
    
    db = get_db()
    try:
        pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo_pedido).first()
        
        if not pedido or not pedido.conductor_codigo:
            await query.answer("❌ No hay conductor asignado")
            return
        
        conductor = db.query(Conductor).filter(
            Conductor.codigo_conductor == pedido.conductor_codigo
        ).first()
        
        if not conductor or not conductor.latitud or not conductor.longitud:
            await query.answer("❌ El conductor no tiene ubicación")
            return
        
        # Marcar tracking como activo
        context.user_data[f'tracking_active_{codigo_pedido}'] = True
        
        # Eliminar mensaje de ubicación anterior si existe
        last_location_msg = context.user_data.get(f'location_msg_{codigo_pedido}')
        if last_location_msg:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=last_location_msg)
            except:
                pass
        
        # Enviar mensaje de tracking
        await query.edit_message_text(
            f"🔴 *TRACKING EN VIVO*\n\n"
            f"📦 Pedido: `{codigo_pedido}`\n"
            f"👤 Conductor: {conductor.nombre}\n"
            f"📞 Tel: {conductor.telefono}\n\n"
            f"_Actualizando cada 10 segundos..._\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}",
            parse_mode='Markdown',
            reply_markup=get_tracking_keyboard(codigo_pedido)
        )
        
        # Enviar ubicación en vivo (Live Location por 30 minutos)
        try:
            live_msg = await context.bot.send_location(
                chat_id=chat_id,
                latitude=float(conductor.latitud),
                longitude=float(conductor.longitud),
                live_period=1800,  # 30 minutos
                heading=None,
                proximity_alert_radius=100
            )
            context.user_data[f'live_location_msg_{codigo_pedido}'] = live_msg.message_id
        except Exception as e:
            # Si no funciona live location, usar ubicación normal
            location_msg = await context.bot.send_location(
                chat_id=chat_id,
                latitude=float(conductor.latitud),
                longitude=float(conductor.longitud)
            )
            context.user_data[f'location_msg_{codigo_pedido}'] = location_msg.message_id
        
        # Programar actualizaciones automáticas (si job_queue está disponible)
        if context.job_queue:
            context.job_queue.run_repeating(
                actualizar_tracking_job,
                interval=10,  # Cada 10 segundos
                first=10,
                chat_id=chat_id,
                name=f"tracking_{codigo_pedido}_{chat_id}",
                data={
                    'codigo_pedido': codigo_pedido,
                    'chat_id': chat_id,
                    'conductor_codigo': conductor.codigo_conductor
                }
            )
        
    finally:
        db.close()


async def actualizar_tracking_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que actualiza la ubicación del conductor periódicamente"""
    from app.services.conductor_service import calcular_distancia_conductor_cliente
    from datetime import datetime
    
    job = context.job
    data = job.data
    codigo_pedido = data['codigo_pedido']
    chat_id = data['chat_id']
    conductor_codigo = data['conductor_codigo']
    
    # Verificar si el tracking sigue activo
    if not context.application.user_data.get(chat_id, {}).get(f'tracking_active_{codigo_pedido}'):
        job.schedule_removal()
        return
    
    db = get_db()
    try:
        conductor = db.query(Conductor).filter(
            Conductor.codigo_conductor == conductor_codigo
        ).first()
        
        pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo_pedido).first()
        
        if not conductor or not conductor.latitud or not pedido:
            return
        
        # Si el pedido ya fue entregado, detener tracking
        if pedido.estado in ["ENTREGADO", "CANCELADO"]:
            context.application.user_data.get(chat_id, {})[f'tracking_active_{codigo_pedido}'] = False
            job.schedule_removal()
            return
        
        # Actualizar Live Location si existe
        live_msg_id = context.application.user_data.get(chat_id, {}).get(f'live_location_msg_{codigo_pedido}')
        if live_msg_id:
            try:
                await context.bot.edit_message_live_location(
                    chat_id=chat_id,
                    message_id=live_msg_id,
                    latitude=float(conductor.latitud),
                    longitude=float(conductor.longitud)
                )
            except:
                pass
        
    finally:
        db.close()


async def detener_tracking_live(query, context: ContextTypes.DEFAULT_TYPE, codigo_pedido: str):
    """Detiene el tracking en vivo"""
    chat_id = query.message.chat_id
    
    # Marcar tracking como inactivo
    context.user_data[f'tracking_active_{codigo_pedido}'] = False
    
    # Cancelar el job de actualización (si job_queue está disponible)
    if context.job_queue:
        current_jobs = context.job_queue.get_jobs_by_name(f"tracking_{codigo_pedido}_{chat_id}")
        for job in current_jobs:
            job.schedule_removal()
    
    # Eliminar mensaje de live location
    live_msg_id = context.user_data.get(f'live_location_msg_{codigo_pedido}')
    if live_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=live_msg_id)
        except:
            pass
        context.user_data.pop(f'live_location_msg_{codigo_pedido}', None)
    
    # Eliminar mensaje de ubicación normal
    location_msg_id = context.user_data.get(f'location_msg_{codigo_pedido}')
    if location_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=location_msg_id)
        except:
            pass
        context.user_data.pop(f'location_msg_{codigo_pedido}', None)
    
    await query.edit_message_text(
        "⏹️ *Tracking detenido*\n\n"
        "El seguimiento en vivo ha sido detenido.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Ver Pedido", callback_data=f"ver_pedido_{codigo_pedido}")],
            [InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu")]
        ])
    )


async def limpiar_mensajes_ubicacion(query, context: ContextTypes.DEFAULT_TYPE):
    """Limpia todos los mensajes de ubicación y detiene trackings activos"""
    chat_id = query.message.chat_id
    
    # Buscar y eliminar todos los mensajes de ubicación guardados
    keys_to_remove = []
    for key in list(context.user_data.keys()):
        if key.startswith('location_msg_') or key.startswith('live_location_msg_'):
            msg_id = context.user_data.get(key)
            if msg_id:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                except:
                    pass
            keys_to_remove.append(key)
        
        # Desactivar trackings activos
        if key.startswith('tracking_active_'):
            context.user_data[key] = False
            codigo_pedido = key.replace('tracking_active_', '')
            # Cancelar jobs si existen
            if context.job_queue:
                try:
                    current_jobs = context.job_queue.get_jobs_by_name(f"tracking_{codigo_pedido}_{chat_id}")
                    for job in current_jobs:
                        job.schedule_removal()
                except:
                    pass
    
    # Limpiar las keys
    for key in keys_to_remove:
        context.user_data.pop(key, None)


# ============ MANEJAR UBICACIÓN ============
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja cuando el usuario envía su ubicación"""
    location = update.message.location
    chat_id = str(update.effective_chat.id)
    
    db = get_db()
    try:
        cliente = db.query(ClienteBot).filter(ClienteBot.chat_id == chat_id).first()
        if cliente:
            cliente.latitud_ultima = location.latitude
            cliente.longitud_ultima = location.longitude
            db.commit()
        
        await update.message.reply_text(
            f"📍 *Ubicación guardada*\n\n"
            f"Lat: {location.latitude}\n"
            f"Lng: {location.longitude}\n\n"
            "Selecciona el método de pago:",
            parse_mode='Markdown',
            reply_markup=get_metodo_pago_keyboard()
        )
    finally:
        db.close()


# ============ MANEJAR TEXTO GENERAL ============
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto generales"""
    text = update.message.text
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    
    # Si está esperando detalles del pedido
    if context.user_data.get('esperando_detalles'):
        context.user_data['detalles'] = text
        context.user_data['esperando_detalles'] = False
        await update.message.reply_text(
            f"📝 *Detalles guardados:*\n{text}\n\n"
            "Puedes ver el resumen de tu pedido.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Si es un número de teléfono (usuario nuevo escribiendo manualmente)
    if text.isdigit() and len(text) >= 7 and len(text) <= 15:
        db = get_db()
        try:
            # Verificar si el usuario ya existe
            cliente = db.query(ClienteBot).filter(ClienteBot.chat_id == chat_id).first()
            
            if cliente:
                # Actualizar teléfono
                cliente.telefono = text
                db.commit()
                await update.message.reply_text(
                    f"✅ *¡Teléfono actualizado!*\n\n📱 {text}\n\nYa puedes hacer tus pedidos 🍔",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                # Crear nuevo cliente
                cliente = ClienteBot(
                    telefono=text,
                    chat_id=chat_id,
                    nombre=user.first_name
                )
                db.add(cliente)
                db.commit()
                await update.message.reply_text(
                    f"✅ *¡Teléfono registrado!*\n\n📱 {text}\n\nYa puedes hacer tus pedidos 🍔",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard()
                )
        except Exception as e:
            db.rollback()
            await update.message.reply_text(
                "❌ Error al guardar el teléfono. Intenta de nuevo.",
                reply_markup=get_main_menu_keyboard()
            )
        finally:
            db.close()
        return
    
    # Si no es un comando conocido, mostrar menú
    await update.message.reply_text(
        "🤔 No entendí tu mensaje.\n\nUsa los botones del menú 👇",
        reply_markup=get_main_menu_keyboard()
    )


# ============ COMANDO /carrito ============
async def carrito_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /carrito - Muestra el carrito actual"""
    await mostrar_resumen(update, context)


# ============ COMANDO /mispedidos ============
async def mispedidos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /mispedidos - Muestra los pedidos del usuario"""
    chat_id = str(update.effective_chat.id)
    
    db = get_db()
    try:
        # Obtener cliente
        cliente = db.query(ClienteBot).filter(ClienteBot.chat_id == chat_id).first()
        
        if not cliente or not cliente.telefono:
            await update.message.reply_text(
                "❌ No tienes un teléfono registrado.\n"
                "Usa /start para registrarte primero.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Obtener pedidos del cliente
        pedidos = db.query(Pedido).filter(
            Pedido.cliente_telefono == cliente.telefono
        ).order_by(Pedido.fecha.desc()).limit(10).all()
        
        if not pedidos:
            await update.message.reply_text(
                "📦 *MIS PEDIDOS*\n\n"
                "No tienes pedidos registrados aún.\n"
                "¡Haz tu primer pedido! 🍔",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        await update.message.reply_text(
            "📦 *MIS PEDIDOS*\n\n"
            "Selecciona un pedido para ver los detalles:\n\n"
            "🟡 Solicitado | 🟠 Asignado | 🔵 Aceptado\n"
            "🚴 En Camino | ✅ Entregado | ❌ Cancelado",
            parse_mode='Markdown',
            reply_markup=get_mis_pedidos_keyboard(pedidos)
        )
        
    finally:
        db.close()


# ============ COMANDO /rastrear ============
async def rastrear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /rastrear - Rastrea un pedido específico"""
    chat_id = str(update.effective_chat.id)
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "🔍 *RASTREAR PEDIDO*\n\n"
            "Usa: `/rastrear CODIGO_PEDIDO`\n"
            "Ejemplo: `/rastrear PED-ABC123`\n\n"
            "O presiona 'Mis Pedidos' para ver todos tus pedidos.",
            parse_mode='Markdown',
            reply_markup=get_rastrear_keyboard()
        )
        return
    
    codigo_pedido = args[0].upper()
    
    db = get_db()
    try:
        pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo_pedido).first()
        
        if not pedido:
            await update.message.reply_text(
                f"❌ No se encontró el pedido `{codigo_pedido}`\n\n"
                "Verifica el código e intenta nuevamente.",
                parse_mode='Markdown',
                reply_markup=get_rastrear_keyboard()
            )
            return
        
        # Verificar que el pedido pertenece al usuario
        cliente = db.query(ClienteBot).filter(ClienteBot.chat_id == chat_id).first()
        if cliente and pedido.cliente_telefono != cliente.telefono:
            await update.message.reply_text(
                "❌ Este pedido no te pertenece.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Mostrar detalle del pedido
        keyboard = [[InlineKeyboardButton("📦 Ver Detalle", callback_data=f"ver_pedido_{codigo_pedido}")]]
        
        estado_emoji = {
            "SOLICITADO": "🟡",
            "ASIGNADO": "🟠",
            "ACEPTADO": "🔵",
            "EN_CAMINO": "🚴",
            "ENTREGADO": "✅",
            "CANCELADO": "❌"
        }
        emoji = estado_emoji.get(pedido.estado, "⚪")
        
        await update.message.reply_text(
            f"📦 *Pedido Encontrado*\n\n"
            f"🎫 Código: `{pedido.codigo_pedido}`\n"
            f"📊 Estado: {emoji} {pedido.estado}\n"
            f"💰 Total: Bs. {pedido.total}\n\n"
            f"Presiona el botón para ver más detalles:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    finally:
        db.close()


# ============ COMANDO /cancelar ============
async def cancelar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /cancelar - Cancela el pedido actual"""
    context.user_data['carrito'] = []
    context.user_data['detalles'] = ''
    await update.message.reply_text(
        "❌ *Pedido cancelado*\n\nTu carrito ha sido vaciado.",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )


# ============ MANEJAR CONTACTO (TELÉFONO) ============
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja cuando el usuario comparte su contacto/teléfono"""
    contact = update.message.contact
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    
    # Obtener el número de teléfono (sin el +)
    telefono = contact.phone_number.replace("+", "").replace(" ", "")
    
    db = get_db()
    try:
        # Verificar si ya existe un cliente con ese teléfono
        cliente_existente = db.query(ClienteBot).filter(ClienteBot.telefono == telefono).first()
        
        if cliente_existente:
            # Actualizar chat_id si es diferente
            cliente_existente.chat_id = chat_id
            cliente_existente.nombre = user.first_name
            db.commit()
        else:
            # Crear nuevo cliente con el teléfono real
            cliente = ClienteBot(
                telefono=telefono,
                chat_id=chat_id,
                nombre=contact.first_name or user.first_name
            )
            db.add(cliente)
            db.commit()
        
        await update.message.reply_text(
            f"✅ *¡Teléfono registrado!*\n\n"
            f"📱 {telefono}\n\n"
            "Ya puedes hacer tus pedidos 🍔",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        db.rollback()
        await update.message.reply_text(
            f"❌ Error al registrar: {str(e)}\n\nIntenta de nuevo con /start",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()


# ============ OMITIR TELÉFONO ============
async def handle_omitir_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja cuando el usuario omite compartir su teléfono"""
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    
    db = get_db()
    try:
        # Crear cliente con chat_id como teléfono temporal
        cliente = ClienteBot(
            telefono=f"TG-{chat_id}",  # Prefijo TG para identificar que es temporal
            chat_id=chat_id,
            nombre=user.first_name
        )
        db.add(cliente)
        db.commit()
        
        await update.message.reply_text(
            "👍 *¡Sin problema!*\n\n"
            "Puedes agregar tu teléfono después.\n"
            "Por ahora, disfruta del menú 🍔",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
    except:
        db.rollback()
        await update.message.reply_text(
            "Ya tienes una cuenta. ¡Bienvenido de nuevo!",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()
