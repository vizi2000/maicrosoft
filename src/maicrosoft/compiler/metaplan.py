"""Meta-Plan Compiler - generates full application from declarative YAML.

Reads meta-plan.yaml and generates:
- FastAPI backend (models, routers, services)
- React frontend (components, pages, stores)
- Deployment files (docker, nginx)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


class MetaPlanCompiler:
    """Compiles meta-plan.yaml to full application code."""

    def __init__(self, meta_plan_path: str):
        """Load meta-plan from YAML file."""
        with open(meta_plan_path) as f:
            self.plan = yaml.safe_load(f)
        self.output_dir = Path(meta_plan_path).parent

    def compile(self) -> dict[str, list[str]]:
        """Compile full application. Returns dict of generated files."""
        generated = {"backend": [], "frontend": [], "deployment": []}

        # Generate backend
        generated["backend"].extend(self._generate_backend())

        # Generate frontend
        generated["frontend"].extend(self._generate_frontend())

        # Generate deployment
        generated["deployment"].extend(self._generate_deployment())

        return generated

    def _generate_backend(self) -> list[str]:
        """Generate FastAPI backend."""
        files = []
        backend_dir = self.output_dir / "backend" / "src"
        backend_dir.mkdir(parents=True, exist_ok=True)

        # main.py
        files.append(self._write_main_py(backend_dir))

        # config.py
        files.append(self._write_config_py(backend_dir))

        # database.py
        files.append(self._write_database_py(backend_dir))

        # models/
        files.extend(self._generate_models(backend_dir))

        # routers/
        files.extend(self._generate_routers(backend_dir))

        # services/
        files.extend(self._generate_services(backend_dir))

        # middleware/
        files.extend(self._generate_middleware(backend_dir))

        # requirements.txt
        files.append(self._write_requirements(self.output_dir / "backend"))

        return files

    def _write_main_py(self, backend_dir: Path) -> str:
        """Generate main.py FastAPI app."""
        api_config = self.plan.get("api", {})
        prefix = api_config.get("prefix", "/api")

        routers = list(api_config.keys())
        routers = [r for r in routers if r != "prefix"]

        router_imports = "\n".join(
            f"from routers.{r} import router as {r}_router" for r in routers
        )
        router_includes = "\n".join(
            f'app.include_router({r}_router, prefix="{prefix}/{r}", tags=["{r}"])'
            for r in routers
        )

        content = f'''"""Maicrosoft GUI - FastAPI Backend.

Auto-generated from meta-plan.yaml
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base

{router_imports}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="{self.plan['metadata']['name']}",
    version="{self.plan['metadata']['version']}",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
{router_includes}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {{"status": "healthy", "version": "{self.plan['metadata']['version']}"}}
'''
        path = backend_dir / "main.py"
        path.write_text(content)
        return str(path)

    def _write_config_py(self, backend_dir: Path) -> str:
        """Generate config.py with settings."""
        stack = self.plan.get("stack", {}).get("backend", {})

        content = '''"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment."""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/maicrosoft"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # N8N
    n8n_api_url: str = "http://localhost:5678/api/v1"
    n8n_api_key: str = ""

    # Encryption
    encryption_key: str = "change-me-32-bytes-key-here!!"

    # Agent Zero MCP
    agent_zero_mcp_url: str = "http://194.181.240.37:50001/mcp/t-T7kevcXi6oDxfrhK/http"

    class Config:
        env_file = ".env"


