from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Conductor, Pedido
from app.schemas import ConductorCreate, ConductorResponse, UbicacionUpdate, UbicacionResponse, PedidoResponse

router = APIRouter(prefix="/conductores", tags=["Conductores"])


@router.get("/", response_model=list[ConductorResponse])
def listar_conductores(db: Session = Depends(get_db)):
    """Obtener todos los conductores"""
    return db.query(Conductor).all()


@router.get("/disponibles", response_model=list[ConductorResponse])
def listar_conductores_disponibles(db: Session = Depends(get_db)):
    """Obtener conductores disponibles"""
    return db.query(Conductor).filter(Conductor.is_disponible == True).all()


@router.get("/{codigo}", response_model=ConductorResponse)
def obtener_conductor(codigo: str, db: Session = Depends(get_db)):
    """Obtener un conductor por código"""
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    return conductor


@router.post("/", response_model=ConductorResponse)
def crear_conductor(conductor: ConductorCreate, db: Session = Depends(get_db)):
    """Crear un nuevo conductor"""
    db_conductor = Conductor(**conductor.model_dump())
    db.add(db_conductor)
    db.commit()
    db.refresh(db_conductor)
    return db_conductor



@router.get("/{codigo}/ubicacion", response_model=UbicacionResponse)
def obtener_ubicacion(codigo: str, db: Session = Depends(get_db)):
    """
    Obtener la ubicación actual del conductor
    Útil para tracking en tiempo real
    """
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    if conductor.latitud is None or conductor.longitud is None:
        raise HTTPException(status_code=404, detail="El conductor no tiene ubicación registrada")
    
    return conductor


