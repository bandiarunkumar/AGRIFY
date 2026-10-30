"""
AGRIFY Agent Core — Phase 3E
backend/agent/

Pipeline:
  planner.py   → intent classification + entity extraction + tool plan
  tools.py     → tool executor (wraps existing ETL/ML, parallel, timeout-safe)
  context.py   → trust consolidator (merges backend-fetched + client data)
  safety.py    → post-generation safety validator
  responder.py → enhanced rule-based + Gemini response generator
"""
