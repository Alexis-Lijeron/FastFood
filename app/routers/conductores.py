from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Conductor
from app.schemas import ConductorCreate, ConductorResponse, UbicacionUpdate, UbicacionResponse

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
