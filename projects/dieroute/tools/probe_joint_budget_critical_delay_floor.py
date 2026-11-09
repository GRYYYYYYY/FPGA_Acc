"""Capacity-aware single-connection delay floors; no tree is published."""
import csv, hashlib, heapq, json, struct
from pathlib import Path


def main():
    root=Path('work/native_joint_budget_net_repair_v2_20261016')
    protocol=root/'protocol.json'; manifest=root/'ex5p/manifest.json'
    case=json.loads(protocol.read_text())['cases'][0]
    tree=Path(json.loads(manifest.read_text())['current_tree'])
    prior=Path('work/native_joint_budget_ex5p_STA_alignment_20261016/model_delay_comparison.json')
    binding=prior.with_name('RR_task_binding.json')
    nodefile=Path(case['input_prefix']+'.nodes');edgefile=Path(case['input_prefix']+'.edges')
    resourcefile=Path(case['input_prefix']+'.resources')
    nodes=list(struct.iter_unpack('<IHH',nodefile.read_bytes()))
    edges=list(struct.iter_unpack('<IHH',edgefile.read_bytes()))
    resources=list(struct.iter_unpack('<HHHHII',resourcefile.read_bytes()))
    owners=[set() for _ in nodes]
    for row in csv.DictReader(tree.open()):owners[int(row['child'])].add(int(row['net_id']))
    previous={r['task_id']:r for r in json.loads(prior.read_text())['connections']}
    result=[]
    for arc in json.loads(binding.read_text())['arcs']:
        task=arc['task'];net=int(task['net_id']);source=int(task['source']);sink=int(task['sink'])
        allowed=[len(o-{net})<resources[v][1] for v,o in enumerate(owners)]
        assert allowed[source] and allowed[sink]
        dist={source:0};parent={};queue=[(0,source)];expanded=0
        while queue:
            delay,u=heapq.heappop(queue)
            if dist[u]!=delay:continue
            expanded+=1
            if u==sink:break
            begin,count,_=nodes[u]
            for v,_,weight in edges[begin:begin+count]:
                d=delay+weight
                if allowed[v] and d<dist.get(v,10**30):
                    dist[v]=d;parent[v]=u;heapq.heappush(queue,(d,v))
        path=[]
        if sink in dist:
            path=[sink]
            while path[-1]!=source:path.append(parent[path[-1]])
            path.reverse()
        old=previous[int(task['id'])]
        result.append(dict(task_id=int(task['id']),net=arc['net'],minimum_additive_delay_ps=dist.get(sink),
                           current_additive_delay_ps=old['additive_delay_min_ps'],
                           potential_additive_reduction_ps=old['additive_delay_min_ps']-dist[sink] if sink in dist else None,
                           expanded=expanded,path_nodes=path))
    inputs=[protocol,manifest,tree,prior,binding,nodefile,edgefile,resourcefile,Path(__file__)]
    output=dict(status='five_capacity_aware_single_connection_delay_floors_computed',connections=result,
                scope='Other nets retain occupancy. Own net removed for lower bound. No own-net branch sharing, crossing, wire or hop budget; no native STA evaluation. These paths are not adoptable routes.',
                source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},research_complete=False)
    destination=prior.with_name('capacity_delay_floors.json')
    with destination.open('x') as stream:json.dump(output,stream,indent=2);stream.write('\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='path_nodes'} for r in result],indent=2))


if __name__=='__main__':main()
