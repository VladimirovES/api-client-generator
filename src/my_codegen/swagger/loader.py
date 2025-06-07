import json
from typing import Dict, Any

from my_codegen.utils.shell import run_command

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class SwaggerInfo(BaseModel):
    title: str
    version: str = "1.0.0"
    description: Optional[str] = None


class SwaggerParameter(BaseModel):
    name: str
    in_: str = Field(alias="in")  # 'in' - зарезервированное слово
    required: bool = False
    schema_: Optional[Dict[str, Any]] = Field(alias="schema")


class SwaggerRequestBody(BaseModel):
    content: Dict[str, Any] = {}
    required: bool = False


class SwaggerResponse(BaseModel):
    description: str = ""
    content: Dict[str, Any] = {}


class SwaggerOperation(BaseModel):
    tags: List[str] = []
    summary: Optional[str] = None
    description: Optional[str] = None
    operationId: Optional[str] = None
    parameters: List[SwaggerParameter] = []
    requestBody: Optional[SwaggerRequestBody] = None
    responses: Dict[str, SwaggerResponse] = {}


class SwaggerPath(BaseModel):
    get: Optional[SwaggerOperation] = None
    post: Optional[SwaggerOperation] = None
    put: Optional[SwaggerOperation] = None
    patch: Optional[SwaggerOperation] = None
    delete: Optional[SwaggerOperation] = None


class SwaggerComponents(BaseModel):
    schemas: Dict[str, Any] = {}


class SwaggerSpec(BaseModel):
    openapi: Optional[str] = None
    swagger: Optional[str] = None
    info: SwaggerInfo
    paths: Dict[str, SwaggerPath]
    components: Optional[SwaggerComponents] = None


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
