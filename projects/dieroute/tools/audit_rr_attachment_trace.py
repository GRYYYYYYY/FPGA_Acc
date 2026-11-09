"""Replay accepted serial node-mode attachments against packed CSR and final trees."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import struct
from audit_rr_experiments import audit

def table(path):
    with path.open() as stream:return [{k:int(v) for k,v in row.items()} for row in csv.DictReader(stream)]

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();path=args.manifest.resolve();base=path.parent
    verified=audit(path);manifest=json.loads(path.read_text());config=manifest['configuration']
    assert config['cleanup_passes']==0 and config['speculative_workers']==0
    nodes_file=base/'input.nodes';edges_file=base/'input.edges'
    nodes=list(struct.iter_unpack('<IHH',nodes_file.read_bytes()))
    edges=list(struct.iter_unpack('<IHH',edges_file.read_bytes()))
    # Connections include a text net name; use only integer identity fields.
    with (Path(manifest['reference'])/'connections.csv').open() as stream:
        tasks={int(r['id']):{k:int(r[k]) for k in ('id','net_id','source','sink','criticality_q','max_hops')} for r in csv.DictReader(stream)}
    def delay(parent,child):
        begin,count,_=nodes[parent];assert begin+count<=len(edges)
        return next(d for dst,c,d in edges[begin:begin+count] if dst==child)
    files=[path,Path(__file__),nodes_file,edges_file];results={}
    for mode,proof in verified['modes'].items():
        assert proof['status']=='passed' and proof['repeats_verified']==5
        assert not proof['counters']['edge_identity']
        prefix=base/f'{mode}_0';row_file=Path(str(prefix)+'.attachments.csv');branch_file=Path(str(prefix)+'.attachment_branches.csv')
        files.extend([row_file,branch_file]);rows=table(row_file);branches={}
        for row in table(branch_file):branches.setdefault(row['row'],[]).append((row['index'],row['node']))
        trees={};epochs={};paths={};counts=Counter();timing={};previous_iteration=-1
        for i,row in enumerate(rows):
            assert row['row']==i and row['iteration']>=previous_iteration
            previous_iteration=row['iteration'];task=tasks[row['task_id']];net=task['net_id'];iteration=row['iteration']
            assert all(row[k]==task[k] for k in ('source','sink','net_id'))
            if epochs.get(net)!=iteration:
                trees[net]={task['source']:None};epochs[net]=iteration
                for t in tasks.values():
                    if t['net_id']==net:paths.pop(t['id'],None)
            tree=trees[net];attachment=row['attachment'];assert attachment in tree
            assert len(tree)==row['tree_nodes_before']
            chain=[];node=attachment
            while node!=task['source']:
                assert node in tree and tree[node] is not None and node not in chain
                chain.append(node);node=tree[node]
            chain.reverse();parent=task['source'];prefix_delay=0
            for node in chain:prefix_delay+=delay(parent,node);parent=node
            assert prefix_delay==row['prefix_delay_q'] and len(chain)==row['seed_hops']
            criticality=min(task['criticality_q'],config['criticality_cap_q'])
            if iteration and config['timing_updates']:
                if iteration-1 not in timing:
                    f=Path(str(prefix)+f'.timing_iteration_{iteration-1}.output.csv');files.append(f)
                    timing[iteration-1]={r['task_id']:r['criticality_q'] for r in table(f)}
                criticality=min(timing[iteration-1][task['id']],config['criticality_cap_q'])
            assert row['criticality_q']==criticality
            scale=config['cost_scale'];weight=config['route_tree_timing_weight_q']
            charge=(prefix_delay*criticality//65535)*weight//256 if scale==1 else prefix_delay*criticality*scale*weight//(65535*256)
            assert row['seed_cost_q']==charge and charge<=0xffffffff
            branch=sorted(branches.pop(i,[]));assert [j for j,n in branch]==list(range(row['branch_nodes']))
            branch=[n for j,n in branch];assert (branch[-1] if branch else attachment)==task['sink']
            assert len(chain)+len(branch)<=task['max_hops']
            parent=attachment;branch_delay=0
            for node in branch:
                assert node not in tree;branch_delay+=delay(parent,node);tree[node]=parent;parent=node
            assert branch_delay==row['branch_delay_q'];paths[task['id']]=chain+branch;counts[iteration]+=1
        assert not branches and paths.keys()==tasks.keys()
        audit_file=Path(str(prefix)+'.audit.csv');files.append(audit_file)
        for row in table(audit_file):assert counts[row['iteration']]==row['committed']
        final_trees=table(Path(str(prefix)+'.route_trees.csv'))
        expected={(r['net_id'],r['child']):r['parent'] for r in final_trees}
        assert expected=={(net,node):parent for net,tree in trees.items() for node,parent in tree.items() if parent is not None}
        final_paths={}
        for row in table(Path(str(prefix)+'.paths.csv')):final_paths.setdefault(row['task_id'],[]).append((row['path_index'],row['resource_id']))
        assert all(paths[t]==[node for j,node in sorted(final_paths[t])] for t in tasks)
        results[mode]=dict(accepted_rows=len(rows),iterations=dict(counts),all_final_paths_and_trees_equal=True)
    report=dict(status='five_repeat_attachment_replay_audited',modes=results,
                source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                scope='Accepted negotiation proposals only. CSR/tree/criticality/seed-charge replay and final path/tree equality; root audit verifies five-repeat trace hashes. No rejected-alternative trace, hardware or causal global-CPD proof.',
                board_result=False,research_complete=False)
    assert not args.output.exists();args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],modes=results)))
