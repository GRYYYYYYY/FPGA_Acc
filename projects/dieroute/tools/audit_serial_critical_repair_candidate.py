"""Independent graph, connectivity, budget and provenance audit of serial candidate."""
import collections,csv,hashlib,json,struct
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    D=Path('work/native_serial_baseline_target_task318_20261016')
    root=Path('work/native_joint_budget_net_repair_v2_20261016');protocol=root/'protocol.json'
    case=json.loads(protocol.read_text())['cases'][0];manifest=root/'ex5p/manifest.json'
    original=Path(json.loads(manifest.read_text())['current_tree']);final=D/'route.route_trees.csv'
    def loadtree(path):
        trees={};sources={}
        for r in csv.DictReader(path.open()):
            net,u,v,s=(int(r[k]) for k in ['net_id','parent','child','source'])
            assert net not in sources or sources[net]==s;sources[net]=s
            assert v not in trees.setdefault(net,{})
            trees[net][v]=u
        return trees,sources
    before,src=loadtree(original);after,src2=loadtree(final);assert src==src2 and set(before)==set(after)
    changed=sorted(n for n in before if before[n]!=after[n]);assert changed==[30,138,222]
    nodefile=Path(case['input_prefix']+'.nodes');edgefile=Path(case['input_prefix']+'.edges');resourcefile=Path(case['input_prefix']+'.resources');diefile=Path(case['topology_prefix']+'.node_die')
    nodes=list(struct.iter_unpack('<IHH',nodefile.read_bytes()));edges=list(struct.iter_unpack('<IHH',edgefile.read_bytes()));resources=list(struct.iter_unpack('<HHHHII',resourcefile.read_bytes()));dies=[r[0] for r in struct.iter_unpack('<H',diefile.read_bytes())]
    occupancy=collections.Counter();edgecount=0
    for net,parent in after.items():
        occupancy.update(parent.keys())
        for v,u in parent.items():
            start,count,_=nodes[u];assert any(dst==v for dst,_,_ in edges[start:start+count]);edgecount+=1
    tasks=list(csv.DictReader(open(case['connections'])))
    for t in tasks:
        net,source,v=(int(t[k]) for k in ['net_id','source','sink']);assert src[net]==source
        seen=set()
        while v!=source:
            assert v not in seen and v in after[net];seen.add(v);v=after[net][v]
        assert len(seen)<=int(t['max_hops'])
    assert all(count<=resources[v][1] for v,count in occupancy.items())
    lengths={};rr=Path(case['native_case'])/'rr_graph.xml'
    for _,e in ET.iterparse(rr,events=('end',)):
        if e.tag=='node':
            a=e.attrib;l=e.find('loc');length=0
            if a['type'] in ('CHANX','CHANY') and a.get('direction')!='NONE':length=1+int(l.attrib['xhigh'])-int(l.attrib['xlow'])+int(l.attrib['yhigh'])-int(l.attrib['ylow'])
            lengths[int(a['id'])]=length;e.clear()
        elif e.tag=='edge':e.clear()
    wire=sum(lengths[v] for p in after.values() for v in p)
    cross=lambda t:sum(dies[v]!=dies[u] for p in t.values() for v,u in p.items())
    baseline,_=loadtree(Path(case['native_tree']))
    qfile=D/'native_validation/validation.json';q=json.loads(qfile.read_text());assert q['legal'] and q['total_wirelength']==wire
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert sha(D/'native.route')==q['inputs']['route_sha256']
    assert sha(protocol.parent/'../vpr_four_layer_build_20261015/build/vpr/vpr')==q['inputs']['vpr_sha256']
    assert wire<=case['baseline_wirelength'] and Decimal(str(q['critical_path_delay_ns']))<=Decimal(str(case['baseline_cpd_ns'])) and cross(after)<=cross(baseline)
    reproduce=D/'fresh_observation/result.json';fresh=json.loads(reproduce.read_text());assert fresh['status']=='fresh_native_observation_complete_setup_report_byte_reproduced'
    inputs=[protocol,manifest,original,final,nodefile,edgefile,resourcefile,diefile,rr,Path(case['connections']),Path(case['native_tree']),qfile,D/'native.route',reproduce,D/'fresh_observation/observation.output.csv',Path(__file__)]
    output=dict(status='serial_three_net_candidate_native_joint_baseline_connectivity_capacity_edges_and_STA_repeat_checked',changed_nets=changed,unchanged_nets=len(before)-len(changed),connections_checked=len(tasks),tree_edges_checked=edgecount,wirelength=wire,cpd_ns=q['critical_path_delay_ns'],crossings=cross(after),baseline_crossings=cross(baseline),cpd_margin_ps=str((Decimal(str(case['baseline_cpd_ns']))-Decimal(str(q['critical_path_delay_ns'])))*1000),
                source_sha256={str(p):sha(p) for p in inputs},adopted=False,research_complete=False,
                scope='Single ex5p diagnostic with three manually selected critical-first net repairs. Fresh same-command STA setup-report byte reproduction. Not a frozen general policy, independent seed, heldout, FPGA or board result; no G4 closure.')
    with (D/'independent_candidate_audit.json').open('x') as stream:json.dump(output,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in output.items() if k!='source_sha256'},indent=2))


if __name__=='__main__':main()
