"""Генератор контейнерных типов"""
import random
from typing import Any, Optional, List, Dict, Set, get_origin, get_args
from faker import Faker

from ..base import BaseGenerator

fake = Faker()


class ContainerGenerator(BaseGenerator):
    """Генератор контейнерных типов"""

    def can_handle(self, field_type: Any, field_name: Optional[str] = None) -> bool:
        origin = get_origin(field_type)
        return origin in (list, List, dict, Dict, set, Set)

    def generate(self, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        if current_depth >= max_depth:
            return self._empty_container(field_type)

        origin = get_origin(field_type)
        args = get_args(field_type)

        if origin in (list, List):
            item_type = args[0] if args else str
            # Импортируем здесь, чтобы избежать циклических импортов
            from ..value_generator import ValueGenerator
            return [
                ValueGenerator.generate(item_type, None, current_depth + 1, max_depth)
                for _ in range(random.randint(1, 2))
            ]

        elif origin in (dict, Dict):
            value_type = args[1] if len(args) > 1 else str
            from ..value_generator import ValueGenerator
            return {
                fake.word(): ValueGenerator.generate(value_type, None, current_depth + 1, max_depth)
                for _ in range(random.randint(1, 2))
            }

        elif origin in (set, Set):
            item_type = args[0] if args else str
            from ..value_generator import ValueGenerator
            return {
                ValueGenerator.generate(item_type, None, current_depth + 1, max_depth)
                for _ in range(random.randint(1, 2))
            }

    def _empty_container(self, field_type: Any) -> Any:
        origin = get_origin(field_type)
        if origin in (list, List):
            return []
        elif origin in (dict, Dict):
            return {}
        elif origin in (set, Set):
            return set()