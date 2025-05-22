import os
import re
from my_codegen.utils.shell import run_command


class ModelGenerator:
    def __init__(self, swagger_path: str, models_file: str = 'models'):
        self.swagger_path = swagger_path
        self.models_file = models_file

    def generate_models(self) -> None:
        """
        Запускает datamodel-codegen, чтобы сгенерировать Pydantic-модели на основе Swagger.
        Результат - файл {self.models_file}.py.
        """
        model_cmd = (
            f"datamodel-codegen --input {self.swagger_path} "
            "--input-file-type openapi "
            f"--output {self.models_file}.py "
            "--reuse-model "
            "--use-title-as-name "
            "--use-schema-description "
            "--collapse-root-models "
            "--target-python-version 3.9 "
            "--output-model-type pydantic_v2.BaseModel "
            "--use-annotated"

        )
        run_command(model_cmd)

    def fix_models_inheritance(self) -> None:
        """
        Заменяет наследование BaseModel -> BaseConfigModel в итоговом файле моделей,
        а также правит импорт, убирая 'BaseModel' из 'from pydantic import ...'
        и добавляя при необходимости 'from http_clients.pydantic_config import BaseConfigModel'.
        """
        models_path = self.models_file + ".py"
        if not os.path.exists(models_path):
            return

        with open(models_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        found_pydantic_config_import = False

        # Регулярка, ловящая слово BaseModel как отдельное
        base_model_pattern = re.compile(r"\bBaseModel\b")

        last_import_index = -1

        for idx, line in enumerate(lines):
            stripped = line.strip()
            # Если это строка импорта, запоминаем индекс для возможной вставки
            if stripped.startswith("import ") or stripped.startswith("from "):
                last_import_index = len(new_lines)

            # Меняем "BaseModel" -> "BaseConfigModel"
            line = base_model_pattern.sub("BaseConfigModel", line)

            # Если это строка вида "from pydantic import ..."
            if stripped.startswith("from pydantic import"):
                prefix = "from pydantic import "
                after_import = stripped[len(prefix):]
                imports_list = [imp.strip() for imp in after_import.split(",")]
                # Убираем "BaseModel" и "BaseConfigModel"
                filtered_imports = [
                    imp for imp in imports_list
                    if imp not in ("BaseModel", "BaseConfigModel")
                ]
                if len(filtered_imports) == 0:
                    # Если ничего не осталось импортировать — пропускаем эту строку
                    continue
                else:
                    new_line = prefix + ", ".join(filtered_imports) + "\n"
                    new_lines.append(new_line)
            else:
                if "from pydantic_config import BaseConfigModel" in line:
                    found_pydantic_config_import = True
                new_lines.append(line)

        if not found_pydantic_config_import:
            import_line = "from my_codegen.pydantic_utils.pydantic_config import BaseConfigModel\n"
            if last_import_index >= 0:
                new_lines.insert(last_import_index + 1, import_line)
            else:
                new_lines.insert(0, import_line)

        with open(models_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    def post_process_code(self, output_dir: str) -> None:
        """
        Запускает autoflake и black для автоформатирования и удаления неиспользуемых импортов.
        """
        autoflake_cmd = (
            "autoflake "
            "--remove-all-unused-imports "
            "--recursive "
            "--in-place "
            f"'{output_dir}'"
        )
        black_cmd = f"black '{output_dir}'"
        run_command(autoflake_cmd)
        run_command(black_cmd)
