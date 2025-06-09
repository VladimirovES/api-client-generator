import json
import logging
import sys
import uuid
from enum import Enum
import textwrap

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

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

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

    def _wrap_long_lines(self, text, width=80):
        """Переносит длинные строки на новые строки"""
        if not text:
            return text

        lines = text.split('\n')
        wrapped_lines = []

        for line in lines:
            if len(line) <= width:
                wrapped_lines.append(line)
            else:
                wrapped = textwrap.fill(line, width=width, subsequent_indent='  ')
                wrapped_lines.append(wrapped)

        return '\n'.join(wrapped_lines)

    def _format_data(self, data, max_total_length=None, line_width=80):
        """Форматирует данные для отображения с переносом длинных строк"""
        if data is None:
            return "None"

        try:
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    return self._wrap_long_lines(data, line_width)

            formatted = json.dumps(data, indent=2, ensure_ascii=False, cls=UUIDEncoder)

            result = self._wrap_long_lines(formatted, line_width)

            if max_total_length and len(result) > max_total_length:
                result = result[:max_total_length] + "\n... (truncated)"

            return result

        except Exception:
            return self._wrap_long_lines(str(data), line_width)

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
            "📤 REQUEST:",
            line,
            self._format_data(self.payload, max_total_length=5000),
            line,
            "📥 RESPONSE:",
            line,
            self._format_data(self.response.text, max_total_length=5000),
            line,
            "🏷️  REQUEST HEADERS:",
            line,
            self._format_data(dict(self.response.request.headers), max_total_length=2000),
            line,
            "🏷️  RESPONSE HEADERS:",
            line,
            self._format_data(dict(self.response.headers), max_total_length=2000),
            separator
        ]

        return '\n'.join(sections)