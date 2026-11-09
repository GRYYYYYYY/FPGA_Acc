"""Matched available-case repetition comparison, no completion inference."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];oldfile=ROOT/'experiments/mux_repair_state_repetition_2026-10-06/receipt.json';newfile=ROOT/'experiments/mux_quadratic_repair_state_repetition_2026-10-06/receipt.json';a=json.loads(oldfile.read_text());b=json.loads(newfile.read_text());old={(r['case'],r['attempt']):r for r in a['rows']};rows=[];keys=['repeated_pair','same_routing_any_prior','same_owner_paths_any_prior','same_routing_and_history_any_prior']
for row in b['rows']:
 prior=old[row['case'],row['attempt']];assert len(prior['releases'])==len(row['releases'])
 rows.append(dict(case=row['case'],attempt=row['attempt'],old={k:sum(e[k] for e in prior['releases']) for k in keys},new={k:sum(e[k] for e in row['releases']) for k in keys}))
totals={k:[sum(r['old'][k] for r in rows),sum(r['new'][k] for r in rows)] for k in keys}
(newfile.parent/'comparison.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),old_receipt_sha256=sha(oldfile),new_receipt_sha256=sha(newfile),rows=rows,totals=totals,scope='Matched attempts available in quadratic replay snapshot only. Repetition counts are diagnostic, not route completion, full-state cycle or accepted benefit proof.'),indent=2)+'\n');print(len(rows),totals)
