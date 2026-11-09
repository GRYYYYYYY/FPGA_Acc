"""Full-node descriptive rank decomposition and unique-NET union accounting."""
import hashlib,json,math,xml.etree.ElementTree as ET
from array import array
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_proxy_budget_concrete_regression_v1_2026-10-17';D.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
primary=R/'experiments/xtea_proxy_budget_full_comparison_v2_2026-10-17/verification.json';proof=json.loads(primary.read_text())
paths={'graph':R/'experiments/freecores_rr_only_v1_2026-10-08/xtea/rr_graph.xml','native':R/'experiments/freecores_native_cold_v1_2026-10-08/xtea/physical_audit.json','control':R/'experiments/xtea_continue_primary_audit_fixture_v1_2026-10-17/model/sketch.json','proxy':R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model/sketch.json'}
bindings={str(primary):sha(primary),str(Path(__file__).resolve()):sha(__file__)}
for p in paths.values():
 h=sha(p);assert h==proof['bindings'][str(p)];bindings[str(p)]=h
write('protocol.json',dict(bindings=bindings,scope='Full fixed known-label XTEA concrete resource domain, original numeric IDs and k=660. Descriptive covariance/rank-variance decomposition and NET-union changes, not isolated causal attribution or correct native NET ownership.',policy='No parameter fit, model rerun, label generation or promotion. Include unchanged resources whose ranks shift with global tie groups.'))
models={m:json.loads(paths[m].read_text()) for m in ['control','proxy']};native=json.loads(paths['native'].read_text())['node_occupancy']
channel=set();src=array('Q');dst=array('Q');nodes=0;stack=[]
for ev,e in ET.iterparse(paths['graph'],events=('start','end')):
 if ev=='start':stack.append(e.tag);continue
 if e.tag=='node' and stack[-2]=='rr_nodes':
  assert int(e.get('id'))==nodes;nodes+=1
  if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:
   assert int(e.get('capacity'))==1;channel.add(int(e.get('id')))
  e.clear()
 elif e.tag=='edge' and stack[-2]=='rr_edges':src.append(int(e.get('src_node')));dst.append(int(e.get('sink_node')));e.clear()
 stack.pop()
assert len(channel)==proof['complete_channel_universe']==13216
truth={n:native.get(str(n),0) for n in channel};assert set(truth.values())=={0,1}
records={m:{r['connection_id']:r for r in d['records']} for m,d in models.items()};assert set(records['control'])==set(records['proxy']) and len(records['control'])==2450
unions={m:defaultdict(set) for m in models};path_changes=[];extra=[]
for cid in sorted(records['control']):
 a,b=records['control'][cid],records['proxy'][cid];assert all(a[k]==b[k] for k in ['connection_id','net_id','source','sink','floor_integer'])
 if a['answer']['physical_edge_ids']!=b['answer']['physical_edge_ids']:path_changes.append(cid)
 assert b['answer']['delay']<=b['budget_integer']
 if b['answer']['delay']>a['budget_integer']:extra.append(cid)
 for m,r in [('control',a),('proxy',b)]:
  u=r['source'];seen={u};unions[m][r['net_id']].add(u)
  for edge in r['answer']['physical_edge_ids']:
   assert src[edge]==u;u=dst[edge];assert u not in seen;seen.add(u);unions[m][r['net_id']].add(u)
  assert u==r['sink']
ledgers={}
for m in models:
 full=Counter(n for ns in unions[m].values() for n in ns);assert dict(full)=={int(n):v for n,v in models[m]['ledger'].items()}
 ledgers[m]={n:full[n] for n in channel}
# Exact doubled midranks. Native binary doubled centered ranks are -N1 / N0.
n0=sum(v==0 for v in truth.values());n1=len(channel)-n0;N=len(channel);rank={};summary={}
for m,pv in ledgers.items():
 hist=Counter(pv.values());prior=0;mid={}
 for v,c in sorted(hist.items()):mid[v]=2*prior+c-1;prior+=c
 rank[m]={n:mid[pv[n]]-(N-1) for n in channel}
 covariance=sum(rank[m][n]*(n0 if truth[n] else -n1) for n in channel)
 variance=sum(v*v for v in rank[m].values());truthvariance=n0*n1*N;rho=covariance/math.sqrt(variance*truthvariance)
 assert abs(rho-proof['metrics'][m+'1_sketch']['concrete']['spearman'])<1e-12
 summary[m]=dict(occupancy_histogram=dict(hist),exact_doubled_centered_rank_covariance=covariance,exact_doubled_rank_square_sum=variance,exact_binary_truth_rank_square_sum=truthvariance,spearman=rho,mean_doubled_centered_rank_native_used=sum(rank[m][n] for n in channel if truth[n])/n1,mean_doubled_centered_rank_native_unused=sum(rank[m][n] for n in channel if not truth[n]),mae=sum(abs(pv[n]-truth[n]) for n in channel)/N)
 summary[m]['mean_doubled_centered_rank_native_unused']/=n0
 strata={}
 for t in [0,1]:
  ids=[n for n in channel if truth[n]==t]
  strata[str(t)]=dict(resources=len(ids),predicted_positive=sum(pv[n]>0 for n in ids),total_predicted_unique_NET_occupancy=sum(pv[n] for n in ids),absolute_error_sum=sum(abs(pv[n]-t) for n in ids),over_capacity_resources=sum(pv[n]>1 for n in ids))
 summary[m]['native_use_strata']=strata
rows=[];groups=defaultdict(lambda:Counter())
for n in sorted(channel):
 a,b=ledgers['control'][n],ledgers['proxy'][n];t=truth[n];dr=rank['proxy'][n]-rank['control'][n];dc=dr*(n0 if t else -n1)
 category=f"native_{t}/"+('increased' if b>a else 'decreased' if b<a else 'unchanged')
 g=groups[category];g['resources']+=1;g['occupancy_delta']+=b-a;g['absolute_error_delta']+=abs(b-t)-abs(a-t);g['doubled_rank_delta']+=dr;g['covariance_delta']+=dc
 rows.append(dict(node=n,native=t,control=a,proxy=b,doubled_rank_delta=dr,exact_covariance_delta=dc))
assert sum(g['covariance_delta'] for g in groups.values())==summary['proxy']['exact_doubled_centered_rank_covariance']-summary['control']['exact_doubled_centered_rank_covariance']
extra_nets={records['proxy'][cid]['net_id'] for cid in extra};netrows=[];membership=defaultdict(Counter)
for net in sorted(unions['control']):
 a=unions['control'][net]&channel;b=unions['proxy'][net]&channel
 if a==b:continue
 added=b-a;removed=a-b;group='new_allowance_NET' if net in extra_nets else 'other_changed_NET'
 g=membership[group]
 for kind,ns in [('added',added),('removed',removed)]:
  for n in ns:g[kind+'_native_'+str(truth[n])]+=1
 netrows.append(dict(net_id=net,has_actual_new_allowance_user=net in extra_nets,added_channels=len(added),removed_channels=len(removed),added_native_used=sum(truth[n] for n in added),removed_native_used=sum(truth[n] for n in removed)))
assert sum(len(unions['proxy'][net]&channel)-len(unions['control'][net]&channel) for net in unions['control'])==sum(ledgers['proxy'].values())-sum(ledgers['control'].values())
for t in [0,1]:
 added=sum(g.get('added_native_'+str(t),0) for g in membership.values());removed=sum(g.get('removed_native_'+str(t),0) for g in membership.values())
 assert added-removed==sum(ledgers['proxy'][n]-ledgers['control'][n] for n in channel if truth[n]==t)
assert all(sha(k)==h for k,h in bindings.items())
write('resource_rows.json',rows);write('NET_membership_changes.json',netrows)
write('verification.json',dict(bindings=bindings,resource_rows_sha256=sha(D/'resource_rows.json'),NET_rows_sha256=sha(D/'NET_membership_changes.json'),all_original_channel_resources= N,all_paths_original_XML_arcs_and_full_unique_NET_ledgers_reconstructed=True,all_reported_concrete_correlations_exactly_reconstructed=True,summary=summary,complete_covariance_change_groups={k:dict(v) for k,v in groups.items()},changed_paths=len(path_changes),actual_new_allowance_users=len(extra),actual_new_allowance_NETs=len(extra_nets),changed_channel_union_NETs=len(netrows),membership_changes={k:dict(v) for k,v in membership.items()},scope='Post-label descriptive full-resource decomposition. All NET memberships, including canceling contributions, are counted. Native-used resource intersection is not correct native owner/path recovery. New-allowance group is observational and not isolated causality. No new metric policy, default, native utility, heldout or performance claim.'))
print(json.dumps(dict(summary=summary,groups={k:dict(v) for k,v in groups.items()},changed_paths=len(path_changes),new_allowance_users=len(extra),new_allowance_NETs=len(extra_nets),membership_changes={k:dict(v) for k,v in membership.items()}),indent=2))
