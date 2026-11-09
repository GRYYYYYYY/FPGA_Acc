"""Execute one manifest-bound native route and physical/canonical audits.

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
    if m['schema']!='ROUTECAST_EXTERNAL_NATIVE_CASE_MANIFEST_V1':raise ValueError('manifest schema')
    if not all(sha(p)==h for p,h in m['bindings'].items()):raise ValueError('manifest input changed')
    matches=[r for r in m['cases'] if r['case']==case]
    if len(matches)!=1:raise ValueError('case identity')
    row=matches[0];ep=json.loads(Path(row['endpoint']).read_text())
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
    if not m['full_workflow_admitted']:raise ValueError('full workflow protocol not yet admitted')
    d=Path(row['output']);d.mkdir(parents=True,exist_ok=False)
    for key,dest in [('blif','design.blif'),('net','design.net'),('place','design.place')]:shutil.copyfile(row['inputs'][key],d/dest)
    cmd=row['command'];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
    (d/'protocol.json').write_text(json.dumps(dict(manifest=str(Path(manifest).resolve()),manifest_sha256=sha(manifest),case=case,command=cmd,child_address_space_limit_bytes=LIMIT,timeout_seconds=None),indent=2)+'\n')
    result=dict(case=case,status='NATIVE_OR_AUDIT_FAILED',exit_status=None)
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
        tick=time.perf_counter();graph=ep['inputs']['graph']['path'];physical=audit(graph,d/'output.route')
        names={int(x[1]):x[2] for line in (d/'output.route').read_text().splitlines() if (x:=NET.match(line))}
        required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections'])
        observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections'])
        if observed!=required or physical['overflow_units']!=0:raise ValueError('physical endpoint/capacity gate')
        (d/'physical_audit.json').write_text(json.dumps(physical)+'\n')
        result['physical_audit_seconds']=time.perf_counter()-tick
        tick=time.perf_counter();inventory=Inventory(Path(graph));canonical.run=canonical_run
        candidate=dict(files={str(p):sha(p) for p in d.iterdir() if p.is_file()},command=cmd,width=row['width'],decision='R',cpd_ns=result['diagnostic_cpd_ns'])
        result['canonical']=canonical.canonical_reload(candidate,d,d.parent/(d.name+'_canonical'),inventory)
        result['canonical_with_inventory_seconds']=time.perf_counter()-tick
        if not result['canonical']['semantic_consistency_gate_pass']:raise ValueError('canonical gate')
        result['status']='FULL_PHYSICAL_AND_CANONICAL_PASS'
    except Exception as exc:result['error']=repr(exc)
    result['complete_case_component_seconds']=time.perf_counter()-begin
    result['scope']='Unseeded native case plus physical/canonical audit. CPD diagnostic only. Not complete matched RouteCast workflow timing.'
    result['bindings']={str(Path(manifest).resolve()):sha(manifest),**{str(p):sha(p) for p in d.rglob('*') if p.is_file()}}
    (d/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('case');p.add_argument('--preflight',action='store_true');a=p.parse_args()
    if a.preflight:
        m,row,ep=validate(a.manifest,a.case);print(json.dumps(dict(case=a.case,preflight_pass=True,full_workflow_admitted=m['full_workflow_admitted'])))
    else:
        result=execute(a.manifest,a.case);print(json.dumps(result));sys.exit(0 if result['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' else 1)
