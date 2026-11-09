"""Audit real objective tables, all packed recurrences, original supports and metrics."""
import json,itertools,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from exact_factor_elimination_v1 import sha,read_segment,verify_certificate
from prediction_metrics import compare
from verify_wbuart_best_support_ranking_v1 import normalize
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_exact_aggregate_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 source=D/'verification.json';v=read(source);manifest=read(D/'manifest.json')
 for doc in [v,manifest]:assert all(sha(p)==h for p,h in doc['bindings'].items())
 graphs={};rows=[];messages=0;cells=0
 for row in v['rows']:
  root=Path(row['certificate']);cert=read(root/'certificate.json');blob=read(row['reduced_payload']);f=blob['factors'];cards={int(n):d for n,d in f['cardinalities'].items()};start={int(n):c for n,c in blob['test_assignments'][0].items()};B=len(cards)+1
  assert row['B']==B and cert['initial_constant']==f['constant']*B and {int(n):d for n,d in cert['cardinalities'].items()}==cards
  assert cert['order']==[s['NET'] for s in blob['symbolic']['steps']]
  assert len(cert['inputs'])==len(cards)+len(blob['nonlinear_scope_groups'])
  terms={t['node']:t for t in f['nonlinear']}
  for i,entry in enumerate(cert['inputs']):
   values=read_segment(root,entry['table'],'initial_tables.bin',8*2**30)
   if i<len(cards):
    net=sorted(cards)[i];assert entry['scope']==[net]
    assert list(values)==[B*cost+(choice!=start[net]) for choice,cost in enumerate(f['unary'][str(net)])]
   else:
    group=blob['nonlinear_scope_groups'][i-len(cards)];scope=group['NETs'];assert entry['scope']==scope
    for index,value in enumerate(values):
     assignment={};q=index
     for net in reversed(scope):q,state=divmod(q,cards[net]);assignment[net]=state
     expected=sum(abs(t['fixed_count']+sum(pattern[assignment[int(net)]] for net,pattern in t['patterns'].items())-t['target']) for t in (terms[node] for node in group['CHANNELs']))*B
     assert value==expected
   cells+=len(values)
  proof=verify_certificate(root);messages+=proof['messages'];selected=proof['selected'];answer=read(row['diagnostic_payload']);assert selected=={int(n):c for n,c in answer['selected'].items()}
  ep=read(row['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.get('sink_node')) for _,e in ET.iterparse(g) if e.tag=='edge']
  dest=graphs[g];resources=[json.loads(x) for x in Path(row['resources']).read_text().splitlines()];ids={r['id'] for r in resources};pools=defaultdict(list);initial=defaultdict(list);final=defaultdict(list);out=Path(row['source_output'])
  def support(rs):return frozenset(dest[e] for q in rs for e in q['answer']['physical_edge_ids'] if dest[e] in ids)
  def add(net,rs):
   s=support(rs)
   if s not in pools[net]:pools[net].append(s)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for net,rs in sorted(initial.items()):add(net,rs)
  for rnd in read(out/'receipt.json')['rounds']:
   for event in rnd['events']:
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:add(event['net_id'],rs)
  for q in read(out/'round1.json')['records']:final[q['net_id']].append(q)
  assert cards=={n:len(cs) for n,cs in pools.items()} and start=={n:pools[n].index(support(rs)) for n,rs in final.items()}
  counts=Counter(node for net,cs in pools.items() for node in cs[selected[net]]);truthcounts={int(n):c for n,c in read(row['truth_payload'])['node_occupancy'].items()};loss=sum(abs(counts[n]-truthcounts.get(n,0)) for n in ids);switches=sum(selected[n]!=start[n] for n in cards)
  assert counts=={int(n):c for n,c in answer['CHANNEL_counts'].items()} and proof['objective']==B*loss+switches==row['encoded_objective'] and loss==row['minimum_L1'] and switches==row['minimum_switches'] and loss<=row['local_L1']
  assert answer['label_dependent'] and not answer['admitted_predictor'] and not row['admitted_predictor']
  bins=read(Path(row['resources']).parent/'spatial_bins.json');domain=read(row['domain_proof']);truth=normalize(resources,bins,truthcounts)
  methods={'exact_label_diagnostic':counts,'previous_native':{int(n):c for n,c in read(row['source_frame'])['ledger'].items()},'actual_raw_min':{int(n):c for n,c in read(row['raw_control'])['ledger'].items()}}
  for name,data in methods.items():
   normalized=normalize(resources,bins,data)
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    m=compare(normalized[scope],truth[scope],k);got=row['metrics'][name][scope];assert got['k']==k and got['hits']==round(m['precision_at_k']*k);assert (m['spearman'] is None and got['rho'] is None) or m['spearman'] is not None and abs(m['spearman']-got['rho'])<=1e-12
  checks={}
  for control in ['previous_native','actual_raw_min']:
   nonreg=[];strict=[]
   for scope in ['resource','spatial']:
    a,b=row['metrics']['exact_label_diagnostic'][scope],row['metrics'][control][scope];valid=a['rho'] is not None and b['rho'] is not None;nonreg.extend([valid and a['rho']>=b['rho']-1e-12,a['hits']>=b['hits']]);strict.extend([valid and a['rho']>b['rho']+1e-12,a['hits']>b['hits']])
   checks[control]=all(nonreg) and any(strict)
  assert checks==row['numeric_diagnostic_comparisons'] and all(checks.values())==row['both_numeric_comparisons']
  rows.append({k:row[k] for k in ['case','initializer','timing_policy','priority','minimum_L1','minimum_switches','local_L1','both_numeric_comparisons']});print('EXACT_AUDIT_PASS',len(rows),row['case'],row['initializer'],row['timing_policy'],row['priority'],flush=True)
 assert len(rows)==72 and len({tuple(r[k] for k in ['case','initializer','timing_policy','priority']) for r in rows})==72
 files=[source,Path(__file__),R/'tools/exact_factor_elimination_v1.py',R/'tools/compiled_exact_min_sum_v1.py',R/'tools/prediction_metrics.py',R/'tools/verify_wbuart_best_support_ranking_v1.py',D/'manifest.json']
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL72_REAL_OBJECTIVES_GLOBAL_CERTIFICATES_SUPPORTS_AND216_METRIC_VECTORS_VERIFIED','rows':rows,'messages':messages,'initial_table_cells':cells,'metric_vectors':216,'bindings':{str(p):sha(p) for p in files},'scope':'Target-dependent finite candidate pool aggregate L1 and secondary switches only. No forecast admission, capacity legality or native utility claim.'},indent=2)+'\n')
if __name__=='__main__':main()
