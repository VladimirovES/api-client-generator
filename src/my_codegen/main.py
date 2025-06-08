import argparse
import os

from dotenv import load_dotenv

from my_codegen.codegen.facade_generator import FacadeGenerator
from my_codegen.codegen.generate_app_facade import generate_app_facade
from my_codegen.codegen.client_generator import ClientGenerator
from my_codegen.codegen.model_generator import ModelGenerator
from my_codegen.swagger.loader import SwaggerLoader
from my_codegen.swagger.processor import SwaggerProcessor
from my_codegen.utils.logger import logger

load_dotenv()


def main():
    # 1. Fetch SWAGGER_URL from .env or environment variables
    swagger_path = 'swagger.json'
    parser = argparse.ArgumentParser(description="API Client Generator")
    parser.add_argument(
        "--swagger-url",
        help="URL to download the Swagger JSON from",
        required=True
    )
    args = parser.parse_args()

    swagger_url = args.swagger_url
    if swagger_url:
        logger.info(f"Swagger URL from CLI: {swagger_url}")
    else:
        logger.info("No CLI swagger-url provided, will fallback to environment variable")
    loader = SwaggerLoader(swagger_path)

    # 2. Download swagger.json
    logger.info("Downloading Swagger file...")
    loader.download_swagger(url=swagger_url)
    logger.info("Swagger file downloaded. Now parsing the local swagger.json...")
    loader.load()
    swagger_spec = loader.swagger_spec
    module_name = loader.get_module_name()
    service_path = loader.get_service_path()
    logger.info(f"Service identified as: {module_name}")

    # 3. Create output directories
    base_output_dir = 'http_clients'
    service_dir = os.path.join(base_output_dir, module_name)
    endpoints_dir = os.path.join(service_dir, "endpoints")
    os.makedirs(service_dir, exist_ok=True)
    os.makedirs(endpoints_dir, exist_ok=True)
    logger.info(f"Created directories for service: '{service_dir}' and '{endpoints_dir}'")

    # 4. Generate models -> http_clients/<service_name>/models.py
    models_file = os.path.join(service_dir, "models")
    model_gen = ModelGenerator(swagger_path, models_file)
    logger.info("Generating Pydantic models (via datamodel-codegen)...")
    model_gen.generate_models()
    logger.info("Models generated. Fixing BaseModel->BaseConfigModel inheritance...")
    model_gen.fix_models_inheritance()
    logger.info("Model inheritance fixed. Ready for further processing.")

    # 5. Parse the Swagger to extract endpoints and imports
    logger.info("Extracting endpoints and imports from swagger.")
    processor = SwaggerProcessor(swagger_spec)
    endpoints = processor.extract_endpoints()
    imports = processor.extract_imports()
    logger.info(f"Found {len(endpoints)} endpoints and {len(imports)} imports.")

    # 6. Generate client classes -> http_clients/<service_name>/endpoints/*.py
    logger.info("Generating client classes (by swagger tags)...")
    client_gen = ClientGenerator(
        endpoints=endpoints,
        imports=imports,
        template_name='client_template.j2'
    )
    file_to_class = client_gen.generate_clients(endpoints_dir, module_name, service_path)
    logger.info(f"Generated {len(file_to_class)} client files.")

    # 7. Auto-format (autoflake, black)
    logger.info(f"Running auto-format (autoflake, black) on '{service_dir}'...")
    model_gen.post_process_code(service_dir)
    logger.info("Auto-format completed.")

    # 8. Generate local facade -> http_clients/<service_name>/facade.py
    facade_gen = FacadeGenerator(
        facade_class_name=f"{module_name.replace('_', '').capitalize()}Api",  # убираем _
        template_name='facade_template.j2'
    )
    facade_filename = "facade.py"
    logger.info("Generating local facade for the service.")
    facade_gen.generate_facade(file_to_class, service_dir, facade_filename)
    logger.info("Local facade generated successfully.")

    # 9. Generate global facade (app_facade) -> http_clients/api_facade.py
    logger.info("Generating global (app) facade...")
    generate_app_facade(
        template_name="app_facade.j2",
        output_path="http_clients/api_facade.py",
        base_dir="http_clients"
    )
    logger.info("Global facade (api_facade.py) generated successfully.")

    logger.info(
        f"Clients (endpoints/*.py), models, and facade for service '{module_name}' have been created at '{service_dir}'.")


if __name__ == "__main__":
    main()
