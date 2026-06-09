#!/usr/bin/env python3
"""Proof Formalizer V3 — Anti-Loop Escalation Architecture.

Submodules:
  error_classifier  — classify Lean 4 compilation errors into 15 categories
  fingerprint      — generate stable fingerprints for loop detection
  escalation       — 7-level escalation ladder decision engine
  ledger           — append-only attempt ledger + segment state manager
"""

from pathlib import Path

V3_DIR = Path(__file__).parent

__all__ = ["error_classifier", "fingerprint", "escalation", "ledger"]
