"""Recompute all named features with independent Fraction timing aggregation."""
import json,math,struct,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from fractions import Fraction
from collections import defaultdict,Counter
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    root=R/'experiments/mmc_label_free_NET_features_v1_2026-10-19';rp=root/'receipt.json';d=json.loads(rp.read_text());assert d['status']=='ALL3_LABEL_FREE_NET_FEATURE_TABLES_PRODUCED' and d['target_labels_read'] is False and all(sha(p)==h for p,h in d['bindings'].items())
    spec=json.loads((root/'protocol.json').read_text());names=spec['feature_names'];assert len(names)==len(set(names))==31 and 'net_id' not in names
    old=json.loads((R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json').read_text());ownerplan=json.loads((R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json').read_text())
    graph=next(Path(p) for p in d['bindings'] if p.endswith('rr_graph.xml'));coords=[];caps=[];span=[];stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
            loc=e.find('loc');assert int(e.get('id'))==len(coords);coords.append((int(loc.get('xlow')),int(loc.get('ylow'))));caps.append(int(e.get('capacity')));length=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1;span.append(length if e.get('type') in ['CHANX','CHANY'] and caps[-1]>0 else 0);stack[-2].remove(e);e.clear()
        if e.tag=='rr_nodes':break
        stack.pop()
    channel={n for n,s in enumerate(span) if s};assert len(coords)==904438 and len(channel)==258720;rows=[]
    for item in old['cases']:
        case=item['case'];ep=Path(item['endpoint']);queries=json.loads(ep.read_text())['connections'];assert old['bindings'][str(ep)]==d['bindings'][str(ep)]==sha(ep)
        producer=R/'experiments/mmc_all_NET_feedback_v1_2026-10-18'/case/'protocol.json';p=json.loads(producer.read_text());tp=Path(p['criticality_input_proof']);timing=json.loads(tp.read_text());assert timing['schema']=='ROUTECAST_FROZEN_TIMING_REMAP_V1';before={x['connection_id']:x for x in json.loads(Path(timing['before_endpoint']).read_text())['connections']};critical={}
        for x in json.loads((tp.parent/'remapped_criticalities.json').read_text()):
            value=struct.unpack('<f',struct.pack('<f',float(x['criticality_float32_text'])))[0];critical[x['connection_id']]=(x,Fraction(value))
        baseproof=Path(p['structural_node_base_proof']);basefile=baseproof.parent/'node_base.u64';bi=json.loads(baseproof.read_text());assert bi['bindings'][str(basefile)]==sha(basefile);base=array('Q');base.frombytes(basefile.read_bytes())
        frames=[]
        for key in ['candidate_A','candidate_B']:
            path=Path(item[key]);assert old['bindings'][str(path)]==d['bindings'][str(path)]==sha(path);frames.append(json.loads(path.read_text()))
        maps=[{x['connection_id']:x for x in f['records']} for f in frames];ledger=[{int(n):v for n,v in f['ledger'].items()} for f in frames];groups=defaultdict(list)
        for q in queries:
            cid=q['connection_id'];t,c=critical[cid];assert (t['net'],t['source_rr'],t['target_rr'])==(q['net_id'],q['source'],q['sink']);assert all(m[cid][k]==v for m in maps for k,v in q.items());groups[q['net_id']].append(q)
        source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/case;gp=source/'graph.json';bp=source/'banks.jsonl'
        for path in [gp,bp]:assert ownerplan['bindings'][str(path)]==d['bindings'][str(path)]==sha(path)
        g=json.loads(gp.read_text());banks={x['net_id']:x for x in map(json.loads,bp.open())};outdegree=Counter(x['source'] for x in g['edges']);indegree=Counter(x['target'] for x in g['edges']);sizes={n:len(c) for c in g['components'] for n in c};seen=set();checked=0
        for row in map(json.loads,(root/(case+'.jsonl')).open()):
            net=row['net_id'];assert net not in seen;seen.add(net);qs=groups[net];ids=[q['connection_id'] for q in qs];F=len(ids);cs=[critical[cid][1] for cid in ids];budgets=[maps[0][cid]['budget_integer'] for cid in ids];nodes=[set(banks[net][k]) for k in ['A','B']];channels=[s&channel for s in nodes];counts=list(map(len,channels));length=[sum(span[n] for n in s) for s in channels];basecost=[Fraction(sum(base[n] for n in s if n!=qs[0]['source']),10**9) for s in nodes];raw=[Fraction(sum(m[cid]['answer']['delay'] for cid in ids),F*10**9) for m in maps]
            changed=0;movement=0;endpoint_coords=[]
            for q in qs:
                oldq=before[q['connection_id']];changed+=int((oldq['source'],oldq['sink'])!=(q['source'],q['sink']))
                for end in ['source','sink']:
                    a,b=coords[oldq[end]],coords[q[end]];movement+=sum(abs(a[i]-b[i]) for i in [0,1]);endpoint_coords.append(b)
            width=max(x for x,y in endpoint_coords)-min(x for x,y in endpoint_coords);height=max(y for x,y in endpoint_coords)-min(y for x,y in endpoint_coords);union=channels[0]|channels[1]
            expected=dict(fanout=F,changed_connections=changed,endpoint_move_L1=movement,bbox_width=width,bbox_height=height,criticality_min=min(cs),criticality_mean=sum(cs)/F,criticality_max=max(cs),budget_mean_ns=Fraction(sum(budgets),F*10**9),A_CHANNELs=counts[0],B_CHANNELs=counts[1],B_minus_A_CHANNELs=counts[1]-counts[0],A_CHANNEL_span=length[0],B_CHANNEL_span=length[1],B_minus_A_span=length[1]-length[0],bank_CHANNEL_Jaccard=Fraction(len(channels[0]&channels[1]),len(union)) if union else 1,A_base_sum_ns=basecost[0],B_base_sum_ns=basecost[1],B_minus_A_base_sum_ns=basecost[1]-basecost[0],A_raw_mean_ns=raw[0],B_raw_mean_ns=raw[1],B_minus_A_raw_mean_ns=raw[1]-raw[0],implication_outdegree=outdegree[net],implication_indegree=indegree[net],SCC_size=sizes[net])
            for i,key in enumerate(['A','B']):
                expected[key+'_max_budget_fraction']=max(Fraction(maps[i][cid]['answer']['delay'],maps[i][cid]['budget_integer']) for cid in ids)
                expected[key+'_overused_CHANNELs']=sum(ledger[i][n]>caps[n] for n in channels[i]);expected[key+'_mean_other_CHANNEL_occupancy']=Fraction(sum(ledger[i][n]-1 for n in channels[i]),max(1,len(channels[i])))
            assert set(expected)==set(names) and len(row['values'])==len(names)
            for name,value in zip(names,row['values']):assert math.isfinite(value) and math.isclose(value,float(expected[name]),rel_tol=1e-12,abs_tol=1e-12),(case,net,name,value,expected[name]);checked+=1
        assert seen==set(groups)==set(banks)==set(g['nodes']) and len(seen)==55300;rows.append(dict(case=case,NETs=len(seen),feature_values_verified=checked));print('LABEL_FREE_FEATURES_INDEPENDENT_PASS',case,checked,flush=True)
    with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_165900_NETS_5142900_FEATURE_VALUES_AND_PINNED_INPUT_NAMESPACES_VERIFIED',rows=rows,bindings={str(p):sha(p) for p in [rp,root/'protocol.json',Path(__file__).resolve()]},scope='Independent named-feature recomputation with rational timing/cost arithmetic, pinned candidate/endpoint/owner-bank admission. No target route/occupancy read, no normalization or fitting. Same old exposed MMC cohort, frozen pre-move timing only.'),f,indent=2)


if __name__=='__main__':main()
