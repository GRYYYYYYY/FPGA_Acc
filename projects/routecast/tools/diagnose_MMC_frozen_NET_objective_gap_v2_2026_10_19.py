"""Score archived native and selected trees with identical frozen input costs."""
import json,sys,time,xml.parsers.expat as expat
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from array import array
from pre_route_endpoints import sha
from load_initial_connection_criticalities_v3 import load
from versioned_digest_cache_v1 import Cache
from diagnose_MMC_native_path_floor_gaps_v1_2026_10_19 import NET,NODE

R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/mmc_frozen_NET_objective_gap_v2_2026-10-19';out.mkdir(exist_ok=False)
    model=R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19'
    ap=R/'experiments/mmc_complete_static_criticality_audit_v1_2026-10-19/verification.json';audit=json.loads(ap.read_text())
    assert audit['status']=='ALL3_COMPLETE_SELECTED_PATHS_XML_BUDGETS_SINGLEPARENT_LEDGER_AND_ACCEPTED_GATE_REPLAY_PASS'
    cases=[f'episode_{i:02d}' for i in range(1,4)]
    protocol=dict(cases=cases,objective='sum_pin c*raw + sum_unique_destination (1-max_user_c)*native_base; exclude SOURCE structural cost. Exact current initialized float32 c and unchanged native-base units.',
        comparisons='All complete NETs; separately classify NETs whose native paths all fit the existing per-CID static-model raw budgets. Native budget failures remain visible and are not feasible-alternative claims.',
        scope='Frozen input-only score applied retrospectively to archived paths; not native evolving congestion/criticality equivalence, optimality, new predictor or quality gain.')
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    cache=Cache();start=time.perf_counter()
    with cache.installed():
        bindings={str(ap):sha(ap),str(Path(__file__).resolve()):sha(__file__)};needed=set();metas={}
        for case in cases:
            ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case/'demand/endpoints.json'
            metas[case]=json.loads(ep.read_text());bindings[str(ep)]=sha(ep)
            records=model/case/'records.jsonl';assert audit['bindings'][str(records)]==sha(records)
            for line in records.open():needed.update(json.loads(line)['answer']['physical_edge_ids'])
            bindings[str(records)]=sha(records)
        graph=Path(metas[cases[0]]['inputs']['graph']['path']);assert sha(graph)==metas[cases[0]]['graph_sha256'];bindings[str(graph)]=sha(graph)
        switches={};arcs={};stack=[];edge=0;switch=None
        def opening(tag,a):
            nonlocal edge,switch
            parent=stack[-1] if stack else None
            if tag=='switch' and parent=='switches':switch=int(a['id'])
            elif tag=='timing' and parent=='switch':
                value=Fraction(a.get('Tdel','0'))*10**18;assert value.denominator==1;switches[switch]=int(value)
            elif tag=='timing' and parent=='node':assert Fraction(a.get('R','0'))==Fraction(a.get('C','0'))==0
            elif tag=='edge' and parent=='rr_edges':
                if edge in needed:arcs[edge]=(int(a['src_node']),int(a['sink_node']),switches[int(a['switch_id'])])
                edge+=1
            stack.append(tag)
        def closing(tag):assert stack.pop()==tag
        parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
        with graph.open('rb') as f:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
        parser.Parse(b'',True);assert set(arcs)==needed and edge==8097539
        bp=R/'experiments/mmc_native_node_base_mapping_v1_2026-10-10/verification.json';baseproof=json.loads(bp.read_text());payload=bp.parent/'node_base.u64';assert baseproof['bindings'][str(payload)]==sha(payload)
        base=array('Q');base.frombytes(payload.read_bytes());assert len(base)==904438 and baseproof['scale']==10**18 and baseproof['array_byteorder']==sys.byteorder
        bindings.update({str(p):sha(p) for p in [bp,payload]});rows=[]
        for case in cases:
            meta=metas[case];queries={q['connection_id']:q for q in meta['connections']};targets={(q['net_id'],q['source'],q['sink']):q['connection_id'] for q in queries.values()};groups=defaultdict(set)
            for cid,q in queries.items():groups[q['net_id']].add(cid)
            timing=R/'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19'/case;values=load(timing)
            Q=max(v['criticality_denominator'] for v in values.values());coeff={cid:v['criticality_numerator']*(Q//v['criticality_denominator']) for cid,v in values.items()};assert all(Q%v['criticality_denominator']==0 for v in values.values())
            for p in [timing/'verification.json',timing/'initial_connection_criticalities.json']:bindings[str(p)]=sha(p)
            selected=defaultdict(lambda:dict(raw=0,users={},cids=set()));budgets={}
            for line in (model/case/'records.jsonl').open():
                record=json.loads(line);cid=record['connection_id'];q=queries[cid];s=selected[q['net_id']];assert cid not in s['cids'];s['cids'].add(cid);u=q['source'];raw=0
                for eid in record['answer']['physical_edge_ids']:
                    a,b,cost=arcs[eid];assert a==u;u=b;raw+=cost;s['users'][b]=max(s['users'].get(b,0),coeff[cid])
                assert u==q['sink'] and raw==record['answer']['delay'];s['raw']+=coeff[cid]*raw;budgets[cid]=record['budget_integer']
            def score(state):return state['raw']+sum((Q-c)*base[n] for n,c in state['users'].items())
            events=model/case/'events.jsonl';assert audit['bindings'][str(events)]==sha(events)
            for line in events.open():
                e=json.loads(line);s=selected[e['net_id']];assert s['cids']==groups[e['net_id']]
                reported=e.get('candidate_score') if e['decision']=='COMMITTED' else e.get('old_score')
                if reported is not None:assert Fraction(score(s),Q)==Fraction(reported)
                else:assert e['decision']=='RETAIN_PRIMARY_FAILURE'
            bindings[str(events)]=sha(events)
            native_root=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case;np=native_root/'verification.json';nv=json.loads(np.read_text());route=native_root/'cold/output.route';assert nv['all_native_physical_and_canonical_pass'] and nv['bindings'][str(route)]==sha(route)
            bindings.update({str(p):sha(p) for p in [np,route]})
            names={name:int(net) for net,name in meta['net_names'].items()};native={};net=None;source=None;current=None;outgoing=None;parents={};arrival={};state=None
            def finish():
                if state is not None:
                    assert state['cids']==groups[net] and net not in native;native[net]=state
            for line in route.open():
                match=NET.match(line)
                if match:
                    finish();net=names[match[2]];source=None;parents={};arrival={};current=None;outgoing=None
                    state=dict(raw=0,users={},cids=set(),budget_failures=0) if net in groups else None
                match=NODE.match(line)
                if not match or state is None:continue
                node=int(match[1]);kind=match[2];sw=int(match[3])
                if kind=='SOURCE':source=node;arrival[node]=0
                elif node in arrival and kind!='SINK':pass
                else:
                    assert current in arrival and outgoing in switches
                    raw=arrival[current]+switches[outgoing]
                    if kind!='SINK':parents[node]=current;arrival[node]=raw
                    else:
                        cid=targets[net,source,node];assert cid not in state['cids'];state['cids'].add(cid);state['raw']+=coeff[cid]*raw;state['budget_failures']+=int(raw>budgets[cid])
                        state['users'][node]=max(state['users'].get(node,0),coeff[cid]);u=current;seen={node}
                        while u!=source:
                            assert u not in seen;seen.add(u);state['users'][u]=max(state['users'].get(u,0),coeff[cid]);u=parents[u]
                current=node;outgoing=sw
            finish();assert set(native)==set(selected) and len(native)==55300
            counts=Counter();budget_counts=Counter();totals=Counter();target=out/(case+'.NETs.jsonl')
            with target.open('x') as f:
                for net in sorted(native):
                    n,s=native[net],selected[net];native_raw=n['raw'];native_struct=score(n)-native_raw;sel_raw=s['raw'];sel_struct=score(s)-sel_raw;delta=score(n)-score(s)
                    relation='native_lower' if delta<0 else 'equal' if delta==0 else 'native_higher';counts[relation]+=1;budget_counts[('native_budget_pass' if not n['budget_failures'] else 'native_budget_fail')+'__'+relation]+=1
                    totals['native_raw']+=native_raw;totals['native_structural']+=native_struct;totals['selected_raw']+=sel_raw;totals['selected_structural']+=sel_struct;totals['native_budget_failure_connections']+=n['budget_failures']
                    f.write(json.dumps(dict(net_id=net,connections=len(n['cids']),denominator=Q,native_raw_numerator=native_raw,native_structural_numerator=native_struct,selected_raw_numerator=sel_raw,selected_structural_numerator=sel_struct,native_budget_failure_connections=n['budget_failures'],relation=relation),separators=(',',':'))+'\n')
            rows.append(dict(case=case,NETs=len(native),connections=sum(len(s['cids']) for s in native.values()),denominator=Q,relations=dict(counts),by_native_budget=dict(budget_counts),totals=dict(totals)))
            bindings[str(target)]=sha(target);print('FROZEN_OBJECTIVE_SCORED',case,dict(counts),dict(budget_counts),flush=True)
        (out/'review.json').write_text(json.dumps(dict(status='ALL3_FROZEN_NATIVE_SELECTED_NET_OBJECTIVES_COMPUTED',rows=rows,bindings=bindings,seconds=time.perf_counter()-start,independent_verification_pending=True,scope=protocol['scope']),indent=2)+'\n')


if __name__=='__main__':main()
