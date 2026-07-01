"""
test_ccp.py
-----------
Automated test suite for the CCP prototype. Run with:

    python3 test_ccp.py

Covers:
  - basic equilibrium detection (positive case)
  - basic no-equilibrium detection (negative case)
  - mutual-dependency case (the bug that an order-dependent greedy
    cascade gets wrong, and that the fixed-point solver gets right)
  - partial-equilibrium exclusion case
  - expired-offer filtering
  - commit-reveal cryptographic correctness (valid + tampered cases)
"""

import time
from preference import PreferenceFunction, new_participant_id
from solver import solve_equilibrium
from crypto import commit, reveal_and_verify

PASS = 0
FAIL = 0


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}")


def test_simple_equilibrium():
    print("\nTest 1: Simple two-party mutual equilibrium")
    future = time.time() + 600
    a = PreferenceFunction("A", "act", 10, min_participants=1, min_pool=10, deadline=future)
    b = PreferenceFunction("B", "act", 10, min_participants=1, min_pool=10, deadline=future)
    result = solve_equilibrium([a, b])
    check("equilibrium found", result.found is True)
    check("both participants bound", len(result.committed) == 2)
    check("pool total correct (20)", result.total_pool == 20)


def test_no_equilibrium():
    print("\nTest 2: Unreachable thresholds -> no equilibrium")
    future = time.time() + 600
    a = PreferenceFunction("A", "act", 10, min_participants=5, min_pool=1000, deadline=future)
    b = PreferenceFunction("B", "act", 10, min_participants=5, min_pool=1000, deadline=future)
    result = solve_equilibrium([a, b])
    check("no equilibrium found", result.found is False)
    check("nobody bound", len(result.committed) == 0)


def test_mutual_dependency_order_independence():
    """
    This is the exact bug class that broke the first (greedy,
    order-dependent) version of the solver: a participant whose
    condition can only be satisfied by someone evaluated AFTER them.
    The fixed-point solver must get this right regardless of input order.
    """
    print("\nTest 3: Mutual dependency must resolve regardless of input order")
    future = time.time() + 600
    # Cara needs >=1 other participant -- but if evaluated first in a
    # naive greedy pass, nobody else has "joined" yet and she'd wrongly
    # be rejected.
    cara = PreferenceFunction("cara", "act", 10, min_participants=1, min_pool=5, deadline=future)
    amy = PreferenceFunction("amy", "act", 5, min_participants=1, min_pool=5, deadline=future)

    result_order1 = solve_equilibrium([cara, amy])
    result_order2 = solve_equilibrium([amy, cara])

    check("order 1 (cara first) finds equilibrium", result_order1.found is True)
    check("order 2 (amy first) finds equilibrium", result_order2.found is True)
    check("both orders agree on coalition size", len(result_order1.committed) == len(result_order2.committed) == 2)


def test_partial_equilibrium_exclusion():
    print("\nTest 4: Partial equilibrium correctly excludes unreachable participants")
    future = time.time() + 600
    a = PreferenceFunction("A", "act", 10, min_participants=1, min_pool=10, deadline=future)
    b = PreferenceFunction("B", "act", 10, min_participants=1, min_pool=10, deadline=future)
    impossible = PreferenceFunction("C", "act", 10, min_participants=50, min_pool=10000, deadline=future)
    result = solve_equilibrium([a, b, impossible])
    ids = {p.participant_id for p in result.committed}
    check("equilibrium found among reachable participants", result.found is True)
    check("A and B are bound", {"A", "B"}.issubset(ids))
    check("impossible participant C correctly excluded", "C" not in ids)


def test_expired_offer_filtered():
    print("\nTest 5: Expired offers are excluded from solving")
    past = time.time() - 10
    future = time.time() + 600
    expired = PreferenceFunction("X", "act", 10, min_participants=1, min_pool=10, deadline=past)
    active = PreferenceFunction("Y", "act", 10, min_participants=0, min_pool=0, deadline=future)
    result = solve_equilibrium([expired, active])
    ids = {p.participant_id for p in result.committed}
    check("expired participant excluded", "X" not in ids)
    check("active participant still resolves", "Y" in ids)


def test_commit_reveal_valid():
    print("\nTest 6: Commit-reveal accepts honest reveal")
    future = time.time() + 600
    pref = PreferenceFunction("Z", "act", 10, min_participants=1, min_pool=10, deadline=future)
    h, nonce = commit(pref)
    check("honest reveal verifies", reveal_and_verify(pref, nonce, h) is True)


def test_commit_reveal_tamper_detected():
    print("\nTest 7: Commit-reveal rejects tampered reveal")
    future = time.time() + 600
    pref = PreferenceFunction("Z", "act", 10, min_participants=1, min_pool=10, deadline=future)
    h, nonce = commit(pref)

    # Participant tries to inflate their contribution AFTER committing.
    tampered = PreferenceFunction("Z", "act", 999, min_participants=1, min_pool=10, deadline=future)
    check("tampered reveal is rejected", reveal_and_verify(tampered, nonce, h) is False)


if __name__ == "__main__":
    print("#" * 72)
    print("# CCP TEST SUITE")
    print("#" * 72)

    test_simple_equilibrium()
    test_no_equilibrium()
    test_mutual_dependency_order_independence()
    test_partial_equilibrium_exclusion()
    test_expired_offer_filtered()
    test_commit_reveal_valid()
    test_commit_reveal_tamper_detected()

    print("\n" + "=" * 72)
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    print("=" * 72)

    if FAIL == 0:
        print("\nAll tests passed. The solver and cryptographic layer behave correctly.")
    else:
        print(f"\n{FAIL} test(s) failed. Review output above.")
        exit(1)
