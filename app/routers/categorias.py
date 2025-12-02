from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Categoria
from app.schemas import CategoriaCreate, CategoriaResponse

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.get("/", response_model=list[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db)):
    """Obtener todas las categorías"""
    return db.query(Categoria).all()


@router.get("/{codigo}", response_model=CategoriaResponse)
def obtener_categoria(codigo: str, db: Session = Depends(get_db)):
    """Obtener una categoría por código"""
    categoria = db.query(Categoria).filter(Categoria.codigo_categoria == codigo).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria


@router.post("/", response_model=CategoriaResponse)
def crear_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    """Crear una nueva categoría"""
    db_categoria = Categoria(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


@router.delete("/{codigo}")
def eliminar_categoria(codigo: str, db: Session = Depends(get_db)):
    """Eliminar una categoría"""
    categoria = db.query(Categoria).filter(Categoria.codigo_categoria == codigo).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    db.delete(categoria)
    db.commit()
    return {"mensaje": "Categoría eliminada"}
