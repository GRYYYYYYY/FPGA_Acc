"""Necessary NET changes from forbidden target-zero channel occupancy; posthoc."""
import pathlib,json,hashlib,array,sys
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 out=R/'experiments/mmc_required_NET_changes_v1_2026-10-18';out.mkdir();bindings={str(pathlib.Path(__file__).resolve()):sha(__file__)}
 def load(p):
  p=pathlib.Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
 idx=load(R/'experiments/real_joint_full_score_v2_2026-10-18/graph_index.json');m=idx['arrays']['edge_destination'];assert sys.byteorder==idx['byteorder'];assert sha(m['path'])==m['sha256'];bindings[m['path']]=m['sha256'];dest=array.array('I');dest.frombytes(pathlib.Path(m['path']).read_bytes());rows=[]
 topo=R/'experiments/mmc_endpoint_geometry_topology_v2_2026-10-18';proof=load(topo/'independent_verification_v1.json');receipt=load(topo/'receipt.json');assert proof['bindings'][str(topo/'receipt.json')]==sha(topo/'receipt.json');assert receipt['bindings'][m['path']]==m['sha256']
 for case in ['case_01','case_02','case_03']:
  base=R/f'experiments/mmc_multiplacement_models_v1_2026-10-18/{case}';w=load(base/'native_retained/verification.json');initial=load(base/'native_retained/initial.json');dirty=set(w['dirty_nets']);assert initial['graph_sha256']==idx['graph_sha256'];quality=R/f'experiments/mmc_atomic_pair_quality_v1_2026-10-18/{case}';audit=load(quality/'verification.json');vp=quality/'vectors.json';assert audit['status']=='pass' and audit['bindings'][str(vp)]==sha(vp);vectors=load(vp);zero={x['node'] for x in vectors['channels'] if x['labels']['cold']==0};original={x['connection_id']:x for x in initial['records']};witness={};net_records={}
  for x in initial['records']:
   n=x['net_id'];net_records.setdefault(n,[]).append(x['connection_id'])
   if n in dirty or n in witness:continue
   nodes={x['source']}|{dest[e] for e in x['answer']['physical_edge_ids']};bad=nodes&zero
   if bad:witness[n]=dict(net_id=n,connection_id=x['connection_id'],forbidden_channel=min(bad))
  changed={}
  for name,p in [('original',base/'feedback_on/native_retained/sketch.json'),('atomic',R/f'experiments/mmc_multi_NET_atomic_pair_v1_2026-10-18/{case}/sketch.json')]:
   final=load(p);actual={x['connection_id']:x for x in final['records']};assert set(actual)==set(original);changed[name]={x['net_id'] for cid,x in original.items() if x['source']!=actual[cid]['source'] or x['answer']['physical_edge_ids']!=actual[cid]['answer']['physical_edge_ids']}
  assert not (changed['original']-dirty)
  cert=out/(case+'_witnesses.json');cert.write_text(json.dumps([witness[n] for n in sorted(witness)],separators=(',',':'))+'\n');bindings[str(cert)]=sha(cert)
  # Independent witness replay: test membership in a literal list, not the producer union.
  for n,v in witness.items():
   rec=original[v['connection_id']];assert rec['net_id']==n and n not in dirty
   assert v['forbidden_channel'] in [rec['source'],*[dest[e] for e in rec['answer']['physical_edge_ids']]] and v['forbidden_channel'] in zero
  rows.append(dict(case=case,NETs=len(net_records),endpoint_dirty_NETs=len(dirty),necessary_clean_NET_changes_lower_bound=len(witness),fraction_of_clean_NETs=len(witness)/(len(net_records)-len(dirty)),actual_changed_NETs={k:len(v) for k,v in changed.items()},atomic_changed_outside_dirty=len(changed['atomic']-dirty),certified_required_NETs_untouched_by_atomic=len(set(witness)-changed['atomic'])));print(rows[-1],flush=True)
 assert all(sha(k)==h for k,h in bindings.items())
 result=dict(status='all3_support_zero_witness_certificates_computed_and_replayed',bindings=bindings,cases=rows,derivation='For each certified clean NET, an unchanged path uses a positive-capacity channel whose total target occupancy is zero. Nonnegative occupancy from other NETs cannot cancel this contribution. Hence that NET must change to match target channel occupancy exactly. Witness NETs are distinct, giving a lower bound on necessary changed NET count.',scope='Exposed development labels; necessary for exact cold occupancy matching only, not for improving correlation/topK or producing another legal route. Not a deployable update selector and not a causal placement-effect claim. Does not imply full NET refresh is sufficient; its previous candidate failed quality.',accepted_gain=False)
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
