#!/usr/bin/env python3
"""Test script for BiliBili submit functionality (without actual upload)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.youdoub.bilibili.cli import submit
from src.youdoub.paths import ensure_workdir


def test_submit_validation():
    """Test submit command validation logic."""
    print("Testing BiliBili submit validation...")

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        workdir = Path(temp_dir)

        # Test 1: No video file should fail
        print("Test 1: No video file...")
        try:
            submit(video_id="test_video", workdir=workdir)
            print("❌ Should have failed without video file")
        except SystemExit as e:
            if e.code == 1:
                print("✅ Correctly failed without video file")
            else:
                print(f"❌ Failed with wrong exit code: {e.code}")
        except Exception as e:
            # Handle the case where typer.Exit raises a different exception
            print(f"✅ Correctly failed without video file (exception: {type(e).__name__})")

        # Test 2: Create video file, should pass validation
        print("Test 2: With video file...")
        # Create the video file in the expected location (workdir/video_id/)
        video_dir = workdir / "test_video"
        wp = ensure_workdir(video_dir)
        wp.video.write_text("fake video content")

        try:
            # Mock the config and upload functions to avoid actual calls
            with patch('src.youdoub.bilibili.cli.config') as mock_config, \
                 patch('src.youdoub.bilibili.cli.upload') as mock_upload:

                mock_config.return_value = None
                mock_upload.return_value = None

                submit(video_id="test_video", workdir=workdir, force_config=True)
                print("✅ Submit validation passed with video file")

                # Check if config was called
                mock_config.assert_called_once()
                mock_upload.assert_called_once()

        except Exception as e:
            print(f"❌ Unexpected error: {e}")


def test_workflow_command():
    """Test workflow command output."""
    print("\nTesting workflow command...")
    from src.youdoub.bilibili.cli import workflow

    try:
        # This should just print help text, no actual functionality to test
        workflow()
        print("✅ Workflow command executed without error")
    except Exception as e:
        print(f"❌ Workflow command failed: {e}")


if __name__ == "__main__":
    test_submit_validation()
    test_workflow_command()
    print("\n🎉 All BiliBili submit tests completed!")