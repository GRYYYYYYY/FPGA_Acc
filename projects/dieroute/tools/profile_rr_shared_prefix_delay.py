"""Measure final shared prefixes, without inferring historical attachment points."""
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

root=Path(__file__).resolve().parents[1];files=[Path(__file__)]
def read(path):files.append(path);return json.loads(path.read_text())
tradeoff=read(root/'work/rr_seed_weight_native_timing_tradeoff_20261014.json')
profiles={}
for label in ('full','zero'):
    run=root/f'work/rr_tree_seed_{label}_native_delay_20261014'
    manifest=read(run/'manifest.json');proof=read(run/'independent_xml_audit.json');profile=read(run/'profile.json')
    assert proof['status']=='passed'
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest['inputs'].items())
    assert proof['profile_sha256']==hashlib.sha256((run/'profile.json').read_bytes()).hexdigest()
    pair_file,=[Path(p) for p in manifest['inputs'] if Path(p).name=='pair.json']
    pair=read(pair_file);base=pair_file.parent
    task_file=Path(pair['reference'])/'connections.csv';files.append(task_file)
    with task_file.open() as stream:tasks={int(t['id']):t for t in csv.DictReader(stream)}
    nodes_file=base/'input.nodes';edges_file=base/'input.edges';files.extend([nodes_file,edges_file])
    nodes=list(struct.iter_unpack('<IHH',nodes_file.read_bytes()))
    edges=list(struct.iter_unpack('<IHH',edges_file.read_bytes()))
    path_file=base/'downstream_bounded_0.paths.csv';files.append(path_file)
    paths={}
    with path_file.open() as stream:
        for row in csv.DictReader(stream):
            paths.setdefault(int(row['task_id']),[]).append((int(row['path_index']),int(row['resource_id'])))
    usage=Counter();sink_usage={}
    for task,rows in paths.items():
        rows.sort();assert [i for i,n in rows]==list(range(len(rows)))
        assert len({n for i,n in rows})==len(rows)
        for _,node in rows:
            key=(int(tasks[task]['net_id']),node);usage[key]+=1
            sink_usage.setdefault(key,set()).add(int(tasks[task]['sink']))
    assert paths.keys()==tasks.keys()
    measured={}
    for task,rows in paths.items():
        parent=int(tasks[task]['source']);net=int(tasks[task]['net_id'])
        prefix=True;shared_delay=total_delay=shared_span=0;shared_nodes=0
        distinct_prefix=True;distinct_delay=distinct_span=distinct_nodes=0
        for _,node in rows:
            begin,count,_=nodes[parent];assert begin+count<=len(edges)
            delay=min(d for dst,c,d in edges[begin:begin+count] if dst==node)
            total_delay+=delay
            prefix=prefix and usage[net,node]>=2
            if prefix:
                shared_nodes+=1;shared_delay+=delay;shared_span+=nodes[node][2]
            distinct_prefix=distinct_prefix and len(sink_usage[net,node])>=2
            if distinct_prefix:
                distinct_delay+=delay;distinct_span+=nodes[node][2];distinct_nodes+=1
            parent=node
        assert parent==int(tasks[task]['sink'])
        measured[task]=dict(shared_prefix_delay_ps=shared_delay,local_path_delay_ps=total_delay,
                            shared_prefix_nodes=shared_nodes,shared_prefix_span=shared_span,
                            distinct_sink_prefix_delay_ps=distinct_delay,
                            distinct_sink_prefix_span=distinct_span,distinct_sink_prefix_nodes=distinct_nodes)
    for row in profile['rows']:assert measured[row['task_id']]['local_path_delay_ps']==row['local_rc_ps']
    profiles[label]=measured
rows=[]
for row in tradeoff['rows']:
    task=row['task_id'];rows.append(dict(**row,full_prefix=profiles['full'][task],zero_prefix=profiles['zero'][task]))
report=dict(status='audited_final_shared_prefix_delays_measured',connections=len(rows),
            top_native_increases=rows[:20],rows=rows,
            source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
            scope='Final source prefixes shared by multiple connections, also reported separately for distinct RR sink IDs to exclude endpoint aliases. XML-checked local edge delays and rechecked frozen extraction inputs. Not historical attachment, ordering, transient state or causal CPD evidence.',
            board_result=False,research_complete=False)
output=root/'work/rr_seed_shared_prefix_delay_v2_20261014.json';assert not output.exists()
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],top=rows[:3])))
