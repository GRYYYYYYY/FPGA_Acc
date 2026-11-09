"""Freeze and materialize anchored NET prior before new metric outcomes."""
import hashlib,json,sys
from array import array
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from anchored_NET_collision_prior_v1 import marginal

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path('experiments/mmc_anchored_NET_forecasts_v1_2026-10-18');out.mkdir(exist_ok=False);(out/'vectors').mkdir()
 root=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18');gp=root/'groups.json';g=json.loads(gp.read_text());config=json.loads((root/'protocol.json').read_text());groups=g['groups'];group_of={n:i for i,v in enumerate(groups) for n in v['members']}
 vp=Path('experiments/mmc_typed_collision_risk_verification_v1_2026-10-18/verification.json');proof=json.loads(vp.read_text());assert proof['status']=='pass'
 cp=Path('experiments/anchored_NET_collision_prior_core_v1_2026-10-18/verification.json');core=json.loads(cp.read_text());assert core['status']=='pass'
 ip=Path('experiments/real_joint_full_score_v2_2026-10-18/graph_index.json');index=json.loads(ip.read_text());ip_proof=Path('experiments/real_joint_full_score_v2_2026-10-18/verification.json');iv=json.loads(ip_proof.read_text());assert iv['status']=='pass' and iv['bindings'][str(ip.resolve())]==sha(ip)
 paths=[gp,root/'protocol.json',vp,cp,ip,ip_proof,Path(__file__),Path('tools/anchored_NET_collision_prior_v1.py')]
 bindings={str(p.resolve()):sha(p) for p in paths};bindings.update(core['bindings']);assert proof['bindings'][str(gp.resolve())]==sha(gp)
 for inputs in config['inputs'].values():
  for name in inputs['predictions'].values():assert sha(name)==proof['bindings'][name];bindings[name]=sha(name)
 for item in index['arrays'].values():assert sha(item['path'])==item['sha256'];bindings[item['path']]=item['sha256']
 assert index['graph_sha256']==g['graph_sha256'] and index['byteorder']==sys.byteorder
 protocol=dict(bindings=bindings,weight='1/2',prior='Per NET independently: retain its observed k-node set with probability1/2, or redraw a uniform k-subset of the same graph-only group with probability1/2. Within-NET node choices are correlated, not independent connections. Evaluate exact per-node mean and expected unit overflow.',cases=['case_01','case_02','case_03'],sources=config['methods'],families=['anchored_group_mean','anchored_NET_collision'],primary_pressure_method='anchored_NET_collision__native_retained_on',primary_cold_method='anchored_group_mean__native_retained_on',controls='All existing6source states, raw density, geometry pooling and uniform typed collision; all original gates and labels remain. No source/weight/case selection after outcomes.',fallback='Same exact observed positive resource overflow/capacity for SOURCE/OPIN/SINK and unsupported nodes as existing typed priors.',pressure_evaluation='All2newfamilies*6sources*3cases*2policies*3targets*4domains=864new cells; preserve existing2160. Same rank/tie/domain/normalization rules; no calibrated pressure claim.',cold_evaluation='Anchored occupancy mean only: all6sources*3cases*2domains concrete/spatial, original cold-primary comparison gates. Expected-overflow scores do not replace occupancy scores. Spatial occupancy mass remains exactly unchanged.',scope='Post-exposure development hypothesis only. No weight fitting, no new labels read in producer, no strict-unseen/native utility/primary promotion. All36newvectors require independent source/vector replay before metric interpretation.')
 with (out/'protocol.json').open('x') as f:json.dump(protocol,f,indent=2)
 arrays={}
 for key in ['edge_source','edge_destination','positive_capacity']:
  item=index['arrays'][key];data=array(item['typecode']);data.frombytes(Path(item['path']).read_bytes());assert data.itemsize==4 and len(data)==item['values'];arrays[key]=data
 starts=arrays['edge_source'];dest=arrays['edge_destination'];caps=dict(zip(g['positive_RR_ids'],arrays['positive_capacity']));manifest={};summaries=[]
 for case in protocol['cases']:
  for method in protocol['sources']:
   path=Path(config['inputs'][case]['predictions'][method]);frame=json.loads(path.read_text());assert sha(path)==bindings[str(path)]
   # Previous-native frame lacks a root epoch field: only its admitted same-graph proof is accepted.
   if method!='previous_native':assert frame['graph_sha256']==g['graph_sha256']
   else:
    oldproof=Path('experiments/mmc_native_source_checkpoint_v1_2026-10-18/independent_xml_verification_v1.json');old=json.loads(oldproof.read_text());assert old['all_native_paths_exact'] and old['bindings'][str(path)]==sha(path);bindings[str(oldproof.resolve())]=sha(oldproof)
   nets=defaultdict(list)
   for row in frame['records']:nets[row['net_id']].append(row)
   hist=defaultdict(Counter);owner_hist=defaultdict(Counter);ledger=Counter()
   for net,rows in nets.items():
    owned=set()
    for row in rows:
     node=row['source'];owned.add(node)
     for edge in row['answer']['physical_edge_ids']:
      assert type(edge) is int and 0<=edge<len(dest) and starts[edge]==node;node=dest[edge];owned.add(node)
     assert node==row['sink']
    ledger.update(owned);ks=Counter(group_of[n] for n in owned if n in group_of)
    for gid,k in ks.items():hist[gid][k]+=1
    for n in owned:
     if n in group_of:owner_hist[n][ks[group_of[n]]]+=1
   assert dict(ledger)=={int(n):v for n,v in frame['ledger'].items() if v}
   cache={};totals={}
   for gid,h in hist.items():
    members=groups[gid]['members'];patterns=Counter(tuple(sorted(owner_hist.get(n,{}).items())) for n in members);mean=Fraction(0);risk=Fraction(0)
    for pattern,count in patterns.items():
     result=marginal(len(members),h,dict(pattern));cache[(gid,pattern)]=result;mean+=count*result['expected_occupancy'];risk+=count*result['expected_overflow']
    assert mean==sum(ledger.get(n,0) for n in members)
    totals[gid]=dict(expected_occupancy_total=str(mean),expected_overflow_total=str(risk))
   vectors=[array('d'),array('d')]
   for n in g['positive_RR_ids']:
    value=Fraction(max(0,ledger.get(n,0)-caps[n]),caps[n]);values=(value,value)
    if n in group_of:
     gid=group_of[n]
     if gid in hist:
      result=cache[(gid,tuple(sorted(owner_hist.get(n,{}).items())))];values=(result['expected_occupancy'],result['expected_overflow'])
     else:values=(Fraction(0),Fraction(0))
    for k in range(2):vectors[k].append(float(values[k]))
   for family,values in zip(protocol['families'],vectors):
    p=out/'vectors'/(case+'__'+method+'__'+family+'.f64')
    with p.open('xb') as f:values.tofile(f)
    manifest[case+'__'+method+'__'+family]=dict(path=str(p.resolve()),sha256=sha(p),values=len(values))
   with (out/(case+'__'+method+'.json')).open('x') as f:json.dump(dict(group_totals=totals,source_frame_sha256=sha(path),ownership_histogram_patterns=len(cache)),f)
   summaries.append(dict(case=case,source=method,active_groups=len(hist),patterns=len(cache)));print('ANCHORED SOURCE FROZEN',case,method,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'vector_manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='all36_source_only_anchored_vectors_materialized_independent_replay_pending',bindings=bindings,summaries=summaries,vectors=36,scope=protocol['scope']),f,indent=2)
 print('ALL36 ANCHORED VECTORS MATERIALIZED',flush=True)
if __name__=='__main__':main()
