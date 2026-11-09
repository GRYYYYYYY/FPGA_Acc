"""Bounded first16NET stage diagnosis, original producer preserved."""
import pathlib,json,time,faulthandler,resource
from collections import defaultdict
from MMC_zero_node_RC_shared_CSR_v1 import load
from shortest_NET_tree_csr_v1 import prepare_csr
from NET_tree_expected_occupancy_v1 import predict
R=pathlib.Path(__file__).resolve().parents[1];resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));O=R/'experiments/mmc_full_ensemble_prefix_diagnosis_v2_2026-10-19';O.mkdir();fault=(O/'stack_samples.log').open('x');faulthandler.dump_traceback_later(20,repeat=True,file=fault)
ep=json.loads((R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json').read_text());groups=defaultdict(list)
for q in ep['connections']:groups[q['net_id']].append(q)
print('LOAD',flush=True);offsets,dest,costs,caps,kinds,_=load(pathlib.Path(ep['inputs']['graph']['path']))
for net,qs in sorted(groups.items())[:16]:
 print('NET SEARCH START',net,flush=True);p=prepare_csr(offsets,dest,costs,caps,kinds,qs[0]['source'],sorted({q['sink'] for q in qs}));print('NET PREDICT START',net,'support',len(p['distance']),flush=True);pred=predict(p,net_id=net);print('NET DONE',net,pred['mode'],flush=True)
faulthandler.cancel_dump_traceback_later();print('PREFIX DIAGNOSIS COMPLETE',flush=True)
