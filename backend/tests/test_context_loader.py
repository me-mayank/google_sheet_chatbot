import json
import os
import tempfile
from pathlib import Path
from app.services.context_loader import ContextLoader

def test_context_loader_hot_reload():
    # Use a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        loader = ContextLoader()
        # Override the directory to the temp dir
        loader.contexts_dir = tmp_path
        
        # Write initial context
        file_path = tmp_path / "test_context.json"
        with open(file_path, "w") as f:
            json.dump({
                "context_id": "test_1",
                "name": "Test Context",
                "instructions": "Initial instructions"
            }, f)
            
        # First load
        loader.load_contexts()
        ctx = loader.get_context("test_1")
        assert ctx is not None
        assert ctx.instructions == "Initial instructions"
        
        # Update file for hot reload test
        with open(file_path, "w") as f:
            json.dump({
                "context_id": "test_1",
                "name": "Test Context",
                "instructions": "Updated instructions"
            }, f)
            
        # Hot reload
        loader.load_contexts()
        ctx = loader.get_context("test_1")
        assert ctx is not None
        assert ctx.instructions == "Updated instructions"
