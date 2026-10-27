from fastapi import APIRouter
router = APIRouter()

@router.get("")
def get_allocation():
    return {"by_asset_class": [], "by_account": [], "by_currency": [], "by_holding": []}
