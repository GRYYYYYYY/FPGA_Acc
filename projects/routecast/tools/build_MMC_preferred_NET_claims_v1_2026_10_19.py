"""Input-only soft preferred claims, never actual resource ownership."""
import pathlib,json,hashlib,struct,xml.etree.ElementTree as ET
from fractions import Fraction
from collections import defaultdict,Counter
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 P=R/'experiments/mmc_NET_conditioned_hint_contract_protocol_v1_2026-10-19/protocol.json';p=json.loads(P.read_text())
 for f,h in p['bindings'].items():assert sha(pathlib.Path(f))==h
 O=R/'experiments/mmc_preferred_NET_claims_v1_2026-10-19';O.mkdir(exist_ok=False);B=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';bank=B/'NET_contributions.jsonl';needed=defaultdict(list);spans={};risks={};expected={};winners={};candidate_counts={};probability_ties={};bounds={};bindings={str(f):sha(f) for f in [P,bank,pathlib.Path(__file__).resolve()]};graph=None;digest=None
 for plan in p['cases']:
  case=plan['case'];ep=pathlib.Path(plan['endpoint']);meta=json.loads(ep.read_text());graph=pathlib.Path(meta['inputs']['graph']['path']);assert digest is None or digest==meta['graph_sha256'];digest=meta['graph_sha256'];groups=defaultdict(list)
  for q in meta['connections']:groups[q['net_id']].append(q)
  ids=sorted(groups);indices=json.loads(pathlib.Path(plan['contribution_indices']).read_text());assert len(ids)==len(indices)==55300;features=[json.loads(l) for l in pathlib.Path(plan['features']).read_text().splitlines()];assert [x['net_id'] for x in features]==ids;spans[case]={x['net_id']:Fraction(x['expected_CHANNEL_span']) for x in features};bounds[case]=max(map(int,meta['net_names']))+1;expected[case]={net:(qs[0]['source'],tuple(sorted({q['sink'] for q in qs}))) for net,qs in groups.items()}
  for net,index in zip(ids,indices):needed[index].append((case,net))
  lines=pathlib.Path(plan['risk']).read_text().splitlines();assert lines[0].split()[:3]==['RCRISK1',digest,'904438'];risks[case]={int(l.split()[0]):int(l.split()[1]) for l in lines[1:]};assert len(risks[case])==int(lines[0].split()[3]);winners[case]={};candidate_counts[case]=Counter();probability_ties[case]=Counter()
  for f in [ep,pathlib.Path(plan['features']),pathlib.Path(plan['contribution_indices']),pathlib.Path(plan['risk'])]:bindings[str(f)]=sha(f)
 assert sha(graph)==digest;capacities={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:capacities[int(e.get('id'))]=int(e.get('capacity'))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(capacities)==258720 and all(capacities.get(n)==1 for risk in risks.values() for n in risk);bindings[str(graph)]=sha(graph)
 with bank.open() as f:
  for line in f:
   row=json.loads(line);index=row['index']
   for case,net in needed.get(index,[]):
    assert row['net_id']==net and (row['source'],tuple(row['sinks']))==expected[case][net]
    for key,value in row['probabilities'].items():
     n=int(key)
     if n not in risks[case]:continue
     probability=Fraction(value);assert 0<probability<=1;candidate_counts[case][n]+=1;rank=(probability,spans[case][net],-net);old=winners[case].get(n)
     if old is None or probability>old[0]:probability_ties[case][n]=1
     elif probability==old[0]:probability_ties[case][n]+=1
     if old is None or rank>old:winners[case][n]=rank
 rows=[]
 for case in risks:
  assert set(winners[case])==set(risks[case]);assert all(candidate_counts[case][n]>=2 for n in risks[case]);d=O/case;d.mkdir();fp=d/'claims.jsonl';runtime=d/'cost_claims.txt';chosen=Counter()
  with fp.open('x') as out,runtime.open('x') as native:
   native.write(f'COSTCLAIM1 904438 {bounds[case]} 1 {len(winners[case])}\n')
   for n,(probability,span,negative_net) in sorted(winners[case].items()):
    net=-negative_net;bits=risks[case][n];excess=struct.unpack('<f',struct.pack('<I',bits))[0];hint_bits=struct.unpack('<I',struct.pack('<f',1+excess))[0];assert hint_bits>0x3f800000;chosen[net]+=1;out.write(json.dumps(dict(node=n,preferred_net=net,probability=str(probability),expected_CHANNEL_span=str(span),excess_bits=bits,hint_bits=hint_bits,candidates=candidate_counts[case][n],max_probability_ties=probability_ties[case][n]),separators=(',',':'))+'\n');native.write(f'{n} {net} {hint_bits}\n')
  bindings[str(fp)]=sha(fp);bindings[str(runtime)]=sha(runtime);rows.append(dict(case=case,claims=len(winners[case]),preferred_NETs=len(chosen),net_id_upper_bound=bounds[case],claims_file=str(fp),cost_frame_input=str(runtime),nodes_with_probability_ties=sum(x>1 for x in probability_ties[case].values())));print('PREFERRED_FORECAST_CLAIMS',case,len(winners[case]),'NETs',len(chosen),flush=True)
 (O/'receipt.json').open('x').write(json.dumps(dict(status='ALL3_INPUT_ONLY_SOFT_PREFERRED_NET_CLAIMS_PRODUCED',cases=rows,bindings=bindings,graph_sha256=digest,native_target_or_work_vectors_read=0,scope='Exact frozen probability/span/NETid lexicographic claims on capacity1 positive-risk CHANNELs. These are soft forecast preferences, not physical owners or reservations. No cost/occupancy update or native policy trial. Independent verification pending.'),indent=2)+'\n')
if __name__=='__main__':main()
