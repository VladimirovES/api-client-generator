"""Генератор для Enum типов"""
import random
from typing import Any, Optional

from ..base import BaseGenerator
from ..type_utils import TypeUtils


class EnumGenerator(BaseGenerator):
    """Генератор для Enum типов"""

    def can_handle(self, field_type: Any, field_name: Optional[str] = None) -> bool:
        return TypeUtils.is_enum(field_type)

    def generate(self, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        return random.choice(list(field_type))