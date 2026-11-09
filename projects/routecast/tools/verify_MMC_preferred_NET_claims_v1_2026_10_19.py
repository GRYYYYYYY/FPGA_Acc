"""Independent all-candidate sort and original-XML soft-claim verification."""
import pathlib,json,hashlib,struct,xml.etree.ElementTree as ET
from collections import defaultdict,Counter
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_preferred_NET_claims_v1_2026-10-19';rp=O/'receipt.json';r=json.loads(rp.read_text());P=R/'experiments/mmc_NET_conditioned_hint_contract_protocol_v1_2026-10-19/protocol.json';p=json.loads(P.read_text())
 for f,h in r['bindings'].items():assert sha(pathlib.Path(f))==h
 B=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';needed=defaultdict(list);risks={};spans={};eligible={};candidates={};bindings={str(f):sha(f) for f in [P,rp,pathlib.Path(__file__).resolve()]};graph=None
 for plan in p['cases']:
  case=plan['case'];ep=pathlib.Path(plan['endpoint']);meta=json.loads(ep.read_text());graph=pathlib.Path(meta['inputs']['graph']['path']);eligible[case]=sorted({q['net_id'] for q in meta['connections']});indices=json.loads(pathlib.Path(plan['contribution_indices']).read_text());assert len(indices)==len(eligible[case])==55300
  for net,index in zip(eligible[case],indices):needed[index].append((case,net))
  spans[case]={x['net_id']:Fraction(x['expected_CHANNEL_span']) for x in map(json.loads,pathlib.Path(plan['features']).read_text().splitlines())};risks[case]={int(l.split()[0]):int(l.split()[1]) for l in pathlib.Path(plan['risk']).read_text().splitlines()[1:]};candidates[case]=defaultdict(list)
 assert sha(graph)==r['graph_sha256'];caps={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY']:caps[int(e.get('id'))]=int(e.get('capacity'))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 with (B/'NET_contributions.jsonl').open() as f:
  for line in f:
   row=json.loads(line)
   for case,net in needed.get(row['index'],[]):
    assert net==row['net_id'];prob={int(n):Fraction(x) for n,x in row['probabilities'].items()}
    for n in prob.keys()&risks[case].keys():candidates[case][n].append((prob[n],spans[case][net],net))
 results=[]
 for row in r['cases']:
  case=row['case'];f=pathlib.Path(row['claims_file']);runtime=pathlib.Path(row['cost_frame_input']);records=[json.loads(l) for l in f.read_text().splitlines()];assert [x['node'] for x in records]==sorted(risks[case]);raw=runtime.read_text().splitlines();assert raw[0].split()==['COSTCLAIM1','904438',str(row['net_id_upper_bound']),'1',str(len(records))];owners=Counter()
  for x,line in zip(records,raw[1:]):
   n=x['node'];assert caps[n]==1 and n in candidates[case];ordered=sorted(candidates[case][n],key=lambda y:(-y[0],-y[1],y[2]));assert len(ordered)>=2;prob,span,net=ordered[0];assert net in eligible[case] and net==x['preferred_net'] and prob==Fraction(x['probability']) and span==Fraction(x['expected_CHANNEL_span']);assert len(ordered)==x['candidates'] and sum(y[0]==prob for y in ordered)==x['max_probability_ties'];bits=risks[case][n];hint=struct.unpack('<I',struct.pack('<f',1+struct.unpack('<f',struct.pack('<I',bits))[0]))[0];assert bits==x['excess_bits'] and hint==x['hint_bits'] and 0x3f800000<hint<0x7f800000;assert list(map(int,line.split()))==[n,net,hint];owners[net]+=1
  assert len(raw)==len(records)+1 and len(owners)==row['preferred_NETs'];results.append(dict(case=case,all_risk_CHANNEL_claims_verified=len(records),preferred_NETs=len(owners),all_selected_NETs_from_current_input=True,geometry_capacity_one=True,complete_lexicographic_optima_verified=True));bindings[str(f)]=sha(f);bindings[str(runtime)]=sha(runtime);print('PREFERRED_CLAIMS_INDEPENDENT_PASS',case,len(records),len(owners),flush=True)
 bindings[str(graph)]=sha(graph);(O/'independent_verification_v1.json').open('x').write(json.dumps(dict(status='ALL3_SOFT_PREFERRED_NET_CLAIMS_EXACT_AND_GEOMETRY_VERIFIED',cases=results,bindings=bindings,scope='Full candidate sorting from frozen forecast probabilities/span, original graph and actual declared input NET domain. Not actual ownership, route feasibility, native query integration, work benefit or heldout evidence.'),indent=2)+'\n')
if __name__=='__main__':main()
