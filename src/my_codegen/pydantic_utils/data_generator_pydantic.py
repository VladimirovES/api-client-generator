import random
from datetime import datetime, date, timedelta
from enum import Enum
from typing import (
    Any, List, Dict, Union, Set,
    get_args, get_origin, ForwardRef, Annotated
)
from uuid import UUID, uuid4

from faker import Faker

from my_codegen.pydantic_utils.pydantic_config import BaseConfigModel

from pydantic import Field, StringConstraints, RootModel, BaseModel

fake = Faker()


# ========== Внутренние helper классы ==========

class _TypeAnalyzer:
    """Анализирует типы данных"""

    @staticmethod
    def is_optional(field_type) -> bool:
        origin = get_origin(field_type)
        args = get_args(field_type)
        return origin is Union and type(None) in args

    @staticmethod
    def extract_base_type(field_type) -> Any:
        if _TypeAnalyzer.is_optional(field_type):
            args = get_args(field_type)
            return next(a for a in args if a is not type(None))
        return field_type

    @staticmethod
    def is_annotated(field_type) -> bool:
        origin = get_origin(field_type)
        return origin is Annotated or "Annotated" in str(origin)

    @staticmethod
    def is_union(field_type) -> bool:
        return get_origin(field_type) is Union

    @staticmethod
    def is_container(field_type) -> bool:
        origin = get_origin(field_type)
        return origin in (list, List, dict, Dict, set, Set)


class _ModelChecker:
    """Проверяет типы моделей"""

    @staticmethod
    def is_pydantic_model(field_type) -> bool:
        return (isinstance(field_type, type) and
                (issubclass(field_type, BaseConfigModel) or issubclass(field_type, BaseModel)))

    @staticmethod
    def is_root_model(field_type) -> bool:
        return isinstance(field_type, type) and issubclass(field_type, RootModel)

    @staticmethod
    def is_enum(field_type) -> bool:
        return isinstance(field_type, type) and issubclass(field_type, Enum)


class _SmartFieldGenerator:
    """Генерирует значения на основе названий полей"""

    # Мапинги названий полей к Faker методам
    FIELD_MAPPINGS = {
        # Имена
        'first_name': lambda: fake.first_name(),
        'last_name': lambda: fake.last_name(),
        'middle_name': lambda: fake.first_name(),
        'full_name': lambda: fake.name(),
        'name': lambda: fake.name(),

        # Email и контакты
        'email': lambda: fake.email(),
        'phone': lambda: fake.phone_number(),
        'phone_number': lambda: fake.phone_number(),

        # Адреса
        'address': lambda: fake.address(),
        'street': lambda: fake.street_address(),
        'city': lambda: fake.city(),
        'country': lambda: fake.country(),
        'postal_code': lambda: fake.postcode(),
        'zip_code': lambda: fake.postcode(),

        # Компании
        'company': lambda: fake.company(),
        'company_name': lambda: fake.company(),
        'job_title': lambda: fake.job(),
        'position': lambda: fake.job(),

        # Описания
        'description': lambda: fake.text(max_nb_chars=200),
        'comment': lambda: fake.text(max_nb_chars=100),
        'note': lambda: fake.text(max_nb_chars=100),
        'title': lambda: fake.sentence(nb_words=4),

        # URL и домены
        'url': lambda: fake.url(),
        'website': lambda: fake.url(),
        'domain': lambda: fake.domain_name(),

        # Даты как строки
        'birth_date': lambda: fake.date_of_birth().isoformat(),
        'created_at': lambda: fake.date_time_this_year().isoformat(),
        'updated_at': lambda: fake.date_time_this_month().isoformat(),

        # Цвета
        'color': lambda: fake.color_name(),
        'hex_color': lambda: fake.hex_color(),

        # Финансы
        'price': lambda: f"{fake.pydecimal(left_digits=3, right_digits=2, positive=True)}",
        'amount': lambda: f"{fake.pydecimal(left_digits=4, right_digits=2, positive=True)}",
        'currency': lambda: fake.currency_code(),

        # ID и коды
        'username': lambda: fake.user_name(),
        'password': lambda: fake.password(),
        'token': lambda: fake.uuid4(),
        'code': lambda: fake.bothify(text='??###'),
        'sku': lambda: fake.bothify(text='???-####'),
    }

    # Паттерны для частичного совпадения (содержит подстроку)
    PATTERN_MAPPINGS = {
        'name': lambda: fake.name(),
        'email': lambda: fake.email(),
        'phone': lambda: fake.phone_number(),
        'address': lambda: fake.address(),
        'company': lambda: fake.company(),
        'url': lambda: fake.url(),
        'description': lambda: fake.text(max_nb_chars=150),
        'title': lambda: fake.sentence(nb_words=3),
        'date': lambda: fake.date().isoformat(),
        'time': lambda: fake.time(),
        'id': lambda: str(fake.random_int(1, 999999)),
        'code': lambda: fake.bothify(text='??###'),
        'number': lambda: str(fake.random_int(1, 9999)),
    }

    @staticmethod
    def can_generate_smart_value(field_name: str, field_type: Any) -> bool:
        """Проверяет можно ли сгенерировать умное значение для поля"""
        # Работаем только со строками
        if field_type is not str:
            return False

        field_lower = field_name.lower()

        # Точное совпадение
        if field_lower in _SmartFieldGenerator.FIELD_MAPPINGS:
            return True

        # Частичное совпадение
        return any(pattern in field_lower
                   for pattern in _SmartFieldGenerator.PATTERN_MAPPINGS.keys())

    @staticmethod
    def generate_smart_value(field_name: str) -> str:
        """Генерирует умное значение на основе названия поля"""
        field_lower = field_name.lower()

        # Точное совпадение имеет приоритет
        if field_lower in _SmartFieldGenerator.FIELD_MAPPINGS:
            return _SmartFieldGenerator.FIELD_MAPPINGS[field_lower]()

        # Ищем частичное совпадение
        for pattern, generator in _SmartFieldGenerator.PATTERN_MAPPINGS.items():
            if pattern in field_lower:
                return generator()

        # Fallback (не должно происходить если can_generate_smart_value вернул True)
        return fake.text(max_nb_chars=20)


