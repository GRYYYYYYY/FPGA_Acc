"""Independent IEEE754 risk decoding, XML geometry and exact per-NET sums."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def binary32(bits):
 assert bits>>31==0;exponent=(bits>>23)&255;mantissa=bits&0x7fffff;assert exponent!=255
 if not exponent:return Fraction(mantissa,1<<149)
 value=(1<<23)|mantissa;shift=exponent-150;return Fraction(value<<shift) if shift>=0 else Fraction(value,1<<(-shift))
def main():
 O=R/'experiments/mmc_current_NET_exposure_features_v1_2026-10-19';rp=O/'receipt.json';r=json.loads(rp.read_text());P=R/'experiments/mmc_current_NET_exposure_work_diagnostic_protocol_v1_2026-10-19/protocol.json';p=json.loads(P.read_text());B=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';bp=B/'independent_prediction_verification_v1.json';b=json.loads(bp.read_text());bank=B/'NET_contributions.jsonl';assert r['target_work_vector_files_opened']==0
 for f,h in r['bindings'].items():assert sha(pathlib.Path(f))==h
 metas={};indices=defaultdict(list);risks={};features={};bindings={str(f):sha(f) for f in [P,rp,bp,bank,pathlib.Path(__file__).resolve()]};graph=None;expected={}
 for plan in p['cases']:
  case=plan['case'];ep=pathlib.Path(plan['endpoint']);meta=json.loads(ep.read_text());metas[case]=meta;graph=pathlib.Path(meta['inputs']['graph']['path']);fanout=Counter(q['net_id'] for q in meta['connections']);ids=sorted(fanout);assert len(ids)==55300;f=O/(case+'.jsonl');rows=[json.loads(l) for l in f.read_text().splitlines()];assert [x['net_id'] for x in rows]==ids;features[case]={x['net_id']:{k:Fraction(x[k]) for k in p['methods']} for x in rows};expected[case]=defaultdict(list)
  for q in meta['connections']:expected[case][q['net_id']].append((q['source'],q['sink']))
  for net,index in zip(ids,json.loads(pathlib.Path(plan['contribution_indices']).read_text())):indices[index].append((case,net));assert features[case][net]['manifest_fanout']==fanout[net]
  risks[case]={}
  for line in pathlib.Path(plan['risk']).read_text().splitlines()[1:]:n,bits=map(int,line.split());assert n not in risks[case];risks[case][n]=binary32(bits)
  for path in [ep,f,pathlib.Path(plan['risk']),pathlib.Path(plan['contribution_indices'])]:bindings[str(path)]=sha(path)
 assert sha(graph)==r['graph_sha256'];spans={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   kind=e.get('type')
   if int(e.get('capacity'))>0 and kind in ['CHANX','CHANY']:
    loc=e.find('loc');axis='x' if kind=='CHANX' else 'y';spans[int(e.get('id'))]=int(loc.get(axis+'high'))+1-int(loc.get(axis+'low'))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(spans)==258720;checked=Counter()
 with bank.open() as f:
  for line in f:
   row=json.loads(line)
   if row['index'] not in indices:continue
   prob={int(n):Fraction(x) for n,x in row['probabilities'].items()};assert prob[row['source']]==1;span=sum(prob[n]*spans[n] for n in prob.keys()&spans.keys())
   for case,net in indices[row['index']]:
    assert row['net_id']==net and {s for s,t in expected[case][net]}=={row['source']} and {t for s,t in expected[case][net]}==set(row['sinks']);exposure=sum(prob[n]*risks[case][n] for n in prob.keys()&risks[case].keys());assert features[case][net]['expected_CHANNEL_span']==span and features[case][net]['expected_penalty_exposure']==exposure;checked[case]+=1
 rows=[]
 for case in metas:
  assert checked[case]==55300;lp=B/case/'expected_unique_NET_occupancy.json';assert b['bindings'][str(lp)]==sha(lp);ledger={int(n):Fraction(x) for n,x in json.loads(lp.read_text()).items()};span_total=sum(x['expected_CHANNEL_span'] for x in features[case].values());exposure_total=sum(x['expected_penalty_exposure'] for x in features[case].values());assert span_total==sum(ledger.get(n,0)*value for n,value in spans.items());assert exposure_total==sum(ledger.get(n,0)*value for n,value in risks[case].items());rows.append(dict(case=case,NETs=55300,exact_expected_span_total=str(span_total),exact_expected_exposure_total=str(exposure_total),full_perNET_and_global_conservation_pass=True));bindings[str(lp)]=sha(lp);print('INPUT_ONLY_FEATURES_INDEPENDENT_PASS',case,flush=True)
 bindings[str(graph)]=sha(graph);(O/'independent_verification_v1.json').open('x').write(json.dumps(dict(status='ALL3_INPUT_ONLY_NET_FEATURES_INDEPENDENTLY_VERIFIED',cases=rows,bindings=bindings,target_work_vectors_opened=0,scope='Independent full rational features and global linear conservation, no measured work used in arithmetic. No calibration, prediction quality, policy, unseen-family or elapsed-time gain claim.'),indent=2)+'\n')
if __name__=='__main__':main()
