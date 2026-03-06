#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Finding:
    file: str
    kind: str
    name: str
    status: str  # pass|warn|fail
    message: str


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _container_security_findings(manifest_path: Path, manifest: dict) -> list[Finding]:
    abs_path = manifest_path if manifest_path.is_absolute() else (REPO_ROOT / manifest_path).resolve()
    display_path = str(abs_path.relative_to(REPO_ROOT))
    kind = str(manifest.get("kind", ""))
    meta = manifest.get("metadata") or {}
    name = str(meta.get("name", "unknown"))

    if kind != "Deployment":
        return []

    spec = ((manifest.get("spec") or {}).get("template") or {}).get("spec") or {}
    pod_sec = spec.get("securityContext") or {}
    containers = spec.get("containers") or []

    findings: list[Finding] = []

    run_as_non_root = pod_sec.get("runAsNonRoot")
    if run_as_non_root is True:
        findings.append(Finding(display_path, kind, name, "pass", "Pod runs as non-root."))
    else:
        findings.append(
            Finding(
                display_path,
                kind,
                name,
                "fail",
                "Pod must set spec.template.spec.securityContext.runAsNonRoot=true.",
            )
        )

    if not containers:
        findings.append(Finding(display_path, kind, name, "fail", "Deployment has no containers."))
        return findings

    for idx, c in enumerate(containers):
        cname = c.get("name") or f"container-{idx}"
        sec = c.get("securityContext") or {}
        if sec.get("allowPrivilegeEscalation") is False:
            findings.append(Finding(display_path, kind, name, "pass", f"{cname}: no privilege escalation."))
        else:
            findings.append(
                Finding(
                    display_path,
                    kind,
                    name,
                    "fail",
                    f"{cname}: must set securityContext.allowPrivilegeEscalation=false.",
                )
            )

        if sec.get("readOnlyRootFilesystem") is True:
            findings.append(Finding(display_path, kind, name, "pass", f"{cname}: read-only root FS."))
        else:
            findings.append(
                Finding(
                    display_path,
                    kind,
                    name,
                    "warn",
                    f"{cname}: consider setting securityContext.readOnlyRootFilesystem=true.",
                )
            )

        caps = (sec.get("capabilities") or {}).get("drop") or []
        if "ALL" in caps:
            findings.append(Finding(display_path, kind, name, "pass", f"{cname}: drops ALL capabilities."))
        else:
            findings.append(
                Finding(
                    display_path,
                    kind,
                    name,
                    "warn",
                    f"{cname}: consider dropping Linux capabilities (capabilities.drop: [\"ALL\"]).",
                )
            )

        resources = c.get("resources") or {}
        if (resources.get("requests") and resources.get("limits")):
            findings.append(Finding(display_path, kind, name, "pass", f"{cname}: resource requests/limits set."))
        else:
            findings.append(
                Finding(
                    display_path,
                    kind,
                    name,
                    "warn",
                    f"{cname}: consider setting resource requests/limits.",
                )
            )

    return findings


def check_dir(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for file in sorted(path.glob("*.json")):
        manifest = _load_json(file)
        findings.extend(_container_security_findings(file, manifest))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline Kubernetes manifest policy checks (JSON manifests).")
    parser.add_argument("--dir", default="k8s/manifests", help="Directory containing JSON manifests.")
    parser.add_argument("--out", default="artifacts/k8s_policy_findings.json", help="Output path for findings JSON.")
    args = parser.parse_args(argv)

    manifest_dir = (REPO_ROOT / args.dir).resolve()
    if not manifest_dir.exists():
        sys.stderr.write(f"Manifest directory not found: {manifest_dir}\n")
        return 2

    findings = check_dir(manifest_dir)
    out_path = (REPO_ROOT / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps([asdict(f) for f in findings], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")

    failures = [f for f in findings if f.status == "fail"]
    if failures:
        sys.stderr.write("Policy check failures:\n")
        for f in failures:
            sys.stderr.write(f"- {f.file} {f.kind}/{f.name}: {f.message}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
