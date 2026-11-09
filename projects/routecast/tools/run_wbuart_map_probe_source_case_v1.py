"""Execute fixed native utility arms with exact initial-state readback.

Execution requires a completed workflow-admission manifest; --preflight is
read-only. Every failure is recorded without replacing the fixed case.
"""
import argparse,json,os,re,resource,shutil,subprocess,sys,time
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
from shared_compact_native_inventory_v1 import Inventory
import canonical_reload_pin_index_expat_v3 as canonical
LIMIT=32*2**30

def validate(manifest,case):
    m=json.loads(Path(manifest).read_text())
    if m['schema']!='WBUART_FROZEN_NATIVE_UTILITY_V1':raise ValueError('manifest schema')
    if not all(sha(p)==h for p,h in m['bindings'].items()):raise ValueError('manifest input changed')
    matches=[r for r in m['cases'] if r['case']==case]
    if len(matches)!=1:raise ValueError('case identity')
    row=matches[0]
    if m['phase']=='source_qualification' and row['frame']!='source':raise ValueError('source-only phase')
    if m['phase'] not in ('source_qualification','target_native_control_and_utility'):raise ValueError('native phase')
    ep=json.loads(Path(row['endpoint']).read_text())
    if ep['graph_sha256']!=row['graph_sha256']:raise ValueError('graph epoch')
    for v in ep['inputs'].values():
        if sha(v['path'])!=v['sha256']:raise ValueError('endpoint dependency changed')
    if row['width'] not in (96,128,160):raise ValueError('width')
    return m,row,ep

def child_limit():resource.setrlimit(resource.RLIMIT_AS,(LIMIT,LIMIT))
def canonical_run(cmd,work,log,environment):
    with log.open('x') as stream:
        return subprocess.run(cmd,cwd=work,env=environment,stdout=stream,stderr=subprocess.STDOUT,preexec_fn=child_limit).returncode

