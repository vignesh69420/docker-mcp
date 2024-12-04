# docker-mcp MCP server

Docker MCP server
Supports instantiating containers, and docker compose operations

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  ```
  "mcpServers": {
    "docker-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "<path-to-docker-mcp>",
        "run",
        "docker-mcp"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  ```
  "mcpServers": {
    "docker-mcp": {
      "command": "uvx",
      "args": [
        "docker-mcp"
      ]
    }
  }
  ```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Inspector

You can launch the MCP Inspector with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory <path-to-docker-mcp> run docker-mcp
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.