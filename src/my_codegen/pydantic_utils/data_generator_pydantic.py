import random
from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
from enum import Enum
from typing import (
    Any, List, Dict, Union, Set, Type, Callable, Optional,
    get_args, get_origin, ForwardRef, Annotated
)
from uuid import UUID, uuid4

from faker import Faker
from pydantic import Field, StringConstraints, RootModel, BaseModel

from my_codegen.pydantic_utils.pydantic_config import BaseConfigModel

fake = Faker()


# ========== Конфигурация ==========

class SmartFieldConfig:
    """Конфигурация для умной генерации полей"""

    # Точные совпадения имен полей
    EXACT_MAPPINGS = {
        # Персональные данные
        'first_name': lambda: fake.first_name(),
        'last_name': lambda: fake.last_name(),
        'middle_name': lambda: fake.first_name(),
        'full_name': lambda: fake.name(),
        'name': lambda: fake.name(),
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

        # Бизнес
        'company': lambda: fake.company(),
        'company_name': lambda: fake.company(),
        'job_title': lambda: fake.job(),
        'position': lambda: fake.job(),

        # Тексты
        'description': lambda: fake.text(max_nb_chars=200),
        'comment': lambda: fake.text(max_nb_chars=100),
        'note': lambda: fake.text(max_nb_chars=100),
        'title': lambda: fake.sentence(nb_words=4),

        # Веб
        'url': lambda: fake.url(),
        'website': lambda: fake.url(),
        'domain': lambda: fake.domain_name(),

        # Даты
        'birth_date': lambda: fake.date_of_birth().isoformat(),
        'created_at': lambda: fake.date_time_this_year().isoformat(),
        'updated_at': lambda: fake.date_time_this_month().isoformat(),

        # Прочее
        'color': lambda: fake.color_name(),
        'hex_color': lambda: fake.hex_color(),
        'price': lambda: f"{fake.pydecimal(left_digits=3, right_digits=2, positive=True)}",
        'amount': lambda: f"{fake.pydecimal(left_digits=4, right_digits=2, positive=True)}",
        'currency': lambda: fake.currency_code(),
        'username': lambda: fake.user_name(),
        'password': lambda: fake.password(),
        'token': lambda: fake.uuid4(),
        'code': lambda: fake.bothify(text='??###'),
        'sku': lambda: fake.bothify(text='???-####'),
        'locale': lambda: fake.locale(),
        'timezone': lambda: fake.timezone(),
        'image': lambda: fake.image_url(),
        'filename': lambda: fake.file_name(),
        'file_path': lambda: fake.file_path(),
        'height': lambda: f"{random.randint(150, 250)}",
        'number': lambda: str(random.uniform(0.1, 9999.99)),
        'mark': lambda: fake.bothify(text='MRK-###'),
        'units': lambda: random.choice(['cm', 'm', 'kg', 'pieces', 'liters']),
        'type_name': lambda: fake.word().capitalize(),
    }

    # Паттерны для частичного совпадения
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
        'number': lambda: str(random.uniform(0.1, 9999.99)),
        'image': lambda: fake.image_url(),
        'file': lambda: fake.file_name(),
        'path': lambda: fake.file_path(),
        'height': lambda: f"{random.randint(100, 300)} cm",
        'width': lambda: f"{random.randint(100, 300)} cm",
        'units': lambda: random.choice(['cm', 'm', 'kg', 'pieces']),
    }


# ========== Утилиты для работы с типами ==========

class TypeUtils:
    """Утилиты для анализа типов"""

    @staticmethod
    def is_optional(field_type: Any) -> bool:
        """Проверяет, является ли тип Optional"""
        origin = get_origin(field_type)
        args = get_args(field_type)
        return origin is Union and type(None) in args

    @staticmethod
    def extract_base_type(field_type: Any) -> Any:
        """Извлекает базовый тип из Optional"""
        if TypeUtils.is_optional(field_type):
            args = get_args(field_type)
            return next(a for a in args if a is not type(None))
        return field_type

    @staticmethod
    def is_annotated(field_type: Any) -> bool:
        """Проверяет, является ли тип Annotated"""
        origin = get_origin(field_type)
        return origin is Annotated or "Annotated" in str(origin)

    @staticmethod
    def is_union(field_type: Any) -> bool:
        """Проверяет, является ли тип Union"""
        return get_origin(field_type) is Union

    @staticmethod
    def is_container(field_type: Any) -> bool:
        """Проверяет, является ли тип контейнером"""
        origin = get_origin(field_type)
        return origin in (list, List, dict, Dict, set, Set)

    @staticmethod
    def is_pydantic_model(field_type: Any) -> bool:
        """Проверяет, является ли тип Pydantic моделью"""
        return (isinstance(field_type, type) and
                (issubclass(field_type, BaseConfigModel) or
                 issubclass(field_type, BaseModel)))

    @staticmethod
    def is_root_model(field_type: Any) -> bool:
        """Проверяет, является ли тип RootModel"""
        return isinstance(field_type, type) and issubclass(field_type, RootModel)

    @staticmethod
    def is_enum(field_type: Any) -> bool:
        """Проверяет, является ли тип Enum"""
        return isinstance(field_type, type) and issubclass(field_type, Enum)


