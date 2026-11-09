"""Verify actual adaptive host decisions against independent pressure,credit and seed reconstruction."""
import argparse,csv,hashlib,json,os,shlex,subprocess,sys
from pathlib import Path
from audit_adaptive_task_events import audit
from rr_adaptive_policy_replay import replay


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['variant','parent_host','fixture','output']:p.add_argument(name,type=Path)
    a=p.parse_args();root,parent,fixture,out=[x.resolve() for x in (a.variant,a.parent_host,a.fixture,a.output)]
    out.mkdir(exist_ok=False)
    for name in ['input.nodes','input.edges','input.resources','input.tasks','topology.node_die','topology.node_box','timing.py']:
        (out/name).symlink_to(fixture/name)
    binary=root/'build/dieroute_rr'
    env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
    env.update(DIEROUTE_SPECULATIVE_WORKERS='2',DIEROUTE_REMAINING_LAYER_TAIL='1',DIEROUTE_UPSTREAM_COST='1',DIEROUTE_BOUND_UPSTREAM='1',DIEROUTE_SHADOW_SYNC_WINDOWS='1',DIEROUTE_COST_BITS='64',DIEROUTE_VPR_STYLE_COST='1',DIEROUTE_TREE_TIMING_WEIGHT_Q='128',DIEROUTE_MIN_TIMING_ITERATIONS='6',DIEROUTE_MAX_ITERATIONS='6',PERSISTROUTE_TIMING_COMMAND=shlex.join([sys.executable,str(out/'timing.py')]))
    files=[binary,parent,Path(__file__).resolve()];cases=[];comparisons=0
    def run(host,name,mode,slots,limit):
        e=dict(env,DIEROUTE_TASK_PLACEMENT_MODE=str(mode),DIEROUTE_TASK_TRANSFER_SLOTS=str(slots),DIEROUTE_TASK_TRANSFER_BYTES=str(limit))
        prefix=out/name
        with (out/(name+'.log')).open('w') as log:
            code=subprocess.run([str(host),str(out/'input'),str(out/'topology'),str(prefix),'downstream_bounded'],env=e,stdout=log,stderr=subprocess.STDOUT).returncode
        assert code==0,(name,code)
        return prefix
    for slots,limit in [(1,4096),(4,84)]:
        reference=run(parent,f'fixed_slots{slots}',2,slots,limit)
        for repeat in range(5):
            prefix=run(binary,f'adaptive_slots{slots}_{repeat}',3,slots,limit)
            resource=replay(out/'input',prefix,0,4,6,topology_prefix=out/'topology',workers=2)
            credits=audit(out/'input',out/'topology',prefix,slots,limit,3)
            assert resource['adaptive_decisions_checked']==credits['decision_requests_checked']>0
            for source in sorted(out.glob(reference.name+'.*')):
                suffix=source.name[len(reference.name):]
                if suffix in ['.log','.task_migration.csv','.task_transfer_events.csv']:continue
                target=Path(str(prefix)+suffix)
                if suffix=='.json':
                    x=json.loads(source.read_text());y=json.loads(target.read_text())
                    for row in [x,y]:
                        for key in ['wall_ms','task_placement_mode','remote_shadow_reads']:row.pop(key)
                    assert x==y
                else:assert source.read_bytes()==target.read_bytes(),(prefix,suffix)
                comparisons+=1
            with Path(str(prefix)+'.migration_decisions.csv').open() as stream:decisions=list(csv.DictReader(stream))
            destinations={int(row['selected_die']) for row in decisions}
            assert destinations=={0,1},destinations
            cases.append(dict(name=prefix.name,slots=slots,byte_limit=limit,selected_dies=sorted(destinations),pressure_resource_replay=resource,decision_credit_replay=credits))
    pristine=out/'adaptive_slots1_0';rejected=[];coherent=False
    for kind in ['wrong_score','wrong_selected','wrong_q','wrong_queue_load','coherent_wrong_pressure','wrong_window','missing_decision','duplicate_decision']:
        bad=out/kind;bad.mkdir()
        for source in out.glob(pristine.name+'.*'):(bad/('route'+source.name[len(pristine.name):])).symlink_to(source)
        path=bad/'route.migration_decisions.csv'
        with path.open() as stream:
            reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
        r=rows[0]
        if kind=='wrong_score':r['source_score']=str(int(r['source_score'])+1)
        elif kind=='wrong_selected':r['selected_die']=str(1-int(r['selected_die']))
        elif kind=='wrong_q':r['criticality_q']=str(int(r['criticality_q'])+1)
        elif kind=='wrong_queue_load':r['source_entries']=str(int(r['source_entries'])+1)
        elif kind=='coherent_wrong_pressure':
            q=int(r['criticality_q']);r['source_pressure']=str(int(r['source_pressure'])+1)
            score=(int(r['source_entries'])<<8)+(int(r['source_bytes'])<<8)//int(r['source_byte_limit'])+int(r['source_pressure'])*(65535-q)//65535
            score+=(q<<8)//65535 if r['source_die']!=r['sink_die'] else 0
            r['source_score']=str(score)
        elif kind=='wrong_window':r['window']='99999'
        elif kind=='missing_decision':rows.pop(0)
        elif kind=='duplicate_decision':rows.insert(0,dict(r))
        path.unlink()
        with path.open('w') as stream:
            w=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
        if kind=='coherent_wrong_pressure':
            audit(out/'input',out/'topology',bad/'route',1,4096,3)
            try:replay(out/'input',bad/'route',0,4,6,topology_prefix=out/'topology',workers=2)
            except AssertionError:coherent=True;rejected.append(kind)
            else:raise AssertionError('coherently forged pressure accepted')
        else:
            try:audit(out/'input',out/'topology',bad/'route',1,4096,3)
            except (AssertionError,KeyError):rejected.append(kind)
            else:raise AssertionError(('bad decision accepted',kind))
    assert coherent
    files.extend(p for p in out.iterdir() if p.is_file())
    report=dict(status='ten_tail_enabled_adaptive_host_runs_pressure_credit_seed_and_state_audited',runs=cases,parent_artifact_comparisons=comparisons,rejected_decision_corruptions=rejected,coherently_forged_pressure_independently_rejected=True,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='10actual smallgraph tail-enabled adaptivehostruns,5percreditsetting; static destination control uses same combined binary. Two-die fixture only; three-layer joint native result remains unverified. Allcriticalities/decisionformulas/admissionloads andauthoritativeboundarypressure reconstructed,allseedsandresources replayed;8decisioncorruptions rejected. Notnativefullgraph,globalpolicyoptimality,independentspeculativereadsetorhardwareproof.',board_result=False,research_complete=False)
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],runs=len(cases),comparisons=comparisons,rejected=rejected)))


if __name__=='__main__':main()
