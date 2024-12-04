import asyncio
import os
import platform
import shutil
import signal
import sys
from typing import Tuple, List

import yaml
from mcp.server.models import InitializationOptions
from mcp.server import Server, NotificationOptions
from mcp.types import TextContent, Tool, Prompt, PromptArgument, GetPromptResult, PromptMessage
from python_on_whales import DockerClient
from python_on_whales.exceptions import DockerException

server = Server("docker-mcp")
docker_client = DockerClient()


class DockerComposeExecutor:
    def __init__(self, compose_file: str, project_name: str):
        self.compose_file = os.path.abspath(compose_file)
        self.project_name = project_name

    async def run_command(self, command: str, *args) -> Tuple[int, str, str]:
        try:
            cmd = [
                "docker", "compose",
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
        except Exception as e:
            return -1, "", str(e)

    async def down(self) -> Tuple[int, str, str]:
        return await self.run_command("down", "--volumes")

    async def pull(self) -> Tuple[int, str, str]:
        return await self.run_command("pull")

    async def up(self) -> Tuple[int, str, str]:
        return await self.run_command("up", "-d")

    async def ps(self) -> Tuple[int, str, str]:
        return await self.run_command("ps")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
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


async def handle_deploy_compose(arguments: dict) -> List[TextContent]:
    debug_info = []
    try:
        compose_yaml = arguments.get("compose_yaml")
        project_name = arguments.get("project_name")

        if not compose_yaml or not project_name:
            raise ValueError("Missing required compose_yaml or project_name")

        debug_info.append("Parsing YAML...")
        try:
            yaml_content = yaml.safe_load(compose_yaml)
            debug_info.append("YAML successfully parsed.")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")

        compose_dir = os.path.join(os.getcwd(), "docker_compose_files")
        os.makedirs(compose_dir, exist_ok=True)

        compose_path = os.path.join(
            compose_dir, f"{project_name}-docker-compose.yml")
        debug_info.append(f"Writing compose file to {compose_path}...")
        with open(compose_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f)
        debug_info.append("Compose file written.")

        executor = DockerComposeExecutor(compose_path, project_name)
        try:
            debug_info.append("Running 'down' command...")
            code, out, err = await executor.down()
            debug_info.extend(
                [f"Down: {out.strip()}", f"Error: {err.strip()}"])

            debug_info.append("Running 'pull' command...")
            code, out, err = await executor.pull()
            if code != 0:
                raise Exception(f"Pull failed: {err.strip()}")
            debug_info.extend(
                [f"Pull: {out.strip()}", f"Error: {err.strip()}"])

            debug_info.append("Running 'up' command...")
            code, out, err = await executor.up()
            if code != 0:
                raise Exception(f"Up failed: {err.strip()}")
            debug_info.extend([f"Up: {out.strip()}", f"Error: {err.strip()}"])

            debug_info.append("Running 'ps' command...")
            code, out, err = await executor.ps()
            service_info = out.strip() if code == 0 else "Unable to list services"
            debug_info.append("Services listed successfully.")

            return [
                TextContent(type="text", text=f"Successfully deployed stack '{
                            project_name}'.\n\nServices:\n{service_info}\n\nDebug Info:\n{chr(10).join(debug_info)}")
            ]
        finally:
            debug_info.append("Cleaning up compose files...")
            try:
                if os.path.exists(compose_path):
                    os.remove(compose_path)
                if os.path.exists(compose_dir) and not os.listdir(compose_dir):
                    os.rmdir(compose_dir)
            except Exception as e:
                debug_info.append(f"Cleanup error: {str(e)}")
    except Exception as e:
        debug_output = "\n".join(debug_info)
        return [TextContent(type="text", text=f"Error deploying compose stack: {str(e)}\n\nDebug Info:\n{debug_output}")]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    if name == "deploy-compose":
        return await handle_deploy_compose(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))

    async with server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="docker-mcp",
                server_version="1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
