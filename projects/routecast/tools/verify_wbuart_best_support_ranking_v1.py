"""Independent witness bitset scatter and descriptive rank metric audit."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction as F
from prediction_metrics import compare
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_best_support_ranking_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def normalize(resources,bins,counts):
 r={};s=Counter()
 for n in resources:
  node=n['id'];r[node]=F(counts.get(node,0),n['capacity'])
  for key in n['bins']:s[tuple(key)]+=counts.get(node,0)
 return {'resource':r,'spatial':{tuple(b['key']):F(s[tuple(b['key'])],b['capacity']) for b in bins}}
def main():
 source=D/'verification.json';v=read(source);assert all(sha(p)==h for p,h in v['bindings'].items());graphs={};rows=[];vectors=0
 for row in v['rows']:
  ep=read(row['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(x.get('sink_node')) for _,x in ET.iterparse(g) if x.tag=='edge']
  dest=graphs[g];resources=[json.loads(x) for x in Path(row['resources']).read_text().splitlines()];ids=sorted(x['id'] for x in resources);masks={n:1<<i for i,n in enumerate(ids)};counts=Counter();initial=defaultdict(list);out=Path(row['output']);receipt=read(out/'receipt.json')
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  selected=read(row['diagnostic_payload']);assert selected['label_dependent'] is True and selected['admitted_predictor'] is False;origins={w['net_id']:w['origin'] for w in selected['witnesses']}
  for n in read(row['payload']):
   net=n['net_id'];origin=origins[net];assert origin==n['best']['origin']
   if origin.get('stage')=='initial':records=initial[net]
   else:
    event=receipt['rounds'][origin['round']]['events'][origin['event_index']];assert event['net_id']==net and event['status']==origin['status'];records=event.get('records',event.get('rejected_records'))
   value=0
   for q in records:
    for eid in q['answer']['physical_edge_ids']:value|=masks.get(dest[eid],0)
   expected=0
   for node in n['best']['CHANNEL_nodes']:expected|=masks[node]
   assert value==expected
   while value:
    bit=value&-value;counts[ids[bit.bit_length()-1]]+=1;value-=bit
  assert dict(counts)=={int(n):c for n,c in selected['CHANNEL_counts'].items()};bins=read(Path(row['resources']).parent/'spatial_bins.json');domain=read(row['domain_proof']);truth=normalize(resources,bins,{int(n):c for n,c in read(row['truth_payload'])['node_occupancy'].items()});methods={'best_support_label_diagnostic':counts,'previous_native':{int(n):c for n,c in read(row['source_frame'])['ledger'].items()},'actual_raw_min':{int(n):c for n,c in read(row['raw_control'])['ledger'].items()}};metrics={}
  for method,value in methods.items():
   scores=normalize(resources,bins,value);metrics[method]={};vectors+=1
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    m=compare(scores[scope],truth[scope],k);got=row['metrics'][method][scope];assert got['k']==k and got['hits']==round(m['precision_at_k']*k);assert (m['spearman'] is None and got['rho'] is None) or m['spearman'] is not None and abs(m['spearman']-got['rho'])<=1e-12;metrics[method][scope]={'rho':m['spearman'],'hits':got['hits']}
  checks={}
  for control in ['previous_native','actual_raw_min']:
   nonreg=[];strict=[]
   for scope in ['resource','spatial']:
    a,b=metrics['best_support_label_diagnostic'][scope],metrics[control][scope];valid=a['rho'] is not None and b['rho'] is not None;nonreg.extend([valid and a['rho']>=b['rho']-1e-12,a['hits']>=b['hits']]);strict.extend([valid and a['rho']>b['rho']+1e-12,a['hits']>b['hits']])
   checks[control]=all(nonreg) and any(strict)
  assert checks==row['numeric_diagnostic_comparisons'] and all(checks.values())==row['both_numeric_comparisons'];rows.append({k:row[k] for k in ['case','initializer','timing_policy','priority','both_numeric_comparisons']});print(row['case'],row['initializer'],row['timing_policy'],row['priority'],'LABEL_DIAGNOSTIC_VERIFIED',flush=True)
 assert len(rows)==72 and vectors==216
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL72_LABEL_DEPENDENT_WITNESSES_SCATTER_AND216_METRIC_VECTORS_VERIFIED','rows':rows,'metric_vectors':vectors,'bindings':{str(source):sha(source),str(Path(__file__)):sha(__file__),str(R/'tools/prediction_metrics.py'):sha(R/'tools/prediction_metrics.py'),str(D/'protocol.json'):sha(D/'protocol.json')},'scope':'Pure retrospective diagnostic; no deployment admission, original predictor gate changes, full joint legality or time gain.'},indent=2)+'\n');print('BEST_SUPPORT_DIAGNOSTIC_VERIFIED',vectors)
if __name__=='__main__':main()
