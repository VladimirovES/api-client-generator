import json
import logging
import sys
import uuid
from enum import Enum

import allure
import testit

from http import HTTPStatus


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


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


class ApiRequestError(AssertionError):

    def __init__(self, response, expected_status, method, payload=None):
        self.response = response
        self.expected_status = expected_status
        self.method = method
        self.payload = payload
        super().__init__(self._create_error_message())

    def _truncate_text(self, text, max_length=80):
        """Обрезает текст до указанной длины"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def _format_data(self, data, max_total_length=1500, max_line_length=80):
        """Форматирует данные для отображения"""
        if data is None:
            return "None"

        try:
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    return self._truncate_text(data, max_total_length)

            formatted = json.dumps(data, indent=2, ensure_ascii=False, cls=UUIDEncoder)

            lines = formatted.split('\n')
            truncated_lines = [self._truncate_text(line, max_line_length) for line in lines]
            result = '\n'.join(truncated_lines)

            if len(result) > max_total_length:
                return result[:max_total_length] + "\n... (truncated)"

            return result

        except Exception:
            return self._truncate_text(str(data), max_total_length)

    def _get_status_name(self, status_code):
        """Получает название статуса по коду"""
        try:
            return HTTPStatus(status_code).phrase
        except ValueError:
            return "Unknown"

    def _create_error_message(self):
        """Создает красивое сообщение об ошибке"""
        separator = '=' * 80
        line = '─' * 80

        expected_status_text = f"{self.expected_status.value} ({self.expected_status.phrase})"
        actual_status_text = f"{self.response.status_code} ({self._get_status_name(self.response.status_code)})"

        sections = [
            separator,
            "❌ API REQUEST FAILED - STATUS CODE MISMATCH",
            separator,
            f"EXPECTED: {expected_status_text}",
            f"ACTUAL:   {actual_status_text}",
            line,
            "🔗 REQUEST DETAILS:",
            line,
            f"Method: {self.method}",
            f"URL: {self.response.url}",
            line,
            "📤 REQUEST PAYLOAD:",
            line,
            self._format_data(self.payload, max_total_length=1000),
            line,
            "📥 SERVER RESPONSE:",
            line,
            self._format_data(self.response.text),
            line,
            "🏷️  REQUEST HEADERS:",
            line,
            self._format_data(dict(self.response.request.headers), max_total_length=800),
            line,
            "🏷️  RESPONSE HEADERS:",
            line,
            self._format_data(dict(self.response.headers), max_total_length=800),
            separator
        ]

        return '\n'.join(sections)
