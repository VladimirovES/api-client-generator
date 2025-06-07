import json
from typing import Dict, Any

from my_codegen.utils.shell import run_command

from typing import Dict, List, Optional, Any

from my_codegen.swagger.swagger_models import SwaggerSpec

class SwaggerLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.swagger_spec: Optional[SwaggerSpec] = None

    def load(self) -> None:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                swagger_dict = json.load(f)
            self.swagger_spec = SwaggerSpec(**swagger_dict)
        except ValidationError as e:
            raise ValueError(f"Invalid swagger format: {e}")

    def get_service_name(self) -> str:
        title = self.swagger_spec.info.title
        normalized = re.sub(r'[^a-zA-Z0-9]+', '_', title.strip())
        return normalized.lower().strip('_')

    def download_swagger(self, url: str):
        swagger_cmd = f"curl {url} -o ./swagger.json"
        run_command(swagger_cmd)
