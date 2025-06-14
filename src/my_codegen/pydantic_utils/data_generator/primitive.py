"""Генератор примитивных типов"""
import random
from datetime import datetime, date, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4
from faker import Faker

from ..base import BaseGenerator

fake = Faker()


class PrimitiveGenerator(BaseGenerator):
    """Генератор примитивных типов"""

    GENERATORS = {
        str: lambda: fake.text(max_nb_chars=20),
        int: lambda: random.randint(1, 1000),
        float: lambda: random.uniform(1.0, 100.0),
        bool: lambda: random.choice([True, False]),
        datetime: lambda: (datetime.now() + timedelta(days=1)).isoformat() + "Z",
        date: lambda: (datetime.now() + timedelta(days=1)).date().isoformat(),
        UUID: lambda: str(uuid4()),  # TODO убрать STR и посмотреть может лучше сразу json_dump использовать
        Any: lambda: random.choice([fake.word(), random.randint(1, 1000),
                                    random.uniform(1.0, 100.0)]),
    }

    def can_handle(self, field_type: Any, field_name: Optional[str] = None) -> bool:
        return field_type in self.GENERATORS

    def generate(self, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        return self.GENERATORS[field_type]()