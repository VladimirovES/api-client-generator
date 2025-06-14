"""Генератор на основе имен полей"""
from typing import Any, Optional
from faker import Faker

from ..base import BaseGenerator
from ..config import SmartFieldConfig

fake = Faker()


class SmartFieldGenerator(BaseGenerator):
    """Генератор, использующий имя поля для умной генерации"""

    def can_handle(self, field_type: Any, field_name: Optional[str] = None) -> bool:
        if field_type is not str or not field_name:
            return False

        field_lower = field_name.lower()

        # Проверяем точное совпадение
        if field_lower in SmartFieldConfig.EXACT_MAPPINGS:
            return True

        # Проверяем паттерны
        return any(pattern in field_lower
                   for pattern in SmartFieldConfig.PATTERN_MAPPINGS)

    def generate(self, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        if not field_name:
            return fake.text(max_nb_chars=20)

        field_lower = field_name.lower()

        # Точное совпадение приоритетнее
        if field_lower in SmartFieldConfig.EXACT_MAPPINGS:
            return SmartFieldConfig.EXACT_MAPPINGS[field_lower]()

        # Ищем по паттернам
        for pattern, generator in SmartFieldConfig.PATTERN_MAPPINGS.items():
            if pattern in field_lower:
                return generator()

        return fake.text(max_nb_chars=20)