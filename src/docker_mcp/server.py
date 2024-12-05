import asyncio
import os
import platform
import shutil
import subprocess
from typing import Optional, Tuple, List
import yaml
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
from python_on_whales import DockerClient
import signal
import sys

server = Server("docker-mcp")
docker_client = DockerClient()


class DockerComposeExecutor:
    def __init__(self, compose_file: str, project_name: str):
        self.compose_file = os.path.abspath(compose_file)
        self.project_name = project_name

        # Get Docker path
        if platform.system() == 'Windows':
            docker_dir = r"C:\Program Files\Docker\Docker\resources\bin"
            docker_paths = [
                # Try docker-compose first
                os.path.join(docker_dir, "docker-compose.exe"),
                os.path.join(docker_dir, "docker.exe")          # Then docker
            ]
            for path in docker_paths:
                if os.path.exists(path):
                    self.docker_cmd = path
                    break
            else:
                # If not found in Docker Desktop location, try PATH
                self.docker_cmd = shutil.which('docker')
                if not self.docker_cmd:
                    raise RuntimeError("Docker executable not found")
        else:
            self.docker_cmd = shutil.which('docker')
            if not self.docker_cmd:
                raise RuntimeError("Docker executable not found in PATH")

    async def run_command(self, command: str, *args) -> Tuple[int, str, str]:
        if platform.system() == 'Windows':
            compose_file = self.compose_file.replace('\\', '/')
            cmd = f'cd "{os.path.dirname(compose_file)}" && docker compose -f "{os.path.basename(
                compose_file)}" -p {self.project_name} {command} {" ".join(args)}'

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
        else:
            cmd = [
                self.docker_cmd,
                "compose",
                "-f", self.compose_file,
                "-p", self.project_name,
                command,
                *args
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()

    async def down(self) -> Tuple[int, str, str]:
        return await self.run_command("down", "--volumes")

    async def pull(self) -> Tuple[int, str, str]:
        return await self.run_command("pull")

    async def up(self) -> Tuple[int, str, str]:
        return await self.run_command("up", "-d")

    async def ps(self) -> Tuple[int, str, str]:
        return await self.run_command("ps")

    def _debug_cmd(self, command: str, *args) -> str:
        if platform.system() == 'Windows':
            compose_file = self.compose_file.replace('\\', '/')
            return f'cd "{os.path.dirname(compose_file)}" && docker compose -f "{os.path.basename(compose_file)}" -p {self.project_name} {command} {" ".join(args)}'
        else:
            cmd = [
                self.docker_cmd,
                "compose",
                "-f", self.compose_file,
                "-p", self.project_name,
                command,
                *args
            ]
            return " ".join(cmd)


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="deploy-stack",
            description="Generate and deploy a Docker stack based on requirements",
            arguments=[
                types.PromptArgument(
                    name="requirements",
                    description="Description of the desired Docker stack",
                    required=True
                ),
                types.PromptArgument(
                    name="project_name",
                    description="Name for the Docker Compose project",
                    required=True
                )
            ]
        )
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    if name != "deploy-stack":
        raise ValueError(f"Unknown prompt: {name}")

    if not arguments or "requirements" not in arguments or "project_name" not in arguments:
        raise ValueError("Missing required arguments")

    system_message = (
        "You are a Docker deployment specialist. Generate appropriate Docker Compose YAML or "
        "container configurations based on user requirements. For simple single-container "
        "deployments, use the create-container tool. For multi-container deployments, generate "
        "a docker-compose.yml and use the deploy-compose tool."
    )
    user_message = f"""Please help me deploy the following stack:
Requirements: {arguments['requirements']}
Project name: {arguments['project_name']}

Analyze if this needs a single container or multiple containers. Then:
1. For single container: Use the create-container tool with format:
{{
    "image": "image-name",
    "name": "container-name",
    "ports": {{"80": "80"}},
    "environment": {{"ENV_VAR": "value"}}
}}

2. For multiple containers: Use the deploy-compose tool with format:
{{
    "project_name": "example-stack",
    "compose_yaml": "version: '3.8'\\nservices:\\n  service1:\\n    image: image1:latest\\n    ports:\\n      - '8080:80'"
}}"""

    return types.GetPromptResult(
        description="Generate and deploy a Docker stack",
        messages=[
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text=system_message
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=user_message
                )
            )
        ]
    )


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="create-container",
            description="Create a new standalone Docker container",
            inputSchema={
                "type": "object",
                "properties": {
                    "image": {"type": "string"},
                    "name": {"type": "string"},
                    "ports": {
                        "type": "object",
                        "additionalProperties": {"type": "string"}
                    },
                    "environment": {
                        "type": "object",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["image"]
            }
        ),
        types.Tool(
            name="deploy-compose",
            description="Deploy a Docker Compose stack",
            inputSchema={
                "type": "object",
                "properties": {
                    "compose_yaml": {"type": "string"},
                    "project_name": {"type": "string"}
                },
                "required": ["compose_yaml", "project_name"]
            }
        )
    ]


async def parse_port_mapping(host_key: str, container_port: str | int) -> tuple[str, str] | tuple[str, str, str]:
    if '/' in str(host_key):
        host_port, protocol = host_key.split('/')
        if protocol.lower() == 'udp':
            return (str(host_port), str(container_port), 'udp')
        return (str(host_port), str(container_port))

    if isinstance(container_port, str) and '/' in container_port:
        port, protocol = container_port.split('/')
        if protocol.lower() == 'udp':
            return (str(host_key), port, 'udp')
        return (str(host_key), port)

    return (str(host_key), str(container_port))


