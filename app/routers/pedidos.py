from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Pedido, ItemPedido, Conductor
from app.schemas import PedidoCreate, PedidoResponse
import random
import string

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


def generar_codigo_pedido() -> str:
    """Genera un código único para el pedido: PED-XXXXXX"""
    chars = string.ascii_uppercase + string.digits
    return f"PED-{''.join(random.choices(chars, k=6))}"


@router.get("/", response_model=list[PedidoResponse])
def listar_pedidos(db: Session = Depends(get_db)):
    """Obtener todos los pedidos"""
    return db.query(Pedido).all()


@router.get("/{codigo}", response_model=PedidoResponse)
def obtener_pedido(codigo: str, db: Session = Depends(get_db)):
    """Obtener un pedido por código"""
    pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido


@router.get("/cliente/{telefono}", response_model=list[PedidoResponse])
def pedidos_por_cliente(telefono: str, db: Session = Depends(get_db)):
    """Obtener pedidos de un cliente"""
    return db.query(Pedido).filter(Pedido.cliente_telefono == telefono).all()


@router.get("/estado/{estado}", response_model=list[PedidoResponse])
def pedidos_por_estado(estado: str, db: Session = Depends(get_db)):
    """Obtener pedidos por estado"""
    return db.query(Pedido).filter(Pedido.estado == estado.upper()).all()


@router.post("/", response_model=PedidoResponse)
def crear_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    """Crear un nuevo pedido con sus items"""
    # Generar código si no viene
    codigo = pedido.codigo_pedido or generar_codigo_pedido()
    
    # Calcular total
    total = sum(item.cantidad * item.precio_unitario for item in pedido.items)
    
    # Crear pedido
    db_pedido = Pedido(
        codigo_pedido=codigo,
        cliente_telefono=pedido.cliente_telefono,
        latitud_destino=pedido.latitud_destino,
        longitud_destino=pedido.longitud_destino,
        total=total,
        estado="SOLICITADO"
    )
    db.add(db_pedido)
    
    # Crear items
    for item in pedido.items:
        db_item = ItemPedido(
            codigo_pedido=codigo,
            codigo_producto=item.codigo_producto,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_pedido)
    return db_pedido


@router.put("/{codigo}/estado")
def actualizar_estado(codigo: str, nuevo_estado: str, db: Session = Depends(get_db)):
    """
    Actualizar estado del pedido
    Estados: SOLICITADO -> ASIGNADO -> ACEPTADO -> EN_RESTAURANTE -> RECOGIO_PEDIDO -> EN_CAMINO -> ENTREGADO
    """
    estados_validos = [
        "SOLICITADO", "ASIGNADO", "ACEPTADO", 
        "EN_RESTAURANTE", "RECOGIO_PEDIDO", "EN_CAMINO", 
        "ENTREGADO", "CANCELADO"
    ]
    
    nuevo_estado = nuevo_estado.upper().replace(" ", "_")
    
    if nuevo_estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Use: {estados_validos}")
    
    pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    pedido.estado = nuevo_estado
    db.commit()
    
    return {"mensaje": f"Estado actualizado a {nuevo_estado}"}


@router.put("/{codigo}/asignar/{codigo_conductor}")
def asignar_conductor(codigo: str, codigo_conductor: str, db: Session = Depends(get_db)):
    """Asignar un conductor manualmente al pedido"""
    pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo_conductor).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    if not conductor.is_disponible:
        raise HTTPException(status_code=400, detail="Conductor no disponible")
    
    # Asignar conductor y cambiar estado
    pedido.conductor_codigo = codigo_conductor
    pedido.estado = "ASIGNADO"
    conductor.is_disponible = False
    
    db.commit()
    
    return {"mensaje": f"Conductor {codigo_conductor} asignado al pedido {codigo}"}


@router.put("/{codigo}/asignar-automatico")
def asignar_conductor_automatico(codigo: str, db: Session = Depends(get_db)):
    """
    Asignar automáticamente el conductor más cercano al restaurante
    """
    from app.services.conductor_service import asignar_conductor_a_pedido
    
    resultado = asignar_conductor_a_pedido(db, codigo)
    
    if not resultado["exito"]:
        raise HTTPException(status_code=400, detail=resultado["mensaje"])
    
    return resultado


@router.put("/{codigo}/liberar-conductor")
def liberar_conductor_pedido(codigo: str, db: Session = Depends(get_db)):
    """
    Libera el conductor asignado al pedido (lo marca como disponible)
    Útil cuando el pedido se cancela o se entrega
    """
    from app.services.conductor_service import liberar_conductor
    
    pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    if not pedido.conductor_codigo:
        raise HTTPException(status_code=400, detail="El pedido no tiene conductor asignado")
    
    resultado = liberar_conductor(db, pedido.conductor_codigo)
    
    # Limpiar conductor del pedido
    pedido.conductor_codigo = None
    if pedido.estado == "ASIGNADO":
        pedido.estado = "SOLICITADO"
    db.commit()
    
    return resultado