def execute(manifest,case):
    begin=time.perf_counter();m,row,ep=validate(manifest,case)
    if not m['native_execution_admitted']:raise ValueError('native execution phase not admitted')
    utility=row.get('utility_arm')
    if utility not in ('disabled','zero','forecast'):raise ValueError('utility arm')
    risk=None
    if utility!='disabled':
        risk_proof=Path(row['preload_directory'])/'verification.json';risk_admission=json.loads(risk_proof.read_text())
        if risk_admission['status']!='FIXED_EXCESS_AND_ZERO_PRELOAD_INPUTS_EXPORTED_NATIVE_READBACK_PENDING':raise ValueError('risk admission')
        if risk_admission['graph_sha256']!=row['graph_sha256'] or risk_admission['nodes']!=row['graph_nodes']:raise ValueError('risk graph domain')
        if not all(sha(p)==h for p,h in risk_admission['bindings'].items()):raise ValueError('risk binding changed')
        risk=Path(row['preload_directory'])/(utility+'.risk')
        if risk_admission['bindings'].get(str(risk))!=sha(risk):raise ValueError('risk not bound')
    d=Path(row['output']);d.mkdir(parents=True,exist_ok=False)
    for key,dest in [('blif','design.blif'),('net','design.net'),('place','design.place')]:shutil.copyfile(row['inputs'][key],d/dest)
    cmd=row['command'];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
    env['ROUTECAST_NATIVE_OWNER_TRACE']=str(d/'owner_trace.tsv')
    env['ROUTECAST_EXPECTED_COST_TRACE']=str(d/'expected_cost.tsv')
    env.update(ROUTECAST_MAP_QUERY_PROBE=str(d/'map_query.tsv'),ROUTECAST_MAP_PROBE_GRAPH_SHA256=row['graph_sha256'],ROUTECAST_MAP_PROBE_ENDPOINT_SHA256=sha(row['endpoint']))
    if risk is not None:
        env.update(ROUTECAST_EXCESS_PRELOAD=str(risk),ROUTECAST_EXCESS_GRAPH_SHA256=row['graph_sha256'],ROUTECAST_EXCESS_STATE_DUMP=str(d/'preload_state.bin'))
    (d/'protocol.json').write_text(json.dumps(dict(manifest=str(Path(manifest).resolve()),manifest_sha256=sha(manifest),case=case,command=cmd,child_address_space_limit_bytes=LIMIT,timeout_seconds=None),indent=2)+'\n')
    result=dict(case=case,status='NATIVE_OR_AUDIT_FAILED',exit_status=None,strict_unseen_admitted=False,complete_workflow_gain_proven=False,execution_phase=m['phase'])
    try:
        tick=time.perf_counter()
        with (d/'native.log').open('x') as log:
            result['exit_status']=subprocess.run(cmd,cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=child_limit).returncode
        result['native_process_seconds']=time.perf_counter()-tick
        (d/'terminal.json').write_text(json.dumps(result)+'\n')
        if result['exit_status']!=0:raise ValueError('native failure')
        log=(d/'native.log').read_text()
        if 'VPR succeeded' not in log or 'Completed routing consistency check successfully.' not in log:raise ValueError('native FULL gate')
        result['wirelength']=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1])
        result['diagnostic_cpd_ns']=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1])
        result['iterations']=int(re.search(r'Successfully routed after (\d+) routing iterations',log)[1])
        if risk is not None:
            from preload_state_readback_contract_v1 import verify
            result['preload_state']=verify(d/'preload_state.bin',risk,row['graph_sha256'],row['graph_nodes'],log)
        result['utility_arm']=utility
        tick=time.perf_counter();graph=ep['inputs']['graph']['path'];physical=audit(graph,d/'output.route')
        names={int(x[1]):x[2] for line in (d/'output.route').read_text().splitlines() if (x:=NET.match(line))}
        required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections'])
        observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections'])
        if observed!=required or physical['overflow_units']!=0:raise ValueError('physical endpoint/capacity gate')
        (d/'physical_audit.json').write_text(json.dumps(physical)+'\n')
        result['physical_audit_seconds']=time.perf_counter()-tick
        tick=time.perf_counter();inventory=Inventory(Path(graph));canonical.run=canonical_run
        from audit_mmc_v16_native_iteration_work_v1 import parse as parse_work
        from native_owner_trace_replay_v1 import replay
        work=parse_work(log);capacities=[inventory.graph.nodes[n].capacity for n in range(row['graph_nodes'])]
        traced,state=replay(d/'owner_trace.tsv',capacities,work['rows'])
        totals=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',log)
        keys=['NET_operations','connection_operations','heap_pushes','heap_pops']
        observed_totals={k:sum(x[k] for x in traced['iteration_stats']) for k in keys}
        if len(totals)!=1 or tuple(observed_totals[k] for k in keys)!=tuple(map(int,totals[0])):raise ValueError('trace work counters')
        from audit_native_route import NODE
        printed={};net_id=None
        for line in (d/'output.route').read_text().splitlines():
            match=NET.match(line)
            if match:
                net_id=int(match[1])
                if net_id in printed:raise ValueError('duplicate printed NET')
                printed[net_id]=set()
            node=NODE.match(line)
            if node:
                if net_id is None:raise ValueError('node outside NET')
                printed[net_id].add(int(node[1]))
        for net_id,nodes_used in printed.items():
            if nodes_used and (state[net_id][:3]!=(0,1,0) or set(state[net_id][3])!=nodes_used):raise ValueError('final trace/physical NET mismatch')
        if any(value[1] and not value[0] and net_id not in printed for net_id,value in state.items()):raise ValueError('unprinted final tree')
        traced.update(exact_native_work_counters_equal=True,final_physical_NET_unions_equal=True,work=observed_totals)
        (d/'trace_replay.json').write_text(json.dumps(traced)+'\n')
        result['native_work']=observed_totals;result['independent_trace_replay_pass']=True
        candidate=dict(files={str(p):sha(p) for p in d.iterdir() if p.is_file()},command=cmd,width=row['width'],decision='R',cpd_ns=result['diagnostic_cpd_ns'])
        result['canonical']=canonical.canonical_reload(candidate,d,d.parent/(d.name+'_canonical'),inventory)
        result['canonical_with_inventory_seconds']=time.perf_counter()-tick
        if not result['canonical']['semantic_consistency_gate_pass']:raise ValueError('canonical gate')
        result['status']='FULL_PHYSICAL_AND_CANONICAL_PASS'
    except Exception as exc:result['error']=repr(exc)
    result['complete_case_component_seconds']=time.perf_counter()-begin
    result['scope']='Unseeded native case plus physical/canonical audit. CPD diagnostic only. Not complete matched RouteCast workflow timing.'
    result['bindings']={**({**risk_admission['bindings'],str(risk_proof):sha(risk_proof)} if risk is not None else {}),str(Path(manifest).resolve()):sha(manifest),**{str(p):sha(p) for p in d.rglob('*') if p.is_file()}}
    (d/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('case');p.add_argument('--preflight',action='store_true');a=p.parse_args()
    if a.preflight:
        m,row,ep=validate(a.manifest,a.case);print(json.dumps(dict(case=a.case,preflight_pass=True,full_workflow_admitted=m['native_execution_admitted'])))
    else:
        result=execute(a.manifest,a.case);print(json.dumps(result));sys.exit(0 if result['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' else 1)
