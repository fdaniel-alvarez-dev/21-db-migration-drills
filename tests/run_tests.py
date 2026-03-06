#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _print_err(message: str) -> None:
    sys.stderr.write(message.rstrip() + "\n")


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> int:
    proc = subprocess.run(cmd, cwd=cwd, text=True, env=env)
    return proc.returncode


def _mode_from_env_or_arg(mode: str | None) -> str:
    if mode:
        return mode
    return os.environ.get("TEST_MODE", "demo")


def _validate_mode(mode: str) -> None:
    if mode not in {"demo", "production"}:
        raise SystemExit("Invalid mode. Use --mode demo|production or set TEST_MODE=demo|production.")


def run_demo() -> int:
    code = 0
    code |= _run([sys.executable, "-m", "compileall", "-q", "."], cwd=REPO_ROOT)
    code |= _run([sys.executable, "tools/k8s_policy_check.py"], cwd=REPO_ROOT)
    code |= _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-q"], cwd=REPO_ROOT)
    return code


def run_production() -> int:
    if os.environ.get("PRODUCTION_TESTS_CONFIRM") != "1":
        _print_err(
            "Production-mode tests are guarded.\n"
            "Set PRODUCTION_TESTS_CONFIRM=1 to confirm you intend to run kubectl-based validation.\n"
            "Example:\n"
            "  TEST_MODE=production PRODUCTION_TESTS_CONFIRM=1 python3 tests/run_tests.py\n"
        )
        return 2

    kubectl = shutil.which("kubectl")
    if not kubectl:
        _print_err(
            "Missing required tool: kubectl.\n"
            "Install kubectl and configure cluster access, then rerun.\n"
            "Example:\n"
            "  TEST_MODE=production PRODUCTION_TESTS_CONFIRM=1 python3 tests/run_tests.py\n"
        )
        return 2

    if not (os.environ.get("KUBECONFIG") or Path.home().joinpath(".kube/config").exists()):
        _print_err(
            "No Kubernetes configuration found.\n"
            "Set KUBECONFIG to a valid kubeconfig file (or configure ~/.kube/config), then rerun:\n"
            "  KUBECONFIG=/path/to/kubeconfig TEST_MODE=production PRODUCTION_TESTS_CONFIRM=1 python3 tests/run_tests.py\n"
        )
        return 2

    code = 0
    code |= _run([kubectl, "version", "--client=true"], cwd=REPO_ROOT)
    code |= _run([kubectl, "apply", "--dry-run=client", "-f", "k8s/manifests"], cwd=REPO_ROOT)
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run repository tests in demo or production mode.")
    parser.add_argument("--mode", choices=["demo", "production"], help="Execution mode.")
    args = parser.parse_args(argv)

    mode = _mode_from_env_or_arg(args.mode)
    _validate_mode(mode)

    if mode == "demo":
        return run_demo()
    return run_production()


if __name__ == "__main__":
    raise SystemExit(main())
