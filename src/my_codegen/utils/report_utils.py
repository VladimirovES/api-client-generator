import allure
import testit
from functools import wraps

import tempfile
import os
from my_codegen.utils.logger import logger


class Reporter:
    @staticmethod
    def title(title_text):
        def decorator(func):
            @allure.title(title_text)
            @testit.displayName(title_text)
            @testit.title(title_text)
            @testit.externalId(title_text)
            @wraps(func)
            def wrapper(*args, **kwargs):
                logger.info("="* 100)
                logger.info(f"Начало теста: '{title_text}'")
                logger.info("-"* 100)

                try:
                    result = func(*args, **kwargs)
                    logger.info("-" * 100)
                    logger.info(f"Тест успешно завершен: '{title_text}'")
                    logger.info("=" * 100)
                    return result
                except Exception as e:
                    logger.info("-" * 100)
                    logger.error(f"Тест провален: '{title_text}' - {str(e)}")
                    logger.info("=" * 100)
                    raise

            return wrapper

        return decorator

    @staticmethod
    def description(desc_text):
        def decorator(func):
            @allure.description(desc_text)
            @testit.description(desc_text)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def id(id_value):
        def decorator(func):
            @allure.id(id_value)
            @testit.externalId(id_value)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def tags(*tags):
        def decorator(func):
            for tag in tags:
                func = allure.tag(tag)(func)
            func = testit.labels(*tags)(func)
            return func

        return decorator

    @staticmethod
    def link(url, name=None, link_type=None):
        def decorator(func):
            if link_type:
                func = allure.link(url, name, link_type)(func)
            else:
                func = allure.link(url, name)(func)
            func = testit.link(url, name or url)(func)
            return func

        return decorator

    @staticmethod
    def attach(file_path, name=None):
        allure.attach.file(file_path, name=name)
        testit.addAttachments(file_path)

    @staticmethod
    def message(message_text):
        allure.attach(message_text, "Информация", attachment_type=allure.attachment_type.TEXT)
        testit.addMessage(message_text)

    @staticmethod
    def step(name):
        allure_step = allure.step(name)
        testit_step = testit.step(name)

        class DualStepContext:
            def __enter__(self):
                logger.info(f"{name}")
                allure_step.__enter__()
                testit_step.__enter__()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                t_result = testit_step.__exit__(exc_type, exc_val, exc_tb)
                a_result = allure_step.__exit__(exc_type, exc_val, exc_tb)
                return t_result or a_result

        return DualStepContext()

    @staticmethod
    def general_step(name, description=None):

        def decorator(func):
            func = allure.step(name)(func)

            if description:
                func = testit.step(name, description)(func)
            else:
                func = testit.step(name)(func)

            return func

        return decorator

    @staticmethod
    def suite(suite_name):
        def decorator(obj):
            if isinstance(obj, type):
                obj = testit.nameSpace(suite_name)(obj)
                return obj
            else:
                @allure.suite(suite_name)
                @testit.nameSpace(suite_name)
                @wraps(obj)
                def wrapper(*args, **kwargs):
                    return obj(*args, **kwargs)

                return wrapper

        return decorator

    @staticmethod
    def sub_suite(sub_suite_name):
        def decorator(obj):
            if isinstance(obj, type):
                obj = testit.className(sub_suite_name)(obj)
                obj = allure.sub_suite(sub_suite_name)(obj)

                return obj
            else:
                @allure.sub_suite(sub_suite_name)
                @testit.className(sub_suite_name)
                @wraps(obj)
                def wrapper(*args, **kwargs):
                    return obj(*args, **kwargs)

                return wrapper


        return decorator

    @staticmethod
    def attach_bytes(content, name=None, attachment_type=None):
        if attachment_type:
            allure.attach(content, name=name, attachment_type=attachment_type)
        else:
            allure.attach(content, name=name)

        ext = ""
        if attachment_type == allure.attachment_type.PNG:
            ext = ".png"
        elif attachment_type == allure.attachment_type.HTML:
            ext = ".html"
        elif attachment_type == allure.attachment_type.TEXT:
            ext = ".txt"
        elif attachment_type == allure.attachment_type.JSON:
            ext = ".json"

        file_name = (name or "attachment").replace(" ", "_") + ext
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file_name)

        try:
            with open(temp_file_path, 'wb') as f:
                f.write(content)
            testit.addAttachments(temp_file_path)
        finally:
            os.unlink(temp_file_path)
            os.rmdir(temp_dir)