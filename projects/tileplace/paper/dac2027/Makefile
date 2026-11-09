LATEXMK ?= latexmk
OUTPUT ?= ../../work/dac_completion_2026-10-13/ieee_rewrite_build
LOCAL_TEXMF ?= $(abspath ../../work/dac_completion_2026-10-13/texmf)

.PHONY: all
all:
	mkdir -p $(OUTPUT)
	TEXMFHOME="$(LOCAL_TEXMF)" TEXMFVAR="$(abspath $(OUTPUT))/texmf-var" TEXMFCONFIG="$(abspath $(OUTPUT))/texmf-config" MKTEXPK=0 MKTEXTFM=0 $(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error -outdir=$(OUTPUT) main.tex
