from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime


# ============ CATEGORIA ============
class CategoriaBase(BaseModel):
    nombre: str

class CategoriaCreate(CategoriaBase):
    codigo_categoria: str

class CategoriaResponse(CategoriaBase):
    codigo_categoria: str
    
    class Config:
        from_attributes = True


# ============ PRODUCTO ============
class ProductoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: Decimal
    img_url: Optional[str] = None
    codigo_categoria: Optional[str] = None

class ProductoCreate(ProductoBase):
    codigo_producto: str

class ProductoResponse(ProductoBase):
    codigo_producto: str
    
    class Config:
        from_attributes = True


# ============ CLIENTE ============
class ClienteBase(BaseModel):
    nombre: Optional[str] = None
    latitud_ultima: Optional[Decimal] = None
    longitud_ultima: Optional[Decimal] = None

class ClienteCreate(ClienteBase):
    telefono: str
    chat_id: str

class ClienteResponse(ClienteBase):
    telefono: str
    chat_id: str
    fecha_registro: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============ CONDUCTOR ============
class ConductorBase(BaseModel):
    nombre: str
    placa: str
    tipo_vehiculo: Optional[str] = None
    vehiculo: Optional[str] = None
    telefono: Optional[str] = None
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    is_disponible: bool = True

class ConductorCreate(ConductorBase):
    codigo_conductor: str

class ConductorResponse(ConductorBase):
    codigo_conductor: str
    ultima_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Schema para actualizar ubicación
class UbicacionUpdate(BaseModel):
    latitud: Decimal
    longitud: Decimal


# Schema para respuesta de ubicación
class UbicacionResponse(BaseModel):
    codigo_conductor: str
    nombre: str
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    is_disponible: bool
    ultima_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============ PEDIDO ============
class ItemPedidoBase(BaseModel):
    codigo_producto: str
    cantidad: int
    precio_unitario: Decimal

class PedidoBase(BaseModel):
    cliente_telefono: str
    latitud_destino: Optional[Decimal] = None
    longitud_destino: Optional[Decimal] = None

class PedidoCreate(PedidoBase):
    codigo_pedido: str
    items: list[ItemPedidoBase] = []

class PedidoResponse(PedidoBase):
    codigo_pedido: str
    fecha: Optional[datetime] = None
    estado: str
    total: Optional[Decimal] = None
    conductor_codigo: Optional[str] = None
    latitud_origen: Decimal
    longitud_origen: Decimal
    
    class Config:
        from_attributes = True


# ============ TRANSACTION ============
class TransactionBase(BaseModel):
    codigo_pedido: str
    monto: Decimal
    metodo_pago: str = "EFECTIVO"

class TransactionCreate(TransactionBase):
    codigo_transaccion: str

class TransactionResponse(TransactionBase):
    codigo_transaccion: str
    fecha: Optional[datetime] = None
    
    class Config:
        from_attributes = True
