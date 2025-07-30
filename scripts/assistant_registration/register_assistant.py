#!/usr/bin/env python3
"""Script to register new OpenAI assistants with customizable configuration."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.beta import Assistant
from pydantic import ValidationError

from assistant_service.structured_logging import configure_structlog, get_logger

# Handle both direct execution and module execution
try:
    from .registration import AssistantRegistrationConfig
except ImportError:
    from registration import AssistantRegistrationConfig

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# Configure logging
configure_structlog()

# Initialize logger
logger = get_logger(__name__)


class AssistantRegistrar:
    """Handles registration of new OpenAI assistants."""

    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set. Please check your .env file.")
        logger.debug("OpenAI API key loaded successfully")
        self.client = AsyncOpenAI(api_key=api_key)

    async def upload_file(self, file_path: str) -> str:
        """Upload a file for retrieval.

        Args:
            file_path: Path to the file to upload

        Returns:
            File ID from OpenAI
        """
        logger.info(f"Uploading file: {file_path}")
        with open(file_path, "rb") as f:
            file = await self.client.files.create(file=f, purpose="assistants")
        logger.info(f"File uploaded successfully with ID: {file.id}")
        return file.id

    async def create_assistant(
        self,
        name: str,
        instructions: str,
        model: str,
        tools: list[dict[str, Any]],
        tool_resources: dict[str, Any] | None = None,
    ) -> Assistant:
        """Create a new assistant with the specified configuration.

        Args:
            name: Assistant name
            instructions: System instructions for the assistant
            model: Model to use (e.g., gpt-4-turbo-preview)
            tools: List of tool definitions
            tool_resources: Optional tool resources configuration

        Returns:
            Created Assistant object
        """
        logger.info(f"Creating assistant: {name}")
        logger.debug(f"Tools: {tools}")

        create_params = {
            "name": name,
            "instructions": instructions,
            "model": model,
            "tools": tools,  # type: ignore[arg-type]
        }

        if tool_resources:
            create_params["tool_resources"] = tool_resources

        assistant = await self.client.beta.assistants.create(**create_params)

        logger.info(f"Assistant created successfully with ID: {assistant.id}")
        return assistant

    def build_tools(
        self,
        code_interpreter: bool = False,
        file_search: bool = False,
        functions: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Build tool definitions for the assistant.

        Args:
            code_interpreter: Enable code interpreter tool
            file_search: Enable file search tool
            functions: List of function definitions

        Returns:
            List of tool definitions
        """
        tools = []

        if code_interpreter:
            tools.append({"type": "code_interpreter"})

        if file_search:
            tools.append({"type": "file_search"})

        if functions:
            for func in functions:
                tools.append({"type": "function", "function": func})

        return tools

    async def create_vector_store_for_files(
        self,
        name: str,
        file_paths: list[str],
    ) -> str | None:
        """Create a vector store and upload files to it.

        Args:
            name: Name for the vector store
            file_paths: List of file paths to upload

        Returns:
            Vector store ID if successful, None otherwise
        """
        try:
            # Create vector store using official OpenAI client
            vector_store = await self.client.beta.vector_stores.create(name=name)
            vector_store_id = vector_store.id
            logger.info(f"Vector store created with ID: {vector_store_id}")

            # Upload files and add to vector store
            file_ids = []
            for file_path in file_paths:
                logger.info(f"Uploading file: {file_path}")
                with open(file_path, "rb") as f:
                    file = await self.client.files.create(file=f, purpose="assistants")
                file_ids.append(file.id)
                logger.info(f"File {file_path} uploaded with ID: {file.id}")

                # Add file to vector store using official client
                try:
                    await self.client.beta.vector_stores.files.create(
                        vector_store_id=vector_store_id,
                        file_id=file.id
                    )
                    logger.info(f"File {file.id} added to vector store")
                except Exception as e:
                    logger.warning(f"Failed to add file {file.id} to vector store: {e}")

            return vector_store_id

        except Exception as e:
            logger.warning(f"Vector store creation failed: {e}")
            return None


async def load_functions_from_module(module_path: str) -> list[dict[str, Any]]:
    """Load function definitions from a Python module.

    Args:
        module_path: Python module path (e.g., 'client_spec.mycompany.functions')

    Returns:
        List of function definitions
    """
    # This is a placeholder - in a real implementation, you would:
    # 1. Import the module dynamically
    # 2. Find all function definitions
    # 3. Convert them to OpenAI function format
    logger.warning(f"Function loading from module not implemented: {module_path}")
    return []


