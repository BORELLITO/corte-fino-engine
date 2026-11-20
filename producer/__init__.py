"""Provider that materializes the package.json consumed by orchestrator.runflow.

The producer NEVER certifies anything on its own authority: every claim it writes
(hashes, durations, gates) is computed from real bytes, and anything it cannot prove
is written as a failing value so the existing gates keep the run BLOCKED.
"""
