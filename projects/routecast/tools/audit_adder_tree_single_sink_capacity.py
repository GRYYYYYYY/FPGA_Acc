"""Exact full-native occupancy counterfactual for twelve frozen predictor paths."""
import json
import shutil
from collections import Counter
from pathlib import Path
from prepared_csr import read
from pre_route_endpoints import sha
from audit_native_route import NET,NODE


def main():
    base=Path('experiments');design='adder_tree_3L_128bits'
    pathroot=base/'adder_tree_max_single_sink_path_comparison_2026-10-06'
    r=json.loads((pathroot/'receipt.json').read_text());assert sha(pathroot/'report.json')==r['report_sha256']
    report=json.loads((pathroot/'report.json').read_text());rows=report['rows'];nets={row['net_id'] for row in rows}
    native=base/'adder_tree_family_native_path_audit_2026-10-06'/design
    nr=json.loads((native/'receipt.json').read_text());np=json.loads((native/'protocol.json').read_text())
    assert sha(native/'receipt.json')==report['native_receipt_sha256'] and sha(native/'protocol.json')==nr['protocol_sha256']
    assert nr['physical_checks_pass'] and nr['overflow_units']==0
    route=np['inputs']['evaluator_route'];assert sha(route['path'])==route['sha256']
    truthpath=native/'physical_branches.json';assert sha(truthpath)==nr['outputs']['physical_branches.json']
    truth=json.loads(truthpath.read_text());occ={int(k):v for k,v in truth['node_occupancy'].items()}
    prepared=base/'adder_tree_family_length_switch_csr_2026-10-06'/design
    assert sha(prepared/'csr/manifest.json')==report['csr_manifest_sha256']
    m,f=read(prepared/'csr',np['inputs']['rr_graph']['sha256']);assert all(i==v for i,v in enumerate(f['node_ids']))
    old={row['net_id']:set(row['native_node_ids']) for row in rows};new={row['net_id']:set(row['prediction_node_ids']) for row in rows}
    selected=set().union(*new.values());owners={nid:set() for nid in selected};net=None
    with Path(route['path']).open() as stream:
        for line in stream:
            match=NET.match(line)
            if match:net=int(match[1]);continue
            match=NODE.match(line)
            if match and int(match[1]) in selected:owners[int(match[1])].add(net)
    assert all(len(owners[nid])==occ.get(nid,0) for nid in selected)
    single=[]
    for row in rows:
        net=row['net_id'];blocked=[]
        for nid in new[net]:
            occupancy=occ.get(nid,0)-(nid in old[net])+1
            if occupancy>f['capacities'][nid]:
                blocked.append({'node_id':nid,'type':f['types'][nid],'capacity':f['capacities'][nid],'result_occupancy':occupancy,'other_native_owners':sorted(owners[nid]-{net})})
        single.append({'net_id':net,'name':row['name'],'blocking_resources':blocked,'fits_original_native_capacity':not blocked})
    candidate=Counter(occ)
    for net in nets:
        for nid in old[net]:candidate[nid]-=1;assert candidate[nid]>=0
    for net in nets:candidate.update(new[net])
    overflow={nid:value-f['capacities'][nid] for nid,value in candidate.items() if value>f['capacities'][nid]}
    # Independent reconstruction: remove selected owners from printed net unions,
    # then insert whole single-sink predictor node unions without additive row deltas.
    unions={};net=None
    with Path(route['path']).open() as stream:
        for line in stream:
            match=NET.match(line)
            if match:net=int(match[1]);unions.setdefault(net,set());continue
            match=NODE.match(line)
            if match:unions[net].add(int(match[1]))
    assert Counter(nid for nodes in unions.values() for nid in nodes)==Counter(occ)
    assert all(unions[net]==old[net] for net in nets)
    unions.update(new);rebuilt=Counter(nid for nodes in unions.values() for nid in nodes)
    assert +candidate==rebuilt
    assert sha(route['path'])==route['sha256']
    out=base/'adder_tree_max_single_sink_capacity_counterfactual_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py')
    result={'path_comparison_report_sha256':sha(pathroot/'report.json'),'native_receipt_sha256':sha(native/'receipt.json'),'source_sha256':sha(__file__),'single_net_results':single,'single_net_capacity_pass':sum(r['fits_original_native_capacity'] for r in single),'full_batch_overflow_units':sum(overflow.values()),'full_batch_conflicting_resources':len(overflow),'batch_conflicts':[{'node_id':nid,'excess':v,'capacity':f['capacities'][nid],'type':f['types'][nid],'unchanged_native_owners':sorted(owners.get(nid,set())-nets),'candidate_owners':sorted(net for net in nets if nid in new[net])} for nid,v in sorted(overflow.items())],'independent_full_union_rebuild_exact':True,'repair_committed':False,'scope':'twelve post-hoc selected single-sink replacements against full original native occupancy; capacity only, not pin assignment/nonconfigurable closure/electrical/STA or native QoR'}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'single_net_capacity_pass':result['single_net_capacity_pass'],'batch_overflow':sum(overflow.values())},indent=2)+'\n')
    print(json.dumps({'single_net_capacity_pass':result['single_net_capacity_pass'],'nets':12,'batch_overflow':sum(overflow.values()),'conflicting_resources':len(overflow),'blocking_counts':[[r['net_id'],len(r['blocking_resources'])] for r in single]}),flush=True)


if __name__=='__main__':main()
