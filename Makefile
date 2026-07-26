.PHONY: help check test operator-check

help:
	@printf '%s\n' \
		'make check          Validate declarations and run the deterministic suite' \
		'make test           Run unit tests' \
		'make operator-check Also require live context mounts (host only)'

check:
	@python3 -c 'import pathlib,tomllib; r=pathlib.Path("."); d=tomllib.loads((r/"repo.toml").read_text()); assert d["schema_version"] == 1 and d["shape"] == "control-plane"; [(_ for _ in ()).throw(AssertionError(f"missing {p}")) for p in ("README.md","repo.toml","Makefile","AGENTS.md","CLAUDE.md","docs/architecture.md") if not (r/p).exists()]'
	python3 scripts/check_workspace.py
	python3 -m unittest discover -s tests
	git diff --check

test:
	python3 -m unittest discover -s tests

operator-check:
	python3 scripts/check_workspace.py --require-mounts