async def main():
    """Main entry point for the assistant registration script."""
    parser = argparse.ArgumentParser(
        description="Register a new OpenAI assistant from a configuration file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Register assistant from config file
  %(prog)s assistant-config.json
  
  # Generate config schema
  %(prog)s --generate-schema > assistant-config-schema.json
  
  # Save registered assistant config
  %(prog)s assistant-config.json --output-config registered-config.json
""",
    )

    # Positional argument for config file
    parser.add_argument(
        "config_file",
        nargs="?",
        help="Path to JSON configuration file",
    )

    # Output options
    parser.add_argument(
        "--output-config",
        type=str,
        help="Path to save the registered assistant configuration",
    )
    parser.add_argument(
        "--generate-schema",
        action="store_true",
        help="Generate and print JSON schema for configuration files",
    )

    args = parser.parse_args()

    # Handle schema generation
    if args.generate_schema:
        schema = AssistantRegistrationConfig.model_json_schema()
        print(json.dumps(schema, indent=2))
        return

    # Require config file if not generating schema
    if not args.config_file:
        parser.error("config_file is required unless using --generate-schema")

    # Load configuration from file
    try:
        logger.info(f"Loading configuration from: {args.config_file}")
        with open(args.config_file) as f:
            data = json.load(f)
        config = AssistantRegistrationConfig(**data)
    except FileNotFoundError:
        logger.error(f"Config file not found: {args.config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        sys.exit(1)
    except ValidationError as e:
        logger.error(f"Invalid configuration: {e}")
        sys.exit(1)

    # Initialize registrar
    try:
        registrar = AssistantRegistrar()
    except ValueError as e:
        logger.error(f"Failed to initialize: {e}")
        sys.exit(1)

    # Load functions if specified
    functions = []
    if config.functions_module:
        functions = await load_functions_from_module(config.functions_module)
    elif config.function_definitions:
        functions = config.function_definitions

    # Create vector store if files are provided
    vector_store_id = None
    if config.vector_store_file_paths:
        if not config.vector_store_name:
            config.vector_store_name = f"{config.assistant_name} Knowledge Base"

        try:
            # Try to create vector store using direct API
            vector_store_id = await registrar.create_vector_store_for_files(
                name=config.vector_store_name,
                file_paths=config.vector_store_file_paths,
            )

            if not vector_store_id:
                logger.warning("Failed to create vector store. Files will be uploaded without vector store.")
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            sys.exit(1)

    # Build tools
    tools = registrar.build_tools(
        code_interpreter=config.code_interpreter,
        file_search=bool(config.vector_store_file_paths),  # Enable file search if files are provided
        functions=functions,
    )

    # Create assistant
    try:
        # Build tool resources if vector store exists
        tool_resources = {}
        if vector_store_id:
            tool_resources["file_search"] = {"vector_store_ids": [vector_store_id]}

        assistant = await registrar.create_assistant(
            name=config.assistant_name,
            instructions=config.instructions,
            model=config.model,
            tools=tools,
            tool_resources=tool_resources if tool_resources else None,
        )
    except Exception as e:
        logger.error(f"Failed to create assistant: {e}")
        sys.exit(1)

    # Output results
    print("\n" + "=" * 50)
    print("✅ Assistant created successfully!")
    print("=" * 50)
    print(f"Assistant ID: {assistant.id}")
    print(f"Name: {assistant.name}")
    print(f"Model: {assistant.model}")
    if tools:
        print(f"Tools: {[t.get('type') for t in tools]}")
    if vector_store_id:
        print(f"Vector Store: {config.vector_store_name} (ID: {vector_store_id})")
        print(f"Files indexed: {len(config.vector_store_file_paths)}")
    elif config.vector_store_file_paths:
        print(f"Files uploaded: {len(config.vector_store_file_paths)}")
        print("Note: Files uploaded but vector store creation failed")
    print("\n📝 To use this assistant:")
    print(f"1. Update your configuration with assistant_id: '{assistant.id}'")
    print("2. Run the assistant service with this ID")

    # Save output configuration if requested
    if args.output_config:
        runtime_config = config.to_assistant_config(assistant.id)
        output_path = Path(args.output_config)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(runtime_config.model_dump(), f, indent=2)

        print(f"\n💾 Runtime configuration saved to: {output_path}")
        print("   You can use this directly with the assistant service.")

    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
