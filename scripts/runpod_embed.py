#!/usr/bin/env python3
"""Run Editorial IR embedding generation on a RunPod SSH instance.

This is intentionally a small SSH/SCP wrapper, not a RunPod API client.
Create a GPU pod, copy its SSH target/port/key into this script, and it will:

1. zip the local embedding inputs,
2. upload them to the pod,
3. install requirements in a remote venv,
4. run scripts/embed_ir.py with Qwen3-Embedding,
5. download and extract the generated embedding directory.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


AVAILABLE_VIEWS = ("problem_identity", "solution_structure", "skill", "combined")
DEFAULT_VIEWS = ("solution_structure", "skill", "combined")
REMOTE_BUNDLE_NAME = "ac-recommender-embed-input.zip"


@dataclass(frozen=True)
class SshConfig:
    target: str
    port: int | None
    identity_file: Path | None
    ssh: str
    scp: str
    ssh_options: tuple[str, ...]


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Upload this IR workspace to a RunPod SSH instance, run Qwen3 "
            "embedding generation on GPU, and download the results."
        )
    )
    parser.add_argument(
        "target",
        help="SSH target for the pod, for example root@123.45.67.89 or root@ssh.runpod.io.",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=None,
        help="SSH port from RunPod.",
    )
    parser.add_argument(
        "-i",
        "--identity-file",
        type=Path,
        default=None,
        help="SSH private key path.",
    )
    parser.add_argument(
        "--remote-dir",
        default="/workspace/ac_recommender_embed",
        help="Remote working directory. Defaults to /workspace/ac_recommender_embed.",
    )
    parser.add_argument(
        "--remote-python",
        default="python3",
        help="Remote Python command used before the venv exists. Defaults to python3.",
    )
    parser.add_argument(
        "--model-size",
        default="0.6b",
        choices=["0.6", "0.6b", "0.6B", "4", "4b", "4B", "8", "8b", "8B"],
        help="Qwen3 embedding model size alias. Defaults to 0.6b.",
    )
    parser.add_argument(
        "--views",
        nargs="+",
        default=["all"],
        choices=["all", *AVAILABLE_VIEWS],
        help=(
            "Views to embed. Defaults to recommendation views "
            "(solution_structure, skill, combined)."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Remote SentenceTransformer batch size. Defaults to 64.",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Remote device passed to embed_ir.py. Defaults to cuda.",
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=None,
        help="Optional output dimension passed to embed_ir.py.",
    )
    parser.add_argument(
        "--max-seq-length",
        type=int,
        default=None,
        help="Optional max sequence length passed to embed_ir.py.",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Pass --no-normalize to embed_ir.py.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional IR-file limit for smoke tests.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("embeddings"),
        help="Local and remote output root. Defaults to embeddings/.",
    )
    parser.add_argument(
        "--venv-dir",
        default=".venv-runpod",
        help="Remote venv directory under --remote-dir. Defaults to .venv-runpod.",
    )
    parser.add_argument(
        "--no-venv",
        action="store_true",
        help="Use the remote Python directly instead of creating a venv.",
    )
    parser.add_argument(
        "--no-system-site-packages",
        action="store_true",
        help="Do not expose system site packages to the remote venv.",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip pip install -r requirements.txt on the pod.",
    )
    parser.add_argument(
        "--extra-pip-arg",
        action="append",
        default=[],
        help="Additional argument for remote pip install. Can be repeated.",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip remote IR validation before embedding.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Run remotely but do not download the result zip.",
    )
    parser.add_argument(
        "--no-extract",
        action="store_true",
        help="Download the result zip but do not extract it locally.",
    )
    parser.add_argument(
        "--keep-local-zip",
        action="store_true",
        help="Keep the temporary input bundle in dist/.",
    )
    parser.add_argument(
        "--ssh",
        default="ssh",
        help="Local ssh executable. Defaults to ssh.",
    )
    parser.add_argument(
        "--scp",
        default="scp",
        help="Local scp executable. Defaults to scp.",
    )
    parser.add_argument(
        "--ssh-option",
        action="append",
        default=[],
        help="Extra ssh/scp -o option. Can be repeated.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the local bundle and print commands without uploading or running.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    validate_views(args.views)

    ssh_config = SshConfig(
        target=args.target,
        port=args.port,
        identity_file=expand_optional_path(args.identity_file),
        ssh=args.ssh,
        scp=args.scp,
        ssh_options=tuple(args.ssh_option),
    )
    check_local_tools(ssh_config)

    output_name = embedding_output_name(args.model_size, args.views)
    local_output_root = resolve_local_output_root(repo_root, args.output_root)
    local_result_zip = local_output_root / f"runpod-result-{output_name}.zip"
    remote_dir = args.remote_dir.rstrip("/")
    remote_bundle = f"{remote_dir}/{REMOTE_BUNDLE_NAME}"
    remote_result_zip = f"{remote_dir}/runpod-result-{output_name}.zip"

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        bundle_path = temp_dir / REMOTE_BUNDLE_NAME
        create_input_bundle(repo_root, bundle_path)
        if args.keep_local_zip:
            kept_path = keep_bundle(repo_root, bundle_path)
            print(f"Kept local input bundle: {kept_path}")

        remote_script = build_remote_script(
            args=args,
            remote_bundle=remote_bundle,
            remote_result_zip=remote_result_zip,
            output_name=output_name,
        )

        print(f"Input bundle: {bundle_path} ({bundle_path.stat().st_size:,} bytes)")
        print(f"Remote target: {ssh_config.target}")
        print(f"Remote dir: {remote_dir}")
        print(f"Remote output: {remote_dir}/{args.output_root.as_posix()}/{output_name}")

        if args.dry_run:
            print("\n--- Remote script ---")
            print(remote_script)
            return 0

        ssh_run(ssh_config, f"mkdir -p -- {shlex.quote(remote_dir)}")
        scp_upload(ssh_config, bundle_path, remote_bundle)
        ssh_run_script(ssh_config, remote_script)

    if args.no_download:
        print(f"Remote result zip: {remote_result_zip}")
        return 0

    local_output_root.mkdir(parents=True, exist_ok=True)
    scp_download(ssh_config, remote_result_zip, local_result_zip)
    print(f"Downloaded result zip: {local_result_zip}")

    if not args.no_extract:
        extract_result_zip(local_result_zip, local_output_root)
        print(f"Extracted result directory: {local_output_root / output_name}")

    return 0


def validate_views(views: Sequence[str]) -> None:
    if "all" in views and len(views) > 1:
        raise SystemExit("error: use either --views all or a list of specific views, not both")


def expand_optional_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    return Path(os.path.expandvars(os.path.expanduser(str(path))))


def check_local_tools(config: SshConfig) -> None:
    missing = [tool for tool in (config.ssh, config.scp) if shutil.which(tool) is None]
    if missing:
        raise SystemExit(f"error: missing local executable(s): {', '.join(missing)}")
    if config.identity_file is not None and not config.identity_file.is_file():
        raise SystemExit(f"error: SSH identity file not found: {config.identity_file}")


def resolve_local_output_root(repo_root: Path, output_root: Path) -> Path:
    return output_root if output_root.is_absolute() else repo_root / output_root


def create_input_bundle(repo_root: Path, output_path: Path) -> None:
    required_paths = [
        repo_root / "requirements.txt",
        repo_root / "docs" / "ir",
        repo_root / "schema",
        repo_root / "scripts" / "embed_ir.py",
        repo_root / "scripts" / "validate_ir.py",
        repo_root / "taxonomies",
        repo_root / "ir",
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        raise SystemExit("error: missing bundle input(s): " + ", ".join(str(path) for path in missing))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in required_paths:
            if path.is_file():
                write_file(archive, path, repo_root)
            else:
                for child in sorted(path.rglob("*")):
                    if child.is_file() and should_include_file(child):
                        write_file(archive, child, repo_root)


def should_include_file(path: Path) -> bool:
    if "__pycache__" in path.parts:
        return False
    if path.suffix == ".pyc":
        return False
    return True


def write_file(archive: zipfile.ZipFile, path: Path, repo_root: Path) -> None:
    archive.write(path, path.relative_to(repo_root).as_posix())


def keep_bundle(repo_root: Path, bundle_path: Path) -> Path:
    output_dir = repo_root / "dist"
    output_dir.mkdir(parents=True, exist_ok=True)
    kept_path = output_dir / REMOTE_BUNDLE_NAME
    shutil.copy2(bundle_path, kept_path)
    return kept_path


def build_remote_script(
    *,
    args: argparse.Namespace,
    remote_bundle: str,
    remote_result_zip: str,
    output_name: str,
) -> str:
    remote_dir = args.remote_dir.rstrip("/")
    remote_python = args.remote_python
    output_root = args.output_root.as_posix()

    venv_setup = ""
    python_assignment = f"PY={shlex.quote(remote_python)}"
    if not args.no_venv:
        system_site_flag = "" if args.no_system_site_packages else " --system-site-packages"
        venv_dir = shlex.quote(args.venv_dir)
        venv_setup = f"""
