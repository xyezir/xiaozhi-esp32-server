#!/usr/bin/env python3
import pathlib
import re
import subprocess
import sys


IMAGE = "xiaozhi-server:0.9.6-main-20260815-candidate"
BASE_IMAGE = "xiaozhi-server:server-base-local"


def run(*args: str, cwd: pathlib.Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def required_value(text: str, label: str, pattern: str) -> str:
    match = re.search(rf"^- {re.escape(label)}: `({pattern})`\.$", text, re.MULTILINE)
    if match is None:
        raise SystemExit(f"missing or invalid {label.lower()}")
    return match.group(1)


def main() -> int:
    report = pathlib.Path(sys.argv[1])
    text = report.read_text(encoding="utf-8")
    repo = report.resolve().parents[3]
    required = (
        "# Xiaozhi Server v0.9.6 Upgrade Report",
        "## Current state",
        "## Compatibility boundary",
        "## Model recommendation",
        "## Rollout",
        "## Observation gates",
        "## Rollback",
        "xiaozhi-server:0.9.6-main-20260815-candidate",
        "xiaozhi-server:20260813-secure",
        "manager web/API",
        "0.9.1",
        "v0.9.6",
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"missing report evidence: {missing}")
    image_id = required_value(text, "Candidate image ID", r"sha256:[0-9a-f]{64}")
    source_revision = required_value(text, "Candidate source revision", r"[0-9a-f]{40}")
    source_tree = required_value(text, "Candidate source tree", r"[0-9a-f]{40}")
    base_image_id = required_value(text, "Candidate base image ID", r"sha256:[0-9a-f]{64}")
    deployment_manifest = required_value(
        text, "Candidate deployment manifest", r"[0-9a-f]{40}"
    )

    if run("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}") != image_id:
        raise SystemExit("reported candidate image id does not match the local tag")
    if run("docker", "image", "inspect", BASE_IMAGE, "--format", "{{.Id}}") != base_image_id:
        raise SystemExit("reported base image id does not match the local tag")
    if run("git", "rev-parse", "HEAD:main/xiaozhi-server", cwd=repo) != source_tree:
        raise SystemExit("reported source tree does not match the current candidate source")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_revision, "HEAD"], cwd=repo
    ).returncode != 0:
        raise SystemExit("reported source revision is not an ancestor of HEAD")

    expected_labels = {
        "org.opencontainers.image.revision": source_revision,
        "org.opencontainers.image.base.digest": base_image_id,
        "io.xiaozhi.source-tree": source_tree,
        "io.xiaozhi.deployment-manifest": deployment_manifest,
    }
    for label, expected in expected_labels.items():
        actual = run(
            "docker",
            "image",
            "inspect",
            IMAGE,
            "--format",
            f'{{{{index .Config.Labels "{label}"}}}}',
        )
        if actual != expected:
            raise SystemExit(f"candidate image label {label} does not match the report")
    if "docker compose" not in text or "docker image inspect" not in text:
        raise SystemExit("missing executable rollout or rollback verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
