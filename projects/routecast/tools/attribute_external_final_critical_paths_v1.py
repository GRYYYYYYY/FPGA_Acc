"""Native atom map + canonical indexed SINK + original CID endpoints; worst path only."""
import json,csv,re,hashlib
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];M=R/'experiments/prospective_external_family_final_atom_mapping_v1_2026-10-19';C=R/'experiments/prospective_external_family_seed_retention_delay_diagnosis_v1_2026-10-19';D=R/'experiments/prospective_external_family_final_critical_path_attribution_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 v=read(M/'verification.json');assert v['all6_parity_pass'];assert all(sha(p)==h for p,h in v['bindings'].items());D.mkdir(exist_ok=False);bindings={str(M/'verification.json'):sha(M/'verification.json'),str(Path(__file__).resolve()):sha(__file__)};results=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';p=C/case/'connections.json';cohort=read(p);bindings[str(p)]=sha(p);lookup=defaultdict(list)
  for q in cohort:lookup[(q['net_name'],q['source_rr'],q['sink_rr'])].append(q)
  for arm in ('cold','seed'):
   folder=M/case/arm;mapping=folder/'atom_mapping.tsv';route=folder/'design.route';report=folder/'report_timing.setup.rpt'
   for p in (mapping,route,report):bindings[str(p)]=sha(p)
   atoms={}
   for q in csv.DictReader(mapping.open(),delimiter='\t'):
    k=(q['atom'],q['port'],int(q['bit']));assert k not in atoms;atoms[k]=q
   terminals={};net=None;source=None
   for line in route.open():
    if m:=re.match(r'Net \d+ \((.*)\)',line):net=m[1];source=None
    elif m:=re.match(r'Node:\s*(\d+)\s+SOURCE',line):source=int(m[1])
    elif m:=re.match(r'Node:\s*(\d+)\s+SINK.*Net_pin_index:\s*(\d+)',line):
     k=(net,int(m[2]));assert source is not None and k not in terminals;terminals[k]=(source,int(m[1]))
   text=report.read_text().split('#Path 2')[0];rows=[]
   for line in text.splitlines():
    m=re.match(r'(.+)\.(in|D|outpad)\[(\d+)\]\s+\(([^)]+)\)\s+([-0-9.]+)\s+([-0-9.]+)',line)
    if not m:continue
    k=(m[1],m[2],int(m[3]));assert k in atoms,('missing atom pin',k);a=atoms[k];row=dict(atom=k[0],port=k[1],bit=k[2],report_increment_ns=float(m[5]),report_arrival_ns=float(m[6]),atom_net=a['atom_net'],cluster=a['cluster'])
    if a['cluster_pin']:
     assert int(a['local_pin'])>0;source,sink=terminals[(a['cluster_net'],int(a['local_pin']))];candidates=lookup[(a['cluster_net'],source,sink)];assert candidates
     fields=['seed_admitted','seed_path_preserved','cold_delay_as','final_delay_as','delta_as','initial_raw_criticality']
     assert len({tuple(q[f] for f in fields) for q in candidates})==1
     row.update(classification='EXTERNAL_NATIVE_CID',native_net_name=a['cluster_net'],canonical_local_pin=int(a['local_pin']),source_rr=source,sink_rr=sink,CID_candidates=[q['connection_id'] for q in candidates],**{f:candidates[0][f] for f in fields})
    else:row['classification']='NO_EXTERNAL_CLUSTER_PIN'
    rows.append(row)
   assert rows
   ext=[r for r in rows if r['classification']=='EXTERNAL_NATIVE_CID'];summary=dict(case=case,arm=arm,report_sink_points=len(rows),external_points=len(ext),internal_points=len(rows)-len(ext),external_worse=sum(q['delta_as']>0 for q in ext),external_better=sum(q['delta_as']<0 for q in ext),preserved_worse=sum(q['seed_path_preserved'] and q['delta_as']>0 for q in ext),sum_external_delta_as=sum(q['delta_as'] for q in ext),largest_positive_external_delta=sorted([q for q in ext if q['delta_as']>0],key=lambda q:-q['delta_as'])[:3]);results.append(summary)
   out=D/case/arm;out.mkdir(parents=True);(out/'worst_path_points.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(summary),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'attribution.json').write_text(json.dumps(dict(status='ALL6_WORST_PATH_INPUT_POINTS_NATIVE_MAPPED',rows=results,bindings=bindings,scope='Canonical replays byte-identical setup/hold/net/route. Native atom lookup only, no fuzzy atom names. Repeated endpoint CID candidates retained explicitly; raw delays invariant across candidates. External raw sum excludes internal/cell delays and is not full counterfactual STA. Internal rows need separate timing arc analysis; mapping not independently replayed.'),indent=2)+'\n')
if __name__=='__main__':main()
