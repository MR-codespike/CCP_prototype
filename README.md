# CCP — Conditional Commitment Protocol
### Working Prototype — Moonshot Hackathon Submission

This is a runnable implementation of the equilibrium solver described in
the accompanying Moonshot Paper. It requires **no external dependencies**
— pure Python 3 standard library only.

## What This Demonstrates

The core mechanism of CCP: given a set of conditional preference
functions ("I will commit X if at least N others commit, totaling at
least T"), the solver finds the **maximal stable coalition** — a group
where every member's condition is satisfied simultaneously by the rest
of the group — and atomically binds them. If no such coalition exists,
nobody is bound. Zero risk.

This is not a mocked demo. The solver is a genuine constraint-satisfaction
algorithm (bootstrap-percolation / k-core style fixed-point pruning), and
it is covered by an automated test suite.

## Files

| File              | Purpose                                                        |
|-------------------|------------------------------------------------------------------|
| `preference.py`   | The `PreferenceFunction` data model — the core math object of CCP |
| `solver.py`       | The equilibrium solver itself                                  |
| `crypto.py`       | Commit-reveal scheme preventing strategic manipulation          |
| `demo.py`         | Three scripted end-to-end scenarios (run this first)            |
| `interactive.py`  | Live CLI — type in real commitments and watch it solve in real time |
| `test_ccp.py`     | Automated test suite (15 tests, including a regression test for the algorithm fix described below) |

## Run It

```bash
# Run the three scripted scenarios end-to-end
python3 demo.py

# Run the automated test suite
python3 test_ccp.py

# Run a LIVE interactive session (good for presenting to judges)
python3 interactive.py
```

## What the Demo Shows

**Scenario A — Pizza Party.** Four participants with mutually-satisfiable
thresholds. The solver finds a full equilibrium binding all four.

**Scenario B — Park Funding.** Three participants who each require 5
*other* participants to join, but only 3 people exist total. The solver
correctly finds NO equilibrium and binds nobody.

**Scenario C — Climate Coalition (toy model).** Five participants, two of
whom have thresholds unreachable given the group size. The solver finds
a genuine *partial* equilibrium — binding three participants while
correctly excluding the two whose conditions could never be met. This is
the most interesting case: it shows the algorithm doing real constraint
satisfaction, not just returning a scripted yes/no.

## An Honest Note on the Build Process

The first version of the solver used a single-pass greedy cascade
(insert participants one at a time, in threshold order, only counting
people already accepted). It failed on a simple two-person mutual case:
a participant requiring "at least 1 other participant" was wrongly
rejected because, in insertion order, nobody had been accepted yet —
even though the two participants could perfectly satisfy each other.

The fix: a maximal fixed-point pruning algorithm. Start with every
active participant as a provisional candidate, then repeatedly remove
anyone whose condition fails given the *current* candidate group,
until the set stops shrinking. This treats equilibrium membership as a
property of the final group as a whole, not insertion order — which is
mathematically what an equilibrium actually is.

This bug and fix are preserved in `test_ccp.py::test_mutual_dependency_order_independence`,
which specifically tests both input orderings and asserts they agree.

## Relationship to the Moonshot Paper

This prototype implements Section 5 (The Equilibrium Solver) and
Section 6 (The Cryptographic Layer) of the accompanying research paper
in full. Sections 7 (System Architecture — MongoDB, API, React UI) are
described in the paper as the production deployment path but are not
included in this prototype, consistent with the hackathon's guidance
that prototypes need not be complete: "Perfection is not expected.
Originality is."
