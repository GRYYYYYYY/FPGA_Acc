"""Refine geometric pools by direct class access; no full equivalence claim."""
import json,shutil
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from prepared_csr import read
from pre_route_endpoints import sha
from pooled_channel_pressure import payload

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_access_pressure_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('prepare_cw32_access_pressure.py','prepared_csr.py','pre_route_endpoints.py','pooled_channel_pressure.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 parent=root/'experiments/multiplier_cw32_pool_connectivity_2026-10-06';pr=json.loads((parent/'receipt.json').read_text());protocol={'parent_receipt_sha256':sha(parent/'receipt.json'),'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'rule':'refine geometry/direction/segment pool by ordered direct SOURCE class set and SINK class set; coefficient1 sum positive per-track excess / refined capacity','scope':'Complete exposed development cohort. Direct class access only, not identical OPIN/IPIN identities, multi-hop feasibility or electrical/native interchangeability. No native outcomes read.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');reports=[]
 for case in pr['results']:
  name=case['design'];poolsfile=parent/name/'pools.json';assert sha(poolsfile)==case['pools_sha256'];pools=json.loads(poolsfile.read_text());prepared=root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name;cp=json.loads((prepared/'protocol.json').read_text());m,f=read(prepared/'csr',cp['graph']['sha256']);predroot=root/'experiments/multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset';r=json.loads((predroot/'receipt.json').read_text());assert sha(predroot/'prediction.json')==r['prediction_sha256'];pred=json.loads((predroot/'prediction.json').read_text());assert pred['physical_graph_sha256']==cp['graph']['sha256'];occ={int(k):v for k,v in pred['node_occupancy'].items()};groups=[]
  for pool in pools:
   refined=defaultdict(list)
   for n in pool['nodes']:refined[(tuple(pool['source_class_access_by_node'][str(n)]),tuple(pool['sink_class_access_by_node'][str(n)]))].append(n)
   groups.extend(refined.values())
  included={n for g in groups for n in g};eligible={n for n,c in enumerate(f['capacities']) if c>0 and f['types'][n] in (4,5)};groups.extend([n] for n in sorted(eligible-included));assert sum(map(len,groups))==len(eligible)
  pressure={};proofs=[]
  for nodes in groups:
   capacity=sum(f['capacities'][n] for n in nodes);excess=sum(max(0,occ.get(n,0)-f['capacities'][n]) for n in nodes)
   if excess:
    value=1+Fraction(excess,capacity);pressure.update({n:(f['capacities'][n],value) for n in nodes});assert sum(f['capacities'][n]*(value-1) for n in nodes)==excess;proofs.append({'nodes':nodes,'capacity':capacity,'excess':excess})
  dest=out/name;dest.mkdir();(dest/'candidate.pressure').write_text(payload(m['nodes'],cp['graph']['sha256'],pressure));(dest/'proofs.json').write_text(json.dumps(proofs)+'\n');report={'design':name,'eligible_channel_nodes':len(eligible),'refined_groups':len(groups),'multitrack_refined_groups':sum(len(g)>1 for g in groups),'active_groups':len(proofs),'active_multitrack_groups':sum(len(g['nodes'])>1 for g in proofs),'pressure_rows':len(pressure),'channel_excess':sum(p['excess'] for p in proofs),'pressure_sha256':sha(dest/'candidate.pressure'),'proofs_sha256':sha(dest/'proofs.json'),'prediction_receipt_sha256':sha(predroot/'receipt.json'),'pool_report_sha256':sha(poolsfile)};reports.append(report);print(json.dumps(report),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':reports},indent=2)+'\n')
if __name__=='__main__':main()