class _PrimitiveGenerator:
    """Генерирует примитивные типы"""

    @staticmethod
    def generate_string() -> str:
        return fake.text(max_nb_chars=20)

    @staticmethod
    def generate_int() -> int:
        return random.randint(1, 1000)

    @staticmethod
    def generate_float() -> float:
        return random.uniform(1.0, 100.0)

    @staticmethod
    def generate_bool() -> bool:
        return random.choice([True, False])

    @staticmethod
    def generate_datetime() -> str:
        return (datetime.now() + timedelta(days=1)).isoformat() + "Z"

    @staticmethod
    def generate_date() -> str:
        return (datetime.now() + timedelta(days=1)).date().isoformat()

    @staticmethod
    def generate_uuid() -> str:
        return str(uuid4())

    @staticmethod
    def generate_any() -> Any:
        return random.choice([fake.word(), random.randint(1, 1000), random.uniform(1.0, 100.0)])


class _ContainerGenerator:
    """Генерирует контейнерные типы"""

    @staticmethod
    def generate_list(field_type, current_depth: int, max_depth: int) -> List:
        if current_depth >= max_depth:
            return []

        args = get_args(field_type)
        item_type = args[0] if args else str

        return [
            RandomValueGenerator.random_value(item_type, current_depth + 1, max_depth)
            for _ in range(random.randint(1, 2))
        ]

    @staticmethod
    def generate_dict(field_type, current_depth: int, max_depth: int) -> Dict:
        if current_depth >= max_depth:
            return {}

        args = get_args(field_type)
        value_type = args[1] if len(args) > 1 else str

        return {
            fake.word(): RandomValueGenerator.random_value(value_type, current_depth + 1, max_depth)
            for _ in range(random.randint(1, 2))
        }

    @staticmethod
    def generate_set(field_type, current_depth: int, max_depth: int) -> Set:
        if current_depth >= max_depth:
            return set()

        args = get_args(field_type)
        item_type = args[0] if args else str

        return {
            RandomValueGenerator.random_value(item_type, current_depth + 1, max_depth)
            for _ in range(random.randint(1, 2))
        }


