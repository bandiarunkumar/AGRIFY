"""
Centralized configuration loader with strict precedence
Process env > backend/.env > other env files
Empty values do not override process env
"""
import os
from pathlib import Path

class ConfigLoader:
    def __init__(self):
        self._loaded = False
        self.config = {}
    
    def load(self):
        if self._loaded:
            return
        try:
            from dotenv import dotenv_values
        except ImportError:
            dotenv_values = None
        
        base_dir = Path(__file__).parent
        root_dir = base_dir.parent
        
        # Load from files but don't override process env
        env_files = [
            base_dir / '.env',
            root_dir / '.env.local',
            base_dir / '.env.local',
        ]
        
        for env_file in env_files:
            if env_file.exists() and dotenv_values:
                values = dotenv_values(env_file)
                for k, v in values.items():
                    if v is None or str(v).strip() == '':
                        continue  # Don't override with empty
                    if k not in os.environ or os.environ[k] == '':
                        os.environ[k] = str(v)
        
        self._loaded = True

config_loader = ConfigLoader()
config_loader.load()
