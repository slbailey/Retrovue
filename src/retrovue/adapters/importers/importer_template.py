"""
Template for creating new RetroVue importers.

Copy this file to create a new importer implementation.
Rename the file and class to match your importer type.

This template shows how to implement importers with configuration parameters -
specific values needed to connect to sources (API keys, file paths, connection settings, etc.).
"""

from __future__ import annotations

from typing import Any

from .base import (
    BaseImporter,
    DiscoveredItem,
    ImporterConfig,
    ImporterError,
)


class YourImporterName(BaseImporter):
    """
    Your importer description here.
    
    This importer [describe what it does and how it works].
    
    Configuration Parameters:
    - Describe what configuration parameters this importer needs
    - Examples: API keys, file paths, connection settings, discovery options
    """
    
    # Change these to your importer type name
    name = "your-importer-type"
    
    def __init__(self, **config):
        """
        Initialize your importer with configuration parameters.
        
        Args:
            **config: Configuration parameters (define these in get_config_schema)
                     Examples: API keys, file paths, connection settings, etc.
        """
        super().__init__(**config)
        
        # Store configuration parameters
        # Example:
        # self.api_key = config["api_key"]  # Required configuration parameter
        # self.base_url = config["base_url"]  # Required configuration parameter
        # self.timeout = config.get("timeout", 30)  # Optional configuration parameter
        # self.file_path = config["file_path"]  # File path configuration parameter
    
    def discover(self) -> list[DiscoveredItem]:
        """
        Discover content items from your source.
        
        This is the core method that performs the actual discovery.
        
        Returns:
            List of DiscoveredItem objects representing found content
            
        Raises:
            ImporterError: If discovery fails
            ImporterConnectionError: If cannot connect to source
        """
        try:
            # TODO: Implement your discovery logic here
            
            # Example: Connect to external service
            # if not self._test_connection():
            #     raise ImporterConnectionError("Cannot connect to source")
            
            # Example: Scan for content
            # discovered_items = []
            # for item_data in self._scan_source():
            #     item = self._create_discovered_item(item_data)
            #     if item:
            #         discovered_items.append(item)
            
            # Example: Return discovered items
            return []  # Replace with actual discovered items
            
        except Exception as e:
            raise ImporterError(f"Failed to discover content: {str(e)}") from e
    
    @classmethod
    def get_config_schema(cls) -> ImporterConfig:
        """
        Define the configuration schema for your importer.
        
        Configuration parameters are specific values needed to connect to sources:
        - API Credentials: API keys for external service authentication
        - File Paths: Paths to scan for local content
        - Connection Settings: URLs, ports, timeouts
        - Discovery Settings: Patterns, filters, options
        
        Returns:
            ImporterConfig object defining required and optional configuration parameters
        """
        return ImporterConfig(
            required_params=[
                # Define required configuration parameters here
                # Example:
                # {"name": "api_key", "description": "API key for external service authentication"}
                # {"name": "base_url", "description": "Base URL of the external service"}
                # {"name": "file_path", "description": "Path to scan for local content"}
            ],
            optional_params=[
                # Define optional configuration parameters here
                # Example:
                # {"name": "timeout", "description": "Connection timeout in seconds", "default": "30"}
                # {"name": "include_hidden", "description": "Include hidden files", "default": "false"}
                # {"name": "glob_patterns", "description": "File patterns to match", "default": "**/*"}
            ],
            description="Brief description of what this importer does and its configuration parameters"
        )
    
    def _validate_parameter_types(self) -> None:
        """
        Validate configuration parameter types and values.
        
        Override this method to add custom validation logic for configuration parameters.
        Examples:
        - API key format validation
        - File path existence checks
        - URL format validation
        - Connection timeout range validation
        
        Raise ImporterConfigurationError for invalid configuration parameters.
        """
        # TODO: Add validation for your specific configuration parameters
        
        # Example validation for different parameter types:
        
        # API key validation:
        # api_key = self._safe_get_config("api_key")
        # if not api_key or len(api_key) < 10:
        #     raise ImporterConfigurationError("API key configuration parameter must be at least 10 characters long")
        
        # File path validation:
        # file_path = self._safe_get_config("file_path")
        # if file_path and not Path(file_path).exists():
        #     raise ImporterConfigurationError(f"File path configuration parameter '{file_path}' does not exist")
        
        # URL validation:
        # base_url = self._safe_get_config("base_url")
        # if base_url and not base_url.startswith(("http://", "https://")):
        #     raise ImporterConfigurationError("Base URL configuration parameter must be a valid HTTP/HTTPS URL")
        
        # Timeout validation:
        # timeout = self._safe_get_config("timeout", 30)
        # if not isinstance(timeout, int) or timeout <= 0:
        #     raise ImporterConfigurationError("Timeout configuration parameter must be a positive integer")
        
        pass
    
    def _get_examples(self) -> list[str]:
        """
        Get example usage strings for this importer.
        
        Override this method to provide specific examples.
        
        Returns:
            List of example usage strings
        """
        # TODO: Provide specific examples for your importer
        
        # Example:
        # return [
        #     f'retrovue source add --type {self.name} --name "My {self.name.title()} Source" --api-key "your-key"',
        #     f'retrovue source add --type {self.name} --name "Local Files" --file-path "/media/movies"'
        # ]
        
        return super()._get_examples()
    
    def list_asset_groups(self) -> list[dict[str, any]]:
        """
        List the asset groups available from this source.
        
        Override this method to provide asset group listing.
        
        Returns:
            List of asset group dictionaries
        """
        # TODO: Implement asset group listing for your source
        
        # Example for file-based sources:
        # asset_groups = []
        # for path in self.root_paths:
        #     path_obj = Path(path)
        #     if path_obj.exists() and path_obj.is_dir():
        #         asset_groups.append({
        #             "id": str(path_obj),
        #             "name": path_obj.name,
        #             "path": str(path_obj),
        #             "enabled": True,
        #             "asset_count": len(list(path_obj.glob("**/*"))),
        #             "type": "directory"
        #         })
        # return asset_groups
        
        # Example for API-based sources:
        # try:
        #     libraries = self._fetch_libraries()
        #     return [
        #         {
        #             "id": lib["id"],
        #             "name": lib["name"],
        #             "path": lib["path"],
        #             "enabled": True,
        #             "asset_count": lib.get("count", 0),
        #             "type": lib.get("type", "unknown")
        #         }
        #         for lib in libraries
        #     ]
        # except Exception as e:
        #     raise ImporterError(f"Failed to list asset groups: {e}") from e
        
        return super().list_asset_groups()
    
    def enable_asset_group(self, group_id: str) -> bool:
        """
        Enable an asset group for content discovery.
        
        Override this method to provide asset group enabling.
        
        Args:
            group_id: Unique identifier for the asset group
            
        Returns:
            True if successfully enabled, False otherwise
        """
        # TODO: Implement asset group enabling for your source
        
        # Example for file-based sources:
        # path = Path(group_id)
        # return path.exists() and path.is_dir()
        
        # Example for API-based sources:
        # try:
        #     return self._enable_library(group_id)
        # except Exception:
        #     return False
        
        return super().enable_asset_group(group_id)
    
    def disable_asset_group(self, group_id: str) -> bool:
        """
        Disable an asset group from content discovery.
        
        Override this method to provide asset group disabling.
        
        Args:
            group_id: Unique identifier for the asset group
            
        Returns:
            True if successfully disabled, False otherwise
        """
        # TODO: Implement asset group disabling for your source
        
        # Example for API-based sources:
        # try:
        #     return self._disable_library(group_id)
        # except Exception:
        #     return False
        
        return super().disable_asset_group(group_id)
    
    # Helper methods for your specific implementation
    
    def _test_connection(self) -> bool:
        """
        Test connection to the source.
        
        Returns:
            True if connection is successful, False otherwise
        """
        # TODO: Implement connection testing
        
        # Example for API-based sources:
        # try:
        #     response = requests.get(f"{self.base_url}/ping", timeout=self.timeout)
        #     return response.status_code == 200
        # except Exception:
        #     return False
        
        # Example for file-based sources:
        # try:
        #     path = Path(self.file_path)
        #     return path.exists() and path.is_dir()
        # except Exception:
        #     return False
        
        return True
    
    def _scan_source(self) -> list[dict[str, Any]]:
        """
        Scan the source for content items.
        
        Returns:
            List of raw item data dictionaries
        """
        # TODO: Implement source scanning
        
        # Example for file-based sources:
        # items = []
        # for path in Path(self.file_path).glob(self.glob_pattern):
        #     if path.is_file():
        #         items.append({
        #             "path": str(path),
        #             "name": path.name,
        #             "size": path.stat().st_size,
        #             "modified": datetime.fromtimestamp(path.stat().st_mtime)
        #         })
        # return items
        
        # Example for API-based sources:
        # try:
        #     response = requests.get(f"{self.base_url}/items", 
        #                           headers={"Authorization": f"Bearer {self.api_key}"},
        #                           timeout=self.timeout)
        #     response.raise_for_status()
        #     return response.json().get("items", [])
        # except Exception as e:
        #     raise ImporterConnectionError(f"Failed to fetch items: {e}") from e
        
        return []
    
    def _create_discovered_item(self, item_data: dict[str, Any]) -> DiscoveredItem | None:
        """
        Create a DiscoveredItem from raw item data.
        
        Args:
            item_data: Raw item data from the source
            
        Returns:
            DiscoveredItem or None if creation fails
        """
        try:
            # TODO: Extract data from item_data and create DiscoveredItem
            
            # Example for file-based sources:
            # file_path = item_data["path"]
            # path_uri = f"file://{file_path}"
            # provider_key = file_path
            # size = item_data["size"]
            # last_modified = item_data["modified"]
            # 
            # # Extract labels from filename
            # labels = self._extract_labels_from_filename(item_data["name"])
            # 
            # return DiscoveredItem(
            #     path_uri=path_uri,
            #     provider_key=provider_key,
            #     raw_labels=labels,
            #     last_modified=last_modified,
            #     size=size,
            #     hash_sha256=None  # Calculate if needed
            # )
            
            # Example for API-based sources:
            # path_uri = f"{self.name}://{item_data['id']}"
            # provider_key = item_data["id"]
            # labels = self._extract_labels_from_metadata(item_data)
            # 
            # return DiscoveredItem(
            #     path_uri=path_uri,
            #     provider_key=provider_key,
            #     raw_labels=labels,
            #     last_modified=datetime.fromisoformat(item_data["updated_at"]),
            #     size=item_data.get("size"),
            #     hash_sha256=item_data.get("hash")
            # )
            
            return None  # Replace with actual implementation
            
        except Exception as e:
            # Log error but continue with other items
            print(f"Warning: Failed to create discovered item from {item_data}: {e}")
            return None
    
    def _extract_labels_from_filename(self, filename: str) -> list[str]:
        """
        Extract labels from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            List of extracted labels
        """
        # TODO: Implement filename parsing
        
        # Example:
        # labels = []
        # name_without_ext = Path(filename).stem
        # 
        # # Extract year
        # year_match = re.search(r'\b(19|20)\d{2}\b', name_without_ext)
        # if year_match:
        #     labels.append(f"year:{year_match.group()}")
        # 
        # # Extract title
        # title = re.split(r'\s*[\(\[].*?[\)\]]\s*', name_without_ext)[0]
        # if title:
        #     labels.append(f"title:{title.strip()}")
        # 
        # return labels
        
        return []
    
    def _extract_labels_from_metadata(self, metadata: dict[str, Any]) -> list[str]:
        """
        Extract labels from metadata.
        
        Args:
            metadata: Metadata dictionary from the source
            
        Returns:
            List of extracted labels
        """
        # TODO: Implement metadata parsing
        
        # Example:
        # labels = []
        # 
        # if "title" in metadata:
        #     labels.append(f"title:{metadata['title']}")
        # 
        # if "year" in metadata:
        #     labels.append(f"year:{metadata['year']}")
        # 
        # if "genre" in metadata:
        #     labels.append(f"genre:{metadata['genre']}")
        # 
        # return labels
        
        return []


