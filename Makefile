.PHONY: install
install:
	opam install ./mlx.opam ./ocamlmerlin-mlx.opam --deps-only -y

.PHONY: install-dev
install-dev:
	opam install ./mlx.opam ./ocamlmerlin-mlx.opam --deps-only --with-test --with-doc --with-dev-setup -y

.PHONY: create-switch
create-switch:
	opam switch create . 5.5.0 --no-install -y

.PHONY: init
init: create-switch install install-dev

.PHONY: build
build:
	dune build

.PHONY: test
test:
	dune test
