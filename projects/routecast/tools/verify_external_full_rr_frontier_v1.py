"""Independent XML identity/capacity and frontier accounting checks."""
import json,math,sys
from pathlib import Path
from collections import Counter
from xml.parsers import expat
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_full_rr_frontier_observer_v1_2026-10-19';B=R/'experiments/prospective_external_family_early_net_observer_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def load(path):
 nodes={};trees={};metadata=None
 for line in path.open():
  x=line.split()
  if x[0]=='F':assert metadata is None;metadata=x[1:]
  elif x[0]=='N':
   n=int(x[1]);assert n not in nodes;nodes[n]=dict(type=x[2],capacity=int(x[3]),occupancy=int(x[4]),history=float(x[5]),base=float(x[6]),present=float(x[7]),cost_index=int(x[8]))
  elif x[0]=='T':
   net=int(x[1]);ns=list(map(int,x[4:]));assert net not in trees and ns==sorted(set(ns)) and len(ns)==int(x[3]);trees[net]=set(ns)
  else:raise ValueError('unknown frontier row')
 assert metadata is not None;return metadata,nodes,trees

def main():
 manifest=read(D/'manifest.json');ep=read(manifest['cases'][0]['endpoint']);graph=ep['inputs']['graph']['path'];assert sha(graph)==ep['graph_sha256'];xml={};stack=[];parser=expat.ParserCreate()
 def start(tag,a):
  if tag=='node' and stack and stack[-1]=='rr_nodes':
   n=int(a['id']);assert n not in xml;xml[n]=(a['type'],int(a['capacity']))
  stack.append(tag)
 def end(tag):assert stack.pop()==tag
 parser.StartElementHandler=start;parser.EndElementHandler=end
 with open(graph,'rb') as f:parser.ParseFile(f)
 cases=[manifest['cases'][0]]
 if (D/'targets_terminal.json').exists():cases+=read(D/'target_manifest.json')['cases']
 rows=[];bindings={graph:sha(graph),str(Path(__file__).resolve()):sha(__file__)}
 for c in cases:
  folder=Path(c['output']);a=read(folder/'verification.json');assert a['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and all(sha(p)==h for p,h in a['bindings'].items());meta,nodes,trees=load(folder/'rr_frontier.tsv');assert meta[:3]==['2','1','2'] and float(meta[3])==.5;assert nodes.keys()==xml.keys() and len(nodes)==129090;owners=Counter(n for ns in trees.values() for n in ns);residual=Counter();types=Counter()
  for n,r in nodes.items():
   assert (r['type'],r['capacity'])==xml[n] and r['occupancy']>=0 and r['cost_index']>=0;assert all(math.isfinite(r[k]) for k in ['history','base','present']) and r['history']>=1 and r['base']>=0;occ,cap=r['occupancy'],r['capacity'];expected=1+.5*(occ+1-cap) if occ>=cap else 1;assert abs(r['present']-expected)<1e-6*max(1,expected);types[r['type']]+=1
   if occ!=owners[n]:residual[r['type']]+=1
   if r['type'] in ['CHANX','CHANY']:assert occ==owners[n]
  baseline=B/('source' if c['case']=='w160/observer_source' else c['case'])
  assert sha(folder/'early_net_trace.tsv')==sha(baseline/'early_net_trace.tsv') and sha(folder/'iteration_support.tsv')==sha(baseline/'iteration_support.tsv');row=dict(case=c['case'],nodes=len(nodes),NETs=len(trees),node_type_counts=dict(types),occupancy_vs_unique_NET_support_residual_nodes=dict(residual),prior_traces_byte_identical=True);rows.append(row)
  for p in [folder/'rr_frontier.tsv',folder/'verification.json',folder/'early_net_trace.tsv',folder/'iteration_support.tsv',baseline/'early_net_trace.tsv',baseline/'iteration_support.tsv']:bindings[str(p)]=sha(p)
 name='all_case_frontier_verification_v1.json' if len(cases)==4 else 'source_frontier_verification_v1.json'
 with (D/name).open('x') as f:json.dump(dict(status='FULL_RR_FRONTIER_XML_DOMAINS_COST_MULTIPLIERS_AND_CHANNEL_OWNER_COUNTS_VERIFIED',rows=rows,bindings=bindings,scope='NonCHANNEL occupancy may include local OPIN reservations or sink multiplicity, reported as residual rather than equated to unique NET unions. Single-resource multipliers not nonconfigurable group cost. Full RR snapshot is not complete internal router checkpoint.'),f,indent=2)
 print(json.dumps(rows))
if __name__=='__main__':main()
