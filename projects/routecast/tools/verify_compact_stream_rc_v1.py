"""Full XTEA XML/CSR/electrical parity plus unsorted-edge and rejection fixtures."""
import json
import sys
import xml.etree.ElementTree as E
from pathlib import Path
from class_cached_rc_endpoint_context_v1 import load_endpoints as original
from compact_stream_rc_endpoint_context_v1 import load_endpoints as compact
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def node_value(node):return (node.tag,dict(node.attrib),tuple(node_value(c) for c in node))

def compare(ep):
    a=original(ep);b=compact(ep)
    assert a[:2]==b[:2] and a[5]==b[5]
    assert len(a[2])==len(b[2]) and all(node_value(x)==node_value(y) for x,y in zip(a[2],b[2]))
    assert a[3]==b[3]
    x,y=a[4],b[4]
    assert x.scale==y.scale and x.initial_by_class==y.initial_by_class
    assert tuple(x.increments)==tuple(y.increments)
    assert list(x.rc.node_classes)==list(y.rc.node_classes) and x.rc.classes==y.rc.classes
    assert x.rc.switches==y.rc.switches and x.rc.cache==y.rc.cache
    assert all(x.initial(i)==y.initial(i) for i in range(len(a[2])))
    try:b[2].columns[('node','type')][0]=7
    except TypeError:pass
    else:raise AssertionError('mutable node column')
    try:b[4].increments.codes[0]=7
    except TypeError:pass
    else:raise AssertionError('mutable increment class code')
    return dict(nodes=len(b[2]),edges=len(b[3]['edge_ids']),scale=y.scale,
                all_node_subtrees_CSR_electrical_classes_increments_initials_queries_equal=True)

def main():
    out=R/'experiments/compact_stream_rc_contract_v1_2026-10-13';out.mkdir(exist_ok=False)
    ep=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json'
    bindings=closure([Path(__file__)]);bindings[str(ep)]=sha(ep)
    bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
    results={'xtea':compare(ep)}
    def fixture(root,name):
        p=out/(name+'.xml');E.ElementTree(root).write(p);h=sha(p)
        e=out/(name+'.endpoints.json');e.write_text(json.dumps(dict(inputs=dict(graph=dict(path=str(p),sha256=h)),graph_sha256=h,connections=[])))
        bindings[str(p)]=h;bindings[str(e)]=sha(e)
        return e
    root=E.Element('rr_graph');switches=E.SubElement(root,'switches')
    sw=E.SubElement(switches,'switch',id='0',type='mux');E.SubElement(sw,'timing',R='1e-3',Tdel='0',Cinternal='0')
    nodes=E.SubElement(root,'rr_nodes')
    for i in range(4):
        n=E.SubElement(nodes,'node',id=str(i),type='CHANX',capacity='1',direction='INC_DIR')
        E.SubElement(n,'loc',xlow=str(i),xhigh=str(i+1),ylow='0',yhigh='0',ptc=str(i))
        E.SubElement(n,'timing',R='2e-3',C=str((i+1)*1e-20))
        if i%2:E.SubElement(n,'segment',segment_id='1')
    edges=E.SubElement(root,'rr_edges')
    for u,v in [(2,3),(0,2),(1,3),(0,1),(2,2),(0,2)]:E.SubElement(edges,'edge',src_node=str(u),sink_node=str(v),switch_id='0')
    unsorted=fixture(root,'unsorted_parallel_self_edges');results['unsorted']=compare(unsorted)
    a=original(unsorted);b=compact(unsorted)
    assert list(b[3]['edge_ids'])==[1,3,5,2,0,4]
    for source,sink,path in [(0,3,[1,0]),(0,3,[3,2]),(0,2,[5]),(3,3,[])]:
        assert a[4].path(source,sink,path)==b[4].path(source,sink,path)
    rejections=[]
    for case in ['bad_node_id','unknown_switch','bad_destination','nested_metadata']:
        copy=E.fromstring(E.tostring(root))
        if case=='bad_node_id':copy.find('rr_nodes')[1].set('id','9')
        elif case=='unknown_switch':copy.find('rr_edges')[0].set('switch_id','19')
        elif case=='bad_destination':copy.find('rr_edges')[0].set('sink_node','19')
        else:E.SubElement(E.SubElement(copy.find('rr_nodes')[0],'metadata'),'meta').text='retained-or-rejected'
        p=fixture(copy,case)
        try:compact(p)
        except ValueError as e:rejections.append(dict(case=case,error=str(e)))
        else:raise AssertionError(case+' accepted')
    assert all(sha(p)==h for p,h in bindings.items())
    result=dict(bindings=bindings,all_pass=True,cases=results,rejections=rejections,
                scope='Full XTEA input representation equivalence and unsorted-edge/parallel/self-loop fixture; complete model parity and real Titan residency require separate evidence.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(results,indent=2),flush=True)

if __name__=='__main__':main()
