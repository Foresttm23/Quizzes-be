from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def health_check():
    return {
        "statusCode": 200,
        "detail": "ok",
        "result": "working"
    }
