"""Inverse-node ownership score replay and independent B-count label replay."""
import hashlib,json,math
from array import array
from collections import Counter,defaultdict
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(info):
 assert sha(info['path'])==info['sha256'];a=array(info.get('typecode','d'));a.frombytes(Path(info['path']).read_bytes());assert len(a)==info['values'];return a

def main():
 source=Path('experiments/mmc_NET_pressure_exposure_v1_2026-10-18');target=Path('experiments/mmc_NET_pressure_targets_v1_2026-10-18');sp=source/'receipt.json';tp=target/'receipt.json';s=json.loads(sp.read_text());t=json.loads(tp.read_text());assert s['status']=='all90_source_only_NET_exposure_vectors_materialized' and t['status']=='all18_NET_target_vectors_extracted';plan=json.loads((source/'protocol.json').read_text());domains=json.loads((source/'NET_domains.json').read_text());sm=json.loads((source/'vector_manifest.json').read_text());tm=json.loads((target/'vector_manifest.json').read_text());assert len(sm)==90 and len(tm)==18
 out=Path('experiments/mmc_NET_pressure_inputs_verification_v1_2026-10-18');out.mkdir(exist_ok=False);bindings={**s['bindings'],**t['bindings'],str(sp.resolve()):sha(sp),str(tp.resolve()):sha(tp),str((source/'protocol.json').resolve()):sha(source/'protocol.json'),str((source/'NET_domains.json').resolve()):sha(source/'NET_domains.json'),str(Path(__file__).resolve()):sha(__file__)}
 for p,h in bindings.items():assert sha(p)==h
 tr=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18');config=json.loads((tr/'protocol.json').read_text());g=json.loads((tr/'groups.json').read_text());fullindex={n:i for i,n in enumerate(g['positive_RR_ids'])};index=json.loads(Path('experiments/real_joint_full_score_v2_2026-10-18/graph_index.json').read_text());dest=read(index['arrays']['edge_destination']);ar=Path('experiments/mmc_anchored_NET_forecasts_v1_2026-10-18');am=json.loads((ar/'vector_manifest.json').read_text());um=json.loads((tr/'vector_manifest.json').read_text());pm=json.loads(Path('experiments/mmc_pressure_risk_matrix_v1_2026-10-18/vector_manifest.json').read_text());predchecked=targetchecked=0;rows=[]
 for case in plan['cases']:
  e=json.loads(Path(config['inputs'][case]['endpoint']).read_text());identities={q['connection_id']:q['net_id'] for q in e['connections']};ids=domains[case]['NET_ids'];assert ids==sorted(set(identities.values())) and len(ids)==55300;assert domains[case]['NET_names']=={str(n):e['net_names'][str(n)] for n in ids} and len(set(domains[case]['NET_names'].values()))==len(ids)
  for src in plan['sources']:
   frame=json.loads(Path(config['inputs'][case]['predictions'][src]).read_text());assert {r['connection_id']:r['net_id'] for r in frame['records']}==identities;inverse=defaultdict(set)
   for r in frame['records']:
    inverse[r['source']].add(r['net_id'])
    for edge in r['answer']['physical_edge_ids']:inverse[dest[edge]].add(r['net_id'])
   buckets=defaultdict(list)
   for n in sorted(inverse):
    i=fullindex[n]
    for net in inverse[n]:buckets[net].append(i)
   assert set(buckets)==set(ids)
   infos=[am[case+'__'+src+'__anchored_NET_collision'],um[case+'__'+src+'__typed_NET_collision'],um[case+'__'+src+'__observed_overflow'],pm[case+'__'+src+'__all_positive_RR']];fields=[read(info) for info in infos]
   for k,method in enumerate(plan['methods']):
    info=sm[case+'__'+src+'__'+method];actual=read(info);expected=array('d',(math.fsum(fields[k][i] for i in buckets[net]) if k<4 else len(buckets[net]) for net in ids));assert actual==expected;predchecked+=len(ids);bindings[info['path']]=info['sha256']
   print('INDEPENDENT SOURCE NET SCORE PASS',case,src,flush=True)
  for policy in plan['policies']:
   trace=Path('experiments/mmc_native_owner_cascade_trace_v1_2026-10-18')/case/policy/'owner_trace.tsv';proof=json.loads((Path('experiments/mmc_native_owner_trace_replay_v2_2026-10-18')/case/(policy+'.json')).read_text());assert proof['incomplete_attempts']==0
   b=Counter();qover=Counter();qall=Counter();first=set();byiter=Counter();known=set(ids);nS=0
   # B counts are independent of producer's successful E completion count.
   with trace.open() as f:
    for line in f:
     if line.startswith('B '):
      w=line.split();it,net=int(w[2]),int(w[3]);assert net in known;b[net]+=1;byiter[it]+=1
     elif line.startswith('Q '):
      w=line.split();it,net=int(w[2]),int(w[3]);assert net in known;qall[net]+=1
      if w[4]=='overuse':
       qover[net]+=1
       if it==1:first.add(net)
     elif line.startswith('S '):
      w=line.split();it,nets=int(w[1]),int(w[2]);assert byiter[it]==nets==proof['iteration_stats'][nS]['NET_operations'];nS+=1
   assert b==qall and sum(b.values())==proof['setup_attempts']==proof['decisions'] and nS==len(proof['iteration_stats'])
   for name in plan['targets']:
    info=tm[case+'__'+policy+'__'+name];actual=read(info);values=[int(net in first) if name=='first_iteration_overuse_guard' else qover[net] if name=='total_overuse_guard_decisions' else b[net] for net in ids];assert actual==array('Q',values);targetchecked+=len(ids);bindings[info['path']]=info['sha256']
   rows.append(dict(case=case,policy=policy,first_iteration_overuse_NETs=len(first),successful_NET_operations=sum(b.values()),zero_operation_NETs=len(ids)-len(b)));print('INDEPENDENT NET TARGET PASS',case,policy,flush=True)
 assert predchecked==90*55300 and targetchecked==18*55300
 for p,h in bindings.items():assert sha(p)==h
 for p in [source/'vector_manifest.json',target/'vector_manifest.json']:bindings[str(p.resolve())]=sha(p)
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,source_score_values_verified=predchecked,target_values_verified=targetchecked,NETs_per_vector=55300,trace_rows=rows,scope='Independent node->NET inversion and deterministic exact fsum buckets, source/endpoints/trace ID domain equality; B-route attempts equal producer E completions under admitted zero-incomplete runs; Q guards and zero NET labels retained. Not per-NET heap or connection work, causal routing or heldout/utility validation.'),f,indent=2)
if __name__=='__main__':main()
