#!/usr/bin/env bash
set -euo pipefail

main_pdf=${1:-main.pdf}
appendix_pdf=${2:-reproducibility_appendix.pdf}
mode=${3:-draft}

main_pages=$(pdfinfo "$main_pdf" | awk '/^Pages:/ {print $2}')
appendix_pages=$(pdfinfo "$appendix_pdf" | awk '/^Pages:/ {print $2}')
if test "$mode" = strict; then
  test "$main_pages" -eq 7 || { echo "main manuscript must be exactly 7 pages (6 body + references), got $main_pages" >&2; exit 2; }
  test "$appendix_pages" -eq 1 || { echo "separate appendix must be exactly 1 page, got $appendix_pages" >&2; exit 3; }

  tmp_dir=$(mktemp -d)
  trap 'rm -rf "$tmp_dir"' EXIT
  pdftotext -f 7 -l 7 "$main_pdf" "$tmp_dir/page7.txt"
  grep -Eq 'References|REFERENCES' "$tmp_dir/page7.txt" || { echo "page 7 does not contain references" >&2; exit 4; }
  if grep -Eq 'Appendix|APPENDIX|Conclusion|BOARD RESULT REQUIRED' "$tmp_dir/page7.txt"; then
    echo "page 7 contains non-reference manuscript content" >&2
    exit 5
  fi
fi
if grep -Eq 'LaTeX Warning:.*undefined|Citation.*undefined|Reference.*undefined|Overfull \\hbox' main.log; then
  echo "LaTeX warnings require attention" >&2
  grep -E 'LaTeX Warning:.*undefined|Citation.*undefined|Reference.*undefined|Overfull \\hbox' main.log >&2
  exit 6
fi
echo "page_check: PASS (mode=$mode, main=$main_pages, separate_appendix=$appendix_pages)"