settings = Settings()
'''
        path = backend_dir / "config.py"
        path.write_text(content)
        return str(path)

    def _write_database_py(self, backend_dir: Path) -> str:
        """Generate database.py with SQLAlchemy setup."""
        content = '''"""Database configuration and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import settings


engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency for database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
'''
        path = backend_dir / "database.py"
        path.write_text(content)
        return str(path)

    def _generate_models(self, backend_dir: Path) -> list[str]:
        """Generate SQLAlchemy models from meta-plan."""
        models_dir = backend_dir / "models"
        models_dir.mkdir(exist_ok=True)

        files = []
        models = self.plan.get("models", {})

        # __init__.py
        init_content = '"""Database models."""\n\n'
        for model_name in models:
            init_content += f"from .{model_name.lower()} import {model_name}\n"

        init_path = models_dir / "__init__.py"
        init_path.write_text(init_content)
        files.append(str(init_path))

        # Individual model files
        for model_name, model_def in models.items():
            content = self._generate_model_file(model_name, model_def)
            path = models_dir / f"{model_name.lower()}.py"
            path.write_text(content)
            files.append(str(path))

        return files

    def _generate_model_file(self, name: str, definition: dict) -> str:
        """Generate single model file."""
        fields = definition.get("fields", {})
        table_name = definition.get("table", name.lower() + "s")

        imports = set()
        imports.add("from sqlalchemy import Column")
        imports.add("from database import Base")

        column_lines = []
        for field_name, field_def in fields.items():
            col_type, extra_imports = self._map_field_type(field_def)
            imports.update(extra_imports)

            constraints = []
            if field_def.get("primary"):
                constraints.append("primary_key=True")
            if field_def.get("unique"):
                constraints.append("unique=True")
            if field_def.get("required"):
                constraints.append("nullable=False")
            if "default" in field_def:
                default = field_def["default"]
                if default == "now":
                    constraints.append("server_default=func.now()")
                    imports.add("from sqlalchemy import func")
                elif default == "gen_random_uuid":
                    constraints.append("server_default=func.gen_random_uuid()")
                    imports.add("from sqlalchemy import func")
                else:
                    constraints.append(f"default={repr(default)}")
            if "ref" in field_def:
                ref_table = field_def["ref"].split(".")[0].lower() + "s"
                ref_col = field_def["ref"].split(".")[1]
                constraints.append(f'ForeignKey("{ref_table}.{ref_col}")')
                imports.add("from sqlalchemy import ForeignKey")
                if field_def.get("on_delete"):
                    constraints[-1] = constraints[-1].replace(
                        ")",
                        f', ondelete="{field_def["on_delete"].upper()}")'
                    )

            constraint_str = ", ".join(constraints)
            if constraint_str:
                column_lines.append(f"    {field_name} = Column({col_type}, {constraint_str})")
            else:
                column_lines.append(f"    {field_name} = Column({col_type})")

        imports_str = "\n".join(sorted(imports))
        columns_str = "\n".join(column_lines)

        return f'''"""{name} model."""

{imports_str}


class {name}(Base):
    """SQLAlchemy model for {table_name}."""

    __tablename__ = "{table_name}"

{columns_str}
'''

    def _map_field_type(self, field_def: dict) -> tuple[str, set[str]]:
        """Map meta-plan field type to SQLAlchemy type."""
        imports = set()
        field_type = field_def.get("type", "string")

        type_map = {
            "uuid": ("UUID(as_uuid=True)", {"from sqlalchemy.dialects.postgresql import UUID"}),
            "string": (f"String({field_def.get('max', 255)})", {"from sqlalchemy import String"}),
            "text": ("Text", {"from sqlalchemy import Text"}),
            "integer": ("Integer", {"from sqlalchemy import Integer"}),
            "boolean": ("Boolean", {"from sqlalchemy import Boolean"}),
            "timestamp": ("DateTime(timezone=True)", {"from sqlalchemy import DateTime"}),
            "jsonb": ("JSONB", {"from sqlalchemy.dialects.postgresql import JSONB"}),
            "bytes": ("LargeBinary", {"from sqlalchemy import LargeBinary"}),
            "array": ("ARRAY(String)", {"from sqlalchemy.dialects.postgresql import ARRAY", "from sqlalchemy import String"}),
        }

        if field_type == "enum":
            values = field_def.get("values", [])
            values_str = ", ".join(f"'{v}'" for v in values)
            imports.add("from sqlalchemy import Enum")
            return f"Enum({values_str}, name='{field_def.get('name', 'enum_type')}')", imports

        if field_type in type_map:
            col_type, type_imports = type_map[field_type]
            imports.update(type_imports)
            return col_type, imports

        return "String(255)", {"from sqlalchemy import String"}

    def _generate_routers(self, backend_dir: Path) -> list[str]:
        """Generate FastAPI routers from API definition."""
        routers_dir = backend_dir / "routers"
        routers_dir.mkdir(exist_ok=True)

        files = []
        api = self.plan.get("api", {})

        # __init__.py
        init_path = routers_dir / "__init__.py"
        init_path.write_text('"""API routers."""\n')
        files.append(str(init_path))

        for router_name, router_def in api.items():
            if router_name == "prefix":
                continue

            content = self._generate_router_file(router_name, router_def)
            path = routers_dir / f"{router_name}.py"
            path.write_text(content)
            files.append(str(path))

        return files

    def _generate_router_file(self, name: str, definition: dict) -> str:
        """Generate single router file."""
        routes = definition.get("routes", [])
        websocket = definition.get("websocket", [])

        imports = [
            "from fastapi import APIRouter, Depends, HTTPException, status",
            "from sqlalchemy.ext.asyncio import AsyncSession",
            "from database import get_db",
        ]

        if websocket:
            imports.append("from fastapi import WebSocket")

        route_handlers = []
        for route in routes:
            handler = self._generate_route_handler(route)
            route_handlers.append(handler)

        for ws in websocket:
            handler = self._generate_websocket_handler(ws)
            route_handlers.append(handler)

        return f'''"""{name.title()} router."""

{chr(10).join(imports)}

router = APIRouter()

{chr(10).join(route_handlers)}
'''

    def _generate_route_handler(self, route: dict) -> str:
        """Generate single route handler."""
        path = route.get("path", "/")
        method = route.get("method", "GET").lower()
        handler_name = route.get("handler", "handler")
        is_public = route.get("public", False)

        decorator = f'@router.{method}("{path}")'

        # Simplified handler - actual logic would be in services
        return f'''{decorator}
async def {handler_name}(db: AsyncSession = Depends(get_db)):
    """Handler for {method.upper()} {path}."""
    # TODO: Implement {handler_name}
    return {{"message": "Not implemented"}}

'''

    def _generate_websocket_handler(self, ws: dict) -> str:
        """Generate WebSocket handler."""
        path = ws.get("path", "/ws")
        handler_name = ws.get("handler", "websocket_handler")

        return f'''@router.websocket("{path}")
async def {handler_name}(websocket: WebSocket):
    """WebSocket handler for {path}."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # TODO: Implement {handler_name}
            await websocket.send_json({{"status": "received"}})
    except Exception:
        pass

