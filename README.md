# 21-gcp-reliability-security-kubernetes

A production-minded Kubernetes reliability and security kit: policy checks, GitOps-friendly manifests, and guarded production validation.

Focus: kubernetes


## Why this repo exists
Platform automation fails when it’s implicit.
This repository makes baseline expectations explicit (security + operability) and enforces them with fast, offline checks that can gate delivery.

## The top pains this repo addresses
1) Shipping automation safely—baseline security expectations validated as code (least privilege, non-root, hardened pods).
2) Preventing drift—GitOps-friendly manifests and deterministic validation artifacts.
3) Guarded “real” validation—production-mode checks run only with explicit opt-in and clear configuration guidance.

## Quick demo (local)
```bash
make test
```

What you get:
- Kubernetes manifests (JSON) designed for GitOps review
- an offline policy checker that enforces security + reliability invariants
- CI workflow that runs demo-mode checks on every PR

## Design decisions (high level)
- Prefer drills and runbooks over “tribal knowledge”.
- Keep demo mode offline and deterministic.
- Make production-mode checks explicit and guarded.

## What I would do next in production
- Add server-side policy enforcement (OPA Gatekeeper / Kyverno) aligned with the same invariants.
- Integrate with real CI/CD promotion workflows and signed artifacts.
- Add environment-specific overlays and drift detection.

## Tests (two modes)
This repository supports exactly two test modes via `TEST_MODE`:

- `demo`: fast, offline checks against local manifests and fixtures only.
- `production`: runs real `kubectl` validation against a configured cluster (guarded).

Demo:
```bash
TEST_MODE=demo python3 tests/run_tests.py
```

Production (guarded):
```bash
TEST_MODE=production PRODUCTION_TESTS_CONFIRM=1 python3 tests/run_tests.py
```

## Sponsorship and authorship
Sponsored by:
CloudForgeLabs  
https://cloudforgelabs.ainextstudios.com/  
support@ainextstudios.com

Built by:
Freddy D. Alvarez  
https://www.linkedin.com/in/freddy-daniel-alvarez/

For job opportunities, contact:
it.freddy.alvarez@gmail.com

## License
Personal/non-commercial use is free. Commercial use requires permission (paid license).
See `LICENSE` and `COMMERCIAL_LICENSE.md` for details. For commercial licensing, contact: `it.freddy.alvarez@gmail.com`.
Note: this is a non-commercial license and is not OSI-approved; GitHub may not classify it as a standard open-source license.
