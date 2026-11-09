"""Matched-budget raw and native-retained seeds for an explicit external case.

Produces receipts only; independent warm audit must create verification.json.
No native route search, final labels or feedback run is performed here.
"""
import argparse
import json
import sys
import time
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from external_native_anchored_budget_v1 import assign,POLICY
from compiled_criticality_tree_v1 import Graph,BINARY
from native_retained_net_initializer_v1 import initialize
from soft_demand_workspace_bridge_v1 import Search
R=Path(__file__).resolve().parents[1]

def prepare(endpoint,source_directory,floor_proof,output):
    begin=time.perf_counter()
    endpoint,source_directory,floor_proof,output=map(lambda p:Path(p).resolve(),(endpoint,source_directory,floor_proof,output))
    source_proof=source_directory/'independent_xml_verification_v1.json'
    sp=json.loads(source_proof.read_text())
    if sp['status']!='SOURCE_XML_FRACTION_PATH_BUDGET_LEDGER_AUDIT_PASS':raise ValueError('audited source required')
    bindings=closure([Path(__file__)])
    def bind(proof,path):
        for p,h in proof['bindings'].items():
            if p in bindings and bindings[p]!=h:raise ValueError('conflicting binding')
            bindings[p]=h
        bindings[str(path)]=sha(path)
    bind(sp,source_proof)
    source=json.loads((source_directory/'initial.json').read_text())
    sr=json.loads((source_directory/'receipt.json').read_text())
    oldmeta=json.loads(Path(sr['source_endpoint']).read_text())
    meta=json.loads(endpoint.read_text());fp=json.loads(floor_proof.read_text());bind(fp,floor_proof)
    for v in meta['inputs'].values():
        if v['path'] in bindings and bindings[v['path']]!=v['sha256']:raise ValueError('input binding conflict')
        bindings[v['path']]=v['sha256']
    bindings[str(endpoint)]=sha(endpoint)
    if meta['net_names']!=oldmeta['net_names'] or meta['inputs']['net']['sha256']!=oldmeta['inputs']['net']['sha256']:raise ValueError('netlist changed')
    if fp['status']!='ALL_FRAME_RAW_FLOORS_ORIGIN_PROOFS_NEW_MINIMA_AND_CURRENT_XML_PATHS_VERIFIED' or fp['unreachable']!=0 or fp['graph_sha256']!=meta['graph_sha256']:raise ValueError('floor epoch')
    floor_path=floor_proof.parent/'floors.jsonl'
    if bindings.get(str(floor_path))!=sha(floor_path):raise ValueError('unbound floors')
    floors={}
    for line in floor_path.read_text().splitlines():
        row=json.loads(line);cid=row['connection_id']
        if cid in floors:raise ValueError('duplicate floor CID')
        floors[cid]=row
    current=[]
    for q in meta['connections']:
        f=floors[q['connection_id']]
        if any(q[k]!=f[k] for k in ('net_id','source','sink')):raise ValueError('floor endpoint')
        current.append(dict(q,floor_integer=f['minimum_integer']))
    if len(current)!=len(floors):raise ValueError('floor coverage')
    budget_rows=assign(source['records'],current,source['graph_sha256'],meta['graph_sha256'],source['scale'])
    budgets={r['connection_id']:r['budget_integer'] for r in budget_rows}
    old={r['connection_id']:r for r in source['records']}
    dirty={r['net_id'] for r in budget_rows if not r['unchanged_endpoint_pair']}
    for name in ['native_retained_initializer_core_v3_2026-10-18','soft_demand_workspace_radix_contract_v3_2026-10-08']:
        p=R/'experiments'/name/'verification.json';bind(json.loads(p.read_text()),p)
    if not all(sha(p)==h for p,h in bindings.items()):raise ValueError('dependency changed')
    graph,digest,nodes,fields,rc,queries=load_endpoints(endpoint)
    if digest!=source['graph_sha256'] or rc.scale!=source['scale']:raise ValueError('graph scale')
    groups=defaultdict(list)
    for q in queries:groups[q['net_id']].append(q)
    kinds=tuple(n.get('type') for n in nodes);slots={e:i for i,e in enumerate(fields['edge_ids'])}
    binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
    if bindings.get(str(BINARY))!=sha(BINARY) or bindings.get(str(binary))!=sha(binary):raise ValueError('unbound binary')
    g=Graph(fields,rc.increments,[rc.initial(i) for i in range(len(nodes))]);search=Search(fields,rc,binary);search.prepare({},0)
    output.mkdir(exist_ok=False)
    try:
        raw={}
        for net in sorted(dirty):
            qs=sorted(groups[net],key=lambda q:q['connection_id']);source_rr=qs[0]['source']
            if any(q['source']!=source_rr for q in qs):raise ValueError('multiple NET roots')
            dist,pred,settled=search.search(source_rr,{q['sink'] for q in qs})
            answers={}
            for q in qs:
                target=q['sink'];cid=q['connection_id']
                if target not in settled or dist[target]!=floors[cid]['minimum_integer']:raise ValueError('raw minimum mismatch')
                u=target;edges=[];seen=set()
                while u!=source_rr:
                    if u in seen:raise ValueError('raw parent cycle')
                    seen.add(u);u,slot=pred[u];edges.append(fields['edge_ids'][slot])
                edges.reverse();answers[cid]=dict(status='FOUND',physical_edge_ids=edges,delay=dist[target])
            raw[net]=answers
        for mode in ('raw_min','native_retained'):
            answers={cid:dict(r['answer']) for cid,r in old.items()};events=[]
            for net in sorted(dirty):
                qs=sorted(groups[net],key=lambda q:q['connection_id'])
                if mode=='native_retained':
                    result=initialize(g,fields,kinds,qs,[old[q['connection_id']] for q in qs],budgets,slots,lambda net=net:raw[net])
                    selected=result['answers'];events.append(dict(net_id=net,**{k:v for k,v in result.items() if k not in ('answers','owner_nodes')}))
                else:selected=raw[net]
                answers.update(selected)
            records=[];owners=defaultdict(set);independent=Counter();parents=defaultdict(dict)
            for q in queries:
                cid=q['connection_id'];a=answers[cid];u=q['source'];seen={u};value=rc.initial(u)
                for edge_index,eid in enumerate(a['physical_edge_ids']):
                    if type(eid) is not int or eid<0:raise ValueError('invalid physical edge ID')
                    slot=slots[eid]
                    if not fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1]:raise ValueError('arc source')
                    v=fields['dest_ranks'][slot]
                    if v in seen or fields['capacities'][v]<=0:raise ValueError('cycle/disabled node')
                    if edge_index<len(a['physical_edge_ids'])-1 and kinds[v] in ('SOURCE','SINK'):raise ValueError('interior terminal')
                    if kinds[v]!='SINK':
                        incoming=(u,eid);p=parents[q['net_id']]
                        if v in p and p[v]!=incoming:raise ValueError('shared parent conflict')
                        p[v]=incoming
                    seen.add(v);value+=rc.increments[slot];u=v
                if u!=q['sink'] or value!=a['delay'] or not floors[cid]['minimum_integer']<=value<=budgets[cid]:raise ValueError('path budget')
                owners[q['net_id']].update(seen);independent.update(seen)
                records.append(dict(q,answer=a,floor_integer=floors[cid]['minimum_integer'],budget_integer=budgets[cid],proxy_budget_integer=max(rc.scale//10**9,(3*floors[cid]['minimum_integer']+1)//2)))
            ledger=Counter(n for ns in owners.values() for n in ns);d=output/mode;d.mkdir()
            frame=dict(records=records,scale=rc.scale,graph_sha256=digest,required_connections=len(queries),completed_connections=len(records),ledger=dict(ledger),independent_connection_ledger=dict(independent),history={},epochs={str(net):int(net in dirty) for net in groups},overflow_units=sum(max(0,v-fields['capacities'][n]) for n,v in ledger.items()),eligible_for_legal_route_commit=False,budget_policy=POLICY,initializer_policy=mode)
            pairs={}
            for q in queries:
                pair=(q['source'],q['sink']);value=floors[q['connection_id']]['minimum_integer']
                if pair in pairs and pairs[pair]!=value:raise ValueError('pair floor conflict')
                pairs[pair]=value
            for name,data in [('initial.json',frame),('history.json',{}),('floors.json',[dict(source=s,sink=t,minimum_integer=v) for (s,t),v in sorted(pairs.items())]),('initializer_events.json',events)]:
                (d/name).write_text(json.dumps(data)+'\n')
            arm_bindings={**bindings,**{str(p):sha(p) for p in d.iterdir()}}
            if not all(sha(p)==h for p,h in arm_bindings.items()):raise ValueError('changed dependency')
            receipt=dict(status='WARM_PRODUCED_INDEPENDENT_AUDIT_PENDING',bindings=arm_bindings,endpoint=str(endpoint),source_directory=str(source_directory),floor_proof=str(floor_proof),dirty_nets=sorted(dirty),initializer_policy=mode,connections=len(records),native_anchored_budget_policy=POLICY,independent_audit_pending=True,total_shared_producer_elapsed_seconds=time.perf_counter()-begin,scope='Two-arm initialization only; shared timer includes work on earlier arms, not matched flow runtime. No verification.json until independent audit.')
            (d/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    finally:
        search.close();g.close()
    return dict(dirty_nets=len(dirty),connections=len(queries))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('endpoint','source_directory','floor_proof','output'):parser.add_argument(name)
    a=parser.parse_args();print(json.dumps(prepare(a.endpoint,a.source_directory,a.floor_proof,a.output)))
