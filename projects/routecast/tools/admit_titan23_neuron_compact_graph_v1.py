"""Measure full graph loading and independently replay every original XML item.

The 16 GiB address-space bound applies to this input-only admission, not to an
unexecuted full model. It avoids jeopardizing concurrent jobs on shared memory.
"""
import json
import resource
import sys
import time
import xml.etree.ElementTree as E
from array import array
from fractions import Fraction
from math import lcm
from pathlib import Path
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def node_value(node):return (node.tag,dict(node.attrib),tuple(node_value(c) for c in node))

def main():
    out=R/'experiments/titan23_neuron_compact_graph_admission_v1_2026-10-13';out.mkdir(exist_ok=False)
    ep=R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
    lp=R/'experiments/titan23_neuron_graph_recovery_v1_2026-10-13/lattice_readiness.json'
    cp=R/'experiments/compact_stream_rc_contract_v1_2026-10-13/verification.json'
    lattice=json.loads(lp.read_text());contract=json.loads(cp.read_text())
    assert contract['all_pass'] and lattice['original_XML_all_node_and_edge_identities_and_electrical_values_pass']
    bindings={**closure([Path(__file__)]),**contract['bindings'],**lattice['bindings'],str(lp):sha(lp),str(cp):sha(cp),str(ep):sha(ep)}
    bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
    assert all(sha(p)==h for p,h in bindings.items())
    limit=16*2**30;resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
    (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,address_space_limit_bytes=limit,
        scope='All original nodes/edges/queries; exact unchanged electrical lattice. Full XML second-pass audit; no route labels, model execution, or reduced graph.'),indent=2)+'\n')
    begin=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(ep);load_seconds=time.perf_counter()-begin
    assert len(nodes)==lattice['nodes'] and len(f['edge_ids'])==lattice['edges'] and rc.scale==lattice['exact_scale']
    report=dict(nodes=len(nodes),edges=len(f['edge_ids']),connections=len(queries),scale=rc.scale,load_seconds=load_seconds,
                load_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,address_space_limit_bytes=limit,
                scope='Input loading only, before independent full XML replay; not complete model peak memory.')
    (out/'load_observation.json').write_text(json.dumps(report,indent=2)+'\n');print('COMPACT LOAD COMPLETE',report,flush=True)
    # Independent encoding: recover node classes from XML text, evaluate each
    # actually used destination/switch pair with Fraction, and verify every edge.
    tick=time.perf_counter();stack=[];classes=[];lookup={};indices=array('I');switches={}
    pairs={};scale=1;ni=ei=0;previous_source=-1;monotone=True
    # For this original graph source order was independently audited before.
    # Verify again; no assumption is used to omit any edge identity checks.
    assert lattice['raw_edge_sources_nondecreasing']
    for event,node in E.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(node);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if node.tag=='switch' and parent=='switches':
            sid=int(node.get('id'));t=node.find('timing')
            assert sid not in switches and node.get('type') in ['mux','buffer','tristate']
            assert Fraction(t.get('Cinternal','0'))==0
            switches[sid]=(Fraction(t.get('R','0')),Fraction(t.get('Tdel','0')))
            stack[-2].remove(node);node.clear()
        elif node.tag=='node' and parent=='rr_nodes':
            assert node.get('id')==str(ni) and node_value(node)==node_value(nodes[ni])
            assert f['node_ids'][ni]==ni and f['capacities'][ni]==int(node.get('capacity'))
            t=node.find('timing');key=(t.get('R'),t.get('C'))
            if key not in lookup:lookup[key]=len(classes);classes.append(tuple(Fraction(x) for x in key))
            c=lookup[key];indices.append(c);r,cap=classes[c];value=r*cap/2;scale=lcm(scale,value.denominator)
            scaled=value*rc.scale;assert scaled.denominator==1 and scaled.numerator==rc.initial(ni)
            ni+=1;stack[-2].remove(node);node.clear()
        elif node.tag=='edge' and parent=='rr_edges':
            u,v,s=int(node.get('src_node')),int(node.get('sink_node')),int(node.get('switch_id'))
            assert u>=previous_source;previous_source=u
            assert f['row_offsets'][u]<=ei<f['row_offsets'][u+1]
            assert (f['edge_ids'][ei],f['dest_ranks'][ei],f['switch_ids'][ei],f['costs'][ei])==(ei,v,s,1)
            key=(indices[v],s)
            if key not in pairs:
                r,c=classes[key[0]];sr,d=switches[s];value=(sr+r/2)*c+d
                scale=lcm(scale,value.denominator);scaled=value*rc.scale
                assert scaled.denominator==1;pairs[key]=scaled.numerator
            assert rc.increments[ei]==pairs[key]
            ei+=1;stack[-2].remove(node);node.clear()
        elif node.tag=='segment' and parent=='segments':stack[-2].remove(node);node.clear()
        stack.pop()
    assert ni==len(nodes) and ei==len(f['edge_ids']) and scale==rc.scale
    assert tuple(queries)==tuple(json.loads(ep.read_text())['connections'])
    assert all(sha(p)==h for p,h in bindings.items())
    result=dict(bindings=bindings,all_pass=True,**{k:v for k,v in report.items() if k!='scope'},
                audit_seconds=time.perf_counter()-tick,total_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                all_original_node_subtrees_CSR_edges_initials_increments_and_queries_equal=True,
                exact_original_lattice_recomputed=True,electrical_classes=len(classes),used_pairs=len(pairs),
                scope='Complete original neuron input and independent second XML traversal; measured input/audit residency under fixed address-space limit. Not full model memory, prediction quality or hardware evidence.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('FULL COMPACT NEURON INPUT AUDIT PASS',ni,ei,result['total_peak_rss_kib'],flush=True)

if __name__=='__main__':main()