class _ModelGenerator:
    """Генерирует Pydantic модели"""

    @staticmethod
    def generate_pydantic_model(field_type, current_depth: int, max_depth: int):
        if current_depth >= max_depth:
            return None

        from_data = GenerateData(field_type, current_depth + 1, max_depth)
        return from_data.fill_all_fields().build()

    @staticmethod
    def generate_root_model(field_type, current_depth: int, max_depth: int):
        root_annotation = field_type.model_fields["root"].annotation
        generated = RandomValueGenerator.random_value(root_annotation, current_depth, max_depth)
        return field_type.model_construct(root=generated, _fields_set={"root"})

    @staticmethod
    def generate_enum(field_type):
        return random.choice(list(field_type))


class _AnnotatedHandler:
    """Обрабатывает Annotated типы"""

    @staticmethod
    def handle(field_type, current_depth: int, max_depth: int) -> Any:
        args = get_args(field_type)
        base_type = args[0] if args else str
        metadata = args[1:] if len(args) > 1 else ()

        if base_type is str:
            return _AnnotatedHandler._handle_string_constraints(metadata)

        return RandomValueGenerator.random_value(base_type, current_depth, max_depth)

    @staticmethod
    def _handle_string_constraints(metadata: tuple) -> str:
        min_len = 1
        max_len = 20

        for meta in metadata:
            if isinstance(meta, Field):
                if meta.min_length is not None:
                    min_len = meta.min_length
                if meta.max_length is not None:
                    max_len = meta.max_length
            elif isinstance(meta, StringConstraints):
                if meta.min_length is not None:
                    min_len = meta.min_length
                if meta.max_length is not None:
                    max_len = meta.max_length

        length = random.randint(min_len, max_len) if min_len <= max_len else 1
        return fake.pystr(min_chars=length, max_chars=length)


class _FallbackGenerator:
    """Обрабатывает нестандартные случаи"""

    @staticmethod
    def generate(field_type) -> Any:
        if isinstance(field_type, ForwardRef):
            return []

        # Добавляем обработку Pydantic типов по названию
        field_name = getattr(field_type, '__name__', str(field_type))

        # URL типы
        if 'Url' in field_name or 'url' in field_name.lower():
            return fake.url()

        # Email типы
        if 'Email' in field_name or 'email' in field_name.lower():
            return fake.email()

        # JSON типы
        if 'Json' in field_name or 'json' in field_name.lower():
            return {"example": "data"}

        # Если это класс из pydantic.types или pydantic.networks
        field_str = str(field_type)
        if 'pydantic' in field_str:
            if 'Url' in field_str or 'url' in field_str:
                return fake.url()
            elif 'Email' in field_str or 'email' in field_str:
                return fake.email()
            elif 'Json' in field_str:
                return {"example": "data"}
            elif 'Path' in field_str:
                return fake.file_path()
            elif 'Secret' in field_str:
                return fake.password()
            else:
                # Общий fallback для неизвестных pydantic типов
                return fake.word()

        # Если ничего не подошло
        raise ValueError(f"Unsupported field type: {field_type}")


class _ValueDispatcher:
    """Диспетчер для выбора нужного генератора"""

    @staticmethod
    def dispatch(field_type: Any, current_depth: int, max_depth: int) -> Any:
        # 1. Optional типы
        if _TypeAnalyzer.is_optional(field_type):
            real_type = _TypeAnalyzer.extract_base_type(field_type)
            return _ValueDispatcher.dispatch(real_type, current_depth, max_depth)

        # 2. Union (без None)
        if _TypeAnalyzer.is_union(field_type):
            args = get_args(field_type)
            chosen = random.choice(args)
            return _ValueDispatcher.dispatch(chosen, current_depth, max_depth)

        # 3. Annotated
        if _TypeAnalyzer.is_annotated(field_type):
            return _AnnotatedHandler.handle(field_type, current_depth, max_depth)

        # 4. Примитивы
        if field_type in _PRIMITIVE_GENERATORS:
            return _PRIMITIVE_GENERATORS[field_type]()

        # 5. Контейнеры
        origin = get_origin(field_type)
        if origin in _CONTAINER_GENERATORS:
            return _CONTAINER_GENERATORS[origin](field_type, current_depth, max_depth)

        # 6. Enum
        if _ModelChecker.is_enum(field_type):
            return _ModelGenerator.generate_enum(field_type)

        # 7. RootModel
        if _ModelChecker.is_root_model(field_type):
            return _ModelGenerator.generate_root_model(field_type, current_depth, max_depth)

        # 8. Pydantic модели
        if _ModelChecker.is_pydantic_model(field_type):
            return _ModelGenerator.generate_pydantic_model(field_type, current_depth, max_depth)

        # 9. Fallback
        return _FallbackGenerator.generate(field_type)


