# stolen from
# https://github.com/tiangolo/pydantic-sqlalchemy/blob/master/pydantic_sqlalchemy/main.py
from pydantic import BaseModel, ConfigDict, create_model
from sqlalchemy import inspect
from sqlalchemy.orm import ColumnProperty
from typing import Type, Container, Optional, Any
from datetime import datetime
import re

def sqlalchemy_to_pydantic(
    db_model: Type, *, exclude: Container[str] = None
) -> Type[BaseModel]:
    """Convert SQLAlchemy model to Pydantic model"""
    if exclude is None:
        exclude = []
    
    exclude = exclude or []
    mapper = inspect(db_model)
    fields = {}
    
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
                    raise ValueError(f"Couldn't determine type of {type_str} or {db_model}")
                
                # Handle optional fields
                default = None
                if column.default is None and not column.nullable:
                    default = ...
                elif column.nullable:
                    python_type = Optional[python_type]
                
                fields[name] = (python_type, default)
    
    # Create the Pydantic model
    model_name = f"{db_model.__name__}Schema"
    pydantic_model = create_model(
        model_name,
        #__config__=config,
        **fields
    )
    
    return pydantic_model
