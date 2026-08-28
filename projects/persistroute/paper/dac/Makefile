TECTONIC ?= tectonic

.PHONY: all clean check check-submission

all: main.pdf reproducibility_appendix.pdf

main.pdf: main.tex references.bib ../generated/cpu_baseline_table.tex ../generated/u280_resource_table.tex
	$(TECTONIC) --keep-logs --keep-intermediates main.tex

reproducibility_appendix.pdf: reproducibility_appendix.tex
	$(TECTONIC) --keep-logs reproducibility_appendix.tex

check: all
	./check_pages.sh main.pdf reproducibility_appendix.pdf

check-submission: all
	./check_pages.sh main.pdf reproducibility_appendix.pdf strict

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.pdf *.toc
