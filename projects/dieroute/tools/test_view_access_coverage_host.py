"""Verify independently tracked view accesses cover the actual validation journal."""
import argparse,csv,hashlib,json,os,shlex,struct,subprocess,sys
from pathlib import Path
from rr_observed_read_replay import replay
from audit_view_access_coverage import audit


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['variant','parent_host','fixture','output']:p.add_argument(name,type=Path)
    a=p.parse_args();root,parent,fixture,out=[x.resolve() for x in (a.variant,a.parent_host,a.fixture,a.output)]
    out.mkdir(exist_ok=False)
    for name in ['input.nodes','input.edges','input.resources','input.tasks','topology.node_die','topology.node_box','timing.py']:(out/name).symlink_to(fixture/name)
    host=root/'build/dieroute_rr';files=[host,parent,Path(__file__).resolve()];cases=[];comparisons=0
    env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
    env.update(DIEROUTE_SPECULATIVE_WORKERS='2',DIEROUTE_TASK_TRANSFER_SLOTS='1',DIEROUTE_TASK_TRANSFER_BYTES='4096',DIEROUTE_COST_BITS='64',DIEROUTE_VPR_STYLE_COST='1',DIEROUTE_TREE_TIMING_WEIGHT_Q='128',DIEROUTE_MIN_TIMING_ITERATIONS='6',DIEROUTE_MAX_ITERATIONS='6',PERSISTROUTE_TIMING_COMMAND=shlex.join([sys.executable,str(out/'timing.py')]))
    def run(binary,name,mode,sync,record):
        e=dict(env,DIEROUTE_TASK_PLACEMENT_MODE=str(mode),DIEROUTE_SHADOW_SYNC_WINDOWS=str(sync),DIEROUTE_RECORD_READ_VALUES=str(record),DIEROUTE_AUDIT_READ_COVERAGE=str(record if binary==host else 0))
        prefix=out/name
        with (out/(name+'.log')).open('w') as log:code=subprocess.run([str(binary),str(out/'input'),str(out/'topology'),str(prefix),'flat'],env=e,stdout=log,stderr=subprocess.STDOUT).returncode
        assert code==0,(name,code)
        return prefix
    for mode in [2,3]:
        for sync in [1,3]:
            reference=run(parent,f'parent_mode{mode}_sync{sync}',mode,sync,1)
            for repeat in range(5):
                prefix=run(host,f'mode{mode}_sync{sync}_{repeat}',mode,sync,1)
                result=replay(out/'input',prefix,0,4,6,topology_prefix=out/'topology',workers=2,shadow_sync=sync)
                assert result['cpu_legal'] and result['observed_read_rows_checked']>0
                for source in out.glob(reference.name+'.*'):
                    suffix=source.name[len(reference.name):]
                    if suffix=='.log':continue
                    target=Path(str(prefix)+suffix)
                    if suffix=='.json':
                        x=json.loads(source.read_text());y=json.loads(target.read_text());x.pop('wall_ms');y.pop('wall_ms');assert x==y
                    else:assert source.read_bytes()==target.read_bytes(),(prefix,suffix)
                    comparisons+=1
                census=audit(out/'input',out/'topology',prefix)
                assert census['unique_node_occurrences']==result['observed_read_rows_checked']
                cases.append(dict(name=prefix.name,mode=mode,sync=sync,replay=result,coverage=census))
    assert any(r['replay']['fresh_replays_checked']>0 for r in cases if r['sync']==3)
    assert any(r['replay']['remote_shadow_rows_checked']>0 for r in cases)
    pristine=out/'mode3_sync3_0';layout=struct.Struct('<QIIIIIIHHHHIIQQ');rejected=[]
    for kind in ['occupancy','capacity','version','owner','present','history','index','phase','missing','duplicate','truncated']:
        bad=out/kind;bad.mkdir()
        for source in out.glob(pristine.name+'.*'):(bad/('route'+source.name[len(pristine.name):])).symlink_to(source)
        path=bad/'route.observed_reads.bin';raw=path.read_bytes();rows=list(layout.iter_unpack(raw))
        if kind in ['occupancy','capacity','version','owner','present','history','index','phase']:
            fields={'occupancy':7,'capacity':8,'version':11,'owner':12,'present':13,'history':14,'index':5,'phase':3};r=list(rows[0]);r[fields[kind]]^=1;rows[0]=tuple(r);modified=b''.join(layout.pack(*r) for r in rows)
        elif kind=='missing':modified=raw[64:]
        elif kind=='duplicate':modified=raw[:64]+raw
        else:modified=raw[:-1]
        path.unlink();path.write_bytes(modified)
        try:replay(out/'input',bad/'route',0,4,6,topology_prefix=out/'topology',workers=2,shadow_sync=3)
        except (AssertionError,KeyError):rejected.append(kind)
        else:raise AssertionError(('forged read observation accepted',kind))
    coverage_rejected=[];coverage_layout=struct.Struct('<QIIIIIIQQ')
    for kind in ['wrong_node','resource_count','cost_count','reserved','observer','missing','duplicate','summary_total','summary_missing']:
        bad=out/('coverage_'+kind);bad.mkdir()
        for source in out.glob(pristine.name+'.*'):(bad/('route'+source.name[len(pristine.name):])).symlink_to(source)
        if kind in ['summary_total','summary_missing']:
            path=bad/'route.view_access_summary.csv'
            with path.open() as stream:
                reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
            if kind=='summary_total':rows[0]['resource_calls']=str(int(rows[0]['resource_calls'])+1)
            else:rows.pop(0)
            path.unlink()
            with path.open('w') as stream:
                writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
        else:
            path=bad/'route.view_access_coverage.bin';raw=path.read_bytes();rows=list(coverage_layout.iter_unpack(raw))
            if kind=='missing':modified=raw[48:]
            elif kind=='duplicate':modified=raw[:48]+raw
            else:
                row=list(rows[0]);index={'wrong_node':5,'resource_count':7,'cost_count':8,'reserved':6,'observer':4}[kind];row[index]+=1;rows[0]=tuple(row);modified=b''.join(coverage_layout.pack(*row) for row in rows)
            path.unlink();path.write_bytes(modified)
        try:audit(out/'input',out/'topology',bad/'route')
        except (AssertionError,KeyError):coverage_rejected.append(kind)
        else:raise AssertionError(('bad API census accepted',kind))
    files.extend(p for p in out.iterdir() if p.is_file())
    report=dict(status='twenty_actual_host_independent_view_censuses_and_read_journals_checked',runs=cases,parent_artifact_comparisons=comparisons,rejected_corruptions=rejected,rejected_coverage_corruptions=coverage_rejected,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='20actualhostruns,5permode/syncsetting. SeparateexplicitviewAPIcensus exactlymatchesvalidationjournalnodes;pernode/globalcallcounts andproposalidentitieschecked. Fullauthorityvalue/staleness/seedreplay andparentcompatibility includes64byteobservedstreams.11value+9censuscorruptionsrejected. DoesnotprovearbitraryC++pointeraccesses,searchoptimalityorhardware.',board_result=False,research_complete=False)
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],runs=len(cases),comparisons=comparisons,rejected=rejected,coverage_rejected=coverage_rejected)))


if __name__=='__main__':main()
