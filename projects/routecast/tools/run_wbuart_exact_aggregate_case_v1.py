"""All8 exact diagnostic arms for one fixed case, packed globally optimal certificates."""
import json,sys,xml.etree.ElementTree as ET,itertools
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from compiled_exact_min_sum_v1 import Factor
from exact_factor_elimination_v1 import solve,sha
from diagnose_wbuart_best_support_ranking_v1 import measure,numeric_comparison
from verify_wbuart_map_priority_metrics_v1 import scores
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def read(p):return json.loads(Path(p).read_text())
def main():
 manifest=Path(sys.argv[1]);m=read(manifest);assert all(sha(p)==h for p,h in m['bindings'].items());case=sys.argv[2];target=Path(m['output'])/case;target.mkdir(parents=True,exist_ok=False);profiles=read(m['reduced_profile'])['rows'];previous=read(m['local_diagnostics'])['rows'];rows=[];bindings={str(manifest):sha(manifest)};graphcache={}
 for row in [r for r in profiles if r['case']==case]:
  prior=next(r for r in previous if all(r[k]==row[k] for k in ['case','initializer','timing_policy','priority']));blob=read(row['payload']);f=blob['factors'];cards={int(n):d for n,d in f['cardinalities'].items()};start={int(n):c for n,c in blob['test_assignments'][0].items()};B=len(cards)+1;factors=[];groups=[]
  for net in sorted(cards):factors.append(Factor((net,),[v*B+int(i!=start[net]) for i,v in enumerate(f['unary'][str(net)])]));groups.append({'kind':'unary','NET':net})
  terms={t['node']:t for t in f['nonlinear']}
  for group in blob['nonlinear_scope_groups']:
   scope=tuple(group['NETs']);table=array('Q')
   for values in itertools.product(*(range(cards[n]) for n in scope)):
    loss=0
    for node in group['CHANNELs']:
     term=terms[node];count=term['fixed_count']+sum(term['patterns'][str(n)][state] for n,state in zip(scope,values));loss+=abs(count-term['target'])
    table.append(loss*B)
   factors.append(Factor(scope,table));groups.append({'kind':'nonlinear','CHANNELs':group['CHANNELs']})
  out=target/row['initializer']/row['timing_policy']/row['priority'];out.mkdir(parents=True,exist_ok=False);print('EXACT_START',case,row['initializer'],row['timing_policy'],row['priority'],row['largest_bag_states'],flush=True);answer=solve(cards,factors,[s['NET'] for s in blob['symbolic']['steps']],f['constant']*B,out/'certificate',max_bytes=8*2**30);cert=read(out/'certificate/certificate.json');assert all(step['separator']==planned['neighbors'] and step['variable']==planned['NET'] for step,planned in zip(cert['steps'],blob['symbolic']['steps']));ep=read(row['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphcache:graphcache[g]=[int(e.get('sink_node')) for _,e in ET.iterparse(g) if e.tag=='edge']
  dest=graphcache[g];channels={json.loads(x)['id'] for x in Path(row['resources']).read_text().splitlines()};source=Path(row['output']);initial=defaultdict(list);pools=defaultdict(list)
  def add(net,rs):
   s=frozenset(dest[e] for q in rs for e in q['answer']['physical_edge_ids'] if dest[e] in channels)
   if s not in pools[net]:pools[net].append(s)
  for q in read(source/'initial.json')['records']:initial[q['net_id']].append(q)
  for net,rs in sorted(initial.items()):add(net,rs)
  for rnd in read(source/'receipt.json')['rounds']:
   for event in rnd['events']:
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:add(event['net_id'],rs)
  assert cards=={n:len(cs) for n,cs in pools.items()};chosen=answer['selected'];counts=Counter(n for net,cs in pools.items() for n in cs[chosen[net]]);truthcounts={int(n):c for n,c in read(row['truth_payload'])['node_occupancy'].items()};loss=sum(abs(counts[n]-truthcounts.get(n,0)) for n in channels);switches=sum(chosen[n]!=start[n] for n in cards);assert answer['objective']==B*loss+switches and switches<B and loss<=prior['final_L1'];resources=[json.loads(x) for x in Path(row['resources']).read_text().splitlines()];bins=read(Path(row['resources']).parent/'spatial_bins.json');domain=read(prior['domain_proof']);truth=scores(resources,bins,truthcounts);metrics={name:measure(scores(resources,bins,data),truth,domain) for name,data in [('exact_label_diagnostic',counts),('previous_native',{int(n):c for n,c in read(prior['source_frame'])['ledger'].items()}),('actual_raw_min',{int(n):c for n,c in read(prior['raw_control'])['ledger'].items()})]};checks={name:numeric_comparison(metrics['exact_label_diagnostic'],metrics[name]) for name in ['previous_native','actual_raw_min']};payload=out/'label_exact_counts.json';payload.write_text(json.dumps({'label_dependent':True,'admitted_predictor':False,'CHANNEL_counts':dict(counts),'selected':chosen,'minimum_L1':loss,'minimum_switches_at_minimum_L1':switches,'encoded_objective':answer['objective']},separators=(',',':'))+'\n');result={key:row[key] for key in ['case','initializer','timing_policy','priority','output','endpoint','resources','truth_payload']};result.update(output=str(out),source_output=str(source),reduced_payload=row['payload'],certificate=str(out/'certificate'),diagnostic_payload=str(payload),factor_roles=groups,domain_proof=prior['domain_proof'],source_frame=prior['source_frame'],raw_control=prior['raw_control'],B=B,minimum_L1=loss,minimum_switches=switches,local_L1=prior['final_L1'],encoded_objective=answer['objective'],metrics=metrics,numeric_diagnostic_comparisons=checks,both_numeric_comparisons=all(checks.values()),admitted_predictor=False);rows.append(result);print('EXACT_DONE',case,row['initializer'],row['timing_policy'],row['priority'],loss,switches,result['both_numeric_comparisons'],flush=True)
  for path in [Path(row['payload']),payload,out/'certificate/certificate.json',Path(prior['domain_proof']),Path(prior['source_frame']),Path(prior['raw_control'])]:bindings[str(path)]=sha(path)
 assert len(rows)==8
 (target/'verification.json').write_text(json.dumps({'status':'ALL8_CASE_EXACT_AGGREGATE_DIAGNOSTIC_CERTIFICATES_PRODUCED','rows':rows,'bindings':bindings,'independent_certificate_verification_pending':True,'label_dependent':True},indent=2)+'\n')
if __name__=='__main__':main()
