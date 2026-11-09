"""Exercise frozen net-order/schedule factors with exact dispatch and state replay."""
import argparse,csv,hashlib,json,os,shlex,struct,subprocess,sys
from pathlib import Path
from rr_fanout_present_replay import replay


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['variant','parent_host','output']:p.add_argument(name,type=Path)
    a=p.parse_args();root,parent,out=[x.resolve() for x in (a.variant,a.parent_host,a.output)];out.mkdir(exist_ok=False)
    adjacency={0:[1],2:[3,4,5],6:[7,8],9:[10,11]};nodes=[];edges=[]
    for node in range(12):
        next_=adjacency.get(node,[]);nodes.append((len(edges),len(next_),0 if next_ else 1));edges.extend((dst,3,512) for dst in next_)
    tasks=[]
    for net,source,sinks,q in [(9,0,[1],65000),(2,2,[3,4,5],0),(7,6,[7,8],30000),(1,9,[10,11],20000)]:
        for sink in sinks:tasks.append((len(tasks),net,source,sink,q,8,len(tasks),0,0))
    for suffix,layout,rows in [('nodes','<IHH',nodes),('edges','<IHH',edges),('resources','<HHHHII',[(0,1,256,0,0,0xffffffff)]*12),('tasks','<IIIIHHIII',tasks)]:
        (out/('input.'+suffix)).write_bytes(b''.join(struct.pack(layout,*r) for r in rows))
    (out/'topology.node_die').write_bytes(bytes(24));(out/'topology.node_box').write_bytes(bytes(96))
    timing=out/'timing.py';timing.write_text("import csv,sys\nwith open(sys.argv[2]) as s:rows=list(csv.DictReader(s))\nwith open(sys.argv[3],'w') as s:\n w=csv.writer(s,lineterminator='\\n');w.writerow(['task_id','criticality_q','delay_ps','slack_ps','critical_path_delay_ps'])\n for r in rows:w.writerow([r['task_id'],60000-8000*int(r['task_id']),r['delay_ps'],0,1])\n")
    env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))};env.update(DIEROUTE_COST_BITS='64',DIEROUTE_VPR_STYLE_COST='1',DIEROUTE_TREE_TIMING_WEIGHT_Q='128',DIEROUTE_MIN_TIMING_ITERATIONS='6',DIEROUTE_MAX_ITERATIONS='6',PERSISTROUTE_TIMING_COMMAND=shlex.join([sys.executable,str(timing)]))
    binary=root/'build/dieroute_rr';cases=[];checks=0
    def run(host,name,schedule,order):
        prefix=out/name;e=dict(env,DIEROUTE_ORDINARY_SCHEDULE_MODE=str(schedule),DIEROUTE_NET_DISPATCH_ORDER=str(order))
        with (out/(name+'.log')).open('w') as log:code=subprocess.run([str(host),str(out/'input'),str(out/'topology'),str(prefix),'flat'],env=e,stdout=log,stderr=subprocess.STDOUT).returncode
        assert code==0,(name,code)
        return prefix
    for schedule in [0,2]:
        reference=run(parent,f'parent{schedule}',schedule,0)
        for order in [0,1]:
            previous=None
            for repeat in range(5):
                prefix=run(binary,f'schedule{schedule}_order{order}_{repeat}',schedule,order)
                result=replay(out/'input',prefix,schedule,4,6,net_order_mode=order);assert result['cpu_legal']
                report=json.loads(Path(str(prefix)+'.json').read_text());assert report['net_dispatch_order']==order;report.pop('wall_ms')
                hashes={p.name[len(prefix.name):]:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob(prefix.name+'.*') if p.suffix not in ['.json','.log']}
                if previous is not None:assert previous==(report,hashes)
                previous=(report,hashes)
                if not order:
                    for source in out.glob(reference.name+'.*'):
                        suffix=source.name[len(reference.name):]
                        if suffix=='.log':continue
                        target=Path(str(prefix)+suffix)
                        if suffix=='.json':
                            x=json.loads(source.read_text());y=json.loads(target.read_text());x.pop('wall_ms');y.pop('wall_ms');assert y.pop('net_dispatch_order')==0;assert y.pop('present_schedule_mode')==0;assert x==y
                        else:assert source.read_bytes()==target.read_bytes(),(prefix,suffix)
                        checks+=1
                with Path(str(prefix)+'.net_dispatch.csv').open() as stream:rows=list(csv.DictReader(stream))
                if order:
                    first=[]
                    for row in rows:
                        if row['iteration']!='0':break
                        net=int(row['net_id'])
                        if net not in first:first.append(net)
                    assert first==[2,1,7,9],first
                cases.append(dict(name=prefix.name,schedule=schedule,net_order=order,replay=result))
    pristine=out/'schedule2_order1_0';rejected=[]
    for kind in ['fanout','rank','task','position','mode','missing']:
        bad=out/kind;bad.mkdir()
        for source in out.glob(pristine.name+'.*'):(bad/('route'+source.name[len(pristine.name):])).symlink_to(source)
        path=bad/'route.net_dispatch.csv'
        with path.open() as stream:
            reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
        if kind=='missing':rows.pop(0)
        else:
            key={'fanout':'fanout','rank':'net_rank','task':'task_id','position':'position','mode':'net_order_mode'}[kind];rows[0][key]=str(int(rows[0][key])+1)
        path.unlink()
        with path.open('w') as stream:
            w=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
        try:replay(out/'input',bad/'route',2,4,6,net_order_mode=1)
        except AssertionError:rejected.append(kind)
        else:raise AssertionError(('forged dispatch accepted',kind))
    negative=False
    try:replay(out/'input',pristine,2,4,6,net_order_mode=0)
    except AssertionError:negative=True
    assert negative
    files=[binary,parent,Path(__file__).resolve(),Path(__file__).with_name('rr_fanout_present_replay.py'),*out.glob('input.*'),*out.glob('topology.*'),timing]
    proof=dict(status='twenty_actual_fanout_schedule_host_runs_dispatch_and_state_replayed',runs=cases,parent_artifact_comparisons=checks,rejected_dispatch_corruptions=rejected,wrong_policy_rejected=True,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='20actualhostruns/fourfactorialarms,5repeats each,6STAepochs,fanoutcounts3/2/2/1includingnetIDtie. Exactdispatch/priority/seed/resource/version/path/timingreplay andlegacydefaultparentchecks. NativequalityandVPRobjectiveequivalence notestablished.',board_result=False,research_complete=False)
    (out/'audit.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(dict(status=proof['status'],runs=len(cases),checks=checks,rejected=rejected)))


if __name__=='__main__':main()
