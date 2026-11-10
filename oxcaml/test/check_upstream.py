#!/usr/bin/env python3
"""Compare native JSX lowering with the stock backend on upstream echo fixtures.

Run after building both packages, passing their preprocessor executables.
This does not replace the upstream Merlin/cram suite.
"""
import pathlib
import shlex
import subprocess
import sys

stock, native = (str(pathlib.Path(p).resolve()) for p in sys.argv[1:])
root = pathlib.Path(__file__).resolve().parents[2]
count = 0
failures = []


def parse(pp, source):
    return subprocess.run([pp, "-print-ml"], input=source, text=True,
                          capture_output=True, timeout=15)


for path in sorted((root / "test").glob("*.t")):
    for line, text in enumerate(path.read_text().splitlines(), 1):
        if not text.startswith("  $ echo "):
            continue
        try:
            command = shlex.split(text[4:])
        except ValueError:
            continue  # Multi-line shell inputs are covered by the cram suite.
        if len(command) != 4 or command[2:] != ["|", "./mlx"]:
            continue
        source = command[1]
        expected = parse(stock, source)
        actual = parse(native, source)
        # Normalize stock pretty printing through the native pretty printer.
        # The AST shape, not printer whitespace, is the comparison boundary.
        equivalent = (expected.returncode == 0) == (actual.returncode == 0)
        if expected.returncode == 0 and actual.returncode == 0:
            normalized = parse(native, expected.stdout)
            equivalent = normalized.returncode == 0 and normalized.stdout == actual.stdout
        if not equivalent:
            failures.append(f"{path.name}:{line}: {source}\nstock: {expected.stdout}{expected.stderr}\nnative: {actual.stdout}{actual.stderr}")
        count += 1
if failures:
    raise SystemExit("\n\n".join(failures))
print(f"{count} upstream batch fixtures match the stock backend")
