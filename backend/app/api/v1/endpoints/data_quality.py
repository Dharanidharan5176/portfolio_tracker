from fastapi import APIRouter
router = APIRouter()

@router.get("/issues")
def list_issues():
    return []
