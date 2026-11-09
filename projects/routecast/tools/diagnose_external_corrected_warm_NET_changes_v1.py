"""Exact perNET unique-node initialization changes and signed spatial deltas, all3."""
import json,sys,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from zero_rc_budget_certificate_graph_v1 import load_graph
from native_route_ledger_import_compact import physical_paths
E=R/'experiments';I=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19';P=E/'prospective_external_family_corrected_epoch_predictions_v1_2026-10-19';D=E/'prospective_external_family_corrected_warm_NET_attribution_v1_2026-10-19';G=E/'prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/rr_graph.xml'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 audit=read(P/'independent_metrics_verification_v1.json');assert all(sha(k)==h for k,h in audit['bindings'].items());D.mkdir(exist_ok=False);g=load_graph(G);bindings={str(P/'independent_metrics_verification_v1.json'):sha(P/'independent_metrics_verification_v1.json'),str(G):sha(G),str(Path(__file__).resolve()):sha(__file__)};sourcepath=I/'source_checkpoint/initial.json';source=read(sourcepath);bindings[str(sourcepath)]=sha(sourcepath)
 def expand(frame):
  records=defaultdict(dict);owners=defaultdict(set)
  for q in frame['records']:
   net=q['net_id'];records[net][q['connection_id']]=q;u=q['source'];nodes={u}
   for eid in q['answer']['physical_edge_ids']:assert g['us'][eid]==u;u=g['vs'][eid];nodes.add(u)
   assert u==q['sink'];owners[net].update(nodes)
  ledger=Counter(n for ns in owners.values() for n in ns);assert dict(ledger)=={int(n):v for n,v in frame['ledger'].items()};return records,owners,ledger
 old,oldowners,oldledger=expand(source);summaries=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';spec=read(P/case/'comparison_spec.json');warm=I/'warm'/case/'native_retained';wp=warm/'verification.json';proof=read(wp);assert all(sha(k)==h for k,h in proof['bindings'].items());fp=warm/'initial.json';frame=read(fp);current,owners,ledger=expand(frame);events={e['net_id']:e for e in read(warm/'initializer_events.json')};assert old.keys()==current.keys()
  domain=Path(spec['domain_proof']).parent;resources=[json.loads(x) for x in (domain/'resources.jsonl').read_text().splitlines()];bins=read(domain/'spatial_bins.json');rb={r['id']:[tuple(b) for b in r['bins']] for r in resources};caps={tuple(b['key']):b['capacity'] for b in bins};pernet=[];delta=Counter();bin_delta=Counter();cats=defaultdict(lambda:dict(nets=0,CIDs=0,retained_CIDs=0,changed_paths=0,added_nodes=0,removed_nodes=0,added_channel_nodes=0,removed_channel_nodes=0,spatial_absolute_perNET_changes=0));percat=defaultdict(Counter)
  for net in sorted(old):
   a,b=old[net],current[net];assert a.keys()==b.keys();source_changed=any(a[c]['source']!=b[c]['source'] for c in a);sink_changed=any(a[c]['sink']!=b[c]['sink'] for c in a);dirty=source_changed or sink_changed;assert dirty==(net in events);category='source_moved' if source_changed else 'sink_only' if sink_changed else 'clean';event=events.get(net,{});category+='/fallback' if event.get('whole_NET_fallback') else '/retained_expand' if dirty else ''
   add=owners[net]-oldowners[net];remove=oldowners[net]-owners[net];changed=sum(a[c]['answer']['physical_edge_ids']!=b[c]['answer']['physical_edge_ids'] for c in a);retained=sum(a[c]['answer']['physical_edge_ids']==b[c]['answer']['physical_edge_ids'] for c in a)
   if not dirty:assert a==b and not add and not remove
   for cid in event.get('retained_connection_ids',[]):assert a[cid]['answer']==b[cid]['answer']
   netbins=Counter()
   for node in add:
    delta[node]+=1
    for key in rb.get(node,[]):bin_delta[key]+=1;netbins[key]+=1
   for node in remove:
    delta[node]-=1
    for key in rb.get(node,[]):bin_delta[key]-=1;netbins[key]-=1
   c=cats[category];c['nets']+=1;c['CIDs']+=len(a);c['retained_CIDs']+=retained;c['changed_paths']+=changed;c['added_nodes']+=len(add);c['removed_nodes']+=len(remove);c['added_channel_nodes']+=sum(n in rb for n in add);c['removed_channel_nodes']+=sum(n in rb for n in remove);c['spatial_absolute_perNET_changes']+=sum(abs(v) for v in netbins.values());percat[category].update(netbins)
   if dirty:pernet.append(dict(net_id=net,category=category,CIDs=len(a),changed_paths=changed,retained_paths=retained,attempted_retained=len(event['attempted_retained_connection_ids']),repair_calls=event['repair_calls'],fallback_reason=event['fallback_reason'],added_nodes=sorted(add),removed_nodes=sorted(remove),spatial_delta=[dict(bin=list(k),delta=v) for k,v in sorted(netbins.items()) if v]))
  expected={n:ledger.get(n,0)-oldledger.get(n,0) for n in set(ledger)|set(oldledger)};assert {n:v for n,v in delta.items() if v}=={n:v for n,v in expected.items() if v}
  def totals(l):
   result=Counter()
   for n,ks in rb.items():
    for key in ks:result[key]+=l.get(n,0)
   return result
  prior_bins,new_bins=totals(oldledger),totals(ledger);assert all(bin_delta[k]==new_bins[k]-prior_bins[k] for k in caps)
  truth=read(spec['label_physical_audit']);truthbins=totals({int(n):v for n,v in truth['node_occupancy'].items()});truth_top=sorted(caps,key=lambda k:(-truthbins[k]/caps[k],k))[:20];source_top=sorted(caps,key=lambda k:(-prior_bins[k]/caps[k],k))[:20];warm_top=sorted(caps,key=lambda k:(-new_bins[k]/caps[k],k))[:20];lost=set(truth_top)&set(source_top)-set(warm_top)
  explanation=[dict(bin=list(k),source_count=prior_bins[k],warm_count=new_bins[k],truth_count=truthbins[k],delta=new_bins[k]-prior_bins[k],by_category={cat:ds[k] for cat,ds in percat.items() if ds[k]}) for k in sorted(lost)]
  out=D/case;out.mkdir(parents=True);(out/'dirty_NETs.json').write_text(json.dumps(pernet)+'\n');summary=dict(case=case,dirty_NETs=len(events),fallback_NETs=sum(e['whole_NET_fallback'] for e in events.values()),categories=dict(cats),source_truth_top20_hits=len(set(source_top)&set(truth_top)),warm_truth_top20_hits=len(set(warm_top)&set(truth_top)),lost_source_true_hot_bins=explanation,top_NETs_by_spatial_change=[{k:v for k,v in r.items() if k not in ('added_nodes','removed_nodes','spatial_delta')}|dict(spatial_absolute_change=sum(abs(x['delta']) for x in r['spatial_delta'])) for r in sorted(pernet,key=lambda r:-sum(abs(x['delta']) for x in r['spatial_delta']))[:5]]);summaries.append(summary)
  for path in [wp,fp,warm/'initializer_events.json',out/'dirty_NETs.json',Path(spec['label_physical_audit']),domain/'resources.jsonl',domain/'spatial_bins.json']:bindings[str(path)]=sha(path)
  print(json.dumps({k:v for k,v in summary.items() if k!='lost_source_true_hot_bins'}),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'diagnosis.json').write_text(json.dumps(dict(status='ALL3_DIRTY_NET_NODE_AND_INCLUSIVE_BIN_DELTAS_EXACTLY_RECONSTRUCTED',rows=summaries,bindings=bindings,scope='Unique-NET ownership deltas, not additive CID double counts. Actual fixed warm initialization only; fallback absent is explicitly reported. Labels used only for posthoc hot-bin attribution, never initializer or policy selection. No causal rerouting or quality acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
