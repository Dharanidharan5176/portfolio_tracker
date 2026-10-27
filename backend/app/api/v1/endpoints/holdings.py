from fastapi import APIRouter
router = APIRouter()

@router.get("")
def list_holdings():
    return []
