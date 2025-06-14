"""Конфигурация для генераторов данных"""
import random
from faker import Faker

fake = Faker()


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