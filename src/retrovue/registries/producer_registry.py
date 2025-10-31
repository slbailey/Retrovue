"""
Stub Producer Registry for CLI contract compliance.

This provides minimal implementations to satisfy the CLI help surface requirements.
"""


def list_producer_types():
    """List all available producer types."""
    return [
        {"type": "linear", "description": "Linear TV schedule producer"},
        {"type": "preview", "description": "Preview/upcoming content producer"},
        {"type": "yule-log", "description": "Yule log/fireplace content producer"},
        {"type": "test-pattern", "description": "Test pattern generator producer"},
    ]


def get_producer_help(producer_type):
    """Get help information for a specific producer type."""
    help_info = {
        "linear": {
            "description": "Linear TV schedule producer",
            "required_params": [
                {"name": "name", "description": "Human-readable label for this producer"},
                {"name": "channel-id", "description": "Channel ID to produce content for"},
            ],
            "optional_params": [
                {
                    "name": "schedule-path",
                    "description": "Path to schedule configuration file",
                    "default": "./schedule.json",
                }
            ],
            "examples": [
                "retrovue producer add --type linear --name 'Main Channel' --channel-id 1",
                "retrovue producer add --type linear --name 'Secondary Channel' --channel-id 2 --schedule-path /config/schedule2.json",
            ],
        },
        "preview": {
            "description": "Preview/upcoming content producer",
            "required_params": [
                {"name": "name", "description": "Human-readable label for this producer"}
            ],
            "optional_params": [
                {
                    "name": "preview-duration",
                    "description": "Duration of preview segments in seconds",
                    "default": "30",
                }
            ],
            "examples": [
                "retrovue producer add --type preview --name 'Coming Up Next'",
                "retrovue producer add --type preview --name 'Extended Preview' --preview-duration 60",
            ],
        },
        "yule-log": {
            "description": "Yule log/fireplace content producer",
            "required_params": [
                {"name": "name", "description": "Human-readable label for this producer"}
            ],
            "optional_params": [
                {
                    "name": "video-path",
                    "description": "Path to yule log video file",
                    "default": "/media/yule-log.mp4",
                }
            ],
            "examples": [
                "retrovue producer add --type yule-log --name 'Christmas Fireplace'",
                "retrovue producer add --type yule-log --name 'Holiday Ambiance' --video-path /media/holiday.mp4",
            ],
        },
        "test-pattern": {
            "description": "Test pattern generator producer",
            "required_params": [
                {"name": "name", "description": "Human-readable label for this producer"}
            ],
            "optional_params": [
                {
                    "name": "pattern-type",
                    "description": "Type of test pattern to generate",
                    "default": "color-bars",
                }
            ],
            "examples": [
                "retrovue producer add --type test-pattern --name 'Color Bars'",
                "retrovue producer add --type test-pattern --name 'SMPTE Bars' --pattern-type smpte",
            ],
        },
    }

    return help_info.get(
        producer_type,
        {
            "description": f"Unknown producer type: {producer_type}",
            "required_params": [],
            "optional_params": [],
            "examples": [],
        },
    )