@router.put("/{codigo}/ubicacion", response_model=UbicacionResponse)
def actualizar_ubicacion(
    codigo: str, 
    ubicacion: UbicacionUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar ubicación del conductor (GPS)
    Se actualiza automáticamente el timestamp de última actualización
    """
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    conductor.latitud = ubicacion.latitud
    conductor.longitud = ubicacion.longitud
    conductor.ultima_actualizacion = datetime.now()
    
    db.commit()
    db.refresh(conductor)
    
    return conductor


@router.put("/{codigo}/disponibilidad")
def actualizar_disponibilidad(
    codigo: str, 
    disponible: bool,
    db: Session = Depends(get_db)
):
    """
    Actualizar disponibilidad del conductor
    """
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    conductor.is_disponible = disponible
    db.commit()
    
    return {"mensaje": f"Conductor {conductor.nombre} {'disponible' if disponible else 'no disponible'}"}


# ============ ENDPOINTS DE ASIGNACIÓN POR PROXIMIDAD ============
@router.get("/cercanos/restaurante")
def obtener_conductores_cercanos(db: Session = Depends(get_db)):
    """
    Obtener conductores disponibles ordenados por distancia al restaurante
    """
    from app.services.conductor_service import obtener_conductores_ordenados_por_distancia
    
    conductores = obtener_conductores_ordenados_por_distancia(db)
    
    if not conductores:
        return {"mensaje": "No hay conductores disponibles", "conductores": []}
    
    return {
        "total_disponibles": len(conductores),
        "conductores": conductores
    }


@router.get("/cercano/restaurante")
def obtener_conductor_mas_cercano_endpoint(db: Session = Depends(get_db)):
    """
    Obtener el conductor disponible más cercano al restaurante
    """
    from app.services.conductor_service import obtener_conductor_mas_cercano
    
    conductor = obtener_conductor_mas_cercano(db)
    
    if not conductor:
        raise HTTPException(status_code=404, detail="No hay conductores disponibles")
    
    return conductor


@router.get("/{codigo}/distancia")
def calcular_distancia_a_restaurante(codigo: str, db: Session = Depends(get_db)):
    """
    Calcular distancia de un conductor específico al restaurante
    """
    from app.services.conductor_service import (
        obtener_coordenadas_restaurante, 
        calcular_distancia_haversine
    )
    
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    if conductor.latitud is None or conductor.longitud is None:
        raise HTTPException(status_code=400, detail="El conductor no tiene ubicación registrada")
    
    rest_lat, rest_lng = obtener_coordenadas_restaurante(db)
    distancia = calcular_distancia_haversine(
        float(conductor.latitud),
        float(conductor.longitud),
        rest_lat,
        rest_lng
    )
    
    return {
        "conductor": conductor.nombre,
        "codigo": conductor.codigo_conductor,
        "latitud": float(conductor.latitud),
        "longitud": float(conductor.longitud),
        "restaurante_lat": rest_lat,
        "restaurante_lng": rest_lng,
        "distancia_km": distancia,
        "tiempo_estimado_min": int(distancia * 3)
    }


# ============ GESTIÓN DE PEDIDOS DEL CONDUCTOR ============
@router.get("/{codigo}/pedidos", response_model=list[PedidoResponse])
def obtener_pedidos_conductor(codigo: str, db: Session = Depends(get_db)):
    """
    Obtener pedidos activos asignados a un conductor
    Excluye pedidos ENTREGADO y CANCELADO
    """
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    pedidos = db.query(Pedido).filter(
        Pedido.conductor_codigo == codigo,
        Pedido.estado.notin_(["ENTREGADO", "CANCELADO"])
    ).order_by(Pedido.fecha.desc()).all()
    
    return pedidos


@router.get("/{codigo}/pedidos/pendientes")
def obtener_pedidos_pendientes_conductor(codigo: str, db: Session = Depends(get_db)):
    """
    Obtener pedidos pendientes de aceptación (estado ASIGNADO)
    El conductor puede aceptar o rechazar estos pedidos
    """
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    pedidos = db.query(Pedido).filter(
        Pedido.conductor_codigo == codigo,
        Pedido.estado == "ASIGNADO"
    ).order_by(Pedido.fecha.desc()).all()
    
    return {
        "conductor": conductor.nombre,
        "codigo_conductor": codigo,
        "total_pendientes": len(pedidos),
        "pedidos": [
            {
                "codigo_pedido": p.codigo_pedido,
                "fecha": p.fecha,
                "total": float(p.total) if p.total else 0,
                "estado": p.estado,
                "destino": {
                    "latitud": float(p.latitud_destino) if p.latitud_destino else None,
                    "longitud": float(p.longitud_destino) if p.longitud_destino else None
                }
            } for p in pedidos
        ]
    }


@router.put("/{codigo}/pedidos/{codigo_pedido}/aceptar")
def aceptar_pedido(codigo: str, codigo_pedido: str, db: Session = Depends(get_db)):
    """
    El conductor acepta un pedido asignado
    Cambia el estado del pedido de ASIGNADO a ACEPTADO
    """
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Verificar que el pedido esté asignado a este conductor
    if pedido.conductor_codigo != codigo:
        raise HTTPException(status_code=403, detail="Este pedido no está asignado a este conductor")
    
    # Verificar que el pedido esté en estado ASIGNADO
    if pedido.estado != "ASIGNADO":
        raise HTTPException(
            status_code=400, 
            detail=f"El pedido no puede ser aceptado. Estado actual: {pedido.estado}"
        )
    
    # Aceptar el pedido
    pedido.estado = "ACEPTADO"
    db.commit()
    
    return {
        "mensaje": f"Pedido {codigo_pedido} aceptado exitosamente",
        "pedido": {
            "codigo_pedido": pedido.codigo_pedido,
            "estado": pedido.estado,
            "total": float(pedido.total) if pedido.total else 0,
            "destino": {
                "latitud": float(pedido.latitud_destino) if pedido.latitud_destino else None,
                "longitud": float(pedido.longitud_destino) if pedido.longitud_destino else None
            }
        }
    }


@router.put("/{codigo}/pedidos/{codigo_pedido}/rechazar")
def rechazar_pedido(codigo: str, codigo_pedido: str, db: Session = Depends(get_db)):
    """
    El conductor rechaza un pedido asignado
    - El pedido vuelve a estado SOLICITADO
    - Se libera la asignación del conductor
    - El conductor vuelve a estar disponible
    """
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Verificar que el pedido esté asignado a este conductor
    if pedido.conductor_codigo != codigo:
        raise HTTPException(status_code=403, detail="Este pedido no está asignado a este conductor")
    
    # Verificar que el pedido esté en estado ASIGNADO
    if pedido.estado != "ASIGNADO":
        raise HTTPException(
            status_code=400, 
            detail=f"El pedido no puede ser rechazado. Estado actual: {pedido.estado}"
        )
    
    # Rechazar el pedido
    pedido.estado = "SOLICITADO"
    pedido.conductor_codigo = None
    
    # Liberar al conductor
    conductor.is_disponible = True
    
    db.commit()
    
    return {
        "mensaje": f"Pedido {codigo_pedido} rechazado",
        "detalle": "El pedido ha vuelto a la cola de pedidos solicitados",
        "conductor_liberado": True
    }


@router.get("/{codigo}/historial")
def obtener_historial_pedidos(codigo: str, db: Session = Depends(get_db)):
    """
    Obtener historial completo de pedidos de un conductor
    Incluye pedidos entregados y cancelados
    """
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    pedidos = db.query(Pedido).filter(
        Pedido.conductor_codigo == codigo
    ).order_by(Pedido.fecha.desc()).all()
    
    return {
        "conductor": conductor.nombre,
        "codigo_conductor": codigo,
        "total_pedidos": len(pedidos),
        "pedidos": [
            {
                "codigo_pedido": p.codigo_pedido,
                "fecha": p.fecha,
                "total": float(p.total) if p.total else 0,
                "estado": p.estado
            } for p in pedidos
        ]
    }


@router.get("/{codigo}/pedidos/{codigo_pedido}")
def obtener_detalle_pedido_conductor(codigo: str, codigo_pedido: str, db: Session = Depends(get_db)):
    """
    Ver el detalle completo de un pedido asignado al conductor
    Incluye: cliente, items, direcciones, totales
    """
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Verificar que el pedido esté asignado a este conductor
    if pedido.conductor_codigo != codigo:
        raise HTTPException(status_code=403, detail="Este pedido no está asignado a este conductor")
    
    # Obtener items del pedido
    from app.models import ItemPedido, Producto
    items = db.query(ItemPedido, Producto).join(
        Producto, ItemPedido.codigo_producto == Producto.codigo_producto
    ).filter(ItemPedido.codigo_pedido == codigo_pedido).all()
    
    items_detalle = [
        {
            "producto": item.Producto.nombre,
            "cantidad": item.ItemPedido.cantidad,
            "precio_unitario": float(item.ItemPedido.precio_unitario),
            "subtotal": float(item.ItemPedido.cantidad * item.ItemPedido.precio_unitario)
        } for item in items
    ]
    
    return {
        "pedido": {
            "codigo_pedido": pedido.codigo_pedido,
            "fecha": pedido.fecha,
            "estado": pedido.estado,
            "total": float(pedido.total) if pedido.total else 0,
            "observaciones": pedido.observaciones
        },
        "cliente": {
            "telefono": pedido.cliente_telefono,
            "nombre": pedido.cliente.nombre if pedido.cliente else None
        },
        "ubicacion_origen": {
            "latitud": float(pedido.latitud_origen) if pedido.latitud_origen else None,
            "longitud": float(pedido.longitud_origen) if pedido.longitud_origen else None,
            "descripcion": "Restaurante"
        },
        "ubicacion_destino": {
            "latitud": float(pedido.latitud_destino) if pedido.latitud_destino else None,
            "longitud": float(pedido.longitud_destino) if pedido.longitud_destino else None,
            "descripcion": "Cliente"
        },
        "items": items_detalle,
        "total_items": len(items_detalle)
    }


@router.put("/{codigo}/pedidos/{codigo_pedido}/estado")
def actualizar_estado_pedido_conductor(
    codigo: str, 
    codigo_pedido: str, 
    nuevo_estado: str,
    db: Session = Depends(get_db)
):
    """
    El conductor actualiza el estado del pedido.
    
    Estados disponibles (en orden):
    - ACEPTADO: El conductor acepta el pedido
    - EN_RESTAURANTE: El conductor llegó al restaurante
    - RECOGIO_PEDIDO: El conductor recogió el pedido
    - EN_CAMINO: El conductor va hacia el cliente
    - ENTREGADO: El pedido fue entregado (libera al conductor)
    
    Flujo: ASIGNADO -> ACEPTADO -> EN_RESTAURANTE -> RECOGIO_PEDIDO -> EN_CAMINO -> ENTREGADO
    """
    conductor = db.query(Conductor).filter(Conductor.codigo_conductor == codigo).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    
    pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Verificar que el pedido esté asignado a este conductor
    if pedido.conductor_codigo != codigo:
        raise HTTPException(status_code=403, detail="Este pedido no está asignado a este conductor")
    
    # Estados permitidos para el conductor
    estados_conductor = ["ACEPTADO", "EN_RESTAURANTE", "RECOGIO_PEDIDO", "EN_CAMINO", "ENTREGADO"]
    nuevo_estado = nuevo_estado.upper().replace(" ", "_")
    
    if nuevo_estado not in estados_conductor:
        raise HTTPException(
            status_code=400, 
            detail=f"Estado no válido. Estados disponibles: {estados_conductor}"
        )
    
    # Validar transiciones de estado
    transiciones_validas = {
        "ASIGNADO": ["ACEPTADO"],
        "ACEPTADO": ["EN_RESTAURANTE"],
        "EN_RESTAURANTE": ["RECOGIO_PEDIDO"],
        "RECOGIO_PEDIDO": ["EN_CAMINO"],
        "EN_CAMINO": ["ENTREGADO"]
    }
    
    estado_actual = pedido.estado
    
    if estado_actual not in transiciones_validas:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede cambiar el estado desde {estado_actual}"
        )
    
    if nuevo_estado not in transiciones_validas.get(estado_actual, []):
        siguiente_estado = transiciones_validas.get(estado_actual, ["N/A"])[0]
        raise HTTPException(
            status_code=400, 
            detail=f"Transición inválida: {estado_actual} -> {nuevo_estado}. "
                   f"El siguiente estado debe ser: {siguiente_estado}"
        )
    
    # Actualizar estado
    pedido.estado = nuevo_estado
    
    # Si el pedido fue entregado, liberar al conductor
    if nuevo_estado == "ENTREGADO":
        conductor.is_disponible = True
    
    db.commit()
    
    # Emojis para cada estado
    emojis_estado = {
        "ACEPTADO": "✅",
        "EN_RESTAURANTE": "🏪",
        "RECOGIO_PEDIDO": "📦",
        "EN_CAMINO": "🚴",
        "ENTREGADO": "🎉"
    }
    
    return {
        "mensaje": f"{emojis_estado.get(nuevo_estado, '📋')} Estado actualizado a {nuevo_estado}",
        "pedido": {
            "codigo_pedido": pedido.codigo_pedido,
            "estado_anterior": estado_actual,
            "estado_actual": nuevo_estado
        },
        "conductor_liberado": nuevo_estado == "ENTREGADO",
        "siguiente_estado": transiciones_validas.get(nuevo_estado, ["Pedido completado"])[0] if nuevo_estado != "ENTREGADO" else None
    }

