"""Run actual host retention boundaries with synthetic timing and independent replay."""
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
from rr_legal_retention_replay import replay


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs(directory,fanout=16,duplicate=False,failed=False):
    adjacency=[[] for _ in range(23)]
    def edge(a,b,cost):
        adjacency[a].append((b,cost,1))
    edge(0,1,1)
    for i in range(15):
        edge(1,i+2,1)
    for a,b,c in [(1,18,1),(1,19,50),(18,17,1),(18,21,1),(19,17,1),(20,18,1),(20,22,500),(22,21,1)]:
        edge(a,b,c)
    nodes,edges=[],[]
    for row in adjacency:
        nodes.append((len(edges),len(row),1))
        edges.extend(row)
    tasks=[(i,7,0,i+2,0,1 if failed else 8,i+1,0,0) for i in range(16-fanout,16)]
    if duplicate:
        t=list(tasks[1]);t[3]=tasks[0][3];tasks[1]=tuple(t)
    tasks.append((16,8,20,21,0,8,0,0,0))
    for suffix,layout,rows in [('nodes','<IHH',nodes),('edges','<IHH',edges),
                              ('resources','<HHHHII',[(0,1,256,0,0,0xffffffff)]*23),('tasks','<IIIIHHIII',tasks)]:
        (directory/('input.'+suffix)).write_bytes(b''.join(struct.pack(layout,*r) for r in rows))
    (directory/'topology.node_die').write_bytes(bytes(46))
    (directory/'topology.node_box').write_bytes(bytes(184))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path)
    parser.add_argument('parent_host',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    host,parent_host,output=[p.resolve() for p in (args.host,args.parent_host,args.output)]
    output.mkdir(exist_ok=False)
    timing=output/'fixed_timing.py'
    timing.write_text("import csv,sys\nwith open(sys.argv[2]) as f: rows=list(csv.DictReader(f))\nwith open(sys.argv[3],'w') as f:\n w=csv.writer(f,lineterminator='\\n');w.writerow(['task_id','criticality_q','delay_ps','slack_ps','critical_path_delay_ps'])\n for r in rows:w.writerow([r['task_id'],0,r['delay_ps'],0,1])\n")
    files=[Path(__file__).resolve(),host,parent_host,timing]
    cases=[]
    for name,mode,fanout,duplicate,failed,minimum in [('disabled',0,16,False,False,2),
            ('enabled',1,16,False,False,2),('below_threshold',1,15,False,False,2),
            ('duplicate_sink',1,16,True,False,2),('forced_timing',1,16,False,False,12),
            ('failed_tasks',1,16,False,True,2)]:
        directory=output/name
        directory.mkdir()
        inputs(directory,fanout,duplicate,failed)
        prefix=directory/'trace'
        env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
        env.update(DIEROUTE_COST_BITS='64',DIEROUTE_VPR_STYLE_COST='1',DIEROUTE_TREE_TIMING_WEIGHT_Q='128',
                   DIEROUTE_LOCAL_TASK_ORDER='0',DIEROUTE_ISSUE_WIDTH='4',DIEROUTE_ORDINARY_SCHEDULE_MODE='0',
                   DIEROUTE_LEGAL_CONNECTION_RETENTION=str(mode),DIEROUTE_MIN_TIMING_ITERATIONS=str(minimum),
                   DIEROUTE_MAX_ITERATIONS='12',PERSISTROUTE_TIMING_COMMAND=shlex.join([sys.executable,str(timing)]))
        command=[str(host),str(directory/'input'),str(directory/'topology'),str(prefix),'flat']
        with (directory/'run.log').open('w') as log:
            rc=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
        assert rc==(3 if failed else 0),(name,rc)
        proof=replay(directory/'input',prefix,0,4,minimum,retention_mode=mode)
        assert proof['cpu_legal']==(not failed)
        if name in ('enabled','duplicate_sink'):
            assert proof['retained_connection_occurrences']>0
        else:
            assert proof['retained_connection_occurrences']==0
        counter=Path(str(prefix)+'.json')
        data=json.loads(counter.read_text())
        assert data['legal_connection_retention']==mode and data['retention_events']==proof['retention_events']
        cases.append(dict(name=name,command=command,returncode=rc,replay=proof))
        files.extend([counter,*[Path(p) for p in proof['source_sha256']]])
        if name=='disabled':
            parent_prefix=directory/'parent'
            parent_command=[str(parent_host),str(directory/'input'),str(directory/'topology'),str(parent_prefix),'flat']
            with (directory/'parent.log').open('w') as log:
                subprocess.run(parent_command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            equal=0
            for artifact in directory.glob('trace.*'):
                suffix=artifact.name[len('trace.'):]
                other=Path(str(parent_prefix)+'.'+suffix)
                if suffix in ('legal_retention.csv','retention_connections.csv'):
                    with artifact.open() as stream:
                        assert not list(csv.DictReader(stream))
                elif suffix.endswith('.csv') or suffix in ('resources','costs'):
                    assert artifact.read_bytes()==other.read_bytes(),suffix
                    files.extend([artifact,other]);equal+=1
            old=json.loads(Path(str(parent_prefix)+'.json').read_text())
            assert {k:v for k,v in data.items() if k not in ('wall_ms','legal_connection_retention','retention_events')}=={k:v for k,v in old.items() if k!='wall_ms'}
            cases[-1]['equal_parent_artifacts']=equal
    mutations=[]
    for name,suffix,field in [('eligibility','legal_retention.csv','eligible'),
                              ('kept_cardinality','legal_retention.csv','kept_connections'),
                              ('connection_decision','retention_connections.csv','retained'),
                              ('epoch_version_hash','audit.csv','resource_hash')]:
        source=output/'enabled'
        bad=output/('corrupt_'+name)
        bad.mkdir()
        for p in source.glob('trace.*'):
            (bad/p.name).symlink_to(p)
        path=bad/('trace.'+suffix)
        with path.open() as stream:
            reader=csv.DictReader(stream);fields,rows=reader.fieldnames,list(reader)
        selected=next((r for r in rows if r.get('eligible')=='1'),rows[-1])
        selected[field]=str(int(selected[field])^1)
        path.unlink()
        with path.open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        try:
            replay(source/'input',bad/'trace',0,4,2,retention_mode=1)
        except AssertionError:
            mutations.append(dict(name=name,rejected=True,sha256=sha(path)))
        else:
            raise AssertionError('Corrupt retention trace passed')
    report=dict(status='actual_host_retention_boundaries_parent_compatibility_and_versions_replayed',
                cases=cases,copied_fixture_mutations=mutations,
                source_sha256={str(p):sha(p) for p in files},
                scope='Six actual small-graph host runs plus actual disabled parent;fixed synthetic timing. '
                      'Independent complete path/retention/epoch/final version replay and four copied corruptions. '
                      'Not native QoR,five-repeat evidence,search-work oracle orphysicalperformance.',
                board_result=False,research_complete=False)
    (output/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],cases=len(cases),mutations=len(mutations))))
