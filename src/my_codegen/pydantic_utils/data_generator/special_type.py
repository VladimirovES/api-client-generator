"""Генератор для специальных Pydantic типов"""
from typing import Any, Optional, ForwardRef
from faker import Faker

from ..base import BaseGenerator

fake = Faker()


class SpecialTypeGenerator(BaseGenerator):
    """Генератор для специальных Pydantic типов"""

    def can_handle(self, field_type: Any, field_name: Optional[str] = None) -> bool:
        if isinstance(field_type, ForwardRef):
            return True

        field_str = str(field_type)
        return 'pydantic' in field_str or any(
            keyword in field_str
            for keyword in ['Url', 'Email', 'Json', 'Path', 'Secret', 'IPv']
        )

    def generate(self, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        if isinstance(field_type, ForwardRef):
            return []

        field_str = str(field_type)
        field_name_str = getattr(field_type, '__name__', field_str)

        # Маппинг специальных типов
        type_mappings = {
            'url': fake.url,
            'email': fake.email,
            'json': lambda: {"example": "data"},
            'path': fake.file_path,
            'secret': fake.password,
            'ipv4': fake.ipv4,
            'ipv6': fake.ipv6,
        }

        # Ищем подходящий генератор
        for key, generator in type_mappings.items():
            if key in field_str.lower() or key in field_name_str.lower():
                return generator()

        # Fallback для неизвестных pydantic типов
        if 'pydantic' in field_str:
            return fake.word()

        raise ValueError(f"Unsupported field type: {field_type}")