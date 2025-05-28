from app.api.v1.base.tables import BaseMCPTable


class Item(BaseMCPTable, table=True):
    __tablename__ = "items"

    pass