'''

    def _generate_services(self, backend_dir: Path) -> list[str]:
        """Generate service files."""
        services_dir = backend_dir / "services"
        services_dir.mkdir(exist_ok=True)

        files = []

        # __init__.py
        init_path = services_dir / "__init__.py"
        init_path.write_text('"""Business logic services."""\n')
        files.append(str(init_path))

        # maicrosoft_bridge.py
        bridge_content = '''"""Bridge to Maicrosoft core library."""

import sys
from pathlib import Path

# Add maicrosoft to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

from maicrosoft.registry import PrimitiveRegistry
from maicrosoft.validation import PlanValidator
from maicrosoft.compiler import N8NCompiler
from maicrosoft.llm import LLMOrchestrator


class MaicrosoftBridge:
    """Bridge to Maicrosoft core functionality."""

    def __init__(self, primitives_path: str = "primitives"):
        self.registry = PrimitiveRegistry(primitives_path)
        self.validator = PlanValidator(self.registry)
        self.compiler = N8NCompiler(self.registry)
        self.orchestrator = LLMOrchestrator(self.registry)

    def list_primitives(self, category: str = None, status: str = "stable"):
        """List available primitives."""
        return self.registry.list(category=category, status=status)

    def get_primitive(self, primitive_id: str):
        """Get primitive by ID."""
        return self.registry.get(primitive_id)

    def validate_plan(self, plan_data: dict):
        """Validate a plan."""
        from maicrosoft.core.models import Plan
        plan = Plan.model_validate(plan_data)
        return self.validator.validate(plan)

    def compile_plan(self, plan_data: dict):
        """Compile plan to N8N workflow."""
        from maicrosoft.core.models import Plan
        plan = Plan.model_validate(plan_data)
        return self.compiler.compile(plan)

    def search_primitives(self, query: str, limit: int = 5):
        """Search primitives by query."""
        return self.orchestrator.search_primitives(query, limit)


