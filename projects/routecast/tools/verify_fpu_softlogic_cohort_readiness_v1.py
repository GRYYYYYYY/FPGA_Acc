"""Independent full outcome accounting and JSON/BLIF storage census."""
import json,sys
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/fpu_softlogic_cohort_readiness_v1_2026-10-10'
p=json.loads((D/'protocol.json').read_text());r=json.loads((D/'receipt.json').read_text())
assert r['all_eight_frontend_outcomes_accounted']
assert len(p['cases'])==len(r['rows'])==8
assert [x['name'] for x in r['rows']]==[x['name'] for x in p['cases']]==sorted(x['name'] for x in p['cases'])
bindings={**p['bindings'],**r['bindings'],str(Path(__file__).resolve()):sha(__file__),str(D/'receipt.json'):sha(D/'receipt.json'),str(D/'protocol.json'):sha(D/'protocol.json')}
assert all(sha(k)==v for k,v in bindings.items());rows=[]
for case,row in zip(p['cases'],r['rows']):
 assert sha(case['source'])==case['sha256'] and not row['native_admitted'] and not row['heldout_admitted']
 w=Path(row['reused_frontend_receipt']).parent if case['reuse_prior'] else D/case['name']
 if row['exit_code']!=0:
  assert (w/'synthesis.log').is_file();rows.append(dict(name=row['name'],exit_code=row['exit_code'],failed_or_timed_out_retained=True));continue
 m=json.loads((w/'design.json').read_text())['modules'];assert set(m)=={row['name']};counts=Counter(c['type'] for c in m[row['name']]['cells'].values());assert dict(counts)==row['cell_types']
 assert row['unsupported_types']=={k:v for k,v in counts.items() if k not in p['allowed_types']}
 storage=Counter(s.split()[3] for s in (w/'design.blif').read_text().splitlines() if s.startswith('.latch '))
 for kind,code in [('$_DFF_P_','re'),('$_DFF_N_','fe'),('$_DLATCH_N_','al'),('$_DLATCH_P_','ah')]:assert counts[kind]==storage[code],(row['name'],kind)
 assert set(storage)<={'re','fe','al','ah'}
 for f in ['design.json','design.blif','synthesis.log']:bindings[str(w/f)]=sha(w/f)
 rows.append(dict(name=row['name'],exit_code=0,cell_types=dict(counts),serialized_storage=dict(storage),unsupported=row['unsupported_types']))
assert all(sha(k)==v for k,v in bindings.items())
(D/'independent_verification_v1.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_eight_order_inputs_type_and_serialized_storage_censuses_pass=True,scope='Complete accounting/type/storage-count screening, not per-bit functional equivalence, source semantics, native admission, timing or unseen-family proof.'),indent=2)+'\n');print(json.dumps(rows,indent=2))
