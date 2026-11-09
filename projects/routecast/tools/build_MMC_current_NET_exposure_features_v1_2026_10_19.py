"""Fixed input-only features; current native-work vectors never opened."""
import pathlib,json,hashlib,struct,xml.etree.ElementTree as ET,time
from collections import defaultdict,Counter
from fractions import Fraction
from array import array
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 start=time.perf_counter();P=R/'experiments/mmc_current_NET_exposure_work_diagnostic_protocol_v1_2026-10-19/protocol.json';p=json.loads(P.read_text())
 for f,h in p['bindings'].items():assert sha(pathlib.Path(f))==h
 O=R/'experiments/mmc_current_NET_exposure_features_v1_2026-10-19';O.mkdir(exist_ok=False);B=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';bp=B/'independent_prediction_verification_v1.json';proof=json.loads(bp.read_text());bank=B/'NET_contributions.jsonl';assert proof['bindings'][str(bank)]==sha(bank);needed=defaultdict(list);risks={};expected={};netids={};features={};bindings={str(f):sha(f) for f in [P,bp,bank,pathlib.Path(__file__).resolve()]};graph=None;digest=None
 for plan in p['cases']:
  case=plan['case'];ep=pathlib.Path(plan['endpoint']);meta=json.loads(ep.read_text());g=pathlib.Path(meta['inputs']['graph']['path']);assert graph is None or (digest==meta['graph_sha256'] and sha(g)==digest);graph=g;digest=meta['graph_sha256'];groups=defaultdict(list)
  for q in meta['connections']:groups[q['net_id']].append(q)
  ids=sorted(groups);assert len(ids)==55300;netids[case]=ids;indices=json.loads(pathlib.Path(plan['contribution_indices']).read_text());assert len(indices)==55300;expected[case]={};features[case]={}
  for net,index in zip(ids,indices):
   qs=groups[net];sources={q['source'] for q in qs};assert len(sources)==1;expected[case][net]=(next(iter(sources)),tuple(sorted({q['sink'] for q in qs})));needed[index].append((case,net));features[case][net]=dict(manifest_fanout=Fraction(len(qs)))
  lines=pathlib.Path(plan['risk']).read_text().splitlines();header=lines[0].split();assert header[:3]==['RCRISK1',digest,'904438'];risk={}
  for line in lines[1:]:
   n,bits=map(int,line.split());assert n not in risk;risk[n]=Fraction.from_float(struct.unpack('<f',struct.pack('<I',bits))[0]);assert risk[n]>0
  assert len(risk)==int(header[3]);risks[case]=risk
  for f in [ep,pathlib.Path(plan['risk']),pathlib.Path(plan['contribution_indices'])]:bindings[str(f)]=sha(f)
 assert sha(graph)==digest;spans=array('I');stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   assert int(e.get('id'))==len(spans);kind=e.get('type');loc=e.find('loc');value=0
   if kind in ['CHANX','CHANY'] and int(e.get('capacity'))>0:value=(int(loc.get('xhigh'))-int(loc.get('xlow'))+1) if kind=='CHANX' else (int(loc.get('yhigh'))-int(loc.get('ylow'))+1)
   spans.append(value);stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(spans)==904438 and sum(x>0 for x in spans)==258720;assert all(spans[n]>0 for risk in risks.values() for n in risk);bindings[str(graph)]=sha(graph);seen=set()
 with bank.open() as f:
  for line in f:
   row=json.loads(line);i=row['index'];assert i not in seen;seen.add(i)
   if i not in needed:continue
   probabilities={int(n):Fraction(x) for n,x in row['probabilities'].items()};assert all(0<x<=1 for x in probabilities.values());span=sum(x*spans[n] for n,x in probabilities.items() if spans[n]);exposure={case:Fraction(0) for case,net in needed[i]}
   for n,x in probabilities.items():
    for case in exposure:
     if n in risks[case]:exposure[case]+=x*risks[case][n]
   for case,net in needed[i]:
    assert row['net_id']==net and (row['source'],tuple(row['sinks']))==expected[case][net];features[case][net].update(expected_CHANNEL_span=span,expected_penalty_exposure=exposure[case])
 assert set(needed)<=seen;rows=[]
 for case in netids:
  f=O/(case+'.jsonl')
  with f.open('x') as out:
   for net in netids[case]:assert set(features[case][net])==set(p['methods']);out.write(json.dumps(dict(net_id=net,**{k:str(x) for k,x in features[case][net].items()}),separators=(',',':'))+'\n')
  rows.append(dict(case=case,NETs=55300,features=str(f),features_sha256=sha(f)));bindings[str(f)]=sha(f);print('INPUT_ONLY_NET_FEATURES',case,55300,flush=True)
 result=dict(status='ALL3_INPUT_ONLY_NET_FANOUT_EXPECTED_SPAN_AND_EXPOSURE_PRODUCED',cases=rows,bindings=bindings,graph_sha256=digest,production_seconds=time.perf_counter()-start,target_work_vector_files_opened=0,scope='Exact rational sums from authenticated forecast NET probabilities, original RR inclusive spans and decoded native input excess bits. No measured work values or target labels used in feature computation. Known posthoc development diagnostic; independent feature verification and scoring pending.')
 (O/'receipt.json').open('x').write(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
