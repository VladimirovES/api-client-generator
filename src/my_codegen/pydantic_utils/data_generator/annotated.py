"""Генератор для Annotated типов"""
import random
from typing import Any, Optional, get_args
from faker import Faker
from pydantic import Field, StringConstraints

from ..base import BaseGenerator
from ..type_utils import TypeUtils

fake = Faker()


class AnnotatedGenerator(BaseGenerator):
    """Генератор для Annotated типов"""

    def can_handle(self, field_type: Any, field_name: Optional[str] = None) -> bool:
        return TypeUtils.is_annotated(field_type)

    def generate(self, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        args = get_args(field_type)
        base_type = args[0] if args else str
        metadata = args[1:] if len(args) > 1 else ()

        if base_type is str:
            return self._handle_string_constraints(metadata)

        from ..value_generator import ValueGenerator
        return ValueGenerator.generate(base_type, field_name, current_depth, max_depth)

    def _handle_string_constraints(self, metadata: tuple) -> str:
        min_len, max_len = 1, 20

        for meta in metadata:
            if isinstance(meta, (Field, StringConstraints)):
                if hasattr(meta, 'min_length') and meta.min_length is not None:
                    min_len = meta.min_length
                if hasattr(meta, 'max_length') and meta.max_length is not None:
                    max_len = meta.max_length

        length = random.randint(min_len, max_len) if min_len <= max_len else 1
        return fake.pystr(min_chars=length, max_chars=length)