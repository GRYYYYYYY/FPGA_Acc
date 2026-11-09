"""Independent bottom-up tree user maxima and certified native raw scores."""
import json,struct,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from fractions import Fraction
from pre_route_endpoints import sha
from diagnose_MMC_native_path_floor_gaps_v1_2026_10_19 import NET,NODE

R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/mmc_frozen_NET_objective_gap_v1_2026-10-19';rp=out/'review.json';review=json.loads(rp.read_text())
    assert all(sha(p)==h for p,h in review['bindings'].items())
    prior=R/'experiments/mmc_native_path_floor_gap_diagnosis_v1_2026-10-19';pv=prior/'independent_verification_v1.json';proof=json.loads(pv.read_text());assert proof['status']=='ALL9_1040148_NATIVE_PARENT_CHAINS_XML_COSTS_AND_ARCHIVED_FLOOR_JOINS_PASS'
    pr=prior/'review.json';previous=json.loads(pr.read_text());assert proof['bindings'][str(pr)]==sha(pr)
    graph=next(Path(p) for p in review['bindings'] if p.endswith('rr_graph.xml'));dest=array('I');stack=[]
    def opening(tag,a):
        if tag=='edge' and stack and stack[-1]=='rr_edges':dest.append(int(a['sink_node']))
        stack.append(tag)
    def closing(tag):assert stack.pop()==tag
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    with graph.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    parser.Parse(b'',True);assert len(dest)==8097539
    base=array('Q');base.frombytes((R/'experiments/mmc_native_node_base_mapping_v1_2026-10-10/node_base.u64').read_bytes());verified=[]
    for row in review['rows']:
        case=row['case'];Q=row['denominator'];ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case/'demand/endpoints.json';meta=json.loads(ep.read_text());queries={q['connection_id']:q for q in meta['connections']};targets={(q['net_id'],q['source'],q['sink']):cid for cid,q in queries.items()}
        timing=R/'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19'/case/'initial_connection_criticalities.json';coeff={}
        for x in json.loads(timing.read_text()):
            v=struct.unpack('<f',struct.pack('<f',float(x['criticality_float32_text'])))[0];p,q=v.as_integer_ratio();assert Q%q==0;coeff[x['connection_id']]=p*(Q//q)
        selected=defaultdict(lambda:[0,{}]);budget={}
        for line in (R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19'/case/'records.jsonl').open():
            x=json.loads(line);cid=x['connection_id'];net=x['net_id'];selected[net][0]+=coeff[cid]*x['answer']['delay'];budget[cid]=x['budget_integer']
            for eid in x['answer']['physical_edge_ids']:
                node=dest[eid];selected[net][1][node]=max(selected[net][1].get(node,0),coeff[cid])
        gap=prior/(case+'_zero.jsonl');assert previous['bindings'][str(gap)]==sha(gap)
        raw={x['connection_id']:x['native_cost_hops'][0] for x in map(json.loads,gap.open())};assert len(raw)==115572
        route=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case/'cold/output.route'
        certified_route=R/'experiments/mmc_first_iteration_hint_utility_v1_2026-10-19'/case/'zero/cold/output.route';assert previous['bindings'][str(certified_route)]==sha(route)
        names={name:int(net) for net,name in meta['net_names'].items()};active={q['net_id'] for q in queries.values()};native={};net=None;source=None;current=None;parents={};depth={};sink_coeff={};nr=0;fail=0;seen=set()
        def finish():
            if net not in active:return
            maxima=dict(sink_coeff)
            for node in sorted(parents,key=lambda n:depth[n],reverse=True):
                parent=parents[node];maxima[parent]=max(maxima.get(parent,0),maxima.get(node,0))
            structural=sum((Q-c)*base[node] for node,c in maxima.items() if node!=source)
            assert net not in native;native[net]=(nr,structural,fail)
        for line in route.open():
            m=NET.match(line)
            if m:
                finish();net=names[m[2]];source=None;current=None;parents={};depth={};sink_coeff={};nr=0;fail=0
            m=NODE.match(line)
            if not m or net not in active:continue
            node=int(m[1]);kind=m[2]
            if kind=='SOURCE':source=node;depth[node]=0
            elif node in parents and kind!='SINK':pass
            else:
                assert current in depth;parents[node]=current;depth[node]=depth[current]+1
                if kind=='SINK':
                    cid=targets[net,source,node];assert cid not in seen;seen.add(cid);sink_coeff[node]=max(sink_coeff.get(node,0),coeff[cid]);nr+=coeff[cid]*raw[cid];fail+=int(raw[cid]>budget[cid])
            current=node
        finish();assert len(native)==55300 and seen==set(queries)
        counts=Counter();bybudget=Counter();totals=Counter();seen_nets=set()
        for line in (out/(case+'.NETs.jsonl')).open():
            x=json.loads(line);net=x['net_id'];assert net not in seen_nets;seen_nets.add(net);nr,ns,fail=native[net];sr,users=selected[net];ss=sum((Q-c)*base[n] for n,c in users.items())
            assert (nr,ns,sr,ss,fail)==tuple(x[k] for k in ['native_raw_numerator','native_structural_numerator','selected_raw_numerator','selected_structural_numerator','native_budget_failure_connections'])
            delta=nr+ns-sr-ss;relation='native_lower' if delta<0 else 'native_higher' if delta>0 else 'equal';assert x['relation']==relation
            counts[relation]+=1;bybudget[('native_budget_pass' if not fail else 'native_budget_fail')+'__'+relation]+=1
            totals.update(dict(native_raw=nr,native_structural=ns,selected_raw=sr,selected_structural=ss,native_budget_failure_connections=fail))
        assert len(seen_nets)==55300 and dict(counts)==row['relations'] and dict(bybudget)==row['by_native_budget'] and dict(totals)==row['totals']
        verified.append(dict(case=case,NETs=55300,connections=len(seen)))
        print('FROZEN_OBJECTIVE_BOTTOMUP_AND_CERTIFIED_RAW_PASS',case,flush=True)
    with (out/'independent_verification_v1.json').open('x') as f:
        json.dump(dict(status='ALL3_FROZEN_OBJECTIVE_COMPONENTS_BUDGETS_AND_RELATIONS_INDEPENDENTLY_VERIFIED',rows=verified,bindings={str(p):sha(p) for p in [rp,pv,pr,Path(__file__).resolve()]},scope='Independent bottom-up native user maxima, selected destination membership and prior certified native raw delays. Physical validity inherited from existing audits, not re-proven here.'),f,indent=2)


if __name__=='__main__':main()
