"""
Teclados y botones para el bot de Telegram
"""
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado principal con todas las opciones del bot (botones inline)
    """
    keyboard = [
        [
            InlineKeyboardButton("🍔 Ver Menú", callback_data="menu_ver"),
            InlineKeyboardButton("🛒 Iniciar Pedido", callback_data="pedido_iniciar")
        ],
        [
            InlineKeyboardButton("➕ Agregar Producto", callback_data="producto_agregar"),
            InlineKeyboardButton("📝 Agregar Detalles", callback_data="detalles_agregar")
        ],
        [
            InlineKeyboardButton("📋 Ver Resumen", callback_data="resumen_ver"),
            InlineKeyboardButton("✅ Pagar Pedido", callback_data="pagar_pedido")
        ],
        [
            InlineKeyboardButton("📦 Mis Pedidos", callback_data="mis_pedidos"),
            InlineKeyboardButton("🔍 Rastrear Pedido", callback_data="rastrear_pedido")
        ],
        [
            InlineKeyboardButton("📞 Contacto", callback_data="info_contacto"),
            InlineKeyboardButton("🕐 Horarios", callback_data="info_horarios")
        ],
        [
            InlineKeyboardButton("🚚 Delivery", callback_data="info_delivery"),
            InlineKeyboardButton("❓ Ayuda", callback_data="info_ayuda")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_categorias_keyboard(categorias: list) -> InlineKeyboardMarkup:
    """
    Teclado inline con las categorías disponibles
    """
    keyboard = []
    for cat in categorias:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🍽️ {cat.nombre}",
                callback_data=f"categoria_{cat.codigo_categoria}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🏠 Volver al Inicio", callback_data="volver_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_productos_keyboard(productos: list) -> InlineKeyboardMarkup:
    """
    Teclado inline con los productos de una categoría
    """
    keyboard = []
    for prod in productos:
        # Emoji según si tiene imagen o no
        emoji = "🖼️" if prod.img_url else "🍽️"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {prod.nombre} - Bs. {prod.precio}",
                callback_data=f"producto_{prod.codigo_producto}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("📋 Ver Resumen", callback_data="resumen_ver"),
        InlineKeyboardButton("🔙 Categorías", callback_data="ver_categorias")
    ])
    keyboard.append([InlineKeyboardButton("🏠 Volver al Inicio", callback_data="volver_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_cantidad_keyboard(codigo_producto: str) -> InlineKeyboardMarkup:
    """
    Teclado para seleccionar cantidad
    """
    keyboard = [
        [
            InlineKeyboardButton("1️⃣", callback_data=f"cantidad_{codigo_producto}_1"),
            InlineKeyboardButton("2️⃣", callback_data=f"cantidad_{codigo_producto}_2"),
            InlineKeyboardButton("3️⃣", callback_data=f"cantidad_{codigo_producto}_3"),
        ],
        [
            InlineKeyboardButton("4️⃣", callback_data=f"cantidad_{codigo_producto}_4"),
            InlineKeyboardButton("5️⃣", callback_data=f"cantidad_{codigo_producto}_5"),
            InlineKeyboardButton("6️⃣", callback_data=f"cantidad_{codigo_producto}_6"),
        ],
        [
            InlineKeyboardButton("🔙 Volver a Productos", callback_data="ver_categorias"),
            InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmar_pedido_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para confirmar el pedido
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar Pedido", callback_data="confirmar_pedido"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_pedido"),
        ],
        [
            InlineKeyboardButton("✏️ Editar Carrito", callback_data="editar_carrito"),
            InlineKeyboardButton("➕ Agregar más", callback_data="ver_categorias")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_carrito_editar_keyboard(carrito: list) -> InlineKeyboardMarkup:
    """
    Teclado para editar productos del carrito
    """
    keyboard = []
    
    for i, item in enumerate(carrito):
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {item['nombre']} ({item['cantidad']}x)",
                callback_data=f"carrito_item_{i}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🗑️ Vaciar Todo", callback_data="vaciar_carrito"),
        InlineKeyboardButton("📋 Ver Resumen", callback_data="resumen_ver")
    ])
    keyboard.append([InlineKeyboardButton("🏠 Volver al menú", callback_data="volver_menu")])
    
    return InlineKeyboardMarkup(keyboard)


def get_item_carrito_keyboard(indice: int, item: dict) -> InlineKeyboardMarkup:
    """
    Teclado para editar un item específico del carrito
    """
    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data=f"carrito_menos_{indice}"),
            InlineKeyboardButton(f"📦 {item['cantidad']}", callback_data="noop"),
            InlineKeyboardButton("➕", callback_data=f"carrito_mas_{indice}"),
        ],
        [
            InlineKeyboardButton("🗑️ Eliminar", callback_data=f"carrito_eliminar_{indice}"),
        ],
        [
            InlineKeyboardButton("🔙 Volver al Carrito", callback_data="editar_carrito"),
            InlineKeyboardButton("📋 Ver Resumen", callback_data="resumen_ver")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_ubicacion_keyboard() -> ReplyKeyboardMarkup:
    """
    Teclado para solicitar ubicación
    """
    keyboard = [
        [KeyboardButton("📍 Enviar mi ubicación", request_location=True)],
        [KeyboardButton("🔙 Volver al menú")]
    ]
    return ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        one_time_keyboard=False,
        is_persistent=True
    )


def get_solicitar_telefono_keyboard() -> ReplyKeyboardMarkup:
    """
    Teclado para solicitar el número de teléfono
    """
    keyboard = [
        [KeyboardButton("📱 Compartir mi teléfono", request_contact=True)],
        [KeyboardButton("❌ Omitir por ahora")]
    ]
    return ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        one_time_keyboard=False,
        is_persistent=True
    )


def get_metodo_pago_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para seleccionar método de pago
    """
    keyboard = [
        [InlineKeyboardButton("💵 Efectivo", callback_data="pago_EFECTIVO")],
        [InlineKeyboardButton("📱 Pago QR", callback_data="mostrar_qr")],
        [InlineKeyboardButton("💳 Tarjeta de Crédito/Débito", callback_data="pago_tarjeta")],
        [InlineKeyboardButton("🔙 Volver", callback_data="ver_resumen")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_qr_pago_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado después de mostrar QR
    """
    keyboard = [
        [InlineKeyboardButton("✅ Ya pagué", callback_data="confirmar_pago_qr")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="ver_resumen")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_tarjeta_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para ingresar datos de tarjeta
    """
    keyboard = [
        [InlineKeyboardButton("💳 Ingresar datos de tarjeta", callback_data="ingresar_tarjeta")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="ver_resumen")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmar_tarjeta_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para confirmar pago con tarjeta
    """
    keyboard = [
        [InlineKeyboardButton("✅ Confirmar Pago", callback_data="confirmar_pago_tarjeta")],
        [InlineKeyboardButton("🔙 Cambiar datos", callback_data="ingresar_tarjeta")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="ver_resumen")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_mis_pedidos_keyboard(pedidos: list) -> InlineKeyboardMarkup:
    """
    Teclado con lista de pedidos del cliente
    """
    keyboard = []
    
    # Emojis según estado
    estado_emoji = {
        "SOLICITADO": "🟡",
        "ASIGNADO": "🟠",
        "ACEPTADO": "🔵",
        "EN_CAMINO": "🚴",
        "ENTREGADO": "✅",
        "CANCELADO": "❌"
    }
    
    for pedido in pedidos[:10]:  # Mostrar últimos 10
        emoji = estado_emoji.get(pedido.estado, "⚪")
        keyboard.append([
            InlineKeyboardButton(
                f"{emoji} {pedido.codigo_pedido} - Bs.{pedido.total}",
                callback_data=f"ver_pedido_{pedido.codigo_pedido}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🏠 Volver al Inicio", callback_data="volver_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_detalle_pedido_keyboard(codigo_pedido: str, estado: str, tiene_conductor: bool) -> InlineKeyboardMarkup:
    """
    Teclado con opciones para un pedido específico
    """
    keyboard = []
    
    # Si tiene conductor y está en camino, mostrar opción de ver ubicación
    if tiene_conductor and estado in ["ASIGNADO", "ACEPTADO", "EN_CAMINO"]:
        keyboard.append([
            InlineKeyboardButton("📍 Ver Ubicación", callback_data=f"ubicacion_conductor_{codigo_pedido}"),
            InlineKeyboardButton("🔴 Tracking Vivo", callback_data=f"tracking_live_{codigo_pedido}")
        ])
    
    # Si está en estados activos, mostrar actualizar
    if estado not in ["ENTREGADO", "CANCELADO"]:
        keyboard.append([
            InlineKeyboardButton("🔄 Actualizar Estado", callback_data=f"actualizar_pedido_{codigo_pedido}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("📦 Mis Pedidos", callback_data="mis_pedidos"),
        InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_tracking_keyboard(codigo_pedido: str) -> InlineKeyboardMarkup:
    """
    Teclado para el tracking en vivo
    """
    keyboard = [
        [InlineKeyboardButton("⏹️ Detener Tracking", callback_data=f"stop_tracking_{codigo_pedido}")],
        [InlineKeyboardButton("🔙 Volver al Pedido", callback_data=f"ver_pedido_{codigo_pedido}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_rastrear_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para rastrear pedido
    """
    keyboard = [
        [InlineKeyboardButton("📦 Ver Mis Pedidos", callback_data="mis_pedidos")],
        [InlineKeyboardButton("🏠 Volver al Inicio", callback_data="volver_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
