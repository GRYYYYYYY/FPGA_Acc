"""Verify every decoded task seed against controller reconstruction and corruption controls."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shlex
import struct
import subprocess
import sys
from audit_task_credit_events import audit
from rr_transfer_seed_replay import replay


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('host', type=Path)
    p.add_argument('parent_host', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    host, parent, out = [x.resolve() for x in (a.host, a.parent_host, a.output)]
    out.mkdir(exist_ok=False)
    nodes = [(0,2,0),(2,0,1),(2,0,1),(2,2,0),(4,0,1),(4,0,1)]
    edges = [(1,3,512),(2,3,1024),(4,3,512),(5,3,1024)]
    tasks = [(0,7,0,1,32768,8,0,0,0),(1,7,0,2,32768,8,1,0,0),
             (2,8,3,4,32768,8,2,0,0),(3,8,3,5,32768,8,3,0,0)]
    resources = [(0,1,256,0,0,0xffffffff) for _ in nodes]
    for suffix, layout, rows in [('nodes','<IHH',nodes),('edges','<IHH',edges),
                                 ('resources','<HHHHII',resources),('tasks','<IIIIHHIII',tasks)]:
        (out/('input.'+suffix)).write_bytes(b''.join(struct.pack(layout,*r) for r in rows))
    (out/'topology.node_die').write_bytes(struct.pack('<6H',0,1,1,0,1,1))
    (out/'topology.node_box').write_bytes(bytes(8*len(nodes)))
    timing = out/'timing.py'
    timing.write_text("import csv,sys\nwith open(sys.argv[2]) as s: rows=list(csv.DictReader(s))\nwith open(sys.argv[3],'w') as s:\n w=csv.writer(s,lineterminator='\\n');w.writerow(['task_id','criticality_q','delay_ps','slack_ps','critical_path_delay_ps'])\n for r in rows:w.writerow([r['task_id'],12000+6000*int(r['task_id']),r['delay_ps'],0,1])\n")
    env = {k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
    env.update(DIEROUTE_SPECULATIVE_WORKERS='2',DIEROUTE_SHADOW_SYNC_WINDOWS='3',
        DIEROUTE_COST_BITS='64',DIEROUTE_VPR_STYLE_COST='1',DIEROUTE_TREE_TIMING_WEIGHT_Q='128',
        DIEROUTE_MIN_TIMING_ITERATIONS='6',DIEROUTE_MAX_ITERATIONS='6',
        PERSISTROUTE_TIMING_COMMAND=shlex.join([sys.executable,str(timing)]))
    cases, files, comparisons = [], [host,parent,Path(__file__).resolve(),timing], 0

    def run(binary,name,placement,slots=0,byte_limit=4096,valid=True):
        prefix=out/name
        e=dict(env,DIEROUTE_TASK_PLACEMENT_MODE=str(placement),DIEROUTE_TASK_TRANSFER_SLOTS=str(slots),DIEROUTE_TASK_TRANSFER_BYTES=str(byte_limit))
        with (out/(name+'.log')).open('w') as log:
            result=subprocess.run([str(binary),str(out/'input'),str(out/'topology'),str(prefix),'flat'],env=e,stdout=log,stderr=subprocess.STDOUT)
        assert (result.returncode==0)==valid,(name,result.returncode)
        if not valid:
            assert not Path(str(prefix)+'.json').exists()
        return prefix

    def compare(reference,prefix):
        count=0
        for source in sorted(out.glob(reference.name+'.*')):
            suffix=source.name[len(reference.name):]
            if suffix=='.log':continue
            target=Path(str(prefix)+suffix)
            if suffix=='.json':
                x=json.loads(source.read_text());y=json.loads(target.read_text());x.pop('wall_ms');y.pop('wall_ms');assert x==y
            else:assert source.read_bytes()==target.read_bytes(),(prefix,suffix)
            count+=1
        return count

    for mode in range(3):
        reference=run(parent,f'parent{mode}',mode)
        for slots,limit in ([(0,4096)] if mode==0 else [(0,4096),(1,4096),(4,84)]):
            for repeat in range(5):
                prefix=run(host,f'mode{mode}_slots{slots}_bytes{limit}_{repeat}',mode,slots,limit)
                comparisons+=compare(reference,prefix)
                state=replay(out/'input',prefix,0,4,6)
                assert state['cpu_legal'] and state['epochs']==6 and state['final_resources_and_costs_byte_equivalent']
                assert state['received_task_requests_checked'] > 0 if mode else state['received_seed_rows_checked'] == 0
                item=dict(name=prefix.name,placement=mode,slots=slots,byte_limit=limit,state_replay=state)
                if slots:
                    item['credits']=audit(out/'input',out/'topology',prefix,slots,limit,mode)
                    assert item['credits']['events']['backpressure']>=6
                cases.append(item)
    for name,mode,slots,limit in [('disabled_placement',0,1,4096),('short_buffer',1,1,71)]:
        run(host,name,mode,slots,limit,False)
    pristine=out/'mode2_slots1_bytes4096_0'
    rejected=[]
    for name in ['wrong_live_bytes','early_credit_release','wrong_sequence','duplicate_completion','wrong_destination','missing_completion']:
        bad=out/name;bad.mkdir()
        for source in out.glob(pristine.name+'.*'):
            (bad/('route'+source.name[len(pristine.name):])).symlink_to(source)
        path=bad/'route.task_transfer_events.csv'
        with path.open() as stream:
            reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
        if name=='wrong_live_bytes':rows[0]['live_bytes']='0'
        elif name=='early_credit_release':next(r for r in rows if r['event']=='receive')['live_bytes']='0'
        elif name=='wrong_sequence':rows[0]['sequence']='5'
        elif name=='duplicate_completion':
            i=next(i for i,r in enumerate(rows) if r['event']=='complete');rows.insert(i+1,dict(rows[i]))
        elif name=='wrong_destination':rows[0]['destination_die']='0'
        elif name=='missing_completion':rows.pop(next(i for i,r in enumerate(rows) if r['event']=='complete'))
        path.unlink()
        with path.open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
        try:audit(out/'input',out/'topology',bad/'route',1,4096,2)
        except (AssertionError,KeyError):rejected.append(name)
        else:raise AssertionError(('corruption accepted',name))
    seed_rejected=[]
    for name in ['wrong_node','wrong_hops','wrong_cost','missing_unused_seed','duplicate_seed','wrong_window','wrong_epoch','seed_order']:
        bad=out/('seed_'+name);bad.mkdir()
        for source in out.glob(pristine.name+'.*'):
            (bad/('route'+source.name[len(pristine.name):])).symlink_to(source)
        path=bad/'route.received_task_seeds.csv'
        with path.open() as stream:
            reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
        index=next(i for i,r in enumerate(rows) if int(r['seed_index'])==1)
        if name=='wrong_node':rows[index]['node']='5'
        elif name=='wrong_hops':rows[index]['hops']=str(int(rows[index]['hops'])+1)
        elif name=='wrong_cost':rows[index]['cost_q']=str(int(rows[index]['cost_q'])+1)
        elif name=='missing_unused_seed':rows.pop(index)
        elif name=='duplicate_seed':rows.insert(index,dict(rows[index]))
        elif name=='wrong_window':rows[index]['window']='99999'
        elif name=='wrong_epoch':rows[index]['epoch']='99999'
        elif name=='seed_order':rows[index-1],rows[index]=rows[index],rows[index-1]
        path.unlink()
        with path.open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
        try:replay(out/'input',bad/'route',0,4,6)
        except (AssertionError,KeyError):seed_rejected.append(name)
        else:raise AssertionError(('receiver corruption accepted',name))
    files.extend(p for p in out.iterdir() if p.is_file())
    proof=dict(status='actual_receiver_seed_host_controls_and_independent_replay_complete',runs=cases,
        parent_artifact_comparisons=comparisons,rejected_corruptions=rejected,rejected_seed_corruptions=seed_rejected,invalid_host_configurations=2,
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        scope='35actualsmallgraphhostruns,5perconfiguration,6STAepochseach. Nonzeroseedcosts andchangedSTAcriticalities;allreceiverseedsincludingunusedones reconstructedfromtree.8seedand6creditmutationsrejected;parentartifactsidentical. Native fullgraph,independent shadowreads,adaptive andhardware remain open.',
        board_result=False,research_complete=False)
    (out/'audit.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(dict(status=proof['status'],runs=len(cases),comparisons=comparisons,rejected=rejected,seed_rejected=seed_rejected)))


if __name__=='__main__':main()
