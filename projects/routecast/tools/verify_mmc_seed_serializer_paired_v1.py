"""Authenticate full serialization parity and paired arithmetic, not clocks."""
import json,sys,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/mmc_seed_serializer_paired_v1_2026-10-08'
B=R/'experiments/ultraembedded_mmc_continuous_workflow_v3_2026-10-08/seed/native/mmc'
p=json.loads((D/'protocol.json').read_text());r=json.loads((D/'receipt.json').read_text())
assert p['bindings']==r['bindings']
for path,digest in p['bindings'].items():assert sha(path)==digest,path
assert p['orders']==[['baseline','candidate'],['candidate','baseline'],['baseline','candidate']]
rows=r['rows'];assert len(rows)==6
assert [(x['pair'],x['mode']) for x in rows]==[(i,m) for i,order in enumerate(p['orders']) for m in order]
bindings={str(f):sha(f) for f in [Path(__file__),D/'protocol.json',D/'receipt.json']}
for row in rows:
 assert row['status']=='FULL_SERIALIZATION_PARITY_PASS' and row['subprocess_seconds']>0
 out=D/f"{row['pair']}_{row['mode']}"
 assert row['files']=={str(f):sha(f) for f in out.iterdir() if f.is_file()}
 assert (out/'seed.route').read_bytes()==(B/'seed.route').read_bytes()
 assert json.loads((out/'bindings.json').read_text())==json.loads((B/'bindings.json').read_text())
 bindings.update(row['files'])
ratios=[next(x['subprocess_seconds'] for x in rows if x['pair']==i and x['mode']=='candidate')/next(x['subprocess_seconds'] for x in rows if x['pair']==i and x['mode']=='baseline') for i in range(3)]
assert ratios==r['ratios'] and statistics.median(ratios)==r['median']
assert all(sha(k)==v for k,v in bindings.items())
result=dict(bindings=bindings,all_six_complete_route_bytes_and_pin_bindings_authenticated=True,ratios=ratios,median=statistics.median(ratios),all_observed_candidate_faster=all(x<1 for x in ratios),scope='Frozen producer wall intervals; independent full-output and arithmetic authentication, no clock reconstruction/statistical stability/fullworkflow/heldout/hardware claim.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['ratios'],result['median'])
