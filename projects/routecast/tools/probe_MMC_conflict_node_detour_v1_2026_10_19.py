"""Full-graph fixed-node deletion probe; no native labels or parameter search."""
import json,pathlib,time,hashlib
from array import array
from MMC_zero_node_RC_shared_CSR_v1 import load
from shortest_NET_tree_csr_certified_v2 import prepare_csr
R=pathlib.Path(__file__).resolve().parents[1]
O=R/'experiments/mmc_conflict_node_detour_v1_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False)
 cp=R/'experiments/mmc_NET_support_capacity_v1_2026-10-19/results.json'
 cert=json.loads(cp.read_text())['cases'][0]['certificate'];blocked=cert['node']
 graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml'
 protocol=dict(blocked_node=blocked,NET_ids=[a['net_id'] for a in cert['owners']],criterion='Compare all sink lexicographic RC/hops minima before/after deleting fixed conflict node; independent proof pending',bindings={str(p):sha(p) for p in [cp,graph,pathlib.Path(__file__).resolve()]})
 (O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 offsets,dest,cost,caps,kinds,seconds=load(graph);rows=[]
 for owner in cert['owners']:
  net=owner['net_id'];before=None
  for mode in ['original','blocked']:
   cap=array('I',caps)
   if mode=='blocked':cap[blocked]=0
   start=time.monotonic()
   try:p=prepare_csr(offsets,dest,cost,cap,kinds,owner['source'],owner['sinks'])
   except ValueError:
    rows.append(dict(net_id=net,mode=mode,status='UNREACHABLE_SINK_EXISTS'));continue
   for key in ['potential_cost','potential_hops']:(O/f'net_{net}_{mode}_{key}.bin').write_bytes(p[key].tobytes())
   labels={str(s):list(p['distance'][s]) for s in p['sinks']}
   (O/f'net_{net}_{mode}_sink_labels.json').write_text(json.dumps(labels)+'\n')
   if mode=='original':
    assert {str(v):[list(t) for t in row] for v,row in p['choices'].items()}==owner['support_choices']
    assert {str(v):list(d) for v,d in p['distance'].items()}==owner['support_distance'];before=labels
   row=dict(net_id=net,source=p['source'],sinks=len(p['sinks']),mode=mode,seconds=time.monotonic()-start,status='PRODUCED_NOT_INDEPENDENTLY_VERIFIED',search_stats=p['search_stats'])
   if before is not None and mode=='blocked':
    assert all(tuple(labels[s])>=tuple(before[s]) for s in labels)
    row.update(increased_RC_sinks=sum(labels[s][0]>before[s][0] for s in labels),same_RC_more_hops_sinks=sum(labels[s][0]==before[s][0] and labels[s][1]>before[s][1] for s in labels),unchanged_sinks=sum(labels[s]==before[s] for s in labels),witness_before=before[str(owner['dominated_sink'])],witness_after=labels[str(owner['dominated_sink'])])
   rows.append(row);print(json.dumps(row),flush=True)
 (O/'results.json').write_text(json.dumps(dict(graph_load_seconds=seconds,rows=rows,independent_verification_pending=True),indent=2)+'\n')
if __name__=='__main__':main()