# Мапинги для диспетчера
_PRIMITIVE_GENERATORS = {
    str: _PrimitiveGenerator.generate_string,
    int: _PrimitiveGenerator.generate_int,
    float: _PrimitiveGenerator.generate_float,
    bool: _PrimitiveGenerator.generate_bool,
    datetime: _PrimitiveGenerator.generate_datetime,
    date: _PrimitiveGenerator.generate_date,
    UUID: _PrimitiveGenerator.generate_uuid,
    Any: _PrimitiveGenerator.generate_any,
}

_CONTAINER_GENERATORS = {
    list: _ContainerGenerator.generate_list,
    List: _ContainerGenerator.generate_list,
    dict: _ContainerGenerator.generate_dict,
    Dict: _ContainerGenerator.generate_dict,
    set: _ContainerGenerator.generate_set,
    Set: _ContainerGenerator.generate_set,
}


# ========== Публичный API (без изменений) ==========

class RandomValueGenerator:
    """Публичный API остается неизменным"""

    @staticmethod
    def random_value(field_type: Any, current_depth: int = 0, max_depth: int = 3) -> Any:
        return _ValueDispatcher.dispatch(field_type, current_depth, max_depth)

    @staticmethod
    def _handle_annotated(base_type: Any, metadata: tuple, current_depth: int, max_depth: int) -> Any:
        """Backward compatibility - делегируем в новый handler"""
        return _AnnotatedHandler.handle(
            Annotated[base_type, *metadata], current_depth, max_depth
        )


class GenerateData:
    """Публичный API остается неизменным + добавлена смарт-генерация"""

    def __init__(
            self,
            model_class: type[BaseConfigModel],
            current_depth: int = 0,
            max_depth: int = 3,
            use_smart_generation: bool = True,
    ):
        self.model_class = model_class
        self.data = {}
        self.current_depth = current_depth
        self.max_depth = max_depth
        self.use_smart_generation = use_smart_generation

    def _fill_fields(self, required_only: bool = False, optional_only: bool = False):
        """Заполняет поля модели с умной генерацией"""
        fields = self.model_class.model_fields

        for field_name, field_info in fields.items():
            # Если поле уже заполнено вручную — пропускаем
            if field_name in self.data:
                continue

            annotation = field_info.annotation
            is_optional = _TypeAnalyzer.is_optional(annotation)

            # Пропускаем, если не соответствует режиму
            if required_only and is_optional:
                continue
            if optional_only and not is_optional:
                continue

            # Если Optional[...] -> достаём реальный тип
            if is_optional:
                real_type = _TypeAnalyzer.extract_base_type(annotation)
            else:
                real_type = annotation

            # НОВАЯ ЛОГИКА: пробуем смарт-генерацию
            if (self.use_smart_generation and
                    _SmartFieldGenerator.can_generate_smart_value(field_name, real_type)):
                self.data[field_name] = _SmartFieldGenerator.generate_smart_value(field_name)
            else:
                # Обычная генерация
                self.data[field_name] = RandomValueGenerator.random_value(
                    real_type,
                    current_depth=self.current_depth,
                    max_depth=self.max_depth,
                )

    def fill_all_fields(self, **data):
        self.data.update(data)
        self._fill_fields(required_only=False, optional_only=False)
        return self

    def fill_required(self, **data):
        self.data.update(data)
        self._fill_fields(required_only=True, optional_only=False)
        return self

    def fill_optional(self, **data):
        self.data.update(data)
        self._fill_fields(required_only=False, optional_only=True)
        return self

    def set_field(self, **kwargs):
        self.data.update(kwargs)
        return self

    def with_smart_generation(self, enabled: bool = True):
        """Включает/выключает умную генерацию"""
        self.use_smart_generation = enabled
        return self

    def disable_smart_generation(self):
        """Выключает умную генерацию"""
        return self.with_smart_generation(False)

    def build(self):
        """Создаёт модель pydantic v2 без валидации"""
        return self.model_class.model_construct(_validate=False, **self.data)

    def to_dict(self):
        """Рекурсивно приводит итоговый объект к словарю"""
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