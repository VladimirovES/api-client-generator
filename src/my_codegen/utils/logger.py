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
    """Кастомная ошибка для API запросов с красивым форматированием"""

    def __init__(self, response, expected_status, method, payload=None):
        self.response = response
        self.expected_status = expected_status
        self.method = method
        self.payload = payload

        message = self._create_error_message()
        super().__init__(message)

    def _wrap_long_lines(self, text, max_length=80):
        """Переносит длинные строки в обычном тексте"""
        if len(text) <= max_length:
            return text

        lines = text.split('\n')
        wrapped_lines = []

        for line in lines:
            if len(line) <= max_length:
                wrapped_lines.append(line)
            else:
                for i in range(0, len(line), max_length):
                    wrapped_lines.append(line[i:i + max_length])

        return '\n'.join(wrapped_lines)

    def _wrap_json_lines(self, json_str, max_length=80):
        """Переносит длинные строки в JSON сохраняя структуру"""
        lines = json_str.split('\n')
        wrapped_lines = []

        for line in lines:
            if len(line) <= max_length:
                wrapped_lines.append(line)
            else:
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent

                if '": "' in line and (line.strip().endswith('"') or line.strip().endswith('","')):
                    key_part = line[:line.find('": "') + 4]
                    value_start = line.find('": "') + 4
                    value_end = line.rfind('"')
                    ending = line[value_end:]

                    value = line[value_start:value_end]

                    if len(key_part) + len(value) + len(ending) > max_length:
                        max_value_length = max_length - len(key_part) - len(ending) - 10
                        if max_value_length > 20:
                            truncated_value = value[:max_value_length] + "..."
                            wrapped_lines.append(key_part + truncated_value + ending)
                        else:
                            wrapped_lines.append(line)
                    else:
                        wrapped_lines.append(line)
                else:
                    wrapped_lines.append(line[:max_length] + "..." if len(line) > max_length else line)

        return '\n'.join(wrapped_lines)

    def _format_json_nicely(self, data, max_length=1500, max_line_length=80):
        """Красиво форматирует JSON для лучшей читаемости с переносом длинных строк"""
        if data is None:
            return "None"

        try:
            if isinstance(data, str):
                try:
                    parsed_data = json.loads(data)
                except json.JSONDecodeError:
                    return self._wrap_long_lines(data, max_line_length)[:max_length]
            else:
                parsed_data = data

            # ✨ ИСПРАВЛЕНО - теперь UUIDEncoder доступен
            formatted = json.dumps(parsed_data, indent=2, ensure_ascii=False, cls=UUIDEncoder)

            formatted = self._wrap_json_lines(formatted, max_line_length)

            if len(formatted) > max_length:
                return formatted[:max_length] + "\n... (truncated)"

            return formatted

        except Exception:
            return str(data)[:max_length]

    def _create_error_message(self):
        """Создает красивое сообщение об ошибке"""
        payload_str = self._format_json_nicely(self.payload, max_length=1000)
        response_str = self._format_json_nicely(self.response.text, max_length=1500)

        try:
            actual_status_name = HTTPStatus(self.response.status_code).phrase
        except ValueError:
            actual_status_name = "Unknown"

        return f"""
{'=' * 80}
❌ API REQUEST FAILED - STATUS CODE MISMATCH
{'=' * 80}
EXPECTED: {self.expected_status.value} ({self.expected_status.phrase})
ACTUAL:   {self.response.status_code} ({actual_status_name})
{'─' * 80}
🔗 REQUEST DETAILS:
{'─' * 80}
Method: {self.method}
URL: {self.response.url}
{'─' * 80}
📤 REQUEST PAYLOAD:
{'─' * 80}
{payload_str}
{'─' * 80}
📥 SERVER RESPONSE:
{'─' * 80}
{response_str}
{'─' * 80}
🏷️  REQUEST HEADERS:
{'─' * 80}
{self._format_json_nicely(dict(self.response.request.headers), max_length=800)}
{'─' * 80}
🏷️  RESPONSE HEADERS:
{'─' * 80}
{self._format_json_nicely(dict(self.response.headers), max_length=800)}
{'=' * 80}
        """
