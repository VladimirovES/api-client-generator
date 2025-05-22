import json
import logging
import sys

import allure
import testit


def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    logger.addHandler(ch)


configure_logging()
logger = logging.getLogger(__name__)


def allure_report(response, payload):
    """
    Создает отчеты для Allure и Test IT одновременно
    """

    # Подготавливаем данные запроса
    if payload is not None:
        try:
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8')

            formatted_data = json.dumps(
                json.loads(payload) if isinstance(payload, str) else payload,
                indent=4,
                ensure_ascii=False
            )
            html_request = f"<pre><code>{formatted_data}</code></pre>"
            text_request = formatted_data
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
            html_request = "<pre><code>Binary data cannot be serialized</code></pre>"
            text_request = "Binary data cannot be serialized"
    else:
        html_request = "Data is None"
        text_request = "Data is None"

    # Подготавливаем данные ответа
    try:
        formatted_response = json.dumps(
            json.loads(response.text),
            indent=4,
            ensure_ascii=False
        )
        html_response = f"<pre><code>{formatted_response}</code></pre>"
        text_response = formatted_response
    except (ValueError, json.JSONDecodeError):
        html_response = f"<pre>{response.text}</pre>"
        text_response = response.text

    # Отчет для Allure
    allure.attach(
        html_request,
        name="Request",
        attachment_type=allure.attachment_type.HTML
    )
    allure.attach(
        html_response,
        name="Response",
        attachment_type=allure.attachment_type.HTML
    )
