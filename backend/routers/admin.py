"""Admin router — view and update prices in the database."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import db

router = APIRouter(prefix="/admin")


class PriceUpdate(BaseModel):
    price_gel: float


@router.get("/materials")
def list_materials():
    return db.get_all_materials()


@router.get("/labor")
def list_labor():
    return db.get_all_labor()


@router.put("/materials/{material_id}/price")
def update_material(material_id: int, body: PriceUpdate):
    if body.price_gel <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive.")
    db.update_material_price(material_id, body.price_gel)
    return {"ok": True, "id": material_id, "new_price_gel": body.price_gel}


@router.put("/labor/{labor_id}/price")
def update_labor(labor_id: int, body: PriceUpdate):
    if body.price_gel <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive.")
    db.update_labor_price(labor_id, body.price_gel)
    return {"ok": True, "id": labor_id, "new_price_gel": body.price_gel}
