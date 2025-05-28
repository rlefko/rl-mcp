from sqlmodel import Session, select

from .models_item import ItemCreate, ItemRead, ItemUpdate
from .tables_item import Item


class ItemController:
    @staticmethod
    def get_items(db: Session) -> list[ItemRead]:
        return db.exec(select(Item)).all()

    @staticmethod
    def get_item(db: Session, item_id: int) -> ItemRead:
        item = db.exec(select(Item).where(Item.id == item_id)).first()
        if not item:
            raise KeyError("Item not found")
        return item

    @staticmethod
    def create_item(db: Session, item_data: ItemCreate) -> ItemRead:
        item = Item(**item_data.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update_item(db: Session, item_id: int, item_update: ItemUpdate) -> ItemRead:
        item = db.exec(select(Item).where(Item.id == item_id)).first()
        if not item:
            raise KeyError("Item not found")
        if item_update.name:
            item.name = item_update.name
        if item_update.description:
            item.description = item_update.description
        db.commit()
        db.refresh(item)
        return item