# Singleton instance
bridge = MaicrosoftBridge()
'''
        bridge_path = services_dir / "maicrosoft_bridge.py"
        bridge_path.write_text(bridge_content)
        files.append(str(bridge_path))

        # secret_manager.py
        secret_content = '''"""Secret management with AES-256-GCM encryption."""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import settings


class SecretManager:
    """Manages encrypted secrets."""

    def __init__(self):
        key = settings.encryption_key.encode()
        if len(key) < 32:
            key = key.ljust(32, b"0")
        self.aesgcm = AESGCM(key[:32])

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt a secret value."""
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        return nonce + ciphertext

    def decrypt(self, encrypted: bytes) -> str:
        """Decrypt a secret value."""
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()


secret_manager = SecretManager()
'''
        secret_path = services_dir / "secret_manager.py"
        secret_path.write_text(secret_content)
        files.append(str(secret_path))

        # agent_zero_client.py
        agent_content = '''"""Client for Agent Zero MCP integration."""

import httpx

from config import settings


class AgentZeroClient:
    """Client for Agent Zero MCP API."""

    def __init__(self):
        self.mcp_url = settings.agent_zero_mcp_url

    async def analyze_github_repo(self, repo_url: str, branch: str = "main") -> dict:
        """
        Analyze a GitHub repository for primitives-first conversion.

        Returns analysis report with:
        - benefits: list of benefits from conversion
        - current_architecture: analysis of current code
        - suggested_plan: Maicrosoft plan YAML
        - coverage_estimate: percentage of code covered by primitives
        - gaps: list of functionality gaps
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.mcp_url,
                json={
                    "method": "analyze_repository",
                    "params": {
                        "repo_url": repo_url,
                        "branch": branch,
                        "analysis_type": "primitives_conversion",
                    }
                }
            )
            response.raise_for_status()
            return response.json()


agent_zero = AgentZeroClient()
'''
        agent_path = services_dir / "agent_zero_client.py"
        agent_path.write_text(agent_content)
        files.append(str(agent_path))

        return files

    def _generate_middleware(self, backend_dir: Path) -> list[str]:
        """Generate middleware files."""
        middleware_dir = backend_dir / "middleware"
        middleware_dir.mkdir(exist_ok=True)

        files = []

        # __init__.py
        init_path = middleware_dir / "__init__.py"
        init_path.write_text('"""Middleware."""\n')
        files.append(str(init_path))

        # auth.py
        auth_content = '''"""JWT authentication middleware."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": user_id, "role": payload.get("role", "viewer")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
'''
        auth_path = middleware_dir / "auth.py"
        auth_path.write_text(auth_content)
        files.append(str(auth_path))

        # rbac.py
        rbac_content = '''"""Role-based access control middleware."""

from functools import wraps
from fastapi import HTTPException, status


ROLE_HIERARCHY = {
    "admin": 4,
    "owner": 3,
    "editor": 2,
    "viewer": 1,
}


def require_role(allowed_roles: list[str]):
    """Decorator to require specific roles."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict = None, **kwargs):
            if not current_user:
                raise HTTPException(status_code=401, detail="Not authenticated")

            user_role = current_user.get("role", "viewer")
            if user_role not in allowed_roles and user_role != "admin":
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def can_access(user_role: str, required_roles: list[str]) -> bool:
    """Check if user role can access resource."""
    if user_role == "admin":
        return True
    return user_role in required_roles
'''
        rbac_path = middleware_dir / "rbac.py"
        rbac_path.write_text(rbac_content)
        files.append(str(rbac_path))

        return files

    def _write_requirements(self, backend_dir: Path) -> str:
        """Generate requirements.txt."""
        content = '''# Maicrosoft GUI Backend Dependencies

# FastAPI
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6

# Database
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Settings
pydantic-settings>=2.1.0

# HTTP client
httpx>=0.26.0

# Encryption
cryptography>=42.0.0

# Redis
redis>=5.0.0

