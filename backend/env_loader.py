"""
Centralized environment loader for AGRIFY backend
"""
import os
from dotenv import load_dotenv

_LOADED = False

def load_env():
    global _LOADED
    if _LOADED:
        return
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)
    
    # Load in order, don't override process env
    load_dotenv(os.path.join(base_dir, '.env'), override=False)
    load_dotenv(os.path.join(root_dir, '.env.local'), override=False)
    load_dotenv(os.path.join(base_dir, '.env.local'), override=False)
    _LOADED = True

load_env()
