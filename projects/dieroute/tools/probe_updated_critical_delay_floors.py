"""Capacity-aware additive-delay lower bounds on refreshed critical paths."""
import csv,hashlib,heapq,json,struct
from pathlib import Path


def main():
    D=Path('work/native_joint_budget_ex5p_baseline_target_probe_20261016')
    binding=D/'updated_critical_tasks.json';protocol=Path('work/native_joint_budget_net_repair_v2_20261016/protocol.json')
    case=json.loads(protocol.read_text())['cases'][0]
    tree=D/'route.route_trees.csv';nodefile=Path(case['input_prefix']+'.nodes');edgefile=Path(case['input_prefix']+'.edges');resourcefile=Path(case['input_prefix']+'.resources')
    nodes=list(struct.iter_unpack('<IHH',nodefile.read_bytes()));edges=list(struct.iter_unpack('<IHH',edgefile.read_bytes()));resources=list(struct.iter_unpack('<HHHHII',resourcefile.read_bytes()))
    owners=[set() for _ in nodes];parents={}
    for r in csv.DictReader(tree.open()):
        n,u,v=int(r['net_id']),int(r['parent']),int(r['child']);owners[v].add(n);parents[n,v]=u
    result=[]
    for arc in json.loads(binding.read_text())['arcs']:
        if arc['intracluster']:continue
        task=arc['task'];net=int(task['net_id']);source=int(task['source']);sink=int(task['sink'])
        path=[sink]
        while path[-1]!=source:
            u=parents[net,path[-1]];assert u not in path;path.append(u)
        path.reverse();old=0
        for u,v in zip(path,path[1:]):
            begin,count,_=nodes[u];weights=[w for dest,_,w in edges[begin:begin+count] if dest==v];assert len(set(weights))==1;old+=weights[0]
        allowed=[len(o-{net})<resources[v][1] for v,o in enumerate(owners)]
        distance={source:0};queue=[(0,source)];previous={};expanded=0
        while queue:
            delay,u=heapq.heappop(queue)
            if delay!=distance[u]:continue
            expanded+=1
            if u==sink:break
            begin,count,_=nodes[u]
            for v,_,weight in edges[begin:begin+count]:
                candidate=delay+weight
                if allowed[v] and candidate<distance.get(v,10**30):
                    distance[v]=candidate;previous[v]=u;heapq.heappush(queue,(candidate,v))
        assert sink in distance
        best=[sink]
        while best[-1]!=source:best.append(previous[best[-1]])
        best.reverse()
        result.append(dict(endpoint=arc['endpoint'],net=arc['net'],net_id=net,task_id=int(task['id']),current_delay_ps=old,minimum_delay_ps=distance[sink],potential_reduction_ps=old-distance[sink],expanded=expanded,minimum_path=best))
    inputs=[binding,protocol,tree,nodefile,edgefile,resourcefile,Path(__file__)]
    output=dict(status='eleven_refreshed_intercluster_capacity_delay_floors_computed',connections=result,
                source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                scope='Each own net removed independently, other nets fixed. Lower bounds ignore own-net sharing, hop, wire and crossing limits. No native STA or adoption.',research_complete=False)
    with (D/'updated_capacity_delay_floors.json').open('x') as stream:json.dump(output,stream,indent=2);stream.write('\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='minimum_path'} for r in result],indent=2))


if __name__=='__main__':main()
