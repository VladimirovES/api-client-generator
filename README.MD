# API Client Generator


**API Client Generator** — это инструмент для автоматической генерации клиентского кода на основе Swagger (OpenAPI) спецификации. С его помощью можно генерировать:

- **Pydantic модели** для запросов (Request) и ответов (Response)
- **Клиентские классы** для вызова эндпоинтов API (с группировкой по тегам)
- **Локальный фасад** для объединения клиентских классов в единый интерфейс
- **Глобальный фасад** для работы с несколькими API клиентами

## Установка

Установите пакет со всеми зависимостями через `pip`:

```bash
pip install git+ssh://git@liis-it.gitlab.yandexcloud.net/inner/tests/api-client-generator.git@update
```

# Генерация случайных данных для Pydantic моделей

Этот модуль позволяет автоматически генерировать случайны данные для любых Pydantic-моделей. Он особенно полезен для тестирования, создания фиктивных данных и заполнения запросов или ответов, определённых в Swagger (OpenAPI) спецификации.

- **GenerateData**  
  Использует `RandomValueGenerator` для заполнения всех (или только обязательных/опциональных) полей Pydantic-модели и создания экземпляра модели без полной валидации.

## Как использовать
```bash
my-api-client --swagger-url <URL_к_Swagger_JSON>
my-api-client --swagger-url my-api-client --swagger-url <URL_к_Swagger_JSON> --django
```
### Структура, создаваемая в проекте
```
http_clients/
└── <service_name>/
    ├── models.py        # Pydantic модели для запросов (Request) и ответов (Response)
    ├── facade.py        # Локальный фасад, объединяющий клиентские классы
    └── endpoints/       # Клиентские классы, сгенерированные по тегам
         ├── <tag1>_client.py
         ├── <tag2>_client.py
         └── ...
```
