"""Source-only unique-NET node exposure scores, frozen before NET event labels."""
import hashlib,json,math,sys
from array import array
from collections import defaultdict
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(info):
 assert sha(info['path'])==info['sha256'];a=array(info.get('typecode','d'));a.frombytes(Path(info['path']).read_bytes());assert len(a)==info['values'];return a

def main():
 out=Path('experiments/mmc_NET_pressure_exposure_v1_2026-10-18');out.mkdir(exist_ok=False);(out/'vectors').mkdir()
 ar=Path('experiments/mmc_anchored_NET_forecasts_v1_2026-10-18');avp=Path('experiments/mmc_anchored_NET_forecasts_verification_v1_2026-10-18/verification.json');av=json.loads(avp.read_text());assert av['status']=='pass';ap=json.loads((ar/'protocol.json').read_text());am=json.loads((ar/'vector_manifest.json').read_text())
 tr=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18');tvp=Path('experiments/mmc_typed_collision_risk_verification_v1_2026-10-18/verification.json');tv=json.loads(tvp.read_text());assert tv['status']=='pass';tm=json.loads((tr/'vector_manifest.json').read_text());config=json.loads((tr/'protocol.json').read_text());gp=tr/'groups.json';g=json.loads(gp.read_text());fullindex={n:i for i,n in enumerate(g['positive_RR_ids'])}
 pr=Path('experiments/mmc_typed_risk_matrix_verification_v1_2026-10-18/verification.json');pv=json.loads(pr.read_text());assert pv['status']=='pass';pm=json.loads(Path('experiments/mmc_pressure_risk_matrix_v1_2026-10-18/vector_manifest.json').read_text())
 cp=Path('experiments/mmc_native_owner_trace_replay_v2_2026-10-18/cohort_verification.json');cohort=json.loads(cp.read_text());assert cohort['status']=='pass' and cohort['all6_streamed_NET_ownership_checkpoints_final_unions_and_exact_counters_pass']
 ip=Path('experiments/real_joint_full_score_v2_2026-10-18/graph_index.json');ivp=ip.with_name('verification.json');iv=json.loads(ivp.read_text());index=json.loads(ip.read_text());assert iv['status']=='pass' and iv['bindings'][str(ip.resolve())]==sha(ip) and index['graph_sha256']==g['graph_sha256'] and index['byteorder']==sys.byteorder
 paths=[avp,ar/'protocol.json',ar/'vector_manifest.json',tvp,tr/'protocol.json',tr/'vector_manifest.json',pr,cp,ip,ivp,gp,Path('experiments/mmc_pressure_risk_matrix_v1_2026-10-18/vector_manifest.json'),Path(__file__)]
 bindings={str(p.resolve()):sha(p) for p in paths};netdomains={}
 for case in ap['cases']:
  ep=Path(config['inputs'][case]['endpoint']);assert sha(ep)==cohort['bindings'][str(ep.resolve())];bindings[str(ep.resolve())]=sha(ep);e=json.loads(ep.read_text());identities={q['connection_id']:q['net_id'] for q in e['connections']};netids=sorted(set(identities.values()));assert len(netids)==55300
  netdomains[case]=dict(NET_ids=netids,NET_names={str(n):e['net_names'][str(n)] for n in netids},connections=len(identities))
  for source in ap['sources']:
   path=Path(config['inputs'][case]['predictions'][source]);assert sha(path)==av['bindings'][str(path.resolve())];bindings[str(path.resolve())]=sha(path)
   for info,proof in [(am[case+'__'+source+'__anchored_NET_collision'],av),(tm[case+'__'+source+'__typed_NET_collision'],tv),(tm[case+'__'+source+'__observed_overflow'],tv),(pm[case+'__'+source+'__all_positive_RR'],pv)]:
    assert info['sha256']==proof['bindings'][info['path']];bindings[info['path']]=info['sha256']
 for item in index['arrays'].values():assert sha(item['path'])==item['sha256'];bindings[item['path']]=item['sha256']
 methods=['anchored_risk_sum','uniform_risk_sum','observed_overflow_sum','raw_density_sum','unique_node_count']
 protocol=dict(status='source_only_NET_exposure_plan_frozen_before_new_NET_outcome_extraction',bindings=bindings,cases=ap['cases'],sources=ap['sources'],methods=methods,primary_source='native_retained_on',primary_score='anchored_risk_sum',aggregation='math.fsum of authenticated fullRR score over numerically sorted unique NET-owned nodes across all its query paths; never sum query references as separate owners. Length-only is unique node count. These sums are exposure descriptors, not NET probabilities or predicted heap work.',NET_domain='All55300nonignored physical-demand NET IDs, current endpointCID->NET identity preserved for every source; previous_native is an old footprint, not a legal moved route.',policies=['off','on'],targets=['first_iteration_overuse_guard','total_overuse_guard_decisions','total_successful_NET_route_operations'],primary_target='total_successful_NET_route_operations',trace_semantics='Q is first-true observed native guard; B/E is one setup attempt and its completion. All admitted runs have zero incomplete attempts. S heap/connection totals are iteration-only and must NOT be attributed per NET.',metric_plan='All3cases*6sources*5scores*2policies*3targets=540cells. Complete-domain Spearman, original deterministic top5percent overlap with both tie intervals, plus captured target-count fraction and enrichment for selected NETs. Zero total target -> undefined capture, never drop zero-event NETs. Binary positive capture is auxiliary, not a retrofit to old cold gates.',ranking='descending stored score, ascending numeric NET ID; K=floor55300/20=2765',scope='New frozen diagnostic on exposed existing traces only. No native intervention, mixture fitting, source selection or unseen/utility/full-flow promotion.')
 with (out/'protocol.json').open('x') as f:json.dump(protocol,f,indent=2)
 with (out/'NET_domains.json').open('x') as f:json.dump(netdomains,f,indent=2)
 starts=read(index['arrays']['edge_source']);dest=read(index['arrays']['edge_destination']);manifest={};rows=[]
 for case in protocol['cases']:
  e=json.loads(Path(config['inputs'][case]['endpoint']).read_text());identities={q['connection_id']:q['net_id'] for q in e['connections']};netids=netdomains[case]['NET_ids']
  for source in protocol['sources']:
   path=Path(config['inputs'][case]['predictions'][source]);frame=json.loads(path.read_text());assert {r['connection_id']:r['net_id'] for r in frame['records']}==identities and len(frame['records'])==len(identities)
   owned=defaultdict(set)
   for r in frame['records']:
    node=r['source'];owned[r['net_id']].add(node)
    for edge in r['answer']['physical_edge_ids']:
     assert type(edge) is int and 0<=edge<len(dest) and starts[edge]==node;node=dest[edge];owned[r['net_id']].add(node)
    assert node==r['sink']
   assert set(owned)==set(netids)
   infos=[am[case+'__'+source+'__anchored_NET_collision'],tm[case+'__'+source+'__typed_NET_collision'],tm[case+'__'+source+'__observed_overflow'],pm[case+'__'+source+'__all_positive_RR']];vectors=[read(info) for info in infos];scores=[array('d') for _ in methods]
   for net in netids:
    ns=sorted(owned[net]);positions=[fullindex[n] for n in ns]
    for k,values in enumerate(vectors):scores[k].append(math.fsum(values[i] for i in positions))
    scores[-1].append(len(ns))
   for method,values in zip(methods,scores):
    p=out/'vectors'/(case+'__'+source+'__'+method+'.f64')
    with p.open('xb') as f:values.tofile(f)
    manifest[case+'__'+source+'__'+method]=dict(path=str(p.resolve()),sha256=sha(p),values=len(values))
   rows.append(dict(case=case,source=source,NETs=len(netids),unique_NET_node_references=sum(map(len,owned.values()))));print('SOURCE NET EXPOSURE FROZEN',case,source,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'vector_manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='all90_source_only_NET_exposure_vectors_materialized',bindings=bindings,rows=rows,NETs_per_vector=55300,vectors=90,scope=protocol['scope']),f,indent=2)
if __name__=='__main__':main()
