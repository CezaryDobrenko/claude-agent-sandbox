## Local Development

`uv init` — initialize a new Python project and create the base `pyproject.toml` file.

`uv sync` — create or update the virtual environment and install dependencies from the lockfile.

`uv lock` — update the `uv.lock` file based on the current project dependencies.

`uv add <package>` — add a new dependency to the project and update `pyproject.toml` and `uv.lock`.

## Setup

`make build name=ai-agent-sandbox` — build the Docker image and tag it with the provided image name.

`make start image=ai-agent-sandbox container=ai-agent-container port=8001` — start the application container using the selected image, container name, and host port.

`make stop container=ai-agent-container` — stop the running container with the provided container name.

`make logs container=ai-agent-container` — display logs from the selected container.

`make list` — list all currently running Docker containers.

## Communication

Go to [http://localhost:8001/docs](http://localhost:8001/docs) and start chatting via /agent/run endpoint
