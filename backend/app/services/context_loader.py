import os
import json
from pathlib import Path
from app.schemas.context import ContextConfig
import logging

logger = logging.getLogger(__name__)

class ContextLoader:
    def __init__(self):
        self.contexts: dict[str, ContextConfig] = {}
        self.contexts_dir = Path(__file__).parent.parent / "core" / "contexts"

    def load_contexts(self):
        new_contexts = {}
        if not self.contexts_dir.exists():
            logger.warning(f"Contexts directory {self.contexts_dir} does not exist.")
            return

        for filename in os.listdir(self.contexts_dir):
            if filename.endswith(".json"):
                filepath = self.contexts_dir / filename
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        context_config = ContextConfig(**data)
                        new_contexts[context_config.context_id] = context_config
                except Exception as e:
                    logger.error(f"Failed to load context {filename}: {e}")

        self.contexts = new_contexts
        logger.info(f"Loaded {len(self.contexts)} contexts.")

    def get_context(self, context_id: str) -> ContextConfig:
        return self.contexts.get(context_id)

context_loader = ContextLoader()
# Load immediately on startup
context_loader.load_contexts()
