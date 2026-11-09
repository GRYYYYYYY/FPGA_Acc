"""Sequential fixed-pin, exact-budget, full-native-capacity local feedback diagnostic."""
import json
import shutil
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path
from prepared_csr import read,U64
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from csr_exact_budget_search import query
from audit_native_route import NET,NODE
from pre_route_endpoints import sha


def main():
    base=Path('experiments');design='adder_tree_3L_128bits'
    gate=base/'adder_tree_four_candidate_exact_delay_gate_2026-10-06';gr=json.loads((gate/'receipt.json').read_text());assert sha(gate/'report.json')==gr['report_sha256'];gp=json.loads((gate/'report.json').read_text())
    budgets={r['net_id']:Fraction(*r['native_exact_delay']) for r in gp['values']};nets=set(budgets)
    native=base/'adder_tree_family_native_path_audit_2026-10-06'/design;nr=json.loads((native/'receipt.json').read_text());np=json.loads((native/'protocol.json').read_text());assert sha(native/'receipt.json')==gp['native_receipt_sha256'];assert sha(native/'protocol.json')==nr['protocol_sha256'] and nr['physical_checks_pass'] and nr['overflow_units']==0
    route=np['inputs']['evaluator_route'];assert sha(route['path'])==route['sha256'];graph=gp['graph'];assert graph==np['inputs']['rr_graph']
    prepared=base/'adder_tree_family_length_switch_csr_2026-10-06'/design;prep=json.loads((prepared/'receipt.json').read_text());assert sha(prepared/'csr/manifest.json')==prep['manifest_sha256']
    m,f=read(prepared/'csr',graph['sha256'])
    context=base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06'/design;rc=ExactBufferedRC(f,*load(context,graph['sha256']))
    nodes={};unions={};net=None
    with Path(route['path']).open() as stream:
        for line in stream:
            match=NET.match(line)
            if match:net=int(match[1]);unions.setdefault(net,set());continue
            match=NODE.match(line)
            if match:
                nid=int(match[1]);unions[net].add(nid)
                if net in nets:nodes.setdefault(net,[]).append((nid,match[2],int(match[3])))
    truthpath=native/'physical_branches.json';assert sha(truthpath)==nr['outputs']['physical_branches.json']
    occupancy=Counter(n for used in unions.values() for n in used);assert occupancy==Counter({int(k):v for k,v in json.loads(truthpath.read_text())['node_occupancy'].items()})
    original={};queries=[]
    cid_by_net={r['net_id']:r['connection_id'] for r in gp['values']}
    for net in sorted(nets,key=lambda n:cid_by_net[n]):
        ns=nodes[net];source=ns[0][0];sink=ns[-1][0]
        assert ns[0][1]=='SOURCE' and ns[-1][1]=='SINK' and len({n for n,_,_ in ns})==len(ns)
        slots=[]
        for (a,_,switch),(b,_,_) in zip(ns,ns[1:]):
            choices=[i for i in range(f['row_offsets'][a],f['row_offsets'][a+1]) if f['dest_ranks'][i]==b and f['switch_ids'][i]==switch];assert choices;slots.append(min(choices,key=lambda i:f['edge_ids'][i]))
        path=[f['edge_ids'][i] for i in slots];assert rc.path(source,sink,path)==budgets[net]
        original[net]=set(unions[net]);queries.append({'net_id':net,'connection_id':cid_by_net[net],'source':source,'sink':sink,'opin':ns[1][0],'ipin':ns[-2][0],'original_edge_ids':path})
    out=base/'adder_tree_four_budgeted_native_feedback_search_2026-10-06';out.mkdir();(out/'source').mkdir()
    names=['search_adder_tree_budgeted_feedback.py','prepared_csr.py','buffered_rc_context.py','buffered_rc_node_classes.py','csr_exact_buffered_rc.py','csr_exact_budget_search.py','path_rc.py','pre_route_endpoints.py','audit_native_route.py'];sources={n:sha(Path('tools')/n) for n in names}
    for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
    inputs={str(p):sha(p) for p in [gate/'report.json',context/'receipt.json',prepared/'receipt.json',native/'receipt.json',truthpath,Path(route['path'])]}
    protocol={'inputs_sha256':inputs,'source_sha256':sources,'graph':graph,'queries':queries,'order':'ascending CID; each accepted witness updates full occupancy before next query','objective':'minimum per-path channel span subject to exact native path budget, native actual OPIN/IPIN, residual native capacity','label_limit':m['nodes'],'all_four_native_budget_parity_pass':True,'scope':'post-hoc four-net sequential feedback search; not complete joint optimum, native STA/QoR or end-to-end gain'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic();statuses=Counter();records=[]
    with (out/'queries.jsonl').open('w') as journal:
        for q in queries:
            net=q['net_id'];source=q['source'];sink=q['sink'];own=unions[net]
            def allowed(node,slot):
                dest=f['dest_ranks'][slot];kind=f['types'][dest]
                if f['costs'][slot]==U64 or occupancy[dest]-(dest in own)>=f['capacities'][dest]:return False
                if node==source:return dest==q['opin']
                if kind in (4,5):return f['types'][node] in (2,4,5)
                if kind==3:return dest==q['ipin'] and f['types'][node] in (2,4,5)
                return kind==1 and dest==sink and node==q['ipin']
            def cost(node,slot):
                dest=f['dest_ranks'][slot]
                return max(f['xhigh'][dest]-f['xlow'][dest],f['yhigh'][dest]-f['ylow'][dest])+1 if f['types'][dest] in (4,5) else 0
            result=query(rc,source,sink,budgets[net],allowed,cost,max_labels=m['nodes']);statuses[result['status']]+=1
            oldspan=sum(max(f['xhigh'][n]-f['xlow'][n],f['yhigh'][n]-f['ylow'][n])+1 for n in own if f['types'][n] in (4,5))
            if result['status']=='FOUND':
                current=source;used={source}
                for eid in result['physical_edge_ids']:
                    matches=[i for i in range(f['row_offsets'][current],f['row_offsets'][current+1]) if f['edge_ids'][i]==eid];assert len(matches)==1 and allowed(current,matches[0]);current=f['dest_ranks'][matches[0]];assert current not in used;used.add(current)
                assert current==sink and result['delay']<=budgets[net] and result['cost']<=oldspan
                for n in own:occupancy[n]-=1
                occupancy.update(used);unions[net]=used
                assert all(v<=f['capacities'][n] for n,v in occupancy.items())
                result['delay']=[result['delay'].numerator,result['delay'].denominator]
            record={**q,'original_span':oldspan,'result':result};records.append(record);journal.write(json.dumps(record)+'\n');journal.flush();print(json.dumps({'net':net,'status':result['status'],'original_span':oldspan,'candidate_span':result.get('cost')}),flush=True)
    assert +occupancy==Counter(n for used in unions.values() for n in used)
    assert all(sha(p)==h for p,h in inputs.items()) and all(sha(Path('tools')/n)==h for n,h in sources.items())
    receipt={'protocol_sha256':sha(out/'protocol.json'),'journal_sha256':sha(out/'queries.jsonl'),'statuses':dict(statuses),'strict_span_improvements':sum(r['result']['status']=='FOUND' and r['result']['cost']<r['original_span'] for r in records),'full_rebuild_exact':True,'final_overflow_units':sum(max(0,v-f['capacities'][n]) for n,v in occupancy.items()),'wall_s':time.monotonic()-start,'repair_committed':False,'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)


if __name__=='__main__':main()
