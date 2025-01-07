import json
import logging
import sys

import allure


def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    logger.addHandler(ch)


configure_logging()
logger = logging.getLogger(__name__)


def allure_report(response, payload):
    if payload is not None:
        try:
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8')  # Assuming utf-8 encoding
            formatted_data = json.dumps(json.loads(payload), indent=4, ensure_ascii=False) if isinstance(payload, str) else json.dumps(payload, indent=4, ensure_ascii=False)
            html_data = f"<pre><code>{formatted_data}</code></pre>"
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
            html_data = "<pre><code>Binary data cannot be serialized</code></pre>"
        allure.attach(html_data, name=f" Request ", attachment_type=allure.attachment_type.HTML)
    else:
        allure.attach("Data is None", name=f"Request", attachment_type=allure.attachment_type.TEXT)

    try:
        formatted_response = json.dumps(json.loads(response.text), indent=4, ensure_ascii=False)
        html_response = f"<pre><code>{formatted_response}</code></pre>"
    except ValueError:  # If response.text is not JSON
        html_response = f"<pre>{response.text}</pre>"

    allure.attach(html_response, name=f"Response",
                  attachment_type=allure.attachment_type.HTML)