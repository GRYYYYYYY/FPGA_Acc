"""Full-input arithmetic bounds for the frozen two-round hardware candidate.

This is an exact integer domain certificate, not RTL, synthesis or board proof.
IEEE binary32 criticalities have power-of-two denominators; multiplying every
query objective by a common denominator preserves minima and ties exactly.
"""
import json
import struct
import sys
import xml.etree.ElementTree as E
from collections import Counter
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def main():
    out=R/'experiments/neuron_exact_hardware_cost_width_v1_2026-10-13';out.mkdir(exist_ok=False)
    ep_path=R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
    lp=R/'experiments/titan23_neuron_graph_recovery_v1_2026-10-13/lattice_readiness.json'
    bp=R/'experiments/titan23_neuron_node_base_wide_v1_2026-10-13/verification.json'
    cp=R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality/verification.json'
    bindings=closure([Path(__file__)])
    for p in [lp,bp,cp]:
        v=json.loads(p.read_text());assert all(sha(q)==h for q,h in v['bindings'].items())
        for q,h in v['bindings'].items():
            assert q not in bindings or bindings[q]==h;bindings[q]=h
        bindings[str(p)]=sha(p)
    ep=json.loads(ep_path.read_text());bindings[str(ep_path)]=sha(ep_path)
    lattice=json.loads(lp.read_text());base=json.loads(bp.read_text())
    table=cp.parent/'initial_connection_criticalities.json';rows=json.loads(table.read_text())
    assert bindings[str(table)]==sha(table)
    query_ids={q['connection_id'] for q in ep['connections']};seen=set();denominators=Counter();fractions=[]
    for row in rows:
        cid=row['connection_id'];assert cid in query_ids and cid not in seen;seen.add(cid)
        value=struct.unpack('<f',struct.pack('<f',float(row['criticality_float32_text'])))[0]
        assert 0<=value<=1;c=Fraction(value);d=c.denominator
        assert d>0 and d&(d-1)==0;denominators[d]+=1;fractions.append(c)
    assert seen==query_ids and len(seen)==77106
    common=max(denominators)
    assert all(common%d==0 and (c*common).denominator==1 for d in denominators for c in fractions[:1])
    assert all((c*common).denominator==1 for c in fractions)
    graph=Path(ep['inputs']['graph']['path']);span=0;n=0;stack=[]
    for event,node in E.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(node);continue
        if node.tag=='node' and stack[-2].tag=='rr_nodes':
            assert node.get('id')==str(n);n+=1
            if node.get('type') in ['CHANX','CHANY']:
                loc=node.find('loc');s=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1
                assert s>=1;span=max(span,s)
            stack[-2].remove(node);node.clear()
        if node.tag=='rr_nodes':break
        stack.pop()
    assert n==lattice['nodes']==base['nodes']==3593250
    counts=Counter(q['net_id'] for q in ep['connections']);owners=len(counts);assert owners==50767
    # Initial accumulated overuse is skipped. With exactly two rounds, only
    # one previous full-graph overuse update exists; each count is <= owners.
    history_max=owners;other_occupancy_max=owners
    price_max=base['maximum_node_base']*(1+history_max)*(1+other_occupancy_max)+lattice['static_span_price_weight']*span
    raw_max=lattice['maximum_root_word']+(n-1)*lattice['maximum_arc_word']
    queue_max=common*(raw_max+n*price_max)
    score_max=common*(max(counts.values())*raw_max+n*price_max)
    delta_signed_bits=score_max.bit_length()+1
    required=max(queue_max.bit_length(),delta_signed_bits)
    lane_bits=((required+31)//32)*32
    cpp_envelope=2*n*(lattice['maximum_arc_word']+base['maximum_node_base']+price_max)+lattice['maximum_root_word']
    assert cpp_envelope<2**120
    assert all(sha(p)==h for p,h in bindings.items())
    result=dict(bindings=bindings,all_pass=True,nodes=n,edges=lattice['edges'],connections=len(seen),owners=owners,
                fixed_rounds=2,initial_history_update_skipped=True,maximum_channel_span=span,
                common_criticality_denominator=common,common_denominator_bits=common.bit_length(),
                minimum_positive_criticality=str(min(c for c in fractions if c>0)),
                denominator_histogram={str(k):v for k,v in sorted(denominators.items())},
                raw_simple_path_upper_bound=raw_max,conservative_snapshot_congestion_upper_bound=price_max,
                criticality_queue_upper_bound=queue_max,whole_NET_objective_upper_bound=score_max,
                raw_bits=raw_max.bit_length(),congestion_bits=price_max.bit_length(),
                queue_bits=queue_max.bit_length(),signed_objective_delta_bits=delta_signed_bits,
                chosen_full_primary_lane_bits=lane_bits,cpp_noncriticality_queue_120bit_envelope_pass=True,
                normalized_perpin_numerators_all_exact=True,
                scope='Conservative exact cost bounds for complete original graph, frozen native binary32 criticality epoch, <=owners occupancy and one accumulated-overuse update. Positive common-denominator scaling preserves query minima/ties and union-score ordering. New rounds or timing epochs require recertification. No RTL/synthesis/board/runtime-speed or route-quality proof.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k not in ['bindings','denominator_histogram']},flush=True)

if __name__=='__main__':main()
