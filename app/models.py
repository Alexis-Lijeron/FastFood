from sqlalchemy import Column, String, Integer, DECIMAL, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ConfiguracionSistema(Base):
    """Configuración general del sistema"""
    __tablename__ = "configuracion_sistema"
    
    clave = Column(String(50), primary_key=True)
    valor = Column(String(255))


class ClienteBot(Base):
    """Clientes del bot de delivery"""
    __tablename__ = "cliente_bot"
    
    telefono = Column(String(20), primary_key=True)
    chat_id = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100))
    latitud_ultima = Column(DECIMAL(10, 8))
    longitud_ultima = Column(DECIMAL(10, 8))
    fecha_registro = Column(TIMESTAMP, server_default=func.now())
    
    # Relación con pedidos
    pedidos = relationship("Pedido", back_populates="cliente")


class Categoria(Base):
    """Categorías de productos"""
    __tablename__ = "categoria"
    
    codigo_categoria = Column(String(50), primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    
    # Relación con productos
    productos = relationship("Producto", back_populates="categoria")


class Conductor(Base):
    """Conductores de delivery"""
    __tablename__ = "conductor"
    
    codigo_conductor = Column(String(100), primary_key=True)
    nombre = Column(String(100), nullable=False)
    placa = Column(String(20), unique=True, nullable=False)
    tipo_vehiculo = Column(String(20))  # MOTO, AUTO
    vehiculo = Column(String(50))
    telefono = Column(String(20))
    latitud = Column(DECIMAL(10, 8))
    longitud = Column(DECIMAL(10, 8))
    is_disponible = Column(Boolean, default=True)
    ultima_actualizacion = Column(TIMESTAMP, server_default=func.now())
    
    # Relación con pedidos
    pedidos = relationship("Pedido", back_populates="conductor")


class Producto(Base):
    """Productos del menú"""
    __tablename__ = "producto"
    
    codigo_producto = Column(String(100), primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(DECIMAL(10, 2))
    img_url = Column(String(500))
    codigo_categoria = Column(String(50), ForeignKey("categoria.codigo_categoria"))
    
    # Relación con categoría
    categoria = relationship("Categoria", back_populates="productos")
    # Relación con items de pedido
    items = relationship("ItemPedido", back_populates="producto")


class Pedido(Base):
    """Pedidos de los clientes"""
    __tablename__ = "pedido"
    
    codigo_pedido = Column(String(50), primary_key=True)
    fecha = Column(TIMESTAMP, server_default=func.now())
    estado = Column(String(20), default="SOLICITADO")
    total = Column(DECIMAL(10, 2))
    observaciones = Column(Text, nullable=True)  # Detalles extra del pedido
    cliente_telefono = Column(String(20), ForeignKey("cliente_bot.telefono"))
    conductor_codigo = Column(String(100), ForeignKey("conductor.codigo_conductor"))
    latitud_origen = Column(DECIMAL(10, 8), default=-17.7838759)
    longitud_origen = Column(DECIMAL(10, 8), default=-63.1817578)
    latitud_destino = Column(DECIMAL(10, 8))
    longitud_destino = Column(DECIMAL(10, 8))
    
    # Relaciones
    cliente = relationship("ClienteBot", back_populates="pedidos")
    conductor = relationship("Conductor", back_populates="pedidos")
    items = relationship("ItemPedido", back_populates="pedido")
    transaccion = relationship("Transaction", back_populates="pedido", uselist=False)


class ItemPedido(Base):
    """Items dentro de un pedido"""
    __tablename__ = "items_pedido"
    
    codigo_pedido = Column(String(50), ForeignKey("pedido.codigo_pedido"), primary_key=True)
    codigo_producto = Column(String(100), ForeignKey("producto.codigo_producto"), primary_key=True)
    cantidad = Column(Integer)
    precio_unitario = Column(DECIMAL(10, 2))
    
    # Relaciones
    pedido = relationship("Pedido", back_populates="items")
    producto = relationship("Producto", back_populates="items")


class Transaction(Base):
    """Transacciones de pago"""
    __tablename__ = "transaction"
    
    codigo_transaccion = Column(String(50), primary_key=True)
    codigo_pedido = Column(String(50), ForeignKey("pedido.codigo_pedido"), unique=True)
    monto = Column(DECIMAL(10, 2))
    fecha = Column(TIMESTAMP, server_default=func.now())
    metodo_pago = Column(String(50), default="EFECTIVO")
    
    # Relación con pedido
    pedido = relationship("Pedido", back_populates="transaccion")
