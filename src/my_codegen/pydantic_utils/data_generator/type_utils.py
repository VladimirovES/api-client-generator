"""Утилиты для работы с типами"""
from typing import Any, Union, List, Dict, Set, get_args, get_origin, Annotated
from enum import Enum
from pydantic import RootModel, BaseModel
from my_codegen.pydantic_utils.pydantic_config import BaseConfigModel


class TypeUtils:
    """Утилиты для анализа типов"""

    @staticmethod
    def is_optional(field_type: Any) -> bool:
        """Проверяет, является ли тип Optional"""
        origin = get_origin(field_type)
        args = get_args(field_type)
        return origin is Union and type(None) in args

    @staticmethod
    def extract_base_type(field_type: Any) -> Any:
        """Извлекает базовый тип из Optional"""
        if TypeUtils.is_optional(field_type):
            args = get_args(field_type)
            return next(a for a in args if a is not type(None))
        return field_type

    @staticmethod
    def is_annotated(field_type: Any) -> bool:
        """Проверяет, является ли тип Annotated"""
        origin = get_origin(field_type)
        return origin is Annotated or "Annotated" in str(origin)

    @staticmethod
    def is_union(field_type: Any) -> bool:
        """Проверяет, является ли тип Union"""
        return get_origin(field_type) is Union

    @staticmethod
    def is_container(field_type: Any) -> bool:
        """Проверяет, является ли тип контейнером"""
        origin = get_origin(field_type)
        return origin in (list, List, dict, Dict, set, Set)

    @staticmethod
    def is_pydantic_model(field_type: Any) -> bool:
        """Проверяет, является ли тип Pydantic моделью"""
        return (isinstance(field_type, type) and
                (issubclass(field_type, BaseConfigModel) or
                 issubclass(field_type, BaseModel)))

    @staticmethod
    def is_root_model(field_type: Any) -> bool:
        """Проверяет, является ли тип RootModel"""
        return isinstance(field_type, type) and issubclass(field_type, RootModel)

    @staticmethod
    def is_enum(field_type: Any) -> bool:
        """Проверяет, является ли тип Enum"""
        return isinstance(field_type, type) and issubclass(field_type, Enum)