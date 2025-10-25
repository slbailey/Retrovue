"""
Contract tests for retrovue ingest commands.

Tests the ingest command group against the documented contract in docs/operator/CLI.md.
"""

import pytest
from tests.cli.utils import CLITestRunner


class TestIngestCLI:
    """Test cases for ingest command group."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CLITestRunner()
    
    @pytest.mark.xfail(reason="Ingest command not registered in main CLI per audit")
    def test_ingest_run_help(self):
        """Test retrovue ingest run --help."""
        # TODO: According to audit, ingest command exists in code but is not registered in main CLI
        result = self.runner.assert_command_exists(["ingest", "run"])
        assert "Run content ingestion from a source" in result.output
    
    @pytest.mark.xfail(reason="Command signature does not match CLI.md (positional source vs collection_id)")
    def test_ingest_run_collection_id_signature(self):
        """Test retrovue ingest run <collection_id> signature."""
        # TODO: According to CLI.md, should be retrovue ingest run <collection_id>
        # Current implementation has retrovue ingest run <source> (positional)
        # This mismatch should be resolved
        result = self.runner.invoke_help(["ingest", "run"])
        # Should show collection_id as positional argument, not source
        assert "collection_id" in result.output
    
    @pytest.mark.xfail(reason="Command signature does not match CLI.md (positional source vs --source flag)")
    def test_ingest_run_source_flag_signature(self):
        """Test retrovue ingest run --source <source_id> signature."""
        # TODO: According to CLI.md, should be retrovue ingest run --source <source_id>
        # Current implementation has retrovue ingest run <source> (positional)
        # This mismatch should be resolved
        result = self.runner.invoke_help(["ingest", "run"])
        # Should show --source flag, not positional source
        assert "--source" in result.output
    
    @pytest.mark.xfail(reason="Missing validation behavior per CLI.md")
    def test_ingest_run_validates_collection_reachability(self):
        """Test that ingest run validates collection is allowed and reachable."""
        # TODO: According to CLI.md, must validate that the collection is allowed and reachable
        # Current implementation may not have this validation
        pytest.skip("destructive; validation behavior check")
    
    @pytest.mark.xfail(reason="Missing importer call behavior per CLI.md")
    def test_ingest_run_calls_importer(self):
        """Test that ingest run calls the importer for the collection."""
        # TODO: According to CLI.md, must call the importer for that Collection
        # Current implementation may not call importer directly
        pytest.skip("destructive; behavior check")
    
    @pytest.mark.xfail(reason="Missing enricher application behavior per CLI.md")
    def test_ingest_run_applies_enrichers(self):
        """Test that ingest run applies ingest-scope enrichers in priority order."""
        # TODO: According to CLI.md, must apply ingest-scope enrichers in priority order
        # Current implementation may not apply enrichers
        pytest.skip("destructive; behavior check")
    
    @pytest.mark.xfail(reason="Missing catalog write behavior per CLI.md")
    def test_ingest_run_writes_to_catalog(self):
        """Test that ingest run writes enriched assets to catalog."""
        # TODO: According to CLI.md, must store the final enriched assets in the RetroVue catalog
        # Current implementation may not write to catalog
        pytest.skip("destructive; behavior check")
    
    @pytest.mark.xfail(reason="Missing progress indicators per CLI.md")
    def test_ingest_run_shows_progress_indicators(self):
        """Test that ingest run shows progress indicators and summary."""
        # TODO: According to CLI.md, should show progress indicators and summary of ingested assets
        # Current implementation may not show progress
        pytest.skip("destructive; output behavior check")
    
    @pytest.mark.xfail(reason="Missing sync_enabled and local_path filtering per CLI.md")
    def test_ingest_run_source_filters_by_sync_enabled(self):
        """Test that ingest run --source filters by sync_enabled and local_path."""
        # TODO: According to CLI.md, should ingest all Collections where:
        # - sync_enabled=true
        # - local_path is valid/reachable
        # Current implementation may not filter by these criteria
        pytest.skip("destructive; filtering behavior check")
    
    @pytest.mark.xfail(reason="Missing progress for each collection per CLI.md")
    def test_ingest_run_source_shows_progress_per_collection(self):
        """Test that ingest run --source shows progress for each collection and overall summary."""
        # TODO: According to CLI.md, should show progress for each collection and overall summary
        # Current implementation may not show per-collection progress
        pytest.skip("destructive; output behavior check")
