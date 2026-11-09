"""Authenticate a completed-prefix snapshot without declaring live cohort complete."""
import json,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/verilog_frontend_cohort_v3_2026-10-10';pp=D/'protocol.json';p=json.loads(pp.read_text());assert len(p['plans'])==28 and all(sha(k)==h for k,h in p['bindings'].items());rp=D/'rows.json';raw=rp.read_bytes();rows=json.loads(raw);assert [r['name'] for r in rows]==[x['name'] for x in p['plans'][:len(rows)]]
O=R/'experiments/verilog_frontend_checkpoint_v1_2026-10-10';O.mkdir();(O/'observed_rows.json').write_bytes(raw);bindings={**p['bindings'],str(pp):sha(pp),str(O/'observed_rows.json'):sha(O/'observed_rows.json'),str(Path(__file__)):sha(Path(__file__))};verified=[]
for row,plan in zip(rows,p['plans']):
 receipt=Path(row['receipt']);assert receipt.exists();r=json.loads(receipt.read_text());assert r['exit_code']==row['exit_code'];assert all(sha(k)==h for k,h in r['bindings'].items());bindings.update(r['bindings']);bindings[str(receipt)]=sha(receipt)
 if r['exit_code']==0:
  jp=receipt.parent/'design.json';data=json.loads(jp.read_text());assert set(data['modules'])=={plan['top']};cells=data['modules'][plan['top']]['cells'];types=dict(Counter(c['type'] for c in cells.values()));assert types==r['cell_types'];assert all(int(c['parameters']['WIDTH'],2)<=6 for c in cells.values() if c['type']=='$lut');allowed={'$_MUX_','$_XOR_','$_XNOR_','$_NOT_','$_OR_','$_AND_','$_DFF_P_','$_DFF_PP0_','$_DFF_PP1_','$scopeinfo'};unsupported={k:v for k,v in types.items() if k not in allowed};assert unsupported==r['unsupported_for_existing_boolean_schema'];status='SUPPORTED_PRIMITIVES_ONLY' if not unsupported else 'UNSUPPORTED_PRIMITIVES_PRESENT'
 elif r['exit_code']==124:status='SYNTHESIS_TIMEOUT'
 else:
  text=(receipt.parent/'synthesis.log').read_text();assert 'ERROR:' in text;status='YOSYS_ERROR';unsupported=None
 verified.append(dict(name=row['name'],top=plan['top'],exit_code=r['exit_code'],status=status,unsupported_types=unsupported if r['exit_code']==0 else None,strict_family_admitted=False))
assert all(sha(k)==h for k,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=verified,completed_prefix_count=len(rows),whole_cohort_complete=False,scope='Immutable completed-prefix snapshot of live cohort; exact input/receipt hashes, independent full JSON type counts/widths/schema or actual Yosys error verified. Not native/functional/family admission; fixtures are not representative benchmarks; incomplete source tops need separate resolution.'),indent=2)+'\n');print('PREFIX_VERIFIED',len(rows),verified)
