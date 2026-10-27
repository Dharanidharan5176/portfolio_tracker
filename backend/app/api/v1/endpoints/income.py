from fastapi import APIRouter
router = APIRouter()

@router.get("")
def get_income():
    return {"total_income": "0.00", "by_month": [], "by_symbol": []}
