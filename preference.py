"""
preference.py
--------------
Core data model for the Conditional Commitment Protocol (CCP).

A PreferenceFunction encodes not just whether a participant wants an
outcome, but the exact conditions under which they are willing to commit.
This is the central mathematical object of CCP: a function of the form

    P_i(n, T) = 1   if  n >= min_participants  AND  T >= min_pool
              = 0   otherwise

where n is the number of other committing participants and T is the
total pooled contribution.
"""

from dataclasses import dataclass, field
import time
import uuid


@dataclass
class PreferenceFunction:
    participant_id: str
    action: str                 # what the participant will do
    contribution: float         # magnitude of their commitment (money, hours, etc.)
    min_participants: int       # minimum number of OTHER participants required
    min_pool: float             # minimum total pooled contribution required
    deadline: float             # unix timestamp after which the offer expires
    confidence: float = 1.0     # 0..1, how firm this commitment is

    def is_active(self, now: float = None) -> bool:
        now = now if now is not None else time.time()
        return now <= self.deadline

    def conditions_met(self, others_count: int, pool_total_excluding_self: float) -> bool:
        return (
            others_count >= self.min_participants
            and pool_total_excluding_self >= self.min_pool
        )

    def __repr__(self):
        return (
            f"<Pref {self.participant_id}: commit {self.contribution} "
            f"IF others>={self.min_participants} AND pool>={self.min_pool}>"
        )


def new_participant_id(name: str = None) -> str:
    """Generate an anonymized-looking participant id."""
    if name:
        return f"{name}-{uuid.uuid4().hex[:6]}"
    return uuid.uuid4().hex[:10]
