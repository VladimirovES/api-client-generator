"""Главный генератор-диспетчер"""
import random
from typing import Any, List, Optional, get_args

from .base import BaseGenerator
from .type_utils import TypeUtils
from .generators import (
    SmartFieldGenerator,
    AnnotatedGenerator,
    EnumGenerator,
    PydanticModelGenerator,
    ContainerGenerator,
    PrimitiveGenerator,
    SpecialTypeGenerator,
)


class ValueGenerator:
    """Главный генератор, управляющий всеми остальными"""

    # Порядок важен! Более специфичные генераторы должны быть первыми
    _generators: List[BaseGenerator] = [
        SmartFieldGenerator(),
        AnnotatedGenerator(),
        EnumGenerator(),
        PydanticModelGenerator(),
        ContainerGenerator(),
        PrimitiveGenerator(),
        SpecialTypeGenerator(),
    ]

    @classmethod
    def generate(cls, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        """Генерирует значение для заданного типа"""

        # Обработка Optional
        if TypeUtils.is_optional(field_type):
            real_type = TypeUtils.extract_base_type(field_type)
            return cls.generate(real_type, field_name, current_depth, max_depth)

        # Обработка Union (не Optional)
        if TypeUtils.is_union(field_type):
            args = get_args(field_type)
            chosen = random.choice(args)
            return cls.generate(chosen, field_name, current_depth, max_depth)

        # Проходим по цепочке генераторов
        for generator in cls._generators:
            if generator.can_handle(field_type, field_name):
                return generator.generate(field_type, field_name, current_depth, max_depth)

        raise ValueError(f"No generator found for type: {field_type}")