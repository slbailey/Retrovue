"""
Stub Enricher Registry for CLI contract compliance.

This provides minimal implementations to satisfy the CLI help surface requirements.
"""

def list_enricher_types():
    """List all available enricher types."""
    return [
        {
            "type": "ffprobe",
            "description": "Video/audio analysis using FFprobe",
            "scope": "ingest"
        },
        {
            "type": "metadata",
            "description": "Metadata extraction and enrichment",
            "scope": "ingest"
        },
        {
            "type": "playout-enricher",
            "description": "Playout-scope enricher for channel processing",
            "scope": "playout"
        }
    ]


def get_enricher_help(enricher_type):
    """Get help information for a specific enricher type."""
    help_info = {
        "ffprobe": {
            "description": "Video/audio analysis using FFprobe",
            "required_params": [
                {
                    "name": "name",
                    "description": "Human-readable label for this enricher"
                }
            ],
            "optional_params": [
                {
                    "name": "timeout",
                    "description": "Timeout in seconds for FFprobe operations",
                    "default": "30"
                }
            ],
            "examples": [
                "retrovue enricher add --type ffprobe --name 'Video Analysis'",
                "retrovue enricher add --type ffprobe --name 'Fast Analysis' --timeout 10"
            ]
        },
        "metadata": {
            "description": "Metadata extraction and enrichment",
            "required_params": [
                {
                    "name": "name",
                    "description": "Human-readable label for this enricher"
                }
            ],
            "optional_params": [
                {
                    "name": "sources",
                    "description": "Comma-separated list of metadata sources",
                    "default": "imdb,tmdb"
                }
            ],
            "examples": [
                "retrovue enricher add --type metadata --name 'Movie Metadata'",
                "retrovue enricher add --type metadata --name 'TV Metadata' --sources 'tvdb,imdb'"
            ]
        },
        "playout-enricher": {
            "description": "Playout-scope enricher for channel processing",
            "required_params": [
                {
                    "name": "name",
                    "description": "Human-readable label for this enricher"
                }
            ],
            "optional_params": [
                {
                    "name": "config",
                    "description": "JSON configuration for the enricher",
                    "default": "{}"
                }
            ],
            "examples": [
                "retrovue enricher add --type playout-enricher --name 'Channel Branding'"
            ]
        }
    }
    
    return help_info.get(enricher_type, {
        "description": f"Unknown enricher type: {enricher_type}",
        "required_params": [],
        "optional_params": [],
        "examples": []
    })
