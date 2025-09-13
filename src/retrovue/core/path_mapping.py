# path_mapping.py
"""
Path mapping utilities for resolving Plex paths to local paths.
"""

def resolve_local_path(database, server_id: int, plex_path: str) -> str:
    """
    Resolve a Plex path to a local path using the server's path mappings.
    
    Args:
        database: Database connection object
        server_id: ID of the Plex server
        plex_path: The Plex path to resolve
        
    Returns:
        The resolved local path, or the original plex_path if no mapping found
    """
    # Get all path mappings for the server, ordered by prefix length (longest first)
    mappings = database.get_path_mappings(server_id)
    
    # Find the longest matching prefix
    for plex_prefix, local_prefix in mappings:
        if plex_path.startswith(plex_prefix):
            # Replace the plex prefix with the local prefix
            local_path = plex_path.replace(plex_prefix, local_prefix, 1)
            return local_path
    
    # No mapping found, return original path
    return plex_path