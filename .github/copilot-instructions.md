# GitHub Copilot Instructions for RAG CHAT AI Foundry

## Project Overview

RAG CHAT AI Foundry is a  python project to create a RAG (Retrieval-Augmented Generation) system allowing to upload docs and select models. 
The project is designed for extensibility and cloud-native deployment.

## Project Structure

- `infra/` — Infrastructure as Code (IaC) using **Bicep** (always use Bicep for Azure infra):
  - `main.bicep`, `main.parameters.json`, and `modules/` for modular Azure resource definitions (App Insights, Log Analytics, RBAC, etc.)
- `src/` — All service code, organized by microservice:
  - `rag_chat/` — Main agent logic, Chainlit integration, enhanced agent, and configuration.
  - Each service has its own `Dockerfile`, `pyproject.toml`, and `README.md`.
- `azure.yaml` — Azure Developer CLI project configuration.
- `README.md` — Project documentation and usage.

## Infra as Code Guidelines

- **Always use Bicep** for Azure infrastructure. Do not use ARM, Terraform, or manual portal steps.
- Prefer modular Bicep files for reusable resources (see `infra/modules/`).
- Use parameters and outputs for environment-specific values.
- Use Azure Container Apps for microservice deployment.
- Use Managed Identity for authentication where possible.
- Configure RBAC with least privilege.

## Python Coding Best Practices

- Use Python 3.11+ features (type hints, dataclasses, etc.).
- Use `httpx.AsyncClient` for all HTTP requests.
- Use the provided `logger` for all log messages at `INFO` level or above.
- Always handle exceptions for network/API calls and return user-friendly errors.
- Use constants for API base URLs, endpoints, and headers.
- Keep functions small, focused, and documented with docstrings.
- Prefer list comprehensions for formatting lists of results.
- Avoid hardcoding values except for configuration and endpoints.
- Reuse existing code and utilities—**analyze the codebase before generating new code**.
- Follow the structure: main entrypoint files (`main.py`) should only start the server; service logic goes in dedicated modules (e.g., `weather.py`).
- using `uv` for managing dependencies and virtual environments is recommended.

## Code Generation & Reuse

- **Before generating new code, always analyze the codebase to reuse or extend existing functions, classes, or utilities.**
- Refactor and extend rather than duplicate logic.
- Use clear, descriptive names for new functions and variables.
- Add or update docstrings and comments as needed.

## Azure Guidelines

- Use Bicep for all Azure deployments.
- Use Azure Container Apps for microservices.
- Use Managed Identity and RBAC best practices.
- When generating code or scripts for Azure, follow Azure and Python best practices.

## Dev Container Notes

- The dev container includes Python, Chainlit, Docker, Azure CLI, and all required dependencies.
- Use `"$BROWSER" <url>` to open web pages from the terminal.

## Git Commit Guidelines

- Use clear, descriptive commit messages.
- Follow the format: `type(scope): subject` (e.g., `feat(setlist-agent): add new setlist retrieval feature`).
- types include `feat`, `fix`, `docs`, `style`, `refactor`, `test`, and `chore`.

## Contact

For questions or issues, see the project `README.md` or contact the maintainer.
