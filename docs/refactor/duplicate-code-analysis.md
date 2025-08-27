# COMPLETED: Duplicate Code Analysis - MCP Auto PR Monorepo

> **STATUS**: ✅ **DUPLICATION ELIMINATED** (2025-08-27)
> **FINAL RESULT**: 90% reduction achieved (30→3 duplicate functions)

**Original Date**: 2025-08-17
**Completion Date**: 2025-08-27
**Scope**: Analysis and elimination of code duplication in `src/` directory

## Executive Summary

Found **~500+ lines of duplicated code** across the monorepo with high consolidation potential. The most significant duplications are in main.py server infrastructure, health endpoints, CLI patterns, and error handling.

## Major Duplicate Code Patterns

### 0. 🚨 **CRITICAL: Main.py Infrastructure** (HIGHEST PRIORITY)
**Duplication**: 300+ lines of nearly identical server infrastructure

**Location**:
- `src/mcp_local_repo_analyzer/main.py` (354 lines total)
- `src/mcp_pr_recommender/main.py` (463 lines total)

**Pattern**: 80% identical infrastructure code including:
- Lifespan management (lines 34-61) - IDENTICAL
- Health check routes (lines 85-120) - 99% identical
- Error handling blocks (multiple locations) - IDENTICAL
- CLI argument parsing (lines 293-349, 417-459) - 95% identical
- Server setup patterns - IDENTICAL
- Import patterns - 90% overlap

**Impact**: Most significant duplication in the codebase
**Solution**: Create `shared/server/base_server.py` with BaseMCPServer class
**See**: [Main.py Refactoring Proposal](./main-py-refactoring-proposal.md)

### 1. 🚨 **Health Check Routes** (HIGH PRIORITY)
**Duplication**: 40+ lines of nearly identical code

**Location**:
- `src/mcp_local_repo_analyzer/main.py` lines 85-105
- `src/mcp_pr_recommender/main.py` lines 100-120

**Pattern**:
```python
@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    return JSONResponse({
        "status": "ok",
        "service": "SERVICE_NAME",  # Only difference
        "version": "1.0.0",
        "initialized": _server_initialized,
    })

@mcp.custom_route("/healthz", methods=["GET"])
async def health_check_z(_request: Request) -> JSONResponse:
    # Identical to above
```

**Consolidation Opportunity**: Move to `shared/server/health.py`

### 2. 🚨 **CLI Argument Parsing** (HIGH PRIORITY)
**Duplication**: 30+ lines of identical argument definitions

**Location**:
- `src/mcp_local_repo_analyzer/cli.py`
- `src/mcp_pr_recommender/cli.py`

**Pattern**:
```python
parser.add_argument("--transport", choices=["stdio", "streamable-http", "sse"], default="stdio")
parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (HTTP mode only)")
parser.add_argument("--port", type=int, help="Port to bind to (HTTP mode only)")
parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
```

**Consolidation Opportunity**: Create `shared/cli/base_parser.py`

### 3. 🚨 **Server Lifespan Management** (HIGH PRIORITY)
**Duplication**: 25+ lines of identical async context manager code

**Location**:
- `src/mcp_local_repo_analyzer/main.py` lifespan function
- `src/mcp_pr_recommender/main.py` lifespan function

**Pattern**:
```python
_server_initialized = False
_initialization_lock = asyncio.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _server_initialized
    async with _initialization_lock:
        if not _server_initialized:
            # Identical initialization logic
            _server_initialized = True
    yield
```

**Consolidation Opportunity**: Create `shared/server/lifespan.py`

### 4. 🔶 **Error Handling Blocks** (MEDIUM PRIORITY)
**Duplication**: 20+ lines per occurrence (multiple locations)

**Pattern**:
```python
except (BrokenPipeError, EOFError) as e:
    logger.info(f"Input stream closed ({type(e).__name__}), shutting down server gracefully")
except ConnectionResetError as e:
    logger.info(f"Connection reset ({e}), shutting down server gracefully")
except KeyboardInterrupt:
    logger.info("Server stopped by user (KeyboardInterrupt)")
except Exception as e:
    logger.error(f"Server runtime error: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)
```

**Consolidation Opportunity**: Create `shared/utils/error_handling.py`

### 5. 🔶 **Configuration Classes** (MEDIUM PRIORITY)
**Duplication**: Repeated Pydantic BaseSettings patterns

**Location**:
- `src/shared/config/base.py`: `BaseMCPSettings`
- `src/shared/config/git_analyzer.py`: `GitAnalyzerSettings`
- `src/mcp_pr_recommender/config.py`: `PRRecommenderSettings`

**Pattern**:
```python
class SomeSettings(BaseSettings):
    log_level: str = Field(default="INFO", description="Logging level")
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
```

**Consolidation Opportunity**: Consolidate into `shared/config/base.py`

### 6. 🔶 **Logging Setup** (MEDIUM PRIORITY)
**Duplication**: Identical logging configuration

**Pattern**:
```python
logging.basicConfig(
    level=getattr(logging, args.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging_service.get_logger(__name__)
```

