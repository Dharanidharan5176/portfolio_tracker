from fastapi import APIRouter
router = APIRouter()

@router.get("/snapshot")
def get_snapshot():
    return {"generated_at": None, "holdings": []}