# ========== Базовый класс для генераторов ==========

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


# ========== Конкретные генераторы ==========

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


class PrimitiveGenerator(BaseGenerator):
    """Генератор примитивных типов"""

    GENERATORS = {
        str: lambda: fake.text(max_nb_chars=20),
        int: lambda: random.randint(1, 1000),
        float: lambda: random.uniform(1.0, 100.0),
        bool: lambda: random.choice([True, False]),
        datetime: lambda: (datetime.now() + timedelta(days=1)).isoformat() + "Z",
        date: lambda: (datetime.now() + timedelta(days=1)).date().isoformat(),
        UUID: lambda: str(uuid4()), #TODO убрать STR и посмотреть может лучше сразу json_dump использовать
        Any: lambda: random.choice([fake.word(), random.randint(1, 1000),
                                    random.uniform(1.0, 100.0)]),
    }

    def can_handle(self, field_type: Any, field_name: Optional[str] = None) -> bool:
        return field_type in self.GENERATORS

    def generate(self, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        return self.GENERATORS[field_type]()


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
            return [
                ValueGenerator.generate(item_type, None, current_depth + 1, max_depth)
                for _ in range(random.randint(1, 2))
            ]

        elif origin in (dict, Dict):
            value_type = args[1] if len(args) > 1 else str
            return {
                fake.word(): ValueGenerator.generate(value_type, None, current_depth + 1, max_depth)
                for _ in range(random.randint(1, 2))
            }

        elif origin in (set, Set):
            item_type = args[0] if args else str
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


class EnumGenerator(BaseGenerator):
    """Генератор для Enum типов"""

    def can_handle(self, field_type: Any, field_name: Optional[str] = None) -> bool:
        return TypeUtils.is_enum(field_type)

    def generate(self, field_type: Any, field_name: Optional[str] = None,
                 current_depth: int = 0, max_depth: int = 5) -> Any:
        return random.choice(list(field_type))


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
        generated = ValueGenerator.generate(root_annotation, None, current_depth, max_depth)
        return field_type.model_construct(root=generated, _fields_set={"root"})

    def _generate_pydantic_model(self, field_type: Any, current_depth: int, max_depth: int) -> Any:
        if current_depth >= max_depth:
            try:
                from_data = GenerateData(field_type, current_depth, max_depth)
                return from_data.fill_required().build()
            except:
                return None

        from_data = GenerateData(field_type, current_depth + 1, max_depth)
        return from_data.fill_all_fields().build()


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

        for key, generator in type_mappings.items():
            if key in field_str.lower() or key in field_name_str.lower():
                return generator()

        if 'pydantic' in field_str:
            return fake.word()

        raise ValueError(f"Unsupported field type: {field_type}")


# ========== Главный генератор с цепочкой ответственности ==========

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


# ========== Публичный API (сохраняем совместимость) ==========

class RandomValueGenerator:
    """Публичный API для обратной совместимости"""

    @staticmethod
    def random_value(field_type: Any, current_depth: int = 0, max_depth: int = 5) -> Any:
        return ValueGenerator.generate(field_type, None, current_depth, max_depth)

    @staticmethod
    def _handle_annotated(base_type: Any, metadata: tuple, current_depth: int, max_depth: int) -> Any:
        """Обратная совместимость"""
        return ValueGenerator.generate(
            Annotated[base_type, *metadata], None, current_depth, max_depth
        )


class GenerateData:
    """Генератор данных для Pydantic моделей"""

    def __init__(self, model_class: type[BaseConfigModel], current_depth: int = 0,
                 max_depth: int = 5, use_smart_generation: bool = True):
        self.model_class = model_class
        self.data = {}
        self.current_depth = current_depth
        self.max_depth = max_depth
        self.use_smart_generation = use_smart_generation

    def _fill_fields(self, required_only: bool = False, optional_only: bool = False):
        """Заполняет поля модели"""
        fields = self.model_class.model_fields

        for field_name, field_info in fields.items():
            if field_name in self.data:
                continue

            annotation = field_info.annotation
            is_optional = TypeUtils.is_optional(annotation)

            if required_only and is_optional:
                continue
            if optional_only and not is_optional:
                continue

            real_type = TypeUtils.extract_base_type(annotation) if is_optional else annotation

            # Генерируем значение с учетом имени поля (если включена умная генерация)
            field_name_for_gen = field_name if self.use_smart_generation else None
            self.data[field_name] = ValueGenerator.generate(
                real_type, field_name_for_gen, self.current_depth, self.max_depth
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
        self.use_smart_generation = enabled
        return self

    def disable_smart_generation(self):
        return self.with_smart_generation(False)

    def build(self):
        return self.model_class.model_construct(_validate=False, **self.data)

    def to_dict(self):
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