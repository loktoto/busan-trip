#!/usr/bin/env python3
"""Run live monitor v1.5 with the latest research-code commit as provenance."""
from __future__ import annotations

import os
import subprocess


def _model_commit() -> str:
    return subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", "research/market-bottom"],
        text=True,
    ).strip()


def main() -> None:
    os.environ["GITHUB_SHA"] = _model_commit()
    from live_monitor_v15 import main as monitor_main

    monitor_main()


if __name__ == "__main__":
    main()