if [ ! -x {venv_dir}/bin/python ]; then
  {shlex.quote(remote_python)} -m venv{system_site_flag} {venv_dir}
fi
PY={venv_dir}/bin/python
"""
        python_assignment = ""

    install_line = ""
    if not args.skip_install:
        pip_args = shlex.join(args.extra_pip_arg)
        install_line = f"""
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt {pip_args}
"""

    validate_line = ""
    if not args.skip_validate:
        validate_line = '"$PY" scripts/validate_ir.py ir --examples-md docs/ir/examples.md'

    embed_args = [
        "scripts/embed_ir.py",
        "--model-size",
        args.model_size,
        "--output-root",
        output_root,
        "--batch-size",
        str(args.batch_size),
        "--device",
        args.device,
        "--overwrite",
    ]
    if args.views != ["all"]:
        embed_args.extend(["--views", *args.views])
    if args.dimensions is not None:
        embed_args.extend(["--dimensions", str(args.dimensions)])
    if args.max_seq_length is not None:
        embed_args.extend(["--max-seq-length", str(args.max_seq_length)])
    if args.no_normalize:
        embed_args.append("--no-normalize")
    if args.limit is not None:
        embed_args.extend(["--limit", str(args.limit)])
    embed_line = '"$PY" ' + shlex.join(embed_args)

    gpu_check = build_gpu_check(args.device)

    return f"""set -euo pipefail
