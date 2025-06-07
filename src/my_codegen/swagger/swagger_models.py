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


class SwaggerServer(BaseModel):
    url: str
    description: Optional[str] = None
    

class SwaggerSpec(BaseModel):
    servers: List[SwaggerServer] = []
    openapi: Optional[str] = None
    swagger: Optional[str] = None
    info: SwaggerInfo
    paths: Dict[str, SwaggerPath]
    components: Optional[SwaggerComponents] = None
