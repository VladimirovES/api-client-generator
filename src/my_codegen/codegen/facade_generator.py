import os
from typing import Dict, List
from dataclasses import dataclass
from jinja2 import Environment, PackageLoader


@dataclass
class ClientImport:
    module_name: str
    class_name: str
    attribute_name: str


class FacadeGenerator:
    def __init__(self, facade_class_name: str, template_name: str):
        self.facade_class_name = facade_class_name
        self.template_name = template_name
        self.env = Environment(
            loader=PackageLoader("my_codegen", "templates"),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.template = self.env.get_template(self.template_name)

    def generate_facade(self, file_to_class: Dict[str, str], output_dir: str, file_name: str) -> None:
        imports_data = self._prepare_imports_data(file_to_class)

        rendered = self.template.render(
            facade_class_name=self.facade_class_name,
            imports=imports_data,
            docstring_indent=" "
        )

        self._write_facade_file(rendered, output_dir, file_name)

    def _prepare_imports_data(self, file_to_class: Dict[str, str]) -> List[ClientImport]:
        """Подготавливает данные об импортах клиентов"""
        client_files = sorted([f for f in file_to_class if f.endswith("_client.py")])

        imports_data = []
        for fname in client_files:
            module_name = fname[:-3]  # чтобы удалить .py
            class_name = file_to_class[fname]
            attribute_name = class_name.lower()

            imports_data.append(ClientImport(
                module_name=module_name,
                class_name=class_name,
                attribute_name=attribute_name
            ))

        return imports_data

    def _write_facade_file(self, rendered: str, output_dir: str, file_name: str) -> None:
        """Записывает файл фасада"""
        facade_path = os.path.join(output_dir, file_name)
        with open(facade_path, "w", encoding="utf-8") as f:
            f.write(rendered)