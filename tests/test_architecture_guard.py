"""
Architecture guard tests for Retrovue.
Ensures proper layer boundaries are maintained.
"""

import ast
import pytest
from pathlib import Path


class TestArchitectureGuard:
    """Test that architecture layer boundaries are respected."""
    
    def test_api_layer_imports(self):
        """Test that API layer only imports from allowed layers."""
        repo_root = Path(__file__).parent.parent
        api_dir = repo_root / "src" / "retrovue" / "api"
        
        # Allowed imports for API layer
        allowed_imports = {
            'retrovue.app',  # Application services
            'retrovue.cli.uow',  # Unit of Work
            'retrovue.domain',  # Domain entities
            'retrovue.shared',  # Shared utilities
            'fastapi',  # Web framework
            'uvicorn',  # ASGI server
            'pydantic',  # Data validation
            'sqlalchemy',  # Database ORM
            'structlog',  # Logging
            'typer',  # CLI framework
        }
        
        # Scan API files for imports
        violations = []
        for py_file in api_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if not any(alias.name.startswith(allowed) for allowed in allowed_imports):
                                if not alias.name.startswith(('typing', 'pathlib', 'json', 'datetime', 'uuid')):
                                    violations.append(f"{py_file}: {alias.name}")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and not any(node.module.startswith(allowed) for allowed in allowed_imports):
                            if not node.module.startswith(('typing', 'pathlib', 'json', 'datetime', 'uuid', 'os', 'sys')):
                                violations.append(f"{py_file}: from {node.module}")
            except Exception as e:
                print(f"Warning: Could not parse {py_file}: {e}")
        
        assert not violations, f"API layer has forbidden imports: {violations}"
    
    def test_domain_layer_imports(self):
        """Test that domain layer doesn't import web/GUI modules."""
        repo_root = Path(__file__).parent.parent
        domain_dir = repo_root / "src" / "retrovue" / "domain"
        
        # Forbidden imports for domain layer
        forbidden_patterns = [
            'fastapi',
            'uvicorn', 
            'jinja2',
            'starlette',
            'pyside6',
            'pyqt6',
            'qt',
            'tkinter',
            'wx',
        ]
        
        violations = []
        for py_file in domain_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in forbidden_patterns:
                    if pattern in content.lower():
                        violations.append(f"{py_file}: contains {pattern}")
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")
        
        assert not violations, f"Domain layer has forbidden imports: {violations}"
    
    def test_infra_layer_imports(self):
        """Test that infrastructure layer doesn't import GUI modules."""
        repo_root = Path(__file__).parent.parent
        infra_dir = repo_root / "src" / "retrovue" / "infra"
        
        # Forbidden imports for infra layer
        forbidden_patterns = [
            'pyside6',
            'pyqt6',
            'qt',
            'tkinter',
            'wx',
            'fastapi',  # Infra should not directly import web framework
            'uvicorn',
        ]
        
        violations = []
        for py_file in infra_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in forbidden_patterns:
                    if pattern in content.lower():
                        violations.append(f"{py_file}: contains {pattern}")
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")
        
        assert not violations, f"Infrastructure layer has forbidden imports: {violations}"
    
    def test_no_gui_directories(self):
        """Test that no GUI-specific directories exist."""
        repo_root = Path(__file__).parent.parent
        src_dir = repo_root / "src" / "retrovue"
        
        # Check for forbidden directory names
        forbidden_dirs = [
            'gui', 'qt', 'pyside', 'tkinter', 'wx', 'desktop', 'ui'
        ]
        
        violations = []
        for item in src_dir.iterdir():
            if item.is_dir() and item.name.lower() in forbidden_dirs:
                violations.append(f"Forbidden directory: {item}")
        
        assert not violations, f"Found forbidden GUI directories: {violations}"
    
    def test_no_gui_files(self):
        """Test that no GUI-specific files exist."""
        repo_root = Path(__file__).parent.parent
        src_dir = repo_root / "src" / "retrovue"
        
        # Check for forbidden file patterns
        forbidden_patterns = [
            '*.ui',  # Qt UI files
            '*.qrc',  # Qt resource files
            'qrc_*.py',  # Generated Qt resource files
            '*_gui.py',  # GUI files
            '*_qt.py',  # Qt files
            '*_pyside.py',  # PySide files
        ]
        
        violations = []
        for pattern in forbidden_patterns:
            for file_path in src_dir.rglob(pattern):
                violations.append(f"Forbidden file: {file_path}")
        
        assert not violations, f"Found forbidden GUI files: {violations}"
