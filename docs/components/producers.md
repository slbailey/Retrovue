# Producers Framework

**Related:** [Domain: Playout pipeline](../domain/PlayoutPipeline.md) • [Runtime: Channel manager](../runtime/channel_manager.md) • [Runtime: Renderer](../runtime/Renderer.md) • [Developer: Plugin authoring](../developer/PluginAuthoring.md)

## Purpose

Producers are modular source components responsible for supplying playable media to a Renderer. Each producer defines where content comes from — not how it's rendered or encoded.

Producers are designed to be input-driven, meaning they represent any source of audiovisual material that can be fed into the playout pipeline. Examples include local files, test patterns, synthetic feeds, network streams, or dynamically generated sequences.

## Architecture Overview

At runtime, a ChannelManager (or Renderer) selects the appropriate producer based on the scheduled content (e.g., a show, bumper, ad pod, or test signal). The producer then exposes an FFmpeg-compatible input specifier (e.g., file path or lavfi: source) that the Renderer consumes without caring about the underlying implementation.

This modular design allows the system to seamlessly switch between producers without restarting the renderer or altering the output pipeline.

## Core Model / Scope

### Producer Interface

All producers must implement a consistent interface:

- **`get_input_url(context: dict[str, Any] | None = None) -> str`**: Returns an FFmpeg-compatible source string
- **`prepare(context: dict[str, Any] | None = None) -> dict[str, Any] | None`**: Optional metadata or preparation hooks (e.g., validation, pre-roll setup)
- **`cleanup(context: dict[str, Any] | None = None) -> None`**: Optional cleanup hooks

### Configuration Schema

Producers declare their configuration requirements via:

- **`get_config_schema() -> ProducerConfig`**: Defines required and optional configuration parameters
- **`get_update_fields() -> list[UpdateFieldSpec]`**: Defines which fields can be updated via CLI
- **`validate_partial_update(partial_config: dict[str, Any]) -> None`**: Validates partial configuration updates

### Registry System

Producers are registered in the Producer Registry, similar to the Importer and Enricher registries:

- `retrovue producer list-types` - List available producer types
- `retrovue producer add --type <type> --name <label> [config...]` - Create a producer instance
- `retrovue producer list` - List configured producer instances
- `retrovue producer update <producer_id> ...` - Update producer configuration
- `retrovue producer remove <producer_id>` - Remove a producer instance

## Built-in Producers

### FileProducer

Provides FFmpeg-compatible file paths for local media files.

**Configuration:**
- `file_path` (required): Path to the media file

**Example:**
```bash
retrovue producer add --type file --name 'Movie Producer' --file-path /media/movie.mp4
```

**Input URL Format:**
- Returns absolute file path as string (e.g., `/path/to/file.mp4`)

### TestPatternProducer

Generates FFmpeg lavfi (libavfilter) input specifiers for various test patterns.

**Configuration:**
- `pattern_type` (optional): Type of test pattern (color-bars, smpte-bars, color-red, etc.)
- `width` (optional): Width in pixels (default: 1920)
- `height` (optional): Height in pixels (default: 1080)
- `duration` (optional): Duration in seconds (default: None for infinite)

**Example:**
```bash
retrovue producer add --type test-pattern --name 'Color Bars' --pattern-type color-bars
```

**Input URL Format:**
- Returns lavfi specifier (e.g., `lavfi:testsrc=size=1920x1080:duration=10`)

## Creating Custom Producers

To create a new producer:

1. Copy `src/retrovue/adapters/producers/producer_template.py` to a new file
2. Rename the class to match your producer type
3. Implement the abstract methods:
   - `get_input_url()` - Return FFmpeg-compatible input string
   - `get_config_schema()` - Define configuration parameters
   - `get_update_fields()` - Define updatable fields
   - `validate_partial_update()` - Validate configuration updates
4. Register the producer in `src/retrovue/adapters/registry.py`

### Example: Network Stream Producer

```python
class NetworkStreamProducer(BaseProducer):
    name = "network-stream"

    def __init__(self, stream_url: str, timeout: int = 30, **config: Any) -> None:
        super().__init__(stream_url=stream_url, timeout=timeout, **config)
        self.stream_url = stream_url
        self.timeout = timeout

    def get_input_url(self, context: dict[str, Any] | None = None) -> str:
        # FFmpeg can directly consume network stream URLs
        return self.stream_url

    @classmethod
    def get_config_schema(cls) -> ProducerConfig:
        return ProducerConfig(
            required_params=[
                {"name": "stream_url", "description": "URL of the network stream"}
            ],
            optional_params=[
                {"name": "timeout", "description": "Connection timeout in seconds", "default": "30"}
            ],
            description="Network stream producer for RTMP, HLS, HTTP streams, etc.",
        )
```

## Runtime Usage

### Producer Selection

ChannelManager (or Renderer) selects the appropriate producer based on:

- Scheduled content type (show, bumper, ad pod, test signal)
- Asset metadata (file path, stream URL, etc.)
- Channel configuration
- Runtime context (emergency mode, guide mode, etc.)

### Input URL Generation

The producer's `get_input_url()` method is called with optional context:

```python
context = {
    "asset_id": "uuid-here",
    "segment_type": "content",
    "start_time": datetime.now(),
    "metadata": {...}
}

input_url = producer.get_input_url(context)
# Returns: "/path/to/file.mp4" or "lavfi:testsrc=size=1920x1080"
```

### Preparation and Cleanup

Producers can implement optional `prepare()` and `cleanup()` hooks:

- **`prepare()`**: Called before `get_input_url()` to validate availability, allocate resources, etc.
- **`cleanup()`**: Called after input is no longer needed to release resources, close connections, etc.

## Error Handling

Producers raise specific exceptions:

- **`ProducerError`**: Base exception for producer-related errors
- **`ProducerConfigurationError`**: Raised when producer is misconfigured
- **`ProducerInputError`**: Raised when input URL cannot be generated (e.g., file not found)
- **`ProducerNotFoundError`**: Raised when requested producer is not found in registry

## Relationship to Other Components

### Renderer

The Renderer consumes producer input URLs and handles:
- FFmpeg pipeline construction
- Encoding and streaming
- Output format conversion
- Quality management

See [Runtime: Renderer](../runtime/Renderer.md) for detailed documentation on the Renderer component.

### ChannelManager

ChannelManager selects producers based on scheduled content and manages:
- Producer lifecycle (selection, preparation, cleanup)
- Context passing (asset metadata, timing information)
- Error handling and fallback producers

### Playout Pipeline

Producers are part of the playout pipeline:
1. Schedule determines what should air
2. ChannelManager selects appropriate producer
3. Producer provides input URL
4. Renderer consumes input and generates output stream

## Design Principles

- **Input-driven**: Producers define where content comes from, not how it's rendered
- **Stateless**: Producers should be stateless/pure functions where possible
- **Modular**: Producers are swappable without affecting other components
- **FFmpeg-compatible**: All producers return FFmpeg-compatible input specifiers
- **Context-aware**: Producers can use runtime context to influence input selection

## See Also

- [Domain: Playout pipeline](../domain/PlayoutPipeline.md) - Overall playout architecture
- [Runtime: Channel manager](../runtime/ChannelManager.md) - Runtime producer selection
- [Developer: Plugin authoring](../developer/PluginAuthoring.md) - Creating custom producers
- [Importers Framework](./importers.md) - Similar framework for content discovery

