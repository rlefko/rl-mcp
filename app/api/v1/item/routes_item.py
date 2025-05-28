from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.auth import authenticate
from app.databases.database import get_session

from .controllers_item import ItemController
from .models_item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter()


@router.get("", response_model=list[ItemRead], dependencies=[Depends(authenticate)])
def get_items(
    db: Session = Depends(get_session),
) -> list[ItemRead]:
    try:
        return ItemController.get_items(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{item_id}", response_model=ItemRead, dependencies=[Depends(authenticate)])
def get_item(
    item_id: int,
    db: Session = Depends(get_session),
) -> ItemRead:
    try:
        return ItemController.get_item(db, item_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "", status_code=status.HTTP_201_CREATED, dependencies=[Depends(authenticate)]
)
def create_item(item: ItemCreate, db: Session = Depends(get_session)) -> None:
    try:
        ItemController.create_item(db, item)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.patch(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(authenticate)],
)
def update_item(
    item_id: int, item: ItemUpdate, db: Session = Depends(get_session)
) -> None:
    try:
        ItemController.update_item(db, item_id, item)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
