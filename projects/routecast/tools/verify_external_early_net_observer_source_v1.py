"""Source observer noninterference and complete observation identity audit."""
import json,csv,re,math,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_early_net_observer_v1_2026-10-19';C=E/'prospective_external_family_same_place_cold_control_v2_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def trees(path):
 result={};net=None
 for line in path.read_text().splitlines():
  if line.startswith('Net '):
   m=re.fullmatch(r'Net (\d+) \((.*)\)',line.strip());net=int(m[1]) if m else None
   if net is not None:assert net not in result;result[net]=[]
  elif line.startswith('Node:'):
   assert net is not None;result[net].append(line.strip())
 return result

def main():
 source=D/'source';a=read(source/'verification.json');control=read(C/'native/verification.json');assert a['status']==control['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';bindings={str(Path(__file__).resolve()):sha(__file__)}
 for p,d in [(source/'verification.json',a),(C/'native/verification.json',control)]:
  assert all(sha(q)==h for q,h in d['bindings'].items());bindings[str(p)]=sha(p)
 assert trees(source/'output.route')==trees(C/'native/output.route');assert read(source/'physical_audit.json')['node_occupancy']==read(C/'native/physical_audit.json')['node_occupancy'];assert a['iterations']==control['iterations'] and a['wirelength']==control['wirelength']
 rows=list(csv.DictReader((source/'initial_connections.tsv').open(),delimiter='\t'));assert len(rows)==15616;assert len({(int(r['net']),int(r['pin'])) for r in rows})==len(rows)
 manifest=read(D/'manifest.json');ep=read(manifest['cases'][0]['endpoint']);assert Counter((int(r['net']),int(r['source_rr']),int(r['sink_rr'])) for r in rows)==Counter((q['net_id'],q['source'],q['sink']) for q in ep['connections'])
 for r in rows:assert math.isfinite(float(r['delay_s'])) and float(r['delay_s'])>=0 and math.isfinite(float(r['criticality'])) and 0<=float(r['criticality'])<=1
 order=[tuple(map(int,m)) for m in re.findall(r'^RC_FIRST_NET_ORDER (\d+) (\d+)$',(source/'native.log').read_text(),re.M)];assert [i for i,n in order]==list(range(len(order)));assert len({n for i,n in order})==len(order);assert {q['net_id'] for q in ep['connections']}<={n for i,n in order};first=trees(source/'first_iteration.route');assert {q['net_id'] for q in ep['connections']}<=first.keys()
 for p in [source/'initial_connections.tsv',source/'first_iteration.route',source/'native.log',source/'output.route',D/'manifest.json']:bindings[str(p)]=sha(p)
 result=dict(status='SOURCE_OBSERVER_FINAL_ROUTE_EQUIVALENT_ALL15616_INITIAL_CONNECTIONS_AND_FIRST_ORDER_COVERED',initial_connections=len(rows),NET_invocations=len(order),first_tree_NETs=len(first),final_route_identical=True,bindings=bindings,scope='Final printed trees/full occupancy/iterations/wirelength equal fixed source control. Initial endpoint coverage and finite values checked; setup-criticality values not yet independently STA-recomputed, first trees not yet originalXML physical-audited. No hold export or quality/speedup claim.')
 with (D/'source_equivalence_verification_v1.json').open('x') as f:json.dump(result,f,indent=2)
 print(result['status'])
if __name__=='__main__':main()
