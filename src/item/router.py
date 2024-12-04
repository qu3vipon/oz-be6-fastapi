from fastapi import APIRouter, Depends

router = APIRouter(prefix="/items", tags=["Item"])


@router.get("")
def get_items_handler():
    return [
        {"id": 1, "name": "i-phone"},
        {"id": 2, "name": "samsung galaxy"},
    ]
