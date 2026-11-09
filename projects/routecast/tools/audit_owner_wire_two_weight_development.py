"""Full, prespecified development comparison; no native acceptance inference."""
import json, subprocess, sys, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=ROOT/'experiments/owner_wire_two_weight_development_protocol_2026-10-07.json'
p=json.loads(protocol.read_text());label=sys.argv[1]
item=next(x for x in p['weights'] if label in x['output'])
assert sha(item['producer'])==item['producer_sha256']
out=ROOT/'experiments'/item['output'];receipt=out/'receipt.json';r=json.loads(receipt.read_text());assert len(r['rows'])==12
cp=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');assert cp['wire_penalty_weight_ns']==item['weight_ns']
assert all(sha(f)==digest for f,digest in cp['sources'].items())
assert {(x['width'],x['index']) for x in r['rows']}=={(w,i) for w in (8,16,32) for i in range(4)}
for x in r['rows']:
 if x['status']=='PRIOR_ALLOCATION_SKIP':continue
 f=out/f"w{x['width']}_m{x['index']}/result.json";assert sha(f)==x['result_sha256']
 subprocess.run([sys.executable,item['auditors'][1],str(x['width']),str(x['index'])],check=True,cwd=ROOT)
for index in (0,2,3):subprocess.run([sys.executable,item['auditors'][index]],check=True,cwd=ROOT)
geometry=ROOT/f'experiments/mux_owner_wire_{label}_geometry_2026-10-07/receipt.json';g=json.loads(geometry.read_text());rows=[];bindings={str(protocol):sha(protocol),str(receipt):sha(receipt),str(geometry):sha(geometry)}
for x in r['rows']:
 row=dict(x)
 if x['status']!='PRIOR_ALLOCATION_SKIP':
  work=out/f"w{x['width']}_m{x['index']}";d=json.loads((work/'result.json').read_text())
  for name in ('verification.json','history_cost_verification.json','physical_budget_verification.json'):
   f=work/name
   if name=='verification.json':
    # The independent timing audit uses its own descriptive filename.
    candidates=[z for z in work.glob('*verification.json') if 'history' not in z.name and 'physical' not in z.name]
    assert len(candidates)==1;f=candidates[0]
   v=json.loads(f.read_text());assert v['result_sha256']==x['result_sha256'];bindings[str(f)]=sha(f)
  gr=next(z for z in g['rows'] if (z['width'],z['index'])==(x['width'],x['index']))
  row.update(actual_model_cpd_ns=d['candidate_model_gate'].get('actual_cpd_ns'),unique_wirelength=gr['values']['weighted']['unique_wirelength'],cold_wirelength=gr['values']['cold']['unique_wirelength'],wire_delta_to_cold=gr['weighted_minus_cold_unique_wire'],model_pass_and_wire_nonregression=x['status']=='ACTUAL_MODEL_PASS_NATIVE_PENDING' and gr['weighted_minus_cold_unique_wire']<=0,wire_comparison_scope='Complete route' if x['routing_status']=='COMPLETE_CANDIDATE' else 'Partial route: lower wire is not QoR improvement',native_status='NOT_RUN_FOR_THIS_WEIGHT')
 rows.append(row)
report=dict(protocol_sha256=sha(protocol),auditor_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,scope='All12 cases for this prespecified same-family development weight; independent timing, query ownership/cost, originalXML physical and wireunion audits. Cold geometry matches authenticated native logs. Candidate native CPD/serialization/canonical acceptance and complete lifecycle cost remain unverified. Model+wire screen is diagnostic, not native admission.')
(out/'development_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print([(x['width'],x['index'],x.get('wire_delta_to_cold'),x.get('model_pass_and_wire_nonregression')) for x in rows],flush=True)
