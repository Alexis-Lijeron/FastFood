from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Producto
from app.schemas import ProductoCreate, ProductoResponse

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.get("/", response_model=list[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)):
    """Obtener todos los productos"""
    return db.query(Producto).all()


@router.get("/{codigo}", response_model=ProductoResponse)
def obtener_producto(codigo: str, db: Session = Depends(get_db)):
    """Obtener un producto por código"""
    producto = db.query(Producto).filter(Producto.codigo_producto == codigo).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.get("/categoria/{codigo_categoria}", response_model=list[ProductoResponse])
def productos_por_categoria(codigo_categoria: str, db: Session = Depends(get_db)):
    """Obtener productos por categoría"""
    return db.query(Producto).filter(Producto.codigo_categoria == codigo_categoria).all()


@router.post("/", response_model=ProductoResponse)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    """Crear un nuevo producto"""
    db_producto = Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto


@router.put("/{codigo}", response_model=ProductoResponse)
def actualizar_producto(codigo: str, producto: ProductoCreate, db: Session = Depends(get_db)):
    """Actualizar un producto"""
    db_producto = db.query(Producto).filter(Producto.codigo_producto == codigo).first()
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    for key, value in producto.model_dump().items():
        setattr(db_producto, key, value)
    
    db.commit()
    db.refresh(db_producto)
    return db_producto


@router.delete("/{codigo}")
def eliminar_producto(codigo: str, db: Session = Depends(get_db)):
    """Eliminar un producto"""
    producto = db.query(Producto).filter(Producto.codigo_producto == codigo).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(producto)
    db.commit()
    return {"mensaje": "Producto eliminado"}
