from fastapi import APIRouter
router = APIRouter()

@router.get("")
def get_performance():
    return {"status": "insufficient_data", "message": "Record transactions to compute time-weighted returns"}
