"""
Servicio de asignación de conductores
Calcula distancias y asigna el conductor más cercano al restaurante
"""
import math
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Conductor, Pedido, ConfiguracionSistema


# Coordenadas del restaurante (Catedral - por defecto)
RESTAURANTE_LAT = -17.7838759
RESTAURANTE_LNG = -63.1817578


def obtener_coordenadas_restaurante(db: Session) -> tuple:
    """
    Obtiene las coordenadas del restaurante desde la configuración
    """
    try:
        lat_config = db.query(ConfiguracionSistema).filter(
            ConfiguracionSistema.clave == "REST_LAT"
        ).first()
        lng_config = db.query(ConfiguracionSistema).filter(
            ConfiguracionSistema.clave == "REST_LNG"
        ).first()
        
        if lat_config and lng_config:
            return float(lat_config.valor), float(lng_config.valor)
    except:
        pass
    
    return RESTAURANTE_LAT, RESTAURANTE_LNG


def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia entre dos puntos geográficos usando la fórmula Haversine
    
    Args:
        lat1, lon1: Coordenadas del primer punto
        lat2, lon2: Coordenadas del segundo punto
    
    Returns:
        Distancia en kilómetros
    """
    # Radio de la Tierra en kilómetros
    R = 6371.0
    
    # Convertir grados a radianes
    lat1_rad = math.radians(float(lat1))
    lat2_rad = math.radians(float(lat2))
    lon1_rad = math.radians(float(lon1))
    lon2_rad = math.radians(float(lon2))
    
    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distancia = R * c
    return round(distancia, 2)


def obtener_conductores_disponibles(db: Session) -> list:
    """
    Obtiene todos los conductores disponibles con ubicación válida
    """
    conductores = db.query(Conductor).filter(
        Conductor.is_disponible == True,
        Conductor.latitud.isnot(None),
        Conductor.longitud.isnot(None)
    ).all()
    
    return conductores


def calcular_distancia_conductor_restaurante(
    conductor: Conductor, 
    rest_lat: float, 
    rest_lng: float
) -> dict:
    """
    Calcula la distancia de un conductor al restaurante
    
    Returns:
        Dict con info del conductor y su distancia
    """
    distancia = calcular_distancia_haversine(
        float(conductor.latitud),
        float(conductor.longitud),
        rest_lat,
        rest_lng
    )
    
    return {
        "codigo_conductor": conductor.codigo_conductor,
        "nombre": conductor.nombre,
        "telefono": conductor.telefono,
        "tipo_vehiculo": conductor.tipo_vehiculo,
        "vehiculo": conductor.vehiculo,
        "latitud": float(conductor.latitud),
        "longitud": float(conductor.longitud),
        "distancia_km": distancia
    }


def obtener_conductor_mas_cercano(db: Session) -> dict | None:
    """
    Encuentra el conductor disponible más cercano al restaurante
    
    Returns:
        Dict con info del conductor más cercano o None si no hay disponibles
    """
    # Obtener coordenadas del restaurante
    rest_lat, rest_lng = obtener_coordenadas_restaurante(db)
    
    # Obtener conductores disponibles
    conductores = obtener_conductores_disponibles(db)
    
    if not conductores:
        return None
    
    # Calcular distancia de cada conductor
    conductores_con_distancia = []
    for conductor in conductores:
        info = calcular_distancia_conductor_restaurante(conductor, rest_lat, rest_lng)
        conductores_con_distancia.append(info)
    
    # Ordenar por distancia y retornar el más cercano
    conductores_con_distancia.sort(key=lambda x: x["distancia_km"])
    
    return conductores_con_distancia[0] if conductores_con_distancia else None


def obtener_conductores_ordenados_por_distancia(db: Session) -> list:
    """
    Obtiene todos los conductores disponibles ordenados por distancia al restaurante
    
    Returns:
        Lista de conductores con su distancia, ordenados de menor a mayor
    """
    rest_lat, rest_lng = obtener_coordenadas_restaurante(db)
    conductores = obtener_conductores_disponibles(db)
    
    conductores_con_distancia = []
    for conductor in conductores:
        info = calcular_distancia_conductor_restaurante(conductor, rest_lat, rest_lng)
        conductores_con_distancia.append(info)
    
    conductores_con_distancia.sort(key=lambda x: x["distancia_km"])
    
    return conductores_con_distancia


def asignar_conductor_a_pedido(db: Session, codigo_pedido: str) -> dict:
    """
    Asigna automáticamente el conductor más cercano a un pedido
    
    Args:
        db: Sesión de base de datos
        codigo_pedido: Código del pedido a asignar
    
    Returns:
        Dict con resultado de la asignación
    """
    # Verificar que el pedido existe y está en estado SOLICITADO
    pedido = db.query(Pedido).filter(Pedido.codigo_pedido == codigo_pedido).first()
    
    if not pedido:
        return {"exito": False, "mensaje": "Pedido no encontrado"}
    
    if pedido.estado != "SOLICITADO":
        return {"exito": False, "mensaje": f"El pedido ya está en estado: {pedido.estado}"}
    
    if pedido.conductor_codigo:
        return {"exito": False, "mensaje": "El pedido ya tiene un conductor asignado"}
    
    # Obtener conductor más cercano
    conductor_info = obtener_conductor_mas_cercano(db)
    
    if not conductor_info:
        return {"exito": False, "mensaje": "No hay conductores disponibles"}
    
    # Asignar conductor al pedido
    codigo_conductor = conductor_info["codigo_conductor"]
    
    # Actualizar pedido
    pedido.conductor_codigo = codigo_conductor
    pedido.estado = "ASIGNADO"
    
    # Marcar conductor como no disponible
    conductor = db.query(Conductor).filter(
        Conductor.codigo_conductor == codigo_conductor
    ).first()
    conductor.is_disponible = False
    
    db.commit()
    
    return {
        "exito": True,
        "mensaje": f"Conductor {conductor_info['nombre']} asignado al pedido",
        "pedido": codigo_pedido,
        "conductor": conductor_info,
        "distancia_restaurante_km": conductor_info["distancia_km"]
    }


def liberar_conductor(db: Session, codigo_conductor: str) -> dict:
    """
    Libera un conductor (lo marca como disponible)
    Se usa cuando el pedido se entrega o cancela
    """
    conductor = db.query(Conductor).filter(
        Conductor.codigo_conductor == codigo_conductor
    ).first()
    
    if not conductor:
        return {"exito": False, "mensaje": "Conductor no encontrado"}
    
    conductor.is_disponible = True
    db.commit()
    
    return {"exito": True, "mensaje": f"Conductor {conductor.nombre} disponible"}


def calcular_distancia_conductor_cliente(
    db: Session,
    codigo_conductor: str,
    lat_cliente: float,
    lng_cliente: float
) -> dict:
    """
    Calcula la distancia entre un conductor y la ubicación del cliente
    """
    conductor = db.query(Conductor).filter(
        Conductor.codigo_conductor == codigo_conductor
    ).first()
    
    if not conductor or not conductor.latitud or not conductor.longitud:
        return {"distancia_km": None, "mensaje": "Conductor sin ubicación"}
    
    distancia = calcular_distancia_haversine(
        float(conductor.latitud),
        float(conductor.longitud),
        lat_cliente,
        lng_cliente
    )
    
    return {
        "conductor": conductor.nombre,
        "distancia_km": distancia,
        "tiempo_estimado_min": int(distancia * 3)  # Aprox 3 min por km
    }
