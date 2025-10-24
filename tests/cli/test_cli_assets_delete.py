"""
Tests for CLI asset delete and restore commands.

This module tests the CLI commands for asset deletion and restoration,
including dry-run mode, confirmation prompts, and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from typer.testing import CliRunner

from retrovue.cli.commands.assets import app
from retrovue.domain.entities import Asset


class TestCLIAssetDelete:
    """Test CLI asset delete commands."""

    def test_delete_asset_by_uuid_soft_delete(self, db_session):
        """Test soft deleting an asset by UUID via CLI."""
        # Create test asset
        asset = Asset(
            uri="/test/path.mp4",
            size=1000,
            canonical=False
        )
        db_session.add(asset)
        db_session.flush()
        
        runner = CliRunner()
        
        # Test soft delete with confirmation
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "delete", "--uuid", str(asset.uuid), "--yes"
            ])
            
            assert result.exit_code == 0
            assert "soft deleted successfully" in result.output

    def test_delete_asset_by_uuid_dry_run(self, db_session):
        """Test dry run mode for asset deletion."""
        # Create test asset
        asset = Asset(
            uri="/test/path.mp4",
            size=1000,
            canonical=False
        )
        db_session.add(asset)
        db_session.flush()
        
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "delete", "--uuid", str(asset.uuid), "--dry-run"
            ])
            
            assert result.exit_code == 0
            assert "Would soft delete asset" in result.output
            assert "referenced_by_episodes=false" in result.output

    def test_delete_asset_by_uuid_dry_run_json(self, db_session):
        """Test dry run mode with JSON output."""
        # Create test asset
        asset = Asset(
            uri="/test/path.mp4",
            size=1000,
            canonical=False
        )
        db_session.add(asset)
        db_session.flush()
        
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "delete", "--uuid", str(asset.uuid), "--dry-run", "--json"
            ])
            
            assert result.exit_code == 0
            assert '"action": "soft_delete"' in result.output
            assert '"uuid":' in result.output
            assert '"referenced": false' in result.output

    def test_delete_asset_by_id(self, db_session):
        """Test deleting an asset by ID."""
        # Create test asset
        asset = Asset(
            uri="/test/path.mp4",
            size=1000,
            canonical=False
        )
        db_session.add(asset)
        db_session.flush()
        
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "delete", "--id", str(asset.id), "--yes"
            ])
            
            assert result.exit_code == 0
            assert "soft deleted successfully" in result.output

    def test_delete_asset_hard_delete_with_references(self, db_session):
        """Test hard delete with references (should be refused)."""
        # Create test asset
        asset = Asset(
            uri="/test/path.mp4",
            size=1000,
            canonical=False
        )
        db_session.add(asset)
        db_session.flush()
        
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            # Mock the reference check to return True
            with patch('retrovue.content_manager.library_service.LibraryService.is_asset_referenced_by_episodes') as mock_ref:
                mock_ref.return_value = True
                
                result = runner.invoke(app, [
                    "delete", "--uuid", str(asset.uuid), "--hard"
                ])
                
                assert result.exit_code == 1
                assert "referenced by episodes" in result.output

    def test_delete_asset_hard_delete_with_force(self, db_session):
        """Test hard delete with force flag."""
        # Create test asset
        asset = Asset(
            uri="/test/path.mp4",
            size=1000,
            canonical=False
        )
        db_session.add(asset)
        db_session.flush()
        
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "delete", "--uuid", str(asset.uuid), "--hard", "--force", "--yes"
            ])
            
            assert result.exit_code == 0
            assert "hard deleted successfully" in result.output

    def test_delete_asset_nonexistent(self, db_session):
        """Test deleting a non-existent asset."""
        fake_uuid = uuid4()
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "delete", "--uuid", str(fake_uuid), "--yes"
            ])
            
            assert result.exit_code == 1
            assert "Asset not found" in result.output

    def test_delete_asset_invalid_uuid(self, db_session):
        """Test deleting an asset with invalid UUID format."""
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "delete", "--uuid", "invalid-uuid", "--yes"
            ])
            
            assert result.exit_code == 1
            assert "Invalid UUID format" in result.output

    def test_delete_asset_no_selector(self, db_session):
        """Test deleting an asset without specifying a selector."""
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "delete", "--yes"
            ])
            
            assert result.exit_code == 1
            assert "Must specify one selector" in result.output

    def test_delete_asset_multiple_selectors(self, db_session):
        """Test deleting an asset with multiple selectors (should fail)."""
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "delete", "--uuid", str(uuid4()), "--id", "123", "--yes"
            ])
            
            assert result.exit_code == 1
            assert "Can only specify one selector" in result.output


class TestCLIAssetRestore:
    """Test CLI asset restore commands."""

    def test_restore_asset_success(self, db_session):
        """Test restoring a soft-deleted asset."""
        # Create test asset that is soft deleted
        asset = Asset(
            uri="/test/path.mp4",
            size=1000,
            canonical=False,
            is_deleted=True
        )
        db_session.add(asset)
        db_session.flush()
        
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "restore", str(asset.uuid)
            ])
            
            assert result.exit_code == 0
            assert "restored successfully" in result.output

    def test_restore_asset_json_output(self, db_session):
        """Test restoring an asset with JSON output."""
        # Create test asset that is soft deleted
        asset = Asset(
            uri="/test/path.mp4",
            size=1000,
            canonical=False,
            is_deleted=True
        )
        db_session.add(asset)
        db_session.flush()
        
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "restore", str(asset.uuid), "--json"
            ])
            
            assert result.exit_code == 0
            assert '"action": "restore"' in result.output
            assert '"status": "ok"' in result.output

    def test_restore_asset_nonexistent(self, db_session):
        """Test restoring a non-existent asset."""
        fake_uuid = uuid4()
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "restore", str(fake_uuid)
            ])
            
            assert result.exit_code == 1
            assert "Asset not found or not soft-deleted" in result.output

    def test_restore_asset_invalid_uuid(self, db_session):
        """Test restoring an asset with invalid UUID format."""
        runner = CliRunner()
        
        with patch('retrovue.cli.commands.assets.session') as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            
            result = runner.invoke(app, [
                "restore", "invalid-uuid"
            ])
            
            assert result.exit_code == 1
            assert "Invalid UUID format" in result.output
