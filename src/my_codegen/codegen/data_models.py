from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Parameter:
    name: str
    type: str
    required: bool = False


@dataclass
class Endpoint:
    tag: str
    name: str
    http_method: str
    path: str
    path_params: List[Parameter] = field(default_factory=list)
    query_params: List[Parameter] = field(default_factory=list)
    payload_type: Optional[str] = None
    expected_status: str = "OK"
    return_type: str = "Any"
    description: str = ""

    @property
    def sanitized_path(self) -> str:
        return self.path if self.path.startswith("/") else f"/{self.path}"

    @property
    def method_parameters(self) -> List[str]:
        return [f"{p.name}: {p.type}" for p in self.path_params if p.required]


@dataclass
class SubPath:
    name: str
    path: str


@dataclass
class MethodContext:
    """Готовый контекст для рендеринга метода"""
    name: str
    description: str
    path: str
    return_type: str
    expected_status: str

    # Параметры
    required_params: List[str]
    optional_params: List[str]

    # Готовый код
    http_call: str
    return_statement: str

    @classmethod
    def from_endpoint(cls, endpoint: Endpoint) -> 'MethodContext':
        """Конвертирует Endpoint в MethodContext с готовой логикой"""

        # 1. Собираем параметры в правильном порядке
        required_params = []
        optional_params = []

        # Path параметры (всегда required)
        for param in endpoint.path_params:
            required_params.append(f"{param.name}: {param.type}")

        # Query required параметры
        for param in endpoint.query_params:
            if param.required:
                required_params.append(f"{param.name}: {param.type}")

        # Payload (если required)
        if (endpoint.http_method != 'GET' and
                endpoint.payload_type and
                endpoint.payload_type != 'Any'):
            required_params.append(f"payload: {endpoint.payload_type}")

        # Query optional параметры
        for param in endpoint.query_params:
            if not param.required:
                optional_params.append(f"{param.name}: Optional[{param.type}] = None")

        # Дополнительные параметры
        if endpoint.http_method == 'GET':
            optional_params.append("params: Optional[Dict[str, Any]] = None")
        elif endpoint.payload_type == 'Any' or not endpoint.payload_type:
            optional_params.append("payload: Optional[Any] = None")

        # 2. Генерируем HTTP вызов
        http_call = cls._generate_http_call(endpoint)

        # 3. Генерируем return statement
        return_statement = cls._generate_return_statement(endpoint)

        return cls(
            name=endpoint.name,
            description=endpoint.description,
            path=endpoint.path,
            return_type=endpoint.return_type,
            expected_status=endpoint.expected_status,
            required_params=required_params,
            optional_params=optional_params,
            http_call=http_call,
            return_statement=return_statement
        )

    @staticmethod
    def _generate_http_call(endpoint: Endpoint) -> str:
        """Генерирует строку HTTP вызова"""
        method = endpoint.http_method.lower()

        if endpoint.http_method == 'GET':
            params_dict = "{"
            for param in endpoint.query_params:
                params_dict += f"'{param.name}': {param.name}, "
            params_dict += "**(params or {})}"

            return f"""r_json = self._{method}(
                path=self._service + path,
                params={params_dict},
                expected_status=status
            )"""

        else:  # POST, PUT, PATCH, DELETE
            call_parts = [f"path=self._service + path"]

            # Payload
            if endpoint.payload_type:
                if endpoint.payload_type.startswith('List['):
                    call_parts.append("payload=[item.dict() for item in payload] if payload else None")
                elif endpoint.payload_type != 'Any':
                    call_parts.append("payload=payload.dict() if payload else None")

            # Query параметры для non-GET методов
            if endpoint.query_params:
                params_dict = "{"
                for param in endpoint.query_params:
                    params_dict += f"'{param.name}': {param.name}, "
                params_dict += "}"
                call_parts.append(f"params={params_dict}")

            call_parts.append("expected_status=status")

            # Выносим join отдельно
            joined_parts = ',\n            '.join(call_parts)
            return f"""r_json = self._{method}(
                {joined_parts}
            )"""

    @staticmethod
    def _generate_return_statement(endpoint: Endpoint) -> str:
        """Генерирует return statement"""
        if endpoint.return_type == 'Any':
            return "return r_json"

        condition = f"if status == HTTPStatus.{endpoint.expected_status} else r_json"

        if endpoint.return_type.startswith('List['):
            inner_type = endpoint.return_type[5:-1]  # убираем List[]
            if inner_type in {'str', 'int', 'float', 'bool', 'Any'}:
                return f"return [{inner_type}(item) for item in r_json] {condition}"
            else:
                return f"return [{inner_type}(**item) for item in r_json] {condition}"

        elif endpoint.return_type in {'str', 'int', 'float', 'bool'}:
            return f"return {endpoint.return_type}(r_json) {condition}"

        else:
            return f"return {endpoint.return_type}(**r_json) {condition}"