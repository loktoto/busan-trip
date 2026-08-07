#!/usr/bin/env python3
"""Run live monitor v1.1 with the actual research-code commit as model_commit."""
from __future__ import annotations

import os
import subprocess


def _model_commit() -> str:
    return subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", "research/market-bottom"],
        text=True,
    ).strip()


def main() -> None:
    # live_monitor_v11 reads GITHUB_SHA for provenance.  A runtime request/data commit
    # is not a model commit, so override it inside this process with the latest commit
    # that actually touched the deterministic research engine.
    os.environ["GITHUB_SHA"] = _model_commit()
    from live_monitor_v11 import main as monitor_main

    monitor_main()


if __name__ == "__main__":
    main()