# Maicrosoft core deps (already installed)
pyyaml>=6.0.0
'''
        path = backend_dir / "requirements.txt"
        path.write_text(content)
        return str(path)

    def _generate_frontend(self) -> list[str]:
        """Generate React frontend."""
        files = []
        frontend_dir = self.output_dir / "frontend"
        frontend_dir.mkdir(parents=True, exist_ok=True)

        # package.json
        files.append(self._write_package_json(frontend_dir))

        # vite.config.ts
        files.append(self._write_vite_config(frontend_dir))

        # tailwind.config.js
        files.append(self._write_tailwind_config(frontend_dir))

        # index.html
        files.append(self._write_index_html(frontend_dir))

        # src/
        src_dir = frontend_dir / "src"
        src_dir.mkdir(exist_ok=True)

        files.append(self._write_main_tsx(src_dir))
        files.append(self._write_app_tsx(src_dir))
        files.append(self._write_index_css(src_dir))

        # stores/
        files.extend(self._generate_stores(src_dir))

        # api/
        files.extend(self._generate_api_client(src_dir))

        # components/ (basic structure)
        files.extend(self._generate_component_structure(src_dir))

        return files

    def _write_package_json(self, frontend_dir: Path) -> str:
        """Generate package.json."""
        content = '''{
  "name": "maicrosoft-gui",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "@xyflow/react": "^12.0.0",
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.0",
    "@headlessui/react": "^1.7.0",
    "@heroicons/react": "^2.1.0",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
'''
        path = frontend_dir / "package.json"
        path.write_text(content)
        return str(path)

    def _write_vite_config(self, frontend_dir: Path) -> str:
        """Generate vite.config.ts."""
        content = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
'''
        path = frontend_dir / "vite.config.ts"
        path.write_text(content)
        return str(path)

    def _write_tailwind_config(self, frontend_dir: Path) -> str:
        """Generate tailwind.config.js."""
        content = '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
}
'''
        path = frontend_dir / "tailwind.config.js"
        path.write_text(content)
        return str(path)

    def _write_index_html(self, frontend_dir: Path) -> str:
        """Generate index.html."""
        content = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Maicrosoft GUI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''
        path = frontend_dir / "index.html"
        path.write_text(content)
        return str(path)

    def _write_main_tsx(self, src_dir: Path) -> str:
        """Generate main.tsx."""
        content = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
'''
        path = src_dir / "main.tsx"
        path.write_text(content)
        return str(path)

    def _write_app_tsx(self, src_dir: Path) -> str:
        """Generate App.tsx with routing."""
        pages = self.plan.get("pages", [])

        route_imports = []
        route_elements = []

        for page in pages:
            component = page.get("component", "Dashboard")
            path = page.get("path", "/")
            route_imports.append(f"import {component} from './pages/{component}'")
            route_elements.append(f'      <Route path="{path}" element={{<{component} />}} />')

        content = f'''import {{ Routes, Route }} from 'react-router-dom'
import Layout from './components/shared/Layout'

// Pages
{chr(10).join(route_imports)}

function App() {{
  return (
    <Layout>
      <Routes>
{chr(10).join(route_elements)}
      </Routes>
    </Layout>
  )
}}

export default App
'''
        path = src_dir / "App.tsx"
        path.write_text(content)
        return str(path)

    def _write_index_css(self, src_dir: Path) -> str:
        """Generate index.css with Tailwind."""
        content = '''@tailwind base;
@tailwind components;
@tailwind utilities;

/* React Flow styles */
.react-flow__node {
  @apply rounded-lg shadow-md;
}

.react-flow__edge-path {
  @apply stroke-gray-400 stroke-2;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  @apply bg-gray-100;
}

::-webkit-scrollbar-thumb {
  @apply bg-gray-300 rounded;
}
'''
        path = src_dir / "index.css"
        path.write_text(content)
        return str(path)

    def _generate_stores(self, src_dir: Path) -> list[str]:
        """Generate Zustand stores."""
        stores_dir = src_dir / "stores"
        stores_dir.mkdir(exist_ok=True)

        files = []

        # workflowStore.ts
        workflow_content = '''import { create } from 'zustand'
import { Node, Edge, addEdge, applyNodeChanges, applyEdgeChanges } from '@xyflow/react'

interface WorkflowState {
  nodes: Node[]
  edges: Edge[]
  selectedNode: Node | null
  setNodes: (nodes: Node[]) => void
  setEdges: (edges: Edge[]) => void
  onNodesChange: (changes: any) => void
  onEdgesChange: (changes: any) => void
  onConnect: (connection: any) => void
  selectNode: (node: Node | null) => void
  addNode: (node: Node) => void
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNode: null,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  onNodesChange: (changes) => {
    set({ nodes: applyNodeChanges(changes, get().nodes) })
  },

  onEdgesChange: (changes) => {
    set({ edges: applyEdgeChanges(changes, get().edges) })
  },

  onConnect: (connection) => {
    set({ edges: addEdge(connection, get().edges) })
  },

  selectNode: (node) => set({ selectedNode: node }),

  addNode: (node) => set({ nodes: [...get().nodes, node] }),
}))
'''
        workflow_path = stores_dir / "workflowStore.ts"
        workflow_path.write_text(workflow_content)
        files.append(str(workflow_path))

        # authStore.ts
        auth_content = '''import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  name: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  setAuth: (user: User, token: string) => void
  logout: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,

      setAuth: (user, token) => set({ user, token }),

      logout: () => set({ user: null, token: null }),

      isAuthenticated: () => !!get().token,
    }),
    { name: 'auth-storage' }
  )
)
'''
        auth_path = stores_dir / "authStore.ts"
        auth_path.write_text(auth_content)
        files.append(str(auth_path))

        return files

    def _generate_api_client(self, src_dir: Path) -> list[str]:
        """Generate API client."""
        api_dir = src_dir / "api"
        api_dir.mkdir(exist_ok=True)

        files = []

        content = '''import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const api = axios.create({
  baseURL: '/api',
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API functions
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string, name: string) =>
    api.post('/auth/register', { email, password, name }),
  me: () => api.get('/auth/me'),
}

export const plansApi = {
  list: (params?: { page?: number; limit?: number }) =>
    api.get('/plans', { params }),
  get: (id: string) => api.get(`/plans/${id}`),
  create: (data: { name: string; description?: string }) =>
    api.post('/plans', data),
  update: (id: string, data: any) => api.put(`/plans/${id}`, data),
  delete: (id: string) => api.delete(`/plans/${id}`),
}

export const primitivesApi = {
  list: () => api.get('/primitives'),
  get: (id: string) => api.get(`/primitives/${id}`),
  search: (q: string) => api.get('/primitives/search', { params: { q } }),
}

export const validationApi = {
  validate: (planJson: any) => api.post('/validate', { plan_json: planJson }),
}

export const compileApi = {
  compile: (planJson: any) => api.post('/compile', { plan_json: planJson }),
  preview: (planJson: any) => api.post('/compile/preview', { plan_json: planJson }),
}

export const githubApi = {
  analyze: (repoUrl: string, branch?: string) =>
    api.post('/analyze/github', { repo_url: repoUrl, branch }),
}
'''
        path = api_dir / "client.ts"
        path.write_text(content)
        files.append(str(path))

        return files

    def _generate_component_structure(self, src_dir: Path) -> list[str]:
        """Generate component directory structure with placeholder files."""
        files = []

        components = self.plan.get("components", {})
        pages = self.plan.get("pages", [])

        # Create component directories
        components_dir = src_dir / "components"
        for category in ["workflow", "validation", "secrets", "history", "github", "shared"]:
            cat_dir = components_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)

            # Placeholder index
            index_path = cat_dir / "index.ts"
            index_path.write_text(f'// {category} components\nexport {{}}\n')
            files.append(str(index_path))

        # Create shared Layout component
        layout_content = '''import { ReactNode } from 'react'
import Sidebar from './Sidebar'
import Header from './Header'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
'''
        layout_path = components_dir / "shared" / "Layout.tsx"
        layout_path.write_text(layout_content)
        files.append(str(layout_path))

        # Sidebar
        sidebar_content = '''import { Link, useLocation } from 'react-router-dom'
import {
  HomeIcon,
  BoltIcon,
  DocumentDuplicateIcon,
  ClockIcon,
  KeyIcon,
  CodeBracketIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Workflows', href: '/workflows', icon: BoltIcon },
  { name: 'Templates', href: '/templates', icon: DocumentDuplicateIcon },
  { name: 'Run History', href: '/runs', icon: ClockIcon },
  { name: 'Secrets', href: '/secrets', icon: KeyIcon },
  { name: 'Analyze Repo', href: '/analyze', icon: CodeBracketIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="w-64 bg-gray-900 text-white">
      <div className="p-4">
        <h1 className="text-xl font-bold">Maicrosoft</h1>
        <p className="text-xs text-gray-400">Primitives-First AI</p>
      </div>
      <nav className="mt-4">
        {navigation.map((item) => (
          <Link
            key={item.name}
            to={item.href}
            className={clsx(
              'flex items-center px-4 py-3 text-sm',
              location.pathname === item.href
                ? 'bg-gray-800 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            )}
          >
            <item.icon className="w-5 h-5 mr-3" />
            {item.name}
          </Link>
        ))}
      </nav>
    </div>
  )
}
'''
        sidebar_path = components_dir / "shared" / "Sidebar.tsx"
        sidebar_path.write_text(sidebar_content)
        files.append(str(sidebar_path))

        # Header
        header_content = '''import { useAuthStore } from '../../stores/authStore'

export default function Header() {
  const { user, logout } = useAuthStore()

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="flex items-center justify-between px-6 py-4">
        <div></div>
        <div className="flex items-center gap-4">
          {user && (
            <>
              <span className="text-sm text-gray-600">{user.email}</span>
              <button
                onClick={logout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
'''
        header_path = components_dir / "shared" / "Header.tsx"
        header_path.write_text(header_content)
        files.append(str(header_path))

        # Create pages directory with placeholders
        pages_dir = src_dir / "pages"
        pages_dir.mkdir(exist_ok=True)

        for page in pages:
            component = page.get("component", "Dashboard")
            page_content = f'''export default function {component}() {{
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">{component}</h1>
      <p className="text-gray-600">Page content goes here.</p>
    </div>
  )
}}
'''
            page_path = pages_dir / f"{component}.tsx"
            page_path.write_text(page_content)
            files.append(str(page_path))

        return files

    def _generate_deployment(self) -> list[str]:
        """Generate deployment files."""
        files = []

        # docker-compose.yml
        compose_content = '''version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/maicrosoft
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=maicrosoft
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=admin
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  postgres_data:
  n8n_data:
'''
        compose_path = self.output_dir / "docker-compose.yml"
        compose_path.write_text(compose_content)
        files.append(str(compose_path))

        # Backend Dockerfile
        backend_dockerfile = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        backend_docker_path = self.output_dir / "backend" / "Dockerfile"
        backend_docker_path.parent.mkdir(parents=True, exist_ok=True)
        backend_docker_path.write_text(backend_dockerfile)
        files.append(str(backend_docker_path))

        # Frontend Dockerfile
        frontend_dockerfile = '''FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
'''
        frontend_docker_path = self.output_dir / "frontend" / "Dockerfile"
        frontend_docker_path.parent.mkdir(parents=True, exist_ok=True)
        frontend_docker_path.write_text(frontend_dockerfile)
        files.append(str(frontend_docker_path))

        # nginx.conf
        nginx_content = '''server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
'''
        nginx_path = self.output_dir / "frontend" / "nginx.conf"
        nginx_path.write_text(nginx_content)
        files.append(str(nginx_path))

        # .env.example
        env_content = '''# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/maicrosoft

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-super-secret-key-change-in-production

# Encryption
ENCRYPTION_KEY=32-bytes-encryption-key-here!!

# N8N
N8N_API_URL=http://localhost:5678/api/v1
N8N_API_KEY=your-n8n-api-key

# Agent Zero
AGENT_ZERO_MCP_URL=http://194.181.240.37:50001/mcp/t-T7kevcXi6oDxfrhK/http

# OAuth (optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
'''
        env_path = self.output_dir / ".env.example"
        env_path.write_text(env_content)
        files.append(str(env_path))

        return files


def compile_meta_plan(meta_plan_path: str) -> dict[str, list[str]]:
    """Compile meta-plan to full application."""
    compiler = MetaPlanCompiler(meta_plan_path)
    return compiler.compile()
