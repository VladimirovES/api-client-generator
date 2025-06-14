"""Базовый класс для генераторов"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseGenerator(ABC):
    """Базовый класс для всех генераторов значений"""

    @abstractmethod
    def can_handle(self, field_type: Any, field_name: Optional[str] = None) -> bool:
        """Проверяет, может ли генератор обработать данный тип"""
        pass

    @abstractmethod
    def generate(self, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        """Генерирует значение для типа"""
        pass