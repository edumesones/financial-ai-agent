# Contributing to Financial AI Agent

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## 🚀 Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/edumesones/financial-ai-agent.git
   cd financial-ai-agent
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   # Start infrastructure
   docker-compose up -d
   
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -r backend/requirements.txt
   
   # Run migrations
   cd backend
   alembic upgrade head
   ```

## 📝 Development Workflow

### 1. Code Style

We use:
- **Black** for Python formatting
- **Ruff** for linting
- **mypy** for type checking

```bash
# Format code
black backend/app/

# Lint
ruff check backend/app/

# Type check
mypy backend/app/
```

### 2. Testing

```bash
# Run all tests
pytest backend/tests/

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest backend/tests/test_agents.py::test_clasificacion_agent
```

### 3. Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add fuzzy matching to reconciliation agent
fix: resolve bcrypt installation issue on Windows
docs: update ARCHITECTURE.md with caching strategy
test: add integration tests for classification
chore: update dependencies
```

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── api/v1/         # REST endpoints
│   ├── agents/         # LangGraph agents
│   ├── core/           # Config, DB, Security
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # External services (HF, parsers)
│   └── tasks/          # Celery tasks
├── tests/              # Unit & integration tests
└── alembic/            # Database migrations
```

## 🧪 Adding New Features

### Example: Adding a New Agent

1. **Create agent file**: `backend/app/agents/new_agent.py`
   ```python
   from langgraph.graph import StateGraph
   from .base import BaseAgent, AgentState
   
   class NewAgentState(AgentState):
       # Define agent-specific state fields
       pass
   
   class NewAgent(BaseAgent):
       def build_graph(self) -> StateGraph:
           graph = StateGraph(NewAgentState)
           # Define nodes and edges
           return graph
   ```

2. **Add tests**: `backend/tests/test_new_agent.py`
   ```python
   import pytest
   from app.agents.new_agent import NewAgent
   
   @pytest.mark.asyncio
   async def test_new_agent():
       agent = NewAgent(db, hf_service)
       result = await agent.run(initial_state)
       assert result["status"] == "completed"
   ```

3. **Add endpoint**: `backend/app/api/v1/new_endpoint.py`
   ```python
   from fastapi import APIRouter
   from app.agents.new_agent import NewAgent
   
   router = APIRouter(prefix="/new", tags=["new"])
   
   @router.post("/")
   async def execute_new_agent(...):
       agent = NewAgent(db, hf_service)
       return await agent.run(state)
   ```

4. **Update docs**: Add to `docs/ARCHITECTURE.md`

## 🔍 Code Review Guidelines

When reviewing PRs, check for:
- ✅ Tests pass (`pytest`)
- ✅ Linting passes (`ruff`, `black`)
- ✅ Type checks pass (`mypy`)
- ✅ Documentation updated
- ✅ No secrets in code
- ✅ Performance considerations
- ✅ Security implications

## 🐛 Reporting Bugs

Include:
1. **Description**: What happened?
2. **Steps to reproduce**: How can we replicate it?
3. **Expected behavior**: What should happen?
4. **Environment**: OS, Python version, dependencies
5. **Logs**: Relevant error messages

Example:
```markdown
## Bug: Classification fails for transactions > 100 characters

**Steps**:
1. Upload CSV with long descriptions
2. Run classification endpoint
3. Error: `ValueError: Input too long`

**Environment**:
- OS: Windows 10
- Python: 3.11.12
- FastAPI: 0.109.0

**Logs**:
```
ERROR: Unhandled exception in classify_transaction
ValueError: Input exceeds 512 tokens
```
```

## 💡 Feature Requests

Include:
1. **Problem**: What problem does this solve?
2. **Solution**: How would it work?
3. **Alternatives**: Other approaches considered?
4. **Impact**: Who benefits? How much?

## 📋 Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Run full test suite**: `pytest`
4. **Check linting**: `ruff check` and `black --check`
5. **Update CHANGELOG.md** (if applicable)
6. **Request review** from maintainers

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Added unit tests
- [ ] Added integration tests
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

## 🌟 Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Credited in documentation

## 📄 License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

**Questions?** Open an issue or email: e.gzlzmesones@gmail.com

