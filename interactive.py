"""
interactive.py
---------------
Interactive live demo for presenting to judges.

Lets a real group of people (the audience, the judges) type in their
OWN conditional commitments in real time, then runs the solver on
whatever was actually entered.

Run with:

    python3 interactive.py

Type 'done' when everyone has entered their commitment.
"""

import time
from preference import PreferenceFunction, new_participant_id
from crypto import commit, reveal_and_verify
from solver import solve_equilibrium


def prompt_float(label, default=None):
    raw = input(f"{label}{f' [{default}]' if default is not None else ''}: ").strip()
    if raw == "" and default is not None:
        return float(default)
    return float(raw)


def prompt_int(label, default=None):
    raw = input(f"{label}{f' [{default}]' if default is not None else ''}: ").strip()
    if raw == "" and default is not None:
        return int(default)
    return int(raw)


def main():
    print("=" * 72)
    print("CCP — LIVE INTERACTIVE COORDINATION DEMO")
    print("=" * 72)
    print("\nExample problem: 'Would you each chip in toward a shared goal,")
    print("if enough other people in the room also commit?'\n")
    print("Enter each participant's conditional commitment below.")
    print("Type 'done' as the name when everyone has entered theirs.\n")

    future = time.time() + 3600
    submissions = []
    hashes = {}
    nonces = {}

    while True:
        name = input("Participant name (or 'done'): ").strip()
        if name.lower() == "done":
            break
        if not name:
            continue

        contribution = prompt_float("  Your contribution amount", default=1)
        min_participants = prompt_int("  Minimum OTHER participants required", default=0)
        min_pool = prompt_float("  Minimum total pool required", default=0)

        pid = new_participant_id(name)
        pref = PreferenceFunction(
            participant_id=pid,
            action="join_coordination",
            contribution=contribution,
            min_participants=min_participants,
            min_pool=min_pool,
            deadline=future,
        )
        h, nonce = commit(pref)
        submissions.append(pref)
        hashes[pid] = h
        nonces[pid] = nonce
        print(f"  -> sealed. Commitment hash: {h[:16]}...\n")

    if not submissions:
        print("\nNo submissions entered. Exiting.")
        return

    print("\n" + "=" * 72)
    print("REVEAL PHASE")
    print("=" * 72)
    verified = []
    for pref in submissions:
        ok = reveal_and_verify(pref, nonces[pref.participant_id], hashes[pref.participant_id])
        print(f"  {pref.participant_id}: reveal {'VALID' if ok else 'INVALID'}")
        if ok:
            verified.append(pref)

    print("\n" + "=" * 72)
    print("SOLVING FOR EQUILIBRIUM...")
    print("=" * 72)
    result = solve_equilibrium(verified, verbose=True)
    print(result.explanation)

    print("\n" + "=" * 72)
    if result.found:
        print(f"EQUILIBRIUM FOUND — {len(result.committed)} participant(s) are now bound:")
        for p in result.committed:
            print(f"   -> {p.participant_id}: commits {p.contribution}")
        print(f"\nTotal pool: {result.total_pool}")
    else:
        print("NO EQUILIBRIUM FOUND — nobody is bound. Zero risk to all participants.")
    print("=" * 72)


if __name__ == "__main__":
    main()
