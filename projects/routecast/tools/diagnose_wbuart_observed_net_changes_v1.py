"""All-nine signed per-NET CHANNEL change prediction versus frozen cold labels."""
import json,hashlib,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_observed_net_changes_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);W=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';S=E/'wbuart_quality_stage_diagnosis_v1_2026-10-20/verification.json';T=E/'wbuart_strict_progress_trial_v1_2026-10-20/research_decision_v1.json';bindings={str(p):sha(p) for p in [Path(__file__),W,S,T]};stages=read(S);strict=read(T);graphs={};rows=[]
 for c in read(W)['comparisons']:
  spec=read(c['specification']);ep=read(spec['endpoint']);g=ep['inputs']['graph']['path'];digest=sha(g)
  if digest not in graphs:
   edges=[]
   for _,e in ET.iterparse(g):
    if e.tag=='edge':edges.append((int(e.get('src_node')),int(e.get('sink_node'))))
   graphs[digest]=edges
  edges=graphs[digest];resources=Path(spec['domain_proof']).parent/'resources.jsonl';ids={json.loads(x)['id'] for x in resources.read_text().splitlines()};bindings[g]=digest;bindings[str(resources)]=sha(resources)
  def support(frame):
   state=read(frame);nets=defaultdict(set)
   for q in state['records']:
    u=q['source'];nets[q['net_id']].add(u)
    for eid in q['answer']['physical_edge_ids']:
     a,z=edges[eid];assert a==u;u=z;nets[q['net_id']].add(u)
    assert u==q['sink']
   ledger=Counter(n for nodes in nets.values() for n in nodes);assert dict(ledger)=={int(n):x for n,x in state['ledger'].items()};bindings[str(frame)]=sha(frame);return {n:s&ids for n,s in nets.items()},state
  source,prior=support(spec['source_frame']);old={q['connection_id']:q for q in prior['records']};dirty=set();source_moved=set()
  for q in ep['connections']:
   a=old[q['connection_id']]
   if (q['source'],q['sink'])!=(a['source'],a['sink']):dirty.add(q['net_id'])
   if q['source']!=a['source']:source_moved.add(q['net_id'])
  names={name:int(n) for n,name in ep['net_names'].items() if int(n) in source};target=defaultdict(set);current=None;route=Path(spec['label_physical_audit']).parent/'output.route'
  for line in route.read_text().splitlines():
   m=re.match(r'Net\s+\d+\s+\((.*?)\)',line)
   if m:current=names.get(m[1]);continue
   m=re.match(r'\s*Node:\s*(\d+)',line)
   if m and current is not None:target[current].add(int(m[1]))
  assert set(target)==set(source);ledger=Counter(n for nodes in target.values() for n in nodes);audit=read(spec['label_physical_audit']);assert dict(ledger)=={int(n):x for n,x in audit['node_occupancy'].items()};target={n:s&ids for n,s in target.items()};bindings[str(route)]=sha(route);bindings[spec['label_physical_audit']]=sha(spec['label_physical_audit'])
  frames=next(r['stages'] for r in stages['rows'] if r['case']==c['case']);chosen={'warm':next(s['frame'] for s in frames if s['stage']=='native_retained/warm'),'original_primary':spec['predictions']['native_retained_on']['frame'],'strict_primary':str(Path(next(r['counts'] and a['strict_output'] for a in read(E/'wbuart_strict_progress_trial_v1_2026-10-20'/c['case']/'verification.json')['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated' for r in strict['rows'][:1]))/'sketch.json')};methods={}
  def signed(a,b):return {(n,1) for n in b-a}|{(n,-1) for n in a-b}
  for method,path in chosen.items():
   pred,_=support(path);cats=defaultdict(Counter)
   for net in source:
    cat='source_moved' if net in source_moved else 'sink_only' if net in dirty else 'endpoint_unchanged';p=signed(source[net],pred[net]);t=signed(source[net],target[net]);x=cats[cat];x['NETs']+=1;x['observed_changed_NETs']+=bool(t);x['predicted_changed_NETs']+=bool(p);x['NETs_false_change']+=bool(p) and not t;x['NETs_missed_change']+=bool(t) and not p;x['correct_signed_changes']+=len(p&t);x['false_signed_changes']+=len(p-t);x['missed_signed_changes']+=len(t-p);x['predicted_target_support_symmetric_difference']+=len(pred[net]^target[net]);assert len(p-t)+len(t-p)>=len(pred[net]^target[net])
   methods[method]={k:dict(v) for k,v in cats.items()}
  rows.append({'case':c['case'],'methods':methods});print(c['case'],methods['strict_primary']['endpoint_unchanged'],flush=True)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_SIGNED_NET_CHANNEL_CHANGES_VERSUS_FROZEN_NATIVE_TARGET_RECONSTRUCTED','rows':rows,'bindings':bindings,'scope':'Posthoc per-NET CHANNEL support diagnosis; independently verifies target union against original physical ledger, not independent source/prediction graph parser. Cold target is one native solution; changes are solution-specific, not necessary routing changes. Signed false/missed counts diagnostic, original quality gates unchanged.'},indent=2)+'\n')
if __name__=='__main__':main()
