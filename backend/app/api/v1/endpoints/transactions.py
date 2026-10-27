from fastapi import APIRouter
router = APIRouter()

@router.get("")
def list_transactions():
    return {"items": [], "total": 0}
