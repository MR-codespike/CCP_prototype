"""
crypto.py
---------
Commit-Reveal scheme used by CCP to ensure participants cannot observe
each other's preference functions before submitting their own (which
would allow strategic manipulation of the equilibrium).

Phase 1 (Commit):
    Each participant locally computes
        C_i = SHA256( json(preference_function) || nonce )
    and submits only C_i. The underlying preference function is hidden.

Phase 2 (Reveal):
    After all commits are collected (or a deadline passes), participants
    reveal (preference_function, nonce). The system verifies the hash
    matches the original commitment before accepting it into the solver.

This guarantees:
  1. No participant can see others' functions before committing.
  2. No participant can change their function after committing
     (the hash would no longer match).
  3. The solver only ever runs once, on the full honestly-revealed set.
"""

import hashlib
import json
import secrets
from dataclasses import asdict
from typing import Tuple

from preference import PreferenceFunction


def commit(pref: PreferenceFunction) -> Tuple[str, str]:
    """
    Returns (commitment_hash, nonce).
    The participant publishes ONLY commitment_hash at this stage.
    """
    nonce = secrets.token_hex(16)
    payload = json.dumps(asdict(pref), sort_keys=True) + nonce
    commitment_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return commitment_hash, nonce


def reveal_and_verify(pref: PreferenceFunction, nonce: str, commitment_hash: str) -> bool:
    """
    Verifies that a revealed (preference_function, nonce) pair matches
    the originally published commitment_hash. Returns True if valid,
    False if the reveal does not match (tampering or dishonesty detected).
    """
    payload = json.dumps(asdict(pref), sort_keys=True) + nonce
    recomputed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return recomputed == commitment_hash