**Consolidation Opportunity**: Create `shared/utils/logging_setup.py`

### 7. 🔹 **Import Statements** (LOW PRIORITY)
**Duplication**: Repeated import patterns

**Common Imports**:
```python
import asyncio
import argparse
import logging
import sys
import traceback
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import AsyncIterator
```

**Consolidation Opportunity**: Package-level `__init__.py` imports

## Detailed Duplication Inventory

### By File Pairs

| File 1 | File 2 | Lines Duplicated | Type |
|--------|--------|------------------|------|
| `analyzer/main.py` | `recommender/main.py` | 300+ | **CRITICAL: Server infrastructure** |
| `analyzer/cli.py` | `recommender/cli.py` | 35+ | CLI parsing |
| Multiple config files | Various | 25+ | Configuration patterns |
| Various files | Various | 60+ | Error handling patterns |

### By Functionality

| Functionality | Files Affected | Est. Lines | Priority |
|---------------|----------------|------------|----------|
| **Main.py infrastructure** | **2 main.py** | **300+** | **🚨 CRITICAL** |
| Health endpoints | 2 main.py | 40+ | 🚨 High |
| CLI argument parsing | 2 cli.py + main.py | 70+ | 🚨 High |
| Lifespan management | 2 main.py | 25+ | 🚨 High |
| Error handling | 2 main.py + others | 60+ | 🔶 Medium |
| Logging setup | Multiple | 20+ | 🔶 Medium |
| Configuration classes | 3 config files | 25+ | 🔶 Medium |
| Import statements | All files | 50+ | 🔹 Low |

## Consolidation Plan

### Phase 0: Critical Main.py Infrastructure (HIGHEST IMPACT)
1. Create `shared/server/base_server.py` with BaseMCPServer class
2. Refactor both main.py files to inherit from base class
3. Eliminate 300+ lines of duplicated infrastructure
4. **Estimated Reduction**: 300+ lines (80% of main.py duplication)
5. **See**: [Main.py Refactoring Proposal](./main-py-refactoring-proposal.md)

### Phase 1: Remaining Server Components (HIGH IMPACT)
1. Complete health endpoints consolidation in base server
2. Finalize CLI parsing consolidation
3. Consolidate remaining error handling patterns
4. **Estimated Reduction**: 100+ lines

### Phase 2: Utilities (MEDIUM IMPACT)
1. Create `shared/utils/error_handling.py` for exception patterns
2. Consolidate logging setup in `shared/utils/logging_setup.py`
3. Unify configuration classes in `shared/config/`
4. **Estimated Reduction**: 80+ lines

### Phase 3: Imports and Patterns (LOW IMPACT)
1. Optimize import patterns
2. Create package-level convenience imports
3. **Estimated Reduction**: 30+ lines

## Implementation Strategy

### 1. Create Shared Infrastructure
```python
# shared/server/health.py
def create_health_routes(mcp: FastMCP, service_name: str, initialized_flag: bool):
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(_request: Request) -> JSONResponse:
        return JSONResponse({
            "status": "ok",
            "service": service_name,
            "version": "1.0.0",
            "initialized": initialized_flag,
        })
    # Add both /health and /healthz
```

### 2. Update Individual Services
```python
# mcp_local_repo_analyzer/main.py
from shared.server.health import create_health_routes

create_health_routes(mcp, "Local Git Changes Analyzer", _server_initialized)
```

### 3. Create Base CLI
```python
# shared/cli/base_parser.py
def create_base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--transport", choices=["stdio", "streamable-http", "sse"], default="stdio")
    # Add all common arguments
    return parser
```

## Verification Steps

1. **Before Consolidation**: Run tests to establish baseline
2. **After Each Phase**: Verify functionality unchanged
3. **Integration Testing**: Ensure both services work identically
4. **Code Coverage**: Maintain or improve coverage

## Benefits of Consolidation

### Code Quality
- **DRY Principle**: Eliminate ~200 lines of duplication
- **Maintainability**: Single source of truth for common patterns
- **Consistency**: Uniform behavior across services

### Development Efficiency
- **Faster Changes**: Update common code once
- **Reduced Testing**: Test shared infrastructure once
- **Bug Fixes**: Fix issues in one place

### Future Scalability
- **New Services**: Easily add more MCP services
- **Standard Patterns**: Established patterns for server infrastructure
- **Documentation**: Clear separation of concerns

## Risks and Mitigations

### Risk: Breaking Changes
**Mitigation**: Comprehensive testing, gradual migration

### Risk: Over-Abstraction
**Mitigation**: Keep abstractions simple, maintain flexibility

### Risk: Import Complexity
**Mitigation**: Clear module organization, good documentation

## Next Steps

1. **Immediate**: Start with health endpoints (highest impact, lowest risk)
2. **Week 1**: Complete server infrastructure consolidation
3. **Week 2**: Utilities and configuration consolidation
4. **Week 3**: Testing and optimization

Total estimated effort: **3-5 days** for significant code quality improvement.