async def handle_create_container(arguments: dict) -> list[types.TextContent]:
    try:
        image = arguments["image"]
        container_name = arguments.get("name")
        ports = arguments.get("ports", {})
        environment = arguments.get("environment", {})

        if not image:
            raise ValueError("Image name cannot be empty")

        port_mappings = []
        for host_key, container_port in ports.items():
            mapping = await parse_port_mapping(host_key, container_port)
            port_mappings.append(mapping)

        async def pull_and_run():
            if not docker_client.image.exists(image):
                await asyncio.to_thread(docker_client.image.pull, image)

            container = await asyncio.to_thread(
                docker_client.container.run,
                image,
                name=container_name,
                publish=port_mappings,
                envs=environment,
                detach=True
            )
            return container

        TIMEOUT_AMOUNT = 200
        container = await asyncio.wait_for(pull_and_run(), timeout=TIMEOUT_AMOUNT)
        return [types.TextContent(type="text", text=f"Created container '{container.name}' (ID: {container.id})")]
    except asyncio.TimeoutError:
        return [types.TextContent(type="text", text="Operation timed out after 200 seconds")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error creating container: {str(e)} | Arguments: {arguments}")]


async def handle_deploy_compose(arguments: dict) -> list[types.TextContent]:
    debug_info = []
    try:
        compose_yaml = arguments.get("compose_yaml")
        project_name = arguments.get("project_name")

        if not compose_yaml or not project_name:
            raise ValueError("Missing required compose_yaml or project_name")

        debug_info.append("=== Original YAML ===")
        debug_info.append(compose_yaml)

        try:
            yaml_content = yaml.safe_load(compose_yaml)
            debug_info.append("\n=== Loaded YAML Structure ===")
            debug_info.append(str(yaml_content))
            compose_yaml = yaml.safe_dump(
                yaml_content, default_flow_style=False, sort_keys=False)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")

        compose_dir = os.path.join(os.getcwd(), "docker_compose_files")
        os.makedirs(compose_dir, exist_ok=True)

        compose_path = os.path.join(
            compose_dir, f"{project_name}-docker-compose.yml")
        try:
            with open(compose_path, 'w', encoding='utf-8') as f:
                f.write(compose_yaml)
                f.flush()
                if platform.system() != 'Windows':
                    os.fsync(f.fileno())

            debug_info.append(f"\n=== Compose File Path ===\n{compose_path}")

            if platform.system() == 'Windows':
                debug_info.append("\n=== PowerShell Command ===")
                cmd_parts = [
                    "docker compose",
                    f"-f \"{compose_path}\"",
                    f"-p {project_name}",
                    "up -d"
                ]
                debug_info.append(" ".join(cmd_parts))
            compose = DockerComposeExecutor(compose_path, project_name)

            try:
                code, out, err = await compose.down()
                debug_info.extend([
                    "\n=== Down Command ===",
                    f"Return Code: {code}",
                    f"Stdout: {out}",
                    f"Stderr: {err}"
                ])
            except Exception as e:
                debug_info.append(f"Warning during down: {str(e)}")

            try:
                code, out, err = await compose.pull()
                debug_info.extend([
                    "\n=== Pull Command ===",
                    f"Return Code: {code}",
                    f"Stdout: {out}",
                    f"Stderr: {err}"
                ])
                if code != 0:
                    debug_info.append(f"Warning: Pull failed with code {code}")
            except Exception as e:
                debug_info.append(f"Warning during pull: {str(e)}")

            code, out, err = await compose.up()
            debug_info.extend([
                "\n=== Up Command ===",
                f"Return Code: {code}",
                f"Stdout: {out}",
                f"Stderr: {err}"
            ])

            if code != 0:
                raise Exception(f"Deploy failed with code {code}: {err}")

            code, out, err = await compose.ps()
            service_info = out if code == 0 else "Unable to list services"

            return [types.TextContent(
                type="text",
                text=(
                    f"Successfully deployed compose stack '{project_name}'\n"
                    f"Running services:\n{service_info}\n\n"
                    f"Debug Info:\n{chr(10).join(debug_info)}"
                )
            )]

        finally:
            try:
                if os.path.exists(compose_path):
                    os.remove(compose_path)
                if os.path.exists(compose_dir) and not os.listdir(compose_dir):
                    os.rmdir(compose_dir)
            except Exception as e:
                debug_info.append(f"Warning during cleanup: {str(e)}")

    except Exception as e:
        debug_output = "\n".join(debug_info)
        return [types.TextContent(
            type="text",
            text=(
                f"Error deploying compose stack: {str(e)}\n\n"
                f"Debug Information:\n{debug_output}"
            )
        )]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if not arguments:
        raise ValueError("Missing arguments")

    try:
        if name == "create-container":
            return await handle_create_container(arguments)
        elif name == "deploy-compose":
            return await handle_deploy_compose(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)} | Arguments: {arguments}")]


def handle_shutdown(signum, frame):
    print("Shutting down gracefully...")
    sys.exit(0)


async def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="docker-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