cd {shlex.quote(remote_dir)}
export PIP_DISABLE_PIP_VERSION_CHECK=1
export HF_HOME="${{HF_HOME:-{shlex.quote(remote_dir)}/.cache/huggingface}}"

{shlex.quote(remote_python)} - <<'PY'
from pathlib import Path
import zipfile

bundle = Path({json.dumps(remote_bundle)})
with zipfile.ZipFile(bundle) as archive:
    archive.extractall(".")
print(f"Extracted {{bundle}}")
PY

{python_assignment}
{venv_setup}

{install_line}

"$PY" - <<'PY'
import sys
print("Remote Python:", sys.executable)
PY

{gpu_check}

{validate_line}
{embed_line}

"$PY" - <<'PY'
from pathlib import Path
import zipfile

source = Path({json.dumps(output_root)}) / {json.dumps(output_name)}
zip_path = Path({json.dumps(remote_result_zip)})
if not source.is_dir():
    raise SystemExit(f"embedding output not found: {{source}}")
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(source.rglob("*")):
        if path.is_file():
            archive.write(path, path.relative_to(source.parent).as_posix())
print(f"Wrote {{zip_path}}")
PY
"""


def build_gpu_check(device: str) -> str:
    if device.lower() != "cuda":
        return ""
    return """"$PY" - <<'PY'
import torch

print("Torch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("CUDA version:", torch.version.cuda)
print("CUDA device count:", torch.cuda.device_count())
if not torch.cuda.is_available():
    raise SystemExit("CUDA was requested, but torch.cuda.is_available() is false")
PY
"""


def embedding_output_name(model_size: str, views: Sequence[str]) -> str:
    normalized = model_size.lower()
    if normalized in {"0.6", "0.6b"}:
        size = "0.6b"
    elif normalized in {"4", "4b"}:
        size = "4b"
    elif normalized in {"8", "8b"}:
        size = "8b"
    else:
        raise SystemExit(f"error: unsupported model size: {model_size}")
    view_part = "all" if views == ["all"] else "-".join(views)
    return f"qwen3-embedding-{size}-{view_part}"


def ssh_base_args(config: SshConfig) -> list[str]:
    args = [config.ssh]
    if config.port is not None:
        args.extend(["-p", str(config.port)])
    if config.identity_file is not None:
        args.extend(["-i", str(config.identity_file)])
    args.extend(["-o", "ServerAliveInterval=30"])
    args.extend(["-o", "ServerAliveCountMax=120"])
    args.extend(["-o", "StrictHostKeyChecking=accept-new"])
    for option in config.ssh_options:
        args.extend(["-o", option])
    return args


def scp_base_args(config: SshConfig) -> list[str]:
    args = [config.scp]
    if config.port is not None:
        args.extend(["-P", str(config.port)])
    if config.identity_file is not None:
        args.extend(["-i", str(config.identity_file)])
    args.extend(["-o", "ServerAliveInterval=30"])
    args.extend(["-o", "ServerAliveCountMax=120"])
    args.extend(["-o", "StrictHostKeyChecking=accept-new"])
    for option in config.ssh_options:
        args.extend(["-o", option])
    return args


def ssh_run(config: SshConfig, remote_command: str) -> None:
    run_checked([*ssh_base_args(config), config.target, remote_command])


def ssh_run_script(config: SshConfig, script: str) -> None:
    run_checked([*ssh_base_args(config), config.target, "bash -s"], input_text=script)


def scp_upload(config: SshConfig, local_path: Path, remote_path: str) -> None:
    run_checked([*scp_base_args(config), str(local_path), f"{config.target}:{remote_path}"])


def scp_download(config: SshConfig, remote_path: str, local_path: Path) -> None:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    run_checked([*scp_base_args(config), f"{config.target}:{remote_path}", str(local_path)])


def run_checked(command: Sequence[str], *, input_text: str | None = None) -> None:
    printable = " ".join(shlex.quote(part) for part in command)
    print(f"\n$ {printable}")
    completed = subprocess.run(command, input=input_text, text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def extract_result_zip(zip_path: Path, output_root: Path) -> None:
    resolved_root = output_root.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (output_root / member.filename).resolve()
            if not str(target).startswith(str(resolved_root)):
                raise SystemExit(f"error: unsafe path in result zip: {member.filename}")
        archive.extractall(output_root)


if __name__ == "__main__":
    raise SystemExit(main())