# TODO: Register your importer type
# from .base import register_importer_type
# register_importer_type(YourImporterName)


# =============================================================================
# EXAMPLES OF DIFFERENT CONFIGURATION PARAMETER TYPES
# =============================================================================

# Example 1: API-based importer (requires API key and URL)
class ExampleAPIImporter(BaseImporter):
    """
    Example API-based importer showing API key configuration parameters.
    
    This importer connects to external APIs and requires
    API credentials as configuration parameters.
    """
    
    name = "example-api"
    
    def __init__(self, api_key: str, base_url: str, timeout: int = 30):
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout)
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
    
    def discover(self) -> list[DiscoveredItem]:
        # Implementation would use self.api_key, self.base_url, self.timeout
        return []
    
    @classmethod
    def get_config_schema(cls) -> ImporterConfig:
        return ImporterConfig(
            required_params=[
                {"name": "api_key", "description": "API key for external service authentication"},
                {"name": "base_url", "description": "Base URL of the external service"}
            ],
            optional_params=[
                {"name": "timeout", "description": "Connection timeout in seconds", "default": "30"}
            ],
            description="API-based content discovery using external service"
        )


# Example 2: File-based importer (requires file path)
class ExampleFileImporter(BaseImporter):
    """
    Example file-based importer showing file path configuration parameters.
    
    This importer scans local filesystems and requires
    file paths as configuration parameters.
    """
    
    name = "example-file"
    
    def __init__(self, file_path: str, include_hidden: bool = False, glob_pattern: str = "**/*"):
        super().__init__(file_path=file_path, include_hidden=include_hidden, glob_pattern=glob_pattern)
        self.file_path = file_path
        self.include_hidden = include_hidden
        self.glob_pattern = glob_pattern
    
    def discover(self) -> list[DiscoveredItem]:
        # Implementation would use self.file_path, self.include_hidden, self.glob_pattern
        return []
    
    @classmethod
    def get_config_schema(cls) -> ImporterConfig:
        return ImporterConfig(
            required_params=[
                {"name": "file_path", "description": "Path to scan for local content"}
            ],
            optional_params=[
                {"name": "include_hidden", "description": "Include hidden files", "default": "false"},
                {"name": "glob_pattern", "description": "File patterns to match", "default": "**/*"}
            ],
            description="File-based content discovery from local filesystem"
        )


# Example 3: No-parameter importer (uses system defaults)
class ExampleSystemImporter(BaseImporter):
    """
    Example system importer showing no configuration parameters needed.
    
    This importer uses system defaults and doesn't require any
    configuration parameters.
    """
    
    name = "example-system"
    
    def __init__(self, **config):
        super().__init__(**config)
        # No configuration parameters needed - uses system defaults
    
    def discover(self) -> list[DiscoveredItem]:
        # Implementation uses system defaults (e.g., system directories)
        return []
    
    @classmethod
    def get_config_schema(cls) -> ImporterConfig:
        return ImporterConfig(
            required_params=[
                # No required configuration parameters
            ],
            optional_params=[
                # No optional configuration parameters
            ],
            description="System-based content discovery using default locations (no parameters needed)"
        )

