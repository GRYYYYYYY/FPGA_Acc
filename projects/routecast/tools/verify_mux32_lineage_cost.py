"""Independent integer picosecond-rounded audit of recorded component totals."""
import json
from decimal import Decimal,ROUND_HALF_EVEN
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux32_candidate_lineage_cost_2026-10-07';p=out/'audit.json';r=json.loads(p.read_text());assert all(sha(f)==h for f,h in r['bindings'].items());assert len(r['rows'])==9
# Sum rounded component integer ticks independently of the producer Decimal sum.
unit=Decimal(10)**12;ticks=[]
for row in r['rows']:
 base=ROOT/'experiments'/(row['stage'] if row['stage'].endswith('2026-10-07') else row['stage']+'_2026-10-07');receipt=json.loads((base/'receipt.json').read_text());value=Decimal(str(receipt.get('producer_seconds',receipt.get('seconds'))));assert value==Decimal(row['producer_seconds']) and value>=0;ticks.append(int((value*unit).to_integral_value(rounding=ROUND_HALF_EVEN)))
for count,key in [(7,'recorded_lineage_search_seconds'),(9,'recorded_search_plus_final_native_canonical_seconds')]:
 assert abs(Decimal(sum(ticks[:count]))/unit-Decimal(r[key]))<=Decimal(count)/unit
result=dict(source_sha256=sha(Path(__file__)),audit_sha256=sha(p),ancestor_stages=7,final_native_stages=2,recorded_search_plus_final_native_canonical_seconds=r['recorded_search_plus_final_native_canonical_seconds'],scope='All recorded component receipts bound, independent integer-tick total crosscheck. Scope/exclusions preserved: not continuous elapsed, raw input end-to-end or matched baseline proof.')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('9 recorded clocks independently crosschecked')
