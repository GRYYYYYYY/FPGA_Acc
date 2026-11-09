PYTHON ?= python3
LATEXMK ?= latexmk

.PHONY: all artifacts clean

all: artifacts
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error main.tex

artifacts:
	$(PYTHON) ../prepare_artifacts.py
	$(PYTHON) ../prepare_frontier_table.py
	$(PYTHON) ../prepare_new_cohort_table.py --protocol ../../experiments/tileplace_new_cohort_protocol_v2_2026-09-29.json --sha256 c548ad1e181551cdfb0bbbf5409a49f833bd994b177110675d5ca77574b8df72 --output ../generated

clean:
	$(LATEXMK) -C main.tex
