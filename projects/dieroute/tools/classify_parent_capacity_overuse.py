"""Reconstruct final occupancy/owner and every connection from exported route-tree edges."""
import argparse,csv,json,struct
from collections import defaultdict
from pathlib import Path
from prepare_additional_fresh_parent import digest as sha

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input_prefix',type=Path);p.add_argument('output_prefix',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    inp,out=a.input_prefix.resolve(),a.output_prefix.resolve();files=[]
    def binary(prefix,suffix,fmt):
        path=Path(str(prefix)+suffix);files.append(path);return list(struct.iter_unpack(fmt,path.read_bytes()))
    def table(suffix):
        path=Path(str(out)+suffix);files.append(path)
        with path.open() as stream:return [{k:int(v) for k,v in r.items()} for r in csv.DictReader(stream)]
    nodes=binary(inp,'.nodes','<IHH');edges=binary(inp,'.edges','<IHH');initial=binary(inp,'.resources','<HHHHII');final=binary(out,'.resources','<HHHHII');tasks=binary(inp,'.tasks','<IIIIHHIII')
    assert len(nodes)==len(initial)==len(final)
    roots={};by_task={}
    for task in tasks:
        assert task[0] not in by_task;by_task[task[0]]=task
        assert roots.setdefault(task[1],task[2])==task[2]
    parents=defaultdict(dict);users=defaultdict(set)
    def valid_edge(source,destination):
        assert source<len(nodes) and destination<len(nodes)
        begin,count,_=nodes[source];assert begin+count<=len(edges)
        return any(edges[i][0]==destination for i in range(begin,begin+count))
    for r in table('.route_trees.csv'):
        net,source,parent,child=[r[k] for k in ['net_id','source','parent','child']]
        assert roots[net]==source and child!=source and child not in parents[net]
        assert valid_edge(parent,child)
        parents[net][child]=parent;users[child].add(net)
    # Reaching the unique source proves no cycles,orphan components or detached edges.
    for net,mapping in parents.items():
        for child in mapping:
            seen=set();node=child
            while node!=roots[net]:
                assert node not in seen and node in mapping;seen.add(node);node=mapping[node]
    paths=defaultdict(list)
    for r in table('.paths.csv'):
        path=paths[r['task_id']];assert r['path_index']==len(path);path.append(r['resource_id'])
    assert set(paths)==set(by_task)
    for task_id,path in paths.items():
        task=by_task[task_id];net,source,sink=task[1:4];assert path and path[-1]==sink
        previous=source
        for node in path:
            assert parents[net].get(node)==previous;previous=node
    overused=[]
    for node,(before,actual) in enumerate(zip(initial,final)):
        base_occupancy,capacity,_,_,version,base_owner=before
        known=set(users[node]);occupancy=base_occupancy+len(users[node])-int(base_occupancy>0 and base_owner in users[node])
        if base_occupancy and base_owner!=0xffffffff:known.add(base_owner)
        owner=next(iter(known)) if occupancy==1 and len(known)==1 else 0xffffffff
        assert actual[0]==occupancy and actual[1]==capacity and actual[5]==owner,(node,actual,occupancy,owner)
        assert actual[4]>=version
        if actual[0]>actual[1]:overused.append(node)
    report=dict(status='parent_structure_and_resource_records_verified_capacity_classified',overused_resources=len(overused),overused_resource_ids=overused,capacity_only_failure=bool(overused),tasks=len(tasks),nets=len(roots),tree_edges=sum(len(v) for v in parents.values()),resources=len(nodes),source_sha256={str(p):sha(p) for p in files+[Path(__file__).resolve()]},scope='Classification only; does not convert original failed audit into a pass. Final exported tree edges/PIP adjacency,root reachability,all task paths,net-deduplicated occupancy and owner plus unchanged capacity. Root anchors are not charged as branch resources. Version monotonicity only;not exact epoch/version lineage,cost/search optimality,native RC timing or physical SLL verification.',board_result=False,research_complete=False)
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
