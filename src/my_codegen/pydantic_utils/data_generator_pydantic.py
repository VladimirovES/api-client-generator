import random
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Any, List, Dict, Union, Set, get_args, get_origin, ForwardRef

from faker import Faker
from uuid import UUID, uuid4

from my_codegen.pydantic_utils.pydantic_config import BaseConfigModel
from pydantic import ConstrainedStr


fake = Faker()


class RandomValueGenerator:
    @staticmethod
    def random_value(
        field_type: Any, current_depth: int = 0, max_depth: int = 3
    ) -> Any:
        """
        Генерирует случайное значение для заданного field_type.
        С учётом ограничения рекурсии (current_depth, max_depth).
        """
        origin = get_origin(field_type)
        args = get_args(field_type)

        # 1) Union[Something, None] => извлечь not-None
        if origin is Union and type(None) in args:
            for arg in args:
                if arg is not type(None):
                    return RandomValueGenerator.random_value(
                        arg, current_depth, max_depth
                    )

        # 2) Union[...] (без None)
        if origin is Union:
            chosen = random.choice(args)
            return RandomValueGenerator.random_value(chosen, current_depth, max_depth)

        # 3) Any
        if field_type is Any:
            return random.choice(
                [
                    fake.word(),
                    random.randint(1, 1000),
                    random.uniform(1.0, 100.0),
                ]
            )

        # 4) Примитивные типы
        if field_type is str:
            return fake.text(max_nb_chars=20)
        if field_type is int:
            return random.randint(1, 1000)
        if field_type is float:
            return random.uniform(1.0, 100.0)
        if field_type is bool:
            return random.choice([True, False])

        # 5) datetime / date
        if field_type is datetime:
            return (datetime.now() + timedelta(days=1)).isoformat() + "Z"
        if field_type is date:
            return (datetime.now() + timedelta(days=1)).date().isoformat()

        # 6) UUID
        if field_type is UUID:
            return str(uuid4())

        # 7) Контейнеры: list, dict, set
        if origin in (list, List):
            if current_depth >= max_depth:
                return []
            return [
                RandomValueGenerator.random_value(args[0], current_depth + 1, max_depth)
                for _ in range(random.randint(1, 2))
            ]

        if origin in (dict, Dict):
            if current_depth >= max_depth:
                return {}
            return {
                fake.word(): RandomValueGenerator.random_value(
                    args[1], current_depth + 1, max_depth
                )
                for _ in range(random.randint(1, 2))
            }

        if origin in (set, Set):
            if current_depth >= max_depth:
                return set()
            return {
                RandomValueGenerator.random_value(args[0], current_depth + 1, max_depth)
                for _ in range(random.randint(1, 2))
            }

        if isinstance(field_type, type) and issubclass(field_type, ConstrainedStr):
            # Допустим, генерируем строку соблюдая min_length / max_length
            min_len = getattr(field_type, 'min_length', 1) or 1
            max_len = getattr(field_type, 'max_length', 20) or 20
            if min_len > max_len:
                # fallback если кто-то указал min_len>max_len
                min_len, max_len = 1, 20
            length = random.randint(min_len, max_len)
            return "X" * length

        # 8) Enum
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            return random.choice(list(field_type))

        # 9) BaseConfigModel
        if isinstance(field_type, type) and issubclass(field_type, BaseConfigModel):
            if current_depth >= max_depth:
                return None
            from_data = GenerateData(field_type, current_depth + 1, max_depth)
            return from_data.fill_all_fields().build()

        # 10) ForwardRef (быстрый фикс: вернём пустой список)
        if isinstance(field_type, ForwardRef):
            return []

        # Если ничего не подошло — бросаем ошибку
        raise ValueError(f"Unsupported field type: {field_type}")


class GenerateData:
    def __init__(
        self,
        model_class,
        current_depth: int = 0,
        max_depth: int = 3,
    ):
        self.model_class = model_class
        self.data = {}
        self.current_depth = current_depth
        self.max_depth = max_depth

    def _fill_fields(self, required_only: bool = False, optional_only: bool = False):
        """
        Внутренний метод заполнения полей.
        :param required_only: Если True, заполнять только обязательные (не Optional) поля.
        :param optional_only: Если True, заполнять только опциональные поля (Optional).
        """
        fields = self.model_class.__fields__

        for field_name, field_info in fields.items():
            # Если поле уже заполнено вручную — пропускаем
            if field_name in self.data:
                continue

            # Получаем аннотацию (тип) поля
            annotation = field_info.annotation
            origin = get_origin(annotation)
            args = get_args(annotation)
            # Проверяем, является ли поле "Optional"
            is_union = origin is Union
            is_optional = is_union and (type(None) in args)

            # 1) Если нужно ТОЛЬКО обязательные, а поле опциональное -> пропускаем
            if required_only and is_optional:
                continue

            # 2) Если нужно ТОЛЬКО опциональные, а поле не опциональное -> пропускаем
            if optional_only and not is_optional:
                continue

            # Определяем реальный тип (если Optional — берём «первый не None»)
            if is_optional:
                real_type = next(a for a in args if a is not type(None))
            else:
                real_type = annotation

            # Генерируем значение
            self.data[field_name] = RandomValueGenerator.random_value(
                real_type, current_depth=self.current_depth, max_depth=self.max_depth
            )

    def fill_all_fields(self, **data):
        """
        Заполняет ВСЕ поля (обязательные + опциональные).
        """
        self.data.update(data)
        self._fill_fields(required_only=False, optional_only=False)
        return self

    def fill_required(self, **data):
        """
        Заполняет ТОЛЬКО обязательные (не Optional) поля.
        """
        self.data.update(data)
        self._fill_fields(required_only=True, optional_only=False)
        return self

    def fill_optional(self, **data):
        """
        Заполняет ТОЛЬКО опциональные (Optional) поля.
        """
        self.data.update(data)
        self._fill_fields(required_only=False, optional_only=True)
        return self

    def set_field(self, **kwargs):
        """
        Явно задать (переопределить) значения некоторых полей.
        """
        self.data.update(kwargs)
        return self

    def build(self):
        """
        Собирает модель Pydantic через .construct(...) без валидации.
        """
        return self.model_class.construct(**self.data)

    def to_dict(self):
        """
        Рекурсивно приводит итоговый объект (BaseConfigModel) к словарю.
        """
        return self._convert_to_dict(self.build())

    def _convert_to_dict(self, instance: BaseConfigModel):
        if isinstance(instance, BaseConfigModel):
            result = {}
            for k, v in instance.__dict__.items():
                if isinstance(v, BaseConfigModel):
                    result[k] = self._convert_to_dict(v)
                elif isinstance(v, list):
                    result[k] = [self._convert_to_dict(i) for i in v]
                elif isinstance(v, dict):
                    result[k] = {kk: self._convert_to_dict(vv) for kk, vv in v.items()}
                else:
                    result[k] = v
            return result
        return instance


