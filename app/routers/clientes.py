from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ClienteBot
from app.schemas import ClienteCreate, ClienteResponse

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("/", response_model=list[ClienteResponse])
def listar_clientes(db: Session = Depends(get_db)):
    """Obtener todos los clientes"""
    return db.query(ClienteBot).all()


@router.get("/{telefono}", response_model=ClienteResponse)
def obtener_cliente(telefono: str, db: Session = Depends(get_db)):
    """Obtener un cliente por teléfono"""
    cliente = db.query(ClienteBot).filter(ClienteBot.telefono == telefono).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.get("/chat/{chat_id}", response_model=ClienteResponse)
def obtener_cliente_por_chat(chat_id: str, db: Session = Depends(get_db)):
    """Obtener un cliente por chat_id"""
    cliente = db.query(ClienteBot).filter(ClienteBot.chat_id == chat_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.post("/", response_model=ClienteResponse)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    """Crear o actualizar un cliente"""
    # Verificar si ya existe
    db_cliente = db.query(ClienteBot).filter(ClienteBot.telefono == cliente.telefono).first()
    
    if db_cliente:
        # Actualizar
        for key, value in cliente.model_dump().items():
            setattr(db_cliente, key, value)
    else:
        # Crear nuevo
        db_cliente = ClienteBot(**cliente.model_dump())
        db.add(db_cliente)
    
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


@router.put("/{telefono}/ubicacion")
def actualizar_ubicacion(
    telefono: str, 
    latitud: float, 
    longitud: float, 
    db: Session = Depends(get_db)
):
    """Actualizar ubicación del cliente"""
    cliente = db.query(ClienteBot).filter(ClienteBot.telefono == telefono).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    cliente.latitud_ultima = latitud
    cliente.longitud_ultima = longitud
    db.commit()
    
    return {"mensaje": "Ubicación actualizada"}
