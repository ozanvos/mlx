#!/usr/bin/env python3
"""Exercise the native binary-AST path, including compiler diagnostics."""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

pp, ocamlc, ocamlopt = [str(pathlib.Path(p).resolve()) for p in sys.argv[1:]]
fixtures = pathlib.Path(__file__).resolve().parent / "fixtures"
checks = 0


def run(args, *, success=True, contains=(), source=None):
    global checks
    result = subprocess.run(args, input=source, text=True, capture_output=True,
                            timeout=120)
    output = result.stdout + result.stderr
    assert (result.returncode == 0) == success, (args, result.returncode, output)
    for expected in contains:
        assert expected in output, (args, expected, output)
    checks += 1
    return result


with tempfile.TemporaryDirectory(prefix="mlx-oxcaml-test-") as tmp:
    os.chdir(tmp)
    for fixture in fixtures.glob("*.mlx"):
        shutil.copyfile(fixture, fixture.name)
    for compiler, suffix in [(ocamlc, "byte"), (ocamlopt, "native")]:
        run([compiler, "-pp", pp, "-o", f"runtime.{suffix}", "-impl", "runtime.mlx"])
        run([f"./runtime.{suffix}"], contains=["JSX, modes, unboxed values and effects: ok"])
    for name, line, messages in [
        ("bad_key", 4, ["Runtime.Key.container", "Runtime.Key.leaf"]),
        ("bad_children", 4, ["Runtime.no_children"]),
        ("local_escape", 3, ["local"]),
    ]:
        for compiler in [ocamlc, ocamlopt]:
            run([compiler, "-color", "never", "-pp", pp, "-c", "-impl", name + ".mlx"],
                success=False, contains=[f'File "{name}.mlx", line {line}', *messages])
    run([pp, "mismatched.mlx"], success=False,
        contains=['File "mismatched.mlx", line 4', "</outer>"])
    # Source offsets must survive preprocessing, not just the source filename.
    run([ocamlc, "-color", "never", "-pp", pp, "-c", "-impl", "bad_key.mlx"],
        success=False, contains=['line 4, characters 8-16'])
    # Printing is an inspection facility; the production path above is binary AST.
    run([pp, "-print-ml", "runtime.mlx"], contains=["@ local", "#42L", "Effect.perform"])
    # Adjacent JSX and fragments, module tags, punning, raw identifiers, comments,
    # quoted strings and ordinary object/record/indexing grammar.
    cases = [
        '<div><span /></div>', '<><div /></>', '<>...xs</>',
        '<div>...xs</div>', '<><>"x"</><>"y"</></>',
        '<A.B.C key=x />', '<A.B.value key=x />',
        '<div ?x ?y=z />', '<div children=xs />',
        '[|<div>"x"</div>|]', '{field = <div>"x"</div>}',
        'xs.{ <div>"x"</div>}', '<div (* nested (* comment *) *) />',
        '<div>{|<not_a_tag />|}</div>', '<\\#type />',
        '(object val x = 1 method copy = {<x = 2>} end)',
        '(object val x = 1 method copy = {<x = 2 > } end)',
        '(fun (x : <m : int; ..>) -> x#m)',
        '(fun (x : < m : int >) -> x#m)',
        '((<div />), (<div />))', 'f x <> y',
        'f x (<>"child"</>)', '(fun (local_ x) -> <div value=x />)',
        '(fun () -> #1L)', '#(1, 2)', '[:<div />:]',
    ]
    for expr in cases:
        run([pp, "-print-ml"], source="let _ = " + expr)
print(f"{checks} native MLX checks passed")
