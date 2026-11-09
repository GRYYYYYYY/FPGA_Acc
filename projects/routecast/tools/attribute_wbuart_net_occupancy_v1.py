"""Posthoc additive NET-category occupancy attribution, no routing or tuning."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_net_occupancy_attribution_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);P=E/'wbuart_quality_stage_diagnosis_v1_2026-10-20/verification.json';v=read(P);B=E/'wbuart_native_target_budget_diagnosis_v1_2026-10-20/verification.json';b=read(B);bindings={str(p.resolve()):sha(p) for p in [Path(__file__),P,B]};rows=[];graphs={}
 for case in v['rows']:
  meta=next(r for r in b['rows'] if r['case']==case['case']);ep=read(meta['endpoint']);g=ep['inputs']['graph']['path'];digest=sha(g)
  if digest not in graphs:
   ends=[]
   for event,e in ET.iterparse(g):
    if e.tag=='edge':ends.append((int(e.get('src_node')),int(e.get('sink_node'))))
   graphs[digest]=ends
  edges=graphs[digest];bindings[g]=digest;queries={q['connection_id']:q for q in ep['connections']};source=read(case['stages'][0]['frame']);prior={q['connection_id']:q for q in source['records']};cats={};rank={'endpoint_unchanged':0,'sink_only':1,'source_moved':2}
  for cid,q in queries.items():
   old=prior[cid];c='source_moved' if q['source']!=old['source'] else 'sink_only' if q['sink']!=old['sink'] else 'endpoint_unchanged'
   if rank[c]>rank.get(cats.get(q['net_id']),-1):cats[q['net_id']]=c
  resources=read(Path(meta['warm_directory'])/'verification.json')
  specification=next(c for c in read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons'] if c['case']==case['case']);spec=read(specification['specification']);domainpath=Path(spec['domain_proof']).parent/'resources.jsonl';ids={json.loads(s)['id'] for s in domainpath.read_text().splitlines()};truth={int(n):x for n,x in read(spec['label_physical_audit'])['node_occupancy'].items()};bindings[str(domainpath)]=sha(domainpath);bindings[spec['label_physical_audit']]=sha(spec['label_physical_audit'])
  def supports(state):
   nets=defaultdict(set)
   for q in state['records']:
    u=q['source'];nets[q['net_id']].add(u)
    for eid in q['answer']['physical_edge_ids']:
     a,z=edges[eid];assert a==u;u=z;nets[q['net_id']].add(u)
    assert u==q['sink']
   ledger=Counter(n for ns in nets.values() for n in ns);assert dict(ledger)=={int(n):x for n,x in state['ledger'].items()};return nets,ledger
  original,base=supports(source);stages=[]
  for stage in case['stages']:
   state=read(stage['frame']);current={q['connection_id']:q for q in state['records']};nets,ledger=supports(state);categories={};delta=Counter()
   for cat in rank:
    ns=[n for n in cats if cats[n]==cat];removed=Counter(n for net in ns for n in (original[net]-nets[net])&ids);added=Counter(n for net in ns for n in (nets[net]-original[net])&ids)
    for n,x in added.items():delta[n]+=x
    for n,x in removed.items():delta[n]-=x
    same=[cid for cid,q in queries.items() if cats[q['net_id']]==cat and (q['source'],q['sink'])==(prior[cid]['source'],prior[cid]['sink'])];changed=sum((current[cid]['source'],current[cid]['answer']['physical_edge_ids'])!=(prior[cid]['source'],prior[cid]['answer']['physical_edge_ids']) for cid in same)
    categories[cat]={'NETs':len(ns),'channel_owner_additions':sum(added.values()),'channel_owner_removals':sum(removed.values()),'unchanged_endpoint_CIDs':len(same),'unchanged_endpoint_CIDs_path_changed':changed}
   assert all(delta[n]==ledger[n]-base[n] for n in ids)
   old=sum(abs(base[n]-truth.get(n,0)) for n in ids);new=sum(abs(ledger[n]-truth.get(n,0)) for n in ids)
   stages.append({'stage':stage['stage'],'categories':categories,'source_channel_occupancy_L1_error':old,'channel_occupancy_L1_error':new,'error_delta_vs_source':new-old,'aggregate_delta_reconstruction_exact':True});bindings[stage['frame']]=sha(stage['frame'])
  rows.append({'case':case['case'],'stages':stages});print(case['case'],[(s['stage'],s['error_delta_vs_source']) for s in stages if s['stage'].startswith('native_retained')],flush=True)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL99_NET_CATEGORY_OWNER_DELTAS_RECONSTRUCT_ORIGINAL_LEDGERS','rows':rows,'bindings':bindings,'scope':'Posthoc CHANNEL occupancy L1 diagnostic, not replacement for original rank/topK gates. NET categories use maximum endpoint edit; changed path includes shared NET effects. No causal attribution or label tuning.'},indent=2)+'\n')
if __name__=='__main__':main()
