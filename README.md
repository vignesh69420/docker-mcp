# 🐳 docker-mcp

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful Model Context Protocol (MCP) server for Docker operations, enabling seamless container and compose stack management through Claude AI.

## ✨ Features

- 🚀 Container creation and instantiation
- 📦 Docker Compose stack deployment
- 🔍 Container logs retrieval
- 📊 Container listing and status monitoring
- 🧹 Automatic cleanup of temporary files
- ♻️ Automatic image pulling

### 🎬 Demos
#### Deploying a Docker Compose Stack

<a href="https://streamable.com/0fz6kn" target="_blank">
    <img src="https://cdn-cf-east.streamable.com/image/0fz6kn.jpg?Expires=1733623440&Signature=PIYLK6wY6HM~9kPqmmpabnjHoObDdz9MgjE4-TVD74BN~bXTZFkHKo3B9ufF8HoVqD7lA79gpngGAJ0pJTi62UgirktBx-eG2vxXEj6IbWrTkQJnmePAV6vM8Nu5j1~v6eKiS~a8bUiYnEioyFtufxSbfgTTV3sIYzXe6blabMGf-KSHg9yoAa6CwnfDRusfrUNsJxs2uNxAfhBe8~0KC0OcPujwnPZarJmYsz7CuTgsPb3TbnREdLGb2tNxNAjMFzRxjQvkSXGbxbfytsqMGhqSDqSSuFBRcOgraZoAsJmyWt1fb2VSKaD0I6Zxzzyssr7hJ82JHMVyJZAMgT1tlQ__&Key-Pair-Id=APKAIEYUVEN4EVB2OKEQ" alt="Docker Compose Demo" width="600px"/>
</a>

#### Analyzing Container Logs

<a href="https://streamable.com/3fjqi3" target="_blank">
    <img src="https://cdn-cf-east.streamable.com/image/3fjqi3.jpg?Expires=1733623500&Signature=XaG9q65aFAl8fmk1kvf9TsJj2RB8u035RDpWTLJ7eWzqClmVOPuYEklw4dox3JBQcrcHmg4SJFcyTvhwmyQLc19UKli9yEkO4AqwSlE9SEqrBrOBvCsWoDUa8CBuTU~-9R~sJd8fLVeQNQhvTnTyVFF9z0zkJ3XzDBWcXDMleXL4IbKiD5Z0IcYTsRTJCGD91qtjdO4dDqaaj5fpWNGQixa7ffgvSu5QZJHaLrcnspum7lKKI58eJQlS7T9WqZUXSW2c5vK-EMLrTmV~AXOfZHig-d6XqdBbz0Bg1gLBCdyWsY6PkMhUaR9MIVDVzPwQonVDy5fEDNsnS18zN~1Cfw__&Key-Pair-Id=APKAIEYUVEN4EVB2OKEQ" alt="Container Logs Demo" width="600px"/>
</a>

📝 Click on the images above to watch the demos

## 🚀 Quickstart

### Prerequisites

- Python 3.12+
- Docker Desktop or Docker Engine
- Claude Desktop

### Installation

#### Claude Desktop Configuration

Add the server configuration to your Claude Desktop config file:

**MacOS**: `~/Library/Application\ Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>💻 Development Configuration</summary>

```json
{
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
}
```
</details>

<details>
  <summary>🚀 Production Configuration</summary>

```json
{
  "mcpServers": {
    "docker-mcp": {
      "command": "uvx",
      "args": [
        "docker-mcp"
      ]
    }
  }
}
```
</details>

## 🛠️ Development

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/QuantGeekDev/docker-mcp.git
cd docker-mcp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
uv sync
```

### Building and Publishing

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```
This creates source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

#### PyPI Credentials

Set your credentials via:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Username/Password: 
  - `--username`/`UV_PUBLISH_USERNAME`
  - `--password`/`UV_PUBLISH_PASSWORD`

### 🔍 Debugging

Launch the MCP Inspector for debugging:

```bash
npx @modelcontextprotocol/inspector uv --directory <path-to-docker-mcp> run docker-mcp
```

The Inspector will provide a URL to access the debugging interface.

## 📝 Available Tools

The server provides the following tools:

### create-container
Creates a standalone Docker container
```json
{
    "image": "image-name",
    "name": "container-name",
    "ports": {"80": "80"},
    "environment": {"ENV_VAR": "value"}
}
```

### deploy-compose
Deploys a Docker Compose stack
```json
{
    "project_name": "example-stack",
    "compose_yaml": "version: '3.8'\nservices:\n  service1:\n    image: image1:latest\n    ports:\n      - '8080:80'"
}
```

### get-logs
Retrieves logs from a specific container
```json
{
    "container_name": "my-container"
}
```

### list-containers
Lists all Docker containers
```json
{}
```

## 🚧 Current Limitations

- No built-in environment variable support for containers
- No volume management
- No network management
- No container health checks
- No container restart policies
- No container resource limits

## 🤝 Contributing

1. Fork the repository from [docker-mcp](https://github.com/QuantGeekDev/docker-mcp)
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ✨ Authors

- **Alex Andru** - *Initial work | Core contributor* - [@QuantGeekDev](https://github.com/QuantGeekDev)
- **Ali Sadykov** - *Initial work  | Core contributor* - [@md-archive](https://github.com/md-archive)

---
Made with ❤️ for the Claude community