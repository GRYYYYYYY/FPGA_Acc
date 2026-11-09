"""Bound delay ambiguity on actual final task paths and verify exported STA delay sums."""
import argparse,csv,json,struct
from collections import defaultdict
from pathlib import Path
from persistent_vpr_timing import sha
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pair',type=Path);p.add_argument('output',type=Path);a=p.parse_args();pair=a.pair.resolve();m=json.loads(pair.read_text());mode,=m['modes'];base=pair.parent
    nodes_path=base/'input.nodes';edges_path=base/'input.edges';tasks_path=base/'input.tasks';paths_path=base/(mode+'_0.paths.csv')
    nodes=list(struct.iter_unpack('<IHH',nodes_path.read_bytes()));edges=list(struct.iter_unpack('<IHH',edges_path.read_bytes()));tasks={r[0]:r for r in struct.iter_unpack('<IIIIHHIII',tasks_path.read_bytes())};paths=defaultdict(list)
    with paths_path.open() as stream:
        for row in csv.DictReader(stream):
            path=paths[int(row['task_id'])];assert int(row['path_index'])==len(path);path.append(int(row['resource_id']))
    cache={};results=[];used=set()
    for task_id,path in paths.items():
        previous=tasks[task_id][2];first=minimum=maximum=0;ambiguous=0
        for node in path:
            key=(previous,node);used.add(key)
            if key not in cache:
                begin,count,_=nodes[previous];delays=[edges[i][2] for i in range(begin,begin+count) if edges[i][0]==node];assert delays;cache[key]=delays
            delays=cache[key];first+=delays[0];minimum+=min(delays);maximum+=max(delays);ambiguous+=len(set(delays))>1;previous=node
        results.append(dict(task_id=task_id,first_arc_delay_ps=first,min_arc_delay_ps=minimum,max_arc_delay_ps=maximum,delay_ambiguous_arcs=ambiguous))
    last=m['modes'][mode]['runs'][0]['iterations']-1;timing_path=base/f'{mode}_0.timing_iteration_{last}.input.csv'
    with timing_path.open() as stream:timing={int(r['task_id']):r for r in csv.DictReader(stream)}
    assert set(timing)==set(paths)==set(tasks)
    for r in results:assert timing[r['task_id']]['routed']=='1' and int(timing[r['task_id']]['delay_ps'])==r['min_arc_delay_ps']
    report=dict(status='actual_final_paths_parallel_delay_range_and_sta_min_sum_checked',tasks=len(results),unique_used_arcs=len(used),delay_ambiguous_unique_arcs=sum(len(set(cache[k]))>1 for k in used),affected_tasks=sum(r['delay_ambiguous_arcs']>0 for r in results),maximum_first_minus_sta_min_ps=max(r['first_arc_delay_ps']-r['min_arc_delay_ps'] for r in results),maximum_range_ps=max(r['max_arc_delay_ps']-r['min_arc_delay_ps'] for r in results),largest_ranges=sorted(results,key=lambda r:-(r['max_arc_delay_ps']-r['min_arc_delay_ps']))[:10],source_sha256={str(p):sha(p) for p in [pair,nodes_path,edges_path,tasks_path,paths_path,timing_path,Path(__file__).resolve()]},scope='Observed packed CSR delay ranges on actual final paths;every last-epoch STA delay equals summed minimum parallel-arc delay. Not native switch-level delay reconstruction or CPD causality.',board_result=False,research_complete=False)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','largest_ranges']}))
