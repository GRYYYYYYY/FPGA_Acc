"""Read-only comparison of additive search delays and archived native delays."""
import csv
import hashlib
import json
import struct
from pathlib import Path


def main():
    root=Path('work/native_joint_budget_net_repair_v2_20261016')
    protocol=root/'protocol.json'
    case=json.loads(protocol.read_text())['cases'][0]
    manifest=root/'ex5p/manifest.json'
    state=json.loads(manifest.read_text())
    tree=Path(state['current_tree'])
    observation=tree.parent/'observation.output.csv'
    binding=Path('work/native_joint_budget_ex5p_STA_alignment_20261016/RR_task_binding.json')
    node_file=Path(case['input_prefix']+'.nodes')
    edge_file=Path(case['input_prefix']+'.edges')
    nodes=list(struct.iter_unpack('<IHH',node_file.read_bytes()))
    edges=list(struct.iter_unpack('<IHH',edge_file.read_bytes()))
    parents={}
    for row in csv.DictReader(tree.open()):
        key=(int(row['net_id']),int(row['child']))
        parent=int(row['parent'])
        assert key not in parents or parents[key]==parent
        parents[key]=parent
    obs={int(r['task_id']):r for r in csv.DictReader(observation.open())}
    result=[]
    for arc in json.loads(binding.read_text())['arcs']:
        task={k:int(v) for k,v in arc['task'].items() if k!='net'}
        path=[task['sink']]
        while path[-1]!=task['source']:
            parent=parents[task['net_id'],path[-1]]
            assert parent not in path
            path.append(parent)
        path.reverse()
        weights=[]
        for u,v in zip(path,path[1:]):
            begin,count,_=nodes[u]
            candidates=[edge[2] for edge in edges[begin:begin+count] if edge[0]==v]
            assert candidates, (u,v)
            # Parent-only trees cannot select among parallel switches. Report ranges.
            weights.append((min(candidates),max(candidates)))
        lower=sum(w[0] for w in weights);upper=sum(w[1] for w in weights)
        native=int(obs[task['id']]['delay_ps'])
        result.append(dict(task_id=task['id'],net=arc['net'],sink_atom=arc['sink_atom'],
                           path_nodes=path,additive_delay_min_ps=lower,
                           additive_delay_max_ps=upper,native_delay_ps=native,
                           native_minus_additive_min_ps=native-lower,
                           ambiguous_parallel_edges=sum(a!=b for a,b in weights)))
    inputs=[protocol,manifest,tree,observation,binding,node_file,edge_file,Path(__file__)]
    output=dict(status='five_final_critical_connection_paths_checked_against_packed_graph',
                connections=result,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                scope='Additive packed edge delay comparison only; native RC tree delay and atom internal arcs are not interchangeable. No rerouting or causal proof.',research_complete=False)
    destination=binding.parent/'model_delay_comparison.json'
    with destination.open('x') as stream:
        json.dump(output,stream,indent=2);stream.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
