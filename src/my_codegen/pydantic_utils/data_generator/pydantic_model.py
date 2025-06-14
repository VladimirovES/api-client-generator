"""Генератор для Pydantic моделей"""
from typing import Any, Optional

from ..base import BaseGenerator
from ..type_utils import TypeUtils


class PydanticModelGenerator(BaseGenerator):
    """Генератор для Pydantic моделей"""

    def can_handle(self, field_type: Any, field_name: Optional[str] = None) -> bool:
        return TypeUtils.is_pydantic_model(field_type) or TypeUtils.is_root_model(field_type)

    def generate(self, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        if TypeUtils.is_root_model(field_type):
            return self._generate_root_model(field_type, current_depth, max_depth)
        else:
            return self._generate_pydantic_model(field_type, current_depth, max_depth)

    def _generate_root_model(self, field_type: Any, current_depth: int, max_depth: int) -> Any:
        root_annotation = field_type.model_fields["root"].annotation
        # Импортируем здесь, чтобы избежать циклических импортов
        from ..value_generator import ValueGenerator
        generated = ValueGenerator.generate(root_annotation, None, current_depth, max_depth)
        return field_type.model_construct(root=generated, _fields_set={"root"})

    def _generate_pydantic_model(self, field_type: Any, current_depth: int, max_depth: int) -> Any:
        if current_depth >= max_depth:
            try:
                # Импортируем здесь, чтобы избежать циклических импортов
                from my_codegen.pydantic_utils.data_generator_pydantic import GenerateData
                from_data = GenerateData(field_type, current_depth, max_depth)
                return from_data.fill_required().build()
            except:
                return None

        from my_codegen.pydantic_utils.data_generator_pydantic import GenerateData
        from_data = GenerateData(field_type, current_depth + 1, max_depth)
        return from_data.fill_all_fields().build()