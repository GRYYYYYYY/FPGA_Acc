"""One frozen selection, baseline+trial cold native routes and original gate."""
import json,os,re,shutil,subprocess,sys,time
from pathlib import Path
from collections import Counter
from run_xtea_placement_feedback_native_v1 import audit,NET,Inventory,canonical_reload
from pre_route_endpoints import sha,placements
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text())
def evaluate(baseline_endpoint, selected_endpoint, selected_id, output):
    start=time.perf_counter();output=Path(output);output.mkdir();eps={0:load(Path(baseline_endpoint)),selected_id:load(Path(selected_endpoint))};graph=Path(eps[0]['inputs']['graph']['path']);inventory=Inventory(graph);rows=[]
    binary=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';build=load(binary.parent/'receipt.json');assert sha(binary)==build['binary_sha256']
    for cid,ep in eps.items():
        assert ep['graph_sha256']==eps[0]['graph_sha256'] and all(sha(s['path'])==s['sha256'] for s in ep['inputs'].values())
        d=output/f'candidate_{cid:02d}';d.mkdir()
        for key,target in [('blif','design.blif'),('net','design.net'),('place','design.place')]:
            p=Path(ep['inputs']['net']['path']).parent/target if key=='blif' else Path(ep['inputs'][key]['path']);shutil.copyfile(p,d/target)
        assert placements(d/'design.place',sha(d/'design.net'))==placements(ep['inputs']['place']['path'],sha(ep['inputs']['net']['path']))
        cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full'];tick=time.perf_counter()
        with (d/'native.log').open('x') as log:code=subprocess.call(cmd,cwd=d,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT)
        native_seconds=time.perf_counter()-tick
        if code:raise RuntimeError(('native',cid,code))
        text=(d/'native.log').read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text and 'NET-aware seed imported' not in text
        wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]);cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1]);tick=time.perf_counter();physical=audit(graph,d/'output.route');names={int(m[1]):m[2] for line in (d/'output.route').read_text().splitlines() if (m:=NET.match(line))};required_names=set(ep['net_names'].values());observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections'] if names[q['net_id']] in required_names);required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);assert observed==required and physical['overflow_units']==0
        (d/'physical_audit.json').write_text(json.dumps(physical)+'\n');candidate=dict(files={str(p):sha(p) for p in d.iterdir() if p.is_file()},command=cmd,width=128,decision='R',cpd_ns=cpd);canonical=canonical_reload(candidate,d,output/f'candidate_{cid:02d}_canonical',inventory);assert canonical['semantic_consistency_gate_pass'];rows.append(dict(candidate_id=cid,wirelength=wirelength,diagnostic_cpd_ns=cpd,native_seconds=native_seconds,audit_and_canonical_seconds=time.perf_counter()-tick,canonical_pass=True,route=str(d/'output.route')))
    baseline=rows[0];trial=rows[-1];accepted=selected_id!=0 and trial['wirelength']<baseline['wirelength'] and trial['diagnostic_cpd_ns']<=baseline['diagnostic_cpd_ns'];result=dict(selected_candidate=selected_id,accepted=accepted,final_candidate=selected_id if accepted else 0,rows=rows,driver_seconds=time.perf_counter()-start,scope='Original symmetric diagnostic acceptance. Async CPD not characterized timing closure;not general QoR.')
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':evaluate(sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4])
