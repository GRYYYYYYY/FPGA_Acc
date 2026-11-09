"""One deterministic input-only diagnostic; preserve the original live producer."""
import pathlib,json,time,faulthandler,resource
from MMC_zero_node_RC_shared_CSR_v1 import load
from shortest_NET_tree_csr_v1 import prepare_csr
from NET_tree_expected_occupancy_v1 import predict
R=pathlib.Path(__file__).resolve().parents[1]
resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30))
O=R/'experiments/mmc_full_ensemble_first_NET_diagnosis_v1_2026-10-19';O.mkdir();fault=(O/'stack_samples.log').open('x');faulthandler.dump_traceback_later(20,repeat=True,file=fault)
ep=json.loads((R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json').read_text());qs=[q for q in ep['connections'] if q['net_id']==0];source=qs[0]['source'];sinks=sorted({q['sink'] for q in qs});tick=time.perf_counter();print('DIAGNOSTIC GRAPH LOAD START',flush=True)
offsets,dest,costs,caps,kinds,seconds=load(pathlib.Path(ep['inputs']['graph']['path']));print('PREPARE START',time.perf_counter()-tick,flush=True)
p=prepare_csr(offsets,dest,costs,caps,kinds,source,sinks);print('PREDICT START',time.perf_counter()-tick,'support',len(p['distance']),flush=True)
x=predict(p,net_id=0);print('PREDICT COMPLETE',time.perf_counter()-tick,len(x['probabilities']),flush=True);faulthandler.cancel_dump_traceback_later()
(O/'result.json').write_text(json.dumps(dict(status='first_NET_diagnostic_complete',support_nodes=len(p['distance']),mode=x['mode'],elapsed=time.perf_counter()-tick))+'\n')
