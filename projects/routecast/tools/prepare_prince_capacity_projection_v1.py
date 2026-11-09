"""Score-only physical-range projection of fixed live-ready native demand."""
import json,struct
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_capacity_projection_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);vp=E/'prince_ready_consumer_trial_v1_2026-10-20/ready_event_verification_v1.json';v=json.loads(vp.read_text());protocol=dict(formula='For every full-domain CHANNEL resource: forecast=min(observed native occupancy,capacity); retain zeros. Spatial forecast aggregates these projected per-resource counts over unchanged inclusive bins/capacities.',scope='Score-only development baseline, no new route/ledger legality claim, no change to fixed readiness event or controls/gates. No fitted coefficient or threshold. Final labels do not participate in construction. Projection toward feasible interval cannot increase each resource absolute error for any capacity-feasible truth; no rank/spatial/gate guarantee.',bindings={str(vp):sha(vp),str(Path(__file__)):sha(__file__)})
 (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for entry in v['rows']:
  if entry['mode']!='digest':continue
  case=entry['case'];iteration=entry['selected_iteration']
  if iteration is None:rows.append(dict(case=case,status='NO_READY_EVENT'));continue
  source=E/'prince_ready_consumer_trial_v1_2026-10-20'/case/'digest/callback.tsv.ready_RR.bin';domain=E/'prince_quality_domains_v1_2026-10-20'/case.split('/')[0];rp=domain/'resources.jsonl';dp=domain/'verification.json';meta=json.loads(dp.read_text());raw=source.read_bytes();i,n=struct.unpack_from('<QQ',raw,8);assert i==iteration and n==meta['graph_nodes'];native={nid:(count,capacity) for nid,kind,count,capacity,word in struct.iter_unpack('<QIiiI',raw[24:])};out=D/case;out.mkdir(parents=True);path=out/'resource_scores.jsonl';clipped=0
  with path.open('x') as f:
   for r in map(json.loads,rp.open()):
    nid=r['id'];count,capacity=native[nid];assert capacity==r['capacity'] and count>=0;forecast=min(count,capacity);clipped+=forecast!=count;f.write(json.dumps(dict(id=nid,forecast_count=forecast,native_count=count,capacity=capacity),separators=(',',':'))+'\n')
  proof=out/'verification.json';proof.write_text(json.dumps(dict(case=case,iteration=iteration,status='FULL_DOMAIN_CAPACITY_RANGE_SCORE_PROJECTION',clipped_resources=clipped,score_file=str(path),bindings={str(p):sha(p) for p in [source,rp,dp,path,D/'protocol.json']},scope=protocol['scope']),indent=2)+'\n');rows.append(dict(case=case,status='SCORES_READY',verification=str(proof),sha256=sha(proof)));print('CAPACITY_SCORE_FORECAST',case,clipped,flush=True)
 (D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings={str(D/'protocol.json'):sha(D/'protocol.json')},strict_unseen_admitted=False),indent=2)+'\n')
if __name__=='__main__':main()
