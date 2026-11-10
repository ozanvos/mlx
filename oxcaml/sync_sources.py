#!/usr/bin/env python3
"""Reproduce the vendored frontend from a local, matching OxCaml checkout."""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", type=pathlib.Path, help="OxCaml source checkout")
parser.add_argument("--check", action="store_true", help="verify without changing files")
args = parser.parse_args()
here = pathlib.Path(__file__).resolve().parent
source = json.loads((here / "SOURCE.json").read_text())
with tempfile.TemporaryDirectory(prefix="mlx-frontend-") as tmp:
    target = pathlib.Path(tmp)
    for name, expected in source["files"].items():
        original = args.source / "parsing" / name
        digest = hashlib.sha256(original.read_bytes()).hexdigest()
        if digest != expected:
            raise SystemExit(f"{original}: does not match {source['tag']}")
        shutil.copyfile(original, target / name)
    subprocess.run(["patch", "-p1", "-i", str(here / "frontend.patch")],
                   cwd=target, check=True)
    for name in source["files"]:
        if args.check:
            if (target / name).read_bytes() != (here / name).read_bytes():
                raise SystemExit(f"{name}: vendored copy differs from source + patch")
        else:
            shutil.copyfile(target / name, here / name)
print("OxCaml source + MLX patch verified")
