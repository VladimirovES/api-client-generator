import os
import re
from typing import List
from my_codegen.utils.shell import run_command


class ModelGenerator:
    def __init__(self, swagger_path: str, models_file: str = 'models'):
        self.swagger_path = swagger_path
        self.models_file = models_file
        self.models_path = f"{models_file}.py"

    def generate_models(self) -> None:
        """Генерирует Pydantic модели из Swagger через datamodel-codegen"""
        cmd_parts = [
            "datamodel-codegen",
            f"--input {self.swagger_path}",
            "--input-file-type openapi",
            f"--output {self.models_path}",
            "--reuse-model",
            "--use-title-as-name",
            "--use-schema-description",
            "--collapse-root-models",
            "--target-python-version 3.9",
            "--output-model-type pydantic_v2.BaseModel",
            "--use-annotated"
        ]
        run_command(" ".join(cmd_parts))

    def fix_models_inheritance(self) -> None:
        """Заменяет BaseModel на BaseConfigModel и фиксит импорты"""
        if not os.path.exists(self.models_path):
            return

        lines = self._read_file()
        lines = self._replace_base_model(lines)
        lines = self._fix_pydantic_imports(lines)
        lines = self._add_config_import_if_needed(lines)
        self._write_file(lines)

    def _read_file(self) -> List[str]:
        """Читает файл моделей"""
        with open(self.models_path, 'r', encoding='utf-8') as f:
            return f.readlines()

    def _write_file(self, lines: List[str]) -> None:
        """Записывает файл моделей"""
        with open(self.models_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def _replace_base_model(self, lines: List[str]) -> List[str]:
        """Заменяет BaseModel на BaseConfigModel"""
        base_model_pattern = re.compile(r"\bBaseModel\b")
        return [base_model_pattern.sub("BaseConfigModel", line) for line in lines]

    def _fix_pydantic_imports(self, lines: List[str]) -> List[str]:
        """Убирает BaseModel из pydantic импортов"""
        new_lines = []

        for line in lines:
            if line.strip().startswith("from pydantic import"):
                cleaned_line = self._clean_pydantic_import(line)
                if cleaned_line:  
                    new_lines.append(cleaned_line)
            else:
                new_lines.append(line)

        return new_lines

    def _clean_pydantic_import(self, line: str) -> str:
        """Убирает BaseModel из строки импорта pydantic"""
        prefix = "from pydantic import "
        after_import = line.strip()[len(prefix):]

        imports_list = [imp.strip() for imp in after_import.split(",")]
        filtered_imports = [
            imp for imp in imports_list
            if imp not in ("BaseModel", "BaseConfigModel")
        ]

        if not filtered_imports:
            return ""  

        return f"{prefix}{', '.join(filtered_imports)}\n"

    def _add_config_import_if_needed(self, lines: List[str]) -> List[str]:
        """Добавляет импорт BaseConfigModel если его нет"""
        config_import = "from my_codegen.pydantic_utils.pydantic_config import BaseConfigModel\n"

        if any("BaseConfigModel" in line and "import" in line for line in lines):
            return lines

        last_import_index = self._find_last_import_index(lines)

        if last_import_index >= 0:
            lines.insert(last_import_index + 1, config_import)
        else:
            lines.insert(0, config_import)

        return lines

    def _find_last_import_index(self, lines: List[str]) -> int:
        """Находит индекс последней строки импорта"""
        last_import_index = -1
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                last_import_index = idx
        return last_import_index

    def post_process_code(self, output_dir: str) -> None:
        """Форматирует код через autoflake и black"""
        self._run_autoflake(output_dir)
        self._run_black(output_dir)

    def _run_autoflake(self, output_dir: str) -> None:
        """Убирает неиспользуемые импорты"""
        cmd_parts = [
            "autoflake",
            "--remove-all-unused-imports",
            "--recursive",
            "--in-place",
            f"'{output_dir}'"
        ]
        run_command(" ".join(cmd_parts))

    def _run_black(self, output_dir: str) -> None:
        """Форматирует код"""
        run_command(f"black '{output_dir}'")