# MLX for OxCaml

This fork adds the optional `mlx-oxcaml` package and the `mlx-pp-oxcaml`
preprocessor. It is pinned to **`oxcaml-compiler.5.2.0minus40`** (compiler version
`5.2.0+ox`). The original `mlx` and `ocamlmerlin-mlx` packages remain the stock
OCaml implementation.

The new frontend uses the matching OxCaml parser, lexer and compiler-libs AST.
JSX lowers to ordinary typed function calls, with MLX's existing `[@JSX]`
attributes. Output is the compiler's native binary AST, preserving source
locations, modes, layouts and unboxed syntax. There is no conversion through
ppxlib's stock AST and no text bridge in the compilation path.

## Install in an existing compatible switch

```sh
opam pin add mlx-oxcaml \
  'git+https://github.com/ozanvos/mlx.git#codex/oxcaml-compat'
```

Only pin/install `mlx-oxcaml`, not every package in the repository. This backend
requires the exact compiler package above; matching `ocamlc -version` alone is
not sufficient because several OxCaml releases use that same version string.
The opam constraint enforces the supported compiler revision. Other revisions
need their own frontend port and validation.

For a new isolated switch, register the compiler repository and create the
pinned switch first (the initial compiler build is substantial):

```sh
opam repository add ox \
  'git+https://github.com/oxcaml/opam-repository.git#9d3f5b0c2ce343683e003157fdd3a01124fecc2b'
opam switch create mlx-oxcaml oxcaml-compiler.5.2.0minus40
# Then run the pin command above in that switch.
```

## Use with Dune

In your application's `dune-project`:

```lisp
(lang dune 3.16)
(dialect
 (name mlx)
 (implementation
  (extension mlx)
  (preprocess (run mlx-pp-oxcaml %{input-file}))))
```

Use ordinary executable/library stanzas. No runtime dependency or PPX is required
by MLX itself. Existing PPX rewriters still need to support your OxCaml compiler.
Do not configure `(merlin_reader mlx)` for this backend: the existing reader is
for the stock AST and has not been ported to OxCaml.

A standalone example is in `example/`. After installation:

```sh
dune exec --root oxcaml/example ./main.exe
```

The direct compiler equivalent is:

```sh
ocamlopt -pp mlx-pp-oxcaml -o main -impl main.mlx
```

`mlx-pp-oxcaml -print-ml main.mlx` is useful for inspection. Use the default binary
output for compilation so diagnostics keep the original `.mlx` coordinates.

## Typed components and Bonsai

Component contracts remain OCaml function signatures. For example, an empty
variant prevents a leaf component from accepting children:

```ocaml
type no_children = |
let label ~text ~children:(_ : no_children list) () = text
let column ~children () = String.concat "\n" children

let render (local_ name) =
  <column>
    <label text=(string_of_int (String.length name)) />
  </column>
```

Phantom-typed keys, effect values and locally scoped Bonsai graphs retain their
ordinary compiler checks. MLX does not supply a component runtime, caching,
reactivity or Rust adapters. It can call those existing OCaml APIs. A real
stateful Bonsai/GPUI component with an explicit `local_ graph` was separately
compiled against the existing SDK during this port; that private integration
fixture is not part of this public repository.

`<> ... </>` constructs a list. It is not a retained UI fragment or a Bonsai
incremental boundary. Put a fragment in parentheses when passing it after other
positional arguments, e.g. `f x (<>child</>)`; `f x <> y` remains comparison.
Follow upstream MLX spacing around ambiguous OCaml tokens, e.g. `a.{ <tag /> }`.
Optional component arguments should precede the final `()` in the function
definition, as with ordinary OCaml labelled arguments.

## Build and verify the fork

In the pinned OxCaml switch, without building the stock packages:

```sh
opam install ./mlx-oxcaml.opam --deps-only --with-test
dune build -p mlx-oxcaml @install
dune runtest oxcaml/test -p mlx-oxcaml
opam lint mlx-oxcaml.opam
```

The tests compile and run bytecode and native executables containing JSX,
`local_`, `int64#`, and `Effect.Deep` handlers. Compile-fail fixtures check key
capabilities, leaf children, local-value escape, and original diagnostic line
and character offsets. Parser cases cover module tags, optional/punned props,
fragments, array and record delimiters, object overrides, comments and strings.

For a comparison against the stock parser, build `mlx` in a separate stock OCaml
switch/build directory, then pass both binaries:

```sh
python3 oxcaml/test/check_upstream.py /path/to/stock/mlx-pp /path/to/mlx-pp-oxcaml
```

This compares the single-line `echo ... | ./mlx` upstream fixtures, including
expected parser failures. It does not replace the upstream Merlin/cram suite.

## Maintaining the frontend

`SOURCE.json` records the exact OxCaml commit and original source hashes.
`frontend.patch` contains the lexer/grammar changes. The other copied frontend
files are unchanged. `jsx_helper.ml` adapts upstream MLX lowering to OxCaml's
native `Longident` representation. Copyright notices and `LICENSE.mlx-oxcaml`
are retained.

To reproduce the copies from a local checkout of the recorded OxCaml tag:

```sh
python3 oxcaml/sync_sources.py /path/to/oxcaml --check
# Omit --check to regenerate the vendored sources.
```

The fork generates the parser using Menhir 20260209 and its matching runtime.
It does not regenerate or alter the stock backend. Source-location diagnostics
are verified; OxCaml Merlin/LSP completion, editor formatting, other compiler
revisions and arbitrary third-party PPXs remain outside this port's proof.

The OxCaml port and its tests/documentation were developed with AI assistance.
