from sqlalchemy import select


def base_query(model):
    if hasattr(model, "is_soft_deleted"):
        return select(model).where(model.is_soft_deleted == False)
    return select(model)


def query_deleted(model):
    if hasattr(model, "is_soft_deleted"):
        return select(model).where(model.is_soft_deleted == True)
    return select(model)
