"""
solver.py
---------
The Equilibrium Solver: the mathematical core of the Conditional
Commitment Protocol.

Given a set of N conditional preference functions, the solver searches
for a stable coalition S (a subset of participants) such that EVERY
member of S has their condition satisfied by the rest of S simultaneously.

This is a fixed-point / constraint-satisfaction problem closely related
to finding a Nash equilibrium in an assurance-game-style coordination
problem:

    For every i in S:
        |S| - 1            >= preference_i.min_participants
        sum(contributions of S \\ {i}) >= preference_i.min_pool

If such an S exists (with |S| > 0), the system reports it and all
members become atomically bound. If no such S exists, NOBODY is bound
and there is zero risk to any participant.

Algorithm: Maximal Fixed-Point Pruning (bootstrap-percolation style).

A naive single greedy pass (insert participants one at a time in
threshold order, only counting whoever was already accepted) FAILS on
mutual conditions. Example: participant X requires "at least 1 other
participant already committed" — but if X is evaluated first, nobody
has committed yet, so X is incorrectly rejected, even though X and Y
could perfectly well satisfy each other's conditions simultaneously.

The correct approach treats equilibrium membership as a property of
the WHOLE final set, not insertion order. We therefore start by
assuming EVERYONE active is a candidate member, and repeatedly remove
any participant whose condition is not satisfied by the REST of the
current candidate set. Removing a participant can cause others to fail
too (their pool/count shrinks), so we repeat until the set stops
shrinking — a true fixed point. This is the same family of algorithm
used for k-core graph decomposition and bootstrap percolation, and it
correctly finds the unique MAXIMAL stable coalition.
"""

from dataclasses import dataclass
from typing import List, Optional
import time

from preference import PreferenceFunction


@dataclass
class EquilibriumResult:
    found: bool
    committed: List[PreferenceFunction]
    total_pool: float
    iterations: int
    explanation: str


def _pool_excluding(committed: List[PreferenceFunction], exclude_id: str) -> float:
    return sum(p.contribution for p in committed if p.participant_id != exclude_id)


def solve_equilibrium(
    functions: List[PreferenceFunction],
    now: Optional[float] = None,
    verbose: bool = False,
) -> EquilibriumResult:
    """
    Core CCP solver.

    Step 1: Filter to only active (non-expired) offers.
    Step 2: Start with the FULL active set as candidates (everyone is
            provisionally "in" — this correctly handles mutual
            conditions, since membership is judged against the final
            group, not insertion order).
    Step 3: Repeatedly remove any participant whose condition fails
            given the REST of the current candidate set. Repeat until
            no more removals occur (a fixed point) or the set is empty.
    Step 4: Return the resulting MAXIMAL stable coalition, or report
            that no equilibrium exists.
    """
    now = now if now is not None else time.time()
    log = []

    active = [f for f in functions if f.is_active(now)]
    log.append(f"Step 1: {len(active)}/{len(functions)} preference functions are active (non-expired).")

    if not active:
        return EquilibriumResult(False, [], 0.0, 0, "\n".join(log) + "\nNo active preference functions submitted.")

    candidates = list(active)
    log.append(f"Step 2: starting with the full active set as candidates ({len(candidates)} participants).")

    iterations = 0
    while candidates:
        iterations += 1
        next_candidates = []
        removed_this_round = []
        for f in candidates:
            others_count = len(candidates) - 1
            pool_excl = _pool_excluding(candidates, f.participant_id)
            if f.conditions_met(others_count, pool_excl):
                next_candidates.append(f)
            else:
                removed_this_round.append(f.participant_id)

        if verbose:
            if removed_this_round:
                log.append(
                    f"  Iteration {iterations}: removing {removed_this_round} "
                    f"(condition not met by remaining {len(candidates)} candidates) "
                    f"-> set size {len(next_candidates)}."
                )
            else:
                log.append(f"  Iteration {iterations}: no removals needed. Fixed point reached.")

        if len(next_candidates) == len(candidates):
            # No change this round -> fixed point reached.
            candidates = next_candidates
            break
        candidates = next_candidates

    if candidates:
        total_pool = sum(p.contribution for p in candidates)
        log.append(
            f"Step 3/4: fixed point reached after {iterations} iteration(s). "
            f"Stable coalition of {len(candidates)} participant(s), total pool {total_pool}."
        )
        return EquilibriumResult(
            found=True,
            committed=candidates,
            total_pool=total_pool,
            iterations=iterations,
            explanation="\n".join(log),
        )
    else:
        log.append(
            f"Step 3/4: coalition collapsed to empty after {iterations} iteration(s). "
            "No stable equilibrium exists. Nobody is bound. Zero risk."
        )
        return EquilibriumResult(
            found=False,
            committed=[],
            total_pool=0.0,
            iterations=iterations,
            explanation="\n".join(log),
        )
