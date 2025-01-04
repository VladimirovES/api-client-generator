import os
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
from codegen.data_models import Endpoint, SubPath
from utils.common import class_name_from_tag
from utils.logger import logger


class ClientGenerator:
    def __init__(
        self, endpoints: List[Endpoint], imports: List[str], template_path: str
    ):
        self.endpoints = endpoints
        self.imports = imports
        self.template_path = template_path

        self.env = Environment(
            loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True
        )
        self.template = self.env.get_template(self.template_path)

    def generate_clients(self, output_dir: str, module: str) -> Dict[str, str]:
        """
        Проходит по всем эндпоинтам, группирует по тегам, рендерит файлы.
        Возвращает { filename: className } для фасада.
        """
        os.makedirs(output_dir, exist_ok=True)
        grouped = self._group_endpoints_by_tag(self.endpoints)
        file_to_class = {}

        for tag, eps in grouped.items():
            class_name = class_name_from_tag(tag)
            base_path = self._determine_base_path(eps)
            sub_paths = self._collect_sub_paths(eps, base_path)

            rendered = self.template.render(
                class_name=class_name,
                base_path=base_path,
                sub_paths=sub_paths,
                methods=eps,
                imports=self.imports,
                models_import_path=f"http_clients.{module}.models",
            )

            filename = f"{class_name.lower()}_client.py"
            full_path = os.path.join(output_dir, filename)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(rendered)

            file_to_class[filename] = class_name

        return file_to_class

    @staticmethod
    def _group_endpoints_by_tag(endpoints: List[Endpoint]) -> Dict[str, List[Endpoint]]:
        grouped = {}
        for ep in endpoints:
            grouped.setdefault(ep.tag, []).append(ep)
        return grouped

    def _determine_base_path(self, eps: List[Endpoint]) -> str:
        if not eps:
            return "/"
        paths = [ep.path for ep in eps]
        split_paths = [p.strip("/").split("/") for p in paths]
        common = split_paths[0]
        for sp in split_paths[1:]:
            min_length = min(len(common), len(sp))
            temp = []
            for i in range(min_length):
                if common[i] == sp[i]:
                    temp.append(common[i])
                else:
                    break
            common = temp
        return "/" + "/".join(common)

    def _collect_sub_paths(self, eps: List[Endpoint], base_path: str) -> List[SubPath]:
        sub_paths = []
        for ep in eps:
            path_suffix = ep.sanitized_path
            if path_suffix.startswith(base_path):
                path_suffix = path_suffix[len(base_path) :]
            if not path_suffix.startswith("/"):
                path_suffix = "/" + path_suffix
            if path_suffix and path_suffix != "/":
                sub_path_name = self._extract_sub_path_name(path_suffix)
                if sub_path_name not in [sp.name for sp in sub_paths]:
                    sub_paths.append(SubPath(name=sub_path_name, path=path_suffix))
        return sub_paths

    @staticmethod
    def _extract_sub_path_name(sub_path: str) -> str:
        segments = sub_path.strip("/").split("/")
        if segments:
            first_segment = segments[0]
            if first_segment.startswith("{") and first_segment.endswith("}"):
                return first_segment[1:-1]
            return first_segment
        return "sub_path"
