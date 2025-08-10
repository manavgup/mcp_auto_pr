# Test Coverage Plan - 90% Target

## Current Coverage Status

### Package Coverage
| Package | Current | Target | Gap |
|---------|---------|--------|-----|
| mcp_local_repo_analyzer | 15.65% | 90% | 74.35% |
| mcp_pr_recommender | 0.00% | 90% | 90.00% |
| mcp_shared_lib | 13.22% | 90% | 76.78% |

### Critical Gaps
- **0% Coverage**: All CLI modules, tool implementations, transport layer
- **<30% Coverage**: Service layers, main modules
- **<50% Coverage**: Git utilities, file utilities

## Testing Strategy

### Test Categories

#### 1. Unit Tests (60% of coverage)
- Test individual functions and methods
- Mock external dependencies
- Focus on edge cases and error handling
- Use property-based testing for complex logic

#### 2. Integration Tests (25% of coverage)
- Test component interactions
- Test with real git repositories
- Test MCP server startup and shutdown
- Test tool registration and execution

#### 3. End-to-End Tests (10% of coverage)
- Complete workflow testing
- Docker deployment testing
- PyPI package installation testing
- Cross-package functionality

#### 4. Performance Tests (5% of coverage)
- Load testing with large repositories
- Memory usage monitoring
- Response time benchmarking
- Concurrent operation testing

## Module-Specific Test Requirements

### mcp_local_repo_analyzer

#### High Priority (0% → 90%)
```python
# cli.py - Test all CLI commands and arguments
test_cli_analyze_command()
test_cli_server_mode()
test_cli_transport_selection()
test_cli_error_handling()

# Tool implementations - Test each MCP tool
test_working_directory_tool()
test_staging_area_tool()
test_unpushed_commits_tool()
test_summary_tool()
```

#### Medium Priority (30-69% → 90%)
```python
# Services - Improve existing tests
test_change_detector_edge_cases()
test_diff_analyzer_complex_diffs()
test_status_tracker_all_states()
```

### mcp_pr_recommender

#### Critical (0% → 90%)
```python
# All modules need tests
test_cli_interface()
test_main_server_initialization()
test_config_loading()
test_semantic_analyzer()
test_grouping_engine()
test_atomicity_validator()
test_all_tools()
```

### mcp_shared_lib

#### Transport Layer (0% → 90%)
```python
test_stdio_transport()
test_http_transport()
test_websocket_transport()
test_sse_transport()
test_transport_factory()
```

#### Utilities (15-79% → 90%)
```python
test_git_client_all_operations()
test_file_utils_edge_cases()
test_logging_configuration()
```

## Test Implementation Plan

### Phase 1: Test Infrastructure (Day 5)
- [ ] Set up test fixtures and factories
- [ ] Create mock data generators
- [ ] Configure test database/repositories
- [ ] Set up coverage reporting

### Phase 2: Unit Tests (Day 5-6)
- [ ] Write unit tests for 0% coverage modules
- [ ] Improve tests for low coverage modules
- [ ] Add edge case testing
- [ ] Implement property-based tests

### Phase 3: Integration Tests (Day 6-7)
- [ ] Test service integration
- [ ] Test cross-package dependencies
- [ ] Test MCP server operations
- [ ] Test error propagation

### Phase 4: End-to-End Tests (Day 7)
- [ ] Test complete workflows
- [ ] Test Docker deployments
- [ ] Test PyPI installations
- [ ] Test real-world scenarios

## Test File Organization

```
tests/
├── unit/
│   ├── test_shared_lib/
│   │   ├── test_models/
│   │   │   ├── test_git_models.py
│   │   │   ├── test_analysis_models.py
│   │   │   └── test_base_models.py
│   │   ├── test_services/
│   │   │   └── test_git_client.py
│   │   ├── test_transports/
│   │   │   ├── test_stdio.py
│   │   │   ├── test_http.py
│   │   │   └── test_websocket.py
│   │   └── test_utils/
│   │       ├── test_file_utils.py
│   │       └── test_git_utils.py
│   ├── test_local_repo_analyzer/
│   │   ├── test_cli.py
│   │   ├── test_main.py
│   │   ├── test_services/
│   │   └── test_tools/
│   └── test_pr_recommender/
│       ├── test_cli.py
│       ├── test_main.py
│       ├── test_services/
│       └── test_tools/
├── integration/
│   ├── test_mcp_servers/
│   ├── test_cross_package/
│   └── test_end_to_end/
└── performance/
    ├── test_large_repos.py
    └── test_concurrent_ops.py
```

## Testing Tools and Frameworks

### Required Dependencies
```toml
[tool.poetry.group.test.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
pytest-xdist = "^3.5.0"
pytest-benchmark = "^4.0.0"
pytest-timeout = "^2.2.0"
hypothesis = "^6.92.0"  # Property-based testing
faker = "^20.1.0"       # Test data generation
factory-boy = "^3.3.0"  # Test factories
```

### Coverage Configuration
```toml
[tool.coverage.run]
source = ["src"]
omit = ["*/test_*.py", "*/conftest.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
fail_under = 90
```

## Success Metrics

### Coverage Goals
- Overall: 90%+ coverage
- Critical paths: 95%+ coverage
- Error handling: 100% coverage
- Public APIs: 100% coverage

### Quality Metrics
- All tests pass consistently
- Tests run in <5 minutes
- No flaky tests
- Clear test documentation

## Common Testing Patterns

### Mock Git Repository
```python
@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    # Initialize git repo
    # Add test files
    # Create commits
    return repo_path
```

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async MCP operations."""
    result = await async_function()
    assert result is not None
```

### Parametrized Testing
```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
])
def test_multiple_cases(input, expected):
    assert process(input) == expected
```

## Coverage Reporting

### Commands
```bash
# Run tests with coverage
poetry run pytest --cov=src --cov-report=term-missing

# Generate HTML report
poetry run pytest --cov=src --cov-report=html

# Check coverage threshold
poetry run pytest --cov=src --cov-fail-under=90

# Generate coverage badge
poetry run coverage-badge -o coverage.svg
```

### CI/CD Integration
- Run coverage on every PR
- Block merge if coverage drops
- Generate coverage reports
- Update coverage badges