"""Conservative all-owner closures using existing native target trees, no routing."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_donor_closure_diagnosis_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);P=E/'wbuart_native_warm_snapshot_rescore_v1_2026-10-20/verification.json';proof=read(P);cross=P.parent/'implementation_crosscheck_v1.json';assert len(read(cross)['rows'])==9;bindings={str(p):sha(p) for p in [Path(__file__),P,cross]};graphs={};rows=[]
 for c in proof['rows']:
  ep=read(c['endpoint']);graph=ep['inputs']['graph']['path']
  if graph not in graphs:
   caps=[];dest=[]
   for _,e in ET.iterparse(graph):
    if e.tag=='node' and e.get('capacity') is not None:assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')))
    elif e.tag=='edge':dest.append(int(e.get('sink_node')))
   graphs[graph]=caps,dest;bindings[graph]=sha(graph)
  caps,dest=graphs[graph];warm=read(c['warm_frame']);old=defaultdict(set);owners=defaultdict(set)
  for q in warm['records']:old[q['net_id']].add(q['source']);old[q['net_id']].update(dest[e] for e in q['answer']['physical_edge_ids'])
  for net,ns in old.items():
   for n in ns:owners[n].add(net)
  ledger={n:len(ns) for n,ns in owners.items()};assert ledger=={int(n):x for n,x in warm['ledger'].items()};target={};refs={q['net_id']:q for q in read(c['payload'])}
  for net,q in refs.items():target[net]={r['source'] for r in q['native_records']}|{dest[e] for r in q['native_records'] for e in r['answer']['physical_edge_ids']}
  final=Counter(n for ns in target.values() for n in ns);assert all(x<=caps[n] for n,x in final.items());deps={n:set().union(*(owners[node] for node in target[n]-old[n]))-{n} if target[n]-old[n] else set() for n in old};initial_overflow=sum(max(0,x-caps[n]) for n,x in ledger.items());groups={};roots=[]
  for root,q in sorted(refs.items()):
   if q['overflow_delta']<=0:continue
   closure={root};pending=[root]
   while pending:
    n=pending.pop()
    for donor in deps[n]-closure:closure.add(donor);pending.append(donor)
   key=tuple(sorted(closure))
   if key not in groups:
    index=len(groups);removed=Counter(n for net in closure for n in old[net]);added=Counter(n for net in closure for n in target[net]);changed=set(removed)|set(added);delta=sum(max(0,ledger.get(n,0)-removed[n]+added[n]-caps[n])-max(0,ledger.get(n,0)-caps[n]) for n in changed);assert delta<=0;badnets=sorted(n for n in closure if refs[n]['budget_violating_CIDs']);groups[key]={'group_id':index,'NETs':list(key),'size':len(key),'joint_overflow_delta':delta,'resulting_overflow_units':initial_overflow+delta,'budget_incompatible_NETs':badnets,'all_target_paths_budget_compatible':not badnets,'objective_admission_evaluated':False}
   group=groups[key];roots.append({'root_NET':root,'root_single_overflow_delta':q['overflow_delta'],'root_budget_compatible':not q['budget_violating_CIDs'],'root_coverage':q['coverage'],'group_id':group['group_id']})
  d=D/c['case'];d.mkdir(parents=True);p=d/'groups.json';p.write_text(json.dumps({'dependency_adjacency':{str(n):sorted(ds) for n,ds in deps.items()},'roots':roots,'groups':list(groups.values())})+'\n');sizes=[groups[next(k for k,g in groups.items() if g['group_id']==r['group_id'])]['size'] for r in roots];summary={'case':c['case'],'endpoint':c['endpoint'],'warm_frame':c['warm_frame'],'native_reference_payload':c['payload'],'payload':str(p),'pressure_blocked_roots':len(roots),'unique_closures':len(groups),'root_closure_size_min':min(sizes) if sizes else None,'root_closure_size_max':max(sizes) if sizes else None,'unique_budget_compatible_closures':sum(g['all_target_paths_budget_compatible'] for g in groups.values()),'unique_closures_size_le2':sum(g['size']<=2 for g in groups.values()),'initial_overflow_units':initial_overflow};rows.append(summary);print(summary,flush=True)
  for p in [p,Path(c['warm_frame']),Path(c['payload']),Path(c['endpoint'])]:bindings[str(p)]=sha(p)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_CONSERVATIVE_DONOR_CLOSURES_JOINT_PRESSURE_RECONSTRUCTED','rows':rows,'bindings':bindings,'scope':'Conservative dependencies include ALL warm owners on newly acquired target resources, even when capacity would allow a smaller subset; closures are sufficient, not necessary or minimum. Existing label-directed reference trees only, no executable policy/joint objective qualification, no budget or guard relaxation/promotion.'},indent=2)+'\n')
if __name__=='__main__':main()
