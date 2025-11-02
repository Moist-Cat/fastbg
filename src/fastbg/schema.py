# stolen from
# https://github.com/tiangolo/pydantic-sqlalchemy/blob/master/pydantic_sqlalchemy/main.py
from typing import Type, Container, Optional
import re

from pydantic import BaseModel, create_model, Field
from sqlalchemy import inspect
from sqlalchemy.orm import ColumnProperty


def sqlalchemy_to_pydantic(
    db_model: Type,
    *,
    exclude: Container[str] = None,
    optional: Container[str] = None,
    all_optional: bool = False,
) -> Type[BaseModel]:
    """
    Convert SQLAlchemy model to Pydantic model.
    `all_optional` is used to create 'update' schemas
    """
    if exclude is None:
        exclude = []

    exclude = exclude or []
    mapper = inspect(db_model)
    fields = {}
    patterns = {}
    for attr_name in dir(db_model):
        if attr_name.startswith("pattern_"):
            field_name = attr_name.removeprefix("pattern_")
            patterns[field_name] = getattr(db_model, attr_name)

    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty):
            if attr.columns:
                name = attr.key
                if name in exclude:
                    continue
                column = attr.columns[0]
                python_type: Optional[type] = None

                # Get the Python type from SQLAlchemy column
                if hasattr(column.type, "impl"):
                    if hasattr(column.type.impl, "python_type"):
                        python_type = column.type.impl.python_type
                elif hasattr(column.type, "python_type"):
                    python_type = column.type.python_type

                if not python_type:
                    raise ValueError(
                        f"Couldn't determine type of {column} of {db_model}"
                    )

                field_config = {}
                if hasattr(column.type, "length") and column.type.length is not None:
                    field_config["max_length"] = column.type.length
                if python_type in {
                    str,
                }:
                    # non-empty strings
                    field_config["min_length"] = 1

                if name in patterns:
                    pattern = patterns[name]
                    if isinstance(pattern, (str, re.Pattern)):
                        field_config["pattern"] = pattern

                # optional fields
                default = None
                if all_optional:
                    python_type = Optional[python_type]
                    default = None
                elif column.default is None and not column.nullable:
                    default = ...
                elif column.nullable:
                    python_type = Optional[python_type]
                field_config["default"] = default

                fields[name] = (python_type, Field(**field_config))

    model_name = f"{db_model.__name__}Schema"
    pydantic_model = create_model(
        model_name,
        **fields,
    )

    return pydantic_model
