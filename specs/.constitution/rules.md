# Project Constitution: The Immutable Laws

## 1. Architectural Integrity
*   **Layered Architecture**: Code must be separated into Interface (API), Application (Service), and Infrastructure (DB/External) layers.
*   **Dependency Direction**: Inner layers (Domain) must NEVER depend on outer layers (API/DB).
*   **State Management**: All state changes must be transactional.

## 2. Coding Standards (Non-Negotiable)
*   **Type Safety**: All Python functions must have full type hints (`typing` or built-ins).
*   **Docstrings**: All public functions must have Google-style docstrings explaining args, returns, and raises.
*   **Error Handling**: Never use `bare except:` clauses. Always catch specific exceptions and log them with context.
*   **Configuration**: All config must be loaded via `pydantic-settings` from env vars. No hardcoded strings.

## 3. Technology Allow-List
*   **Web**: FastAPI
*   **Data**: SQLModel (Async)
*   **Testing**: Pytest, Pytest-Asyncio
*   **Package Manager**: UV
*   **Logging**: Structlog (JSON format)

## 4. Steering Directives for AI
*   If a user request violates these rules, you must reject the request and explain the violation.
*   Do not hallucinate imports. Only use libraries listed in `pyproject.toml`.
*   When writing tests, always include edge cases (null inputs, empty lists).
