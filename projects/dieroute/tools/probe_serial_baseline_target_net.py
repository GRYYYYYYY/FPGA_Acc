"""Private diagnostic rebuild of a critical net with baseline-target delay caps."""
import csv,hashlib,json,struct,sys
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET
from shared_tree_budget_repair import repair


def main():
    root=Path('work/native_joint_budget_net_repair_v2_20261016')
    protocol=root/'protocol.json';manifest=root/'ex5p/manifest.json'
    case=json.loads(protocol.read_text())['cases'][0]
    tree=Path('work/native_refreshed_baseline_target_task895_20261016/route.route_trees.csv')
    observation=tree.parent/'fresh_observation/observation.output.csv'
    binding=Path('work/native_joint_budget_ex5p_baseline_target_probe_20261016/updated_critical_tasks.json')
    selected=next(a for a in json.loads(binding.read_text())['arcs'] if not a['intracluster'] and int(a['task']['id'])==int(sys.argv[1]))
    net=int(selected['task']['net_id']);critical_task=int(selected['task']['id'])
    nodefile=Path(case['input_prefix']+'.nodes');edgefile=Path(case['input_prefix']+'.edges')
    resourcefile=Path(case['input_prefix']+'.resources');diefile=Path(case['topology_prefix']+'.node_die')
    nodes=list(struct.iter_unpack('<IHH',nodefile.read_bytes()));edges=list(struct.iter_unpack('<IHH',edgefile.read_bytes()))
    resources=list(struct.iter_unpack('<HHHHII',resourcefile.read_bytes()));dies=[r[0] for r in struct.iter_unpack('<H',diefile.read_bytes())]
    owners=[set() for _ in nodes];trees={}
    for r in csv.DictReader(tree.open()):
        n,u,v=int(r['net_id']),int(r['parent']),int(r['child'])
        trees.setdefault(n,{})[v]=u
        if n!=net:owners[v].add(n)
    allowed=[len(o)<resources[v][1] for v,o in enumerate(owners)]
    length=[0]*len(nodes);rr=Path(case['native_case'])/'rr_graph.xml'
    for _,e in ET.iterparse(rr,events=('end',)):
        if e.tag=='node':
            a=e.attrib;l=e.find('loc')
            if a['type'] in ('CHANX','CHANY') and a.get('direction')!='NONE':
                length[int(a['id'])]=1+int(l.attrib['xhigh'])-int(l.attrib['xlow'])+int(l.attrib['yhigh'])-int(l.attrib['ylow'])
            e.clear()
        elif e.tag=='edge':e.clear()
    baselinecross=sum(dies[int(r['parent'])]!=dies[int(r['child'])] for r in csv.DictReader(open(case['native_tree'])))
    othercross=sum(dies[u]!=dies[v] for n,p in trees.items() if n!=net for v,u in p.items())
    tasks={int(r['id']):r for r in csv.DictReader(open(case['connections'])) if int(r['net_id'])==net}
    obs={int(r['task_id']):{k:int(v) for k,v in r.items()} for r in csv.DictReader(observation.open())}
    limit=int(Decimal(str(case['baseline_cpd_ns']))*1000)
    order=sorted(tasks,key=lambda t:(t!=critical_task,-obs[t]['criticality_q'],t))
    requests=[dict(id=t,sink=int(tasks[t]['sink']),delay_budget=max(0,obs[t]['delay_ps']+limit+obs[t]['slack_ps']),max_hops=int(tasks[t]['max_hops'])) for t in order]
    source=int(tasks[critical_task]['source'])
    answer=repair(nodes,edges,allowed,length,dies,source,requests,baselinecross-othercross,maximum_labels=2097152)
    beforewire=sum(length[v] for v in trees[net]);afterwire=sum(length[int(v)] for v in answer.get('parent',answer.get('private_parent',{})))
    inputs=[protocol,manifest,tree,observation,binding,nodefile,edgefile,resourcefile,diefile,rr,Path(case['native_tree']),Path(case['connections']),Path(__file__),Path('tools/shared_tree_budget_repair.py'),Path('tools/delay_crossing_bounded_wire_search.py')]
    output=dict(status='private_baseline_target_net_probe_complete',net_id=net,critical_task=critical_task,requests=requests,
                crossing_budget=baselinecross-othercross,before_wire=beforewire,private_wire=afterwire,answer=answer,
                source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                scope='One critical-first diagnostic ordering, baseline-target caps, unchanged 2M label budget. No native validation or adopted policy.',research_complete=False)
    destination=Path('work/native_serial_baseline_target_task'+str(critical_task)+'_20261016');destination.mkdir(exist_ok=False)
    (destination/'result.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(dict(complete=answer['complete'],status=answer['status'],before_wire=beforewire,private_wire=afterwire,crossing_budget=baselinecross-othercross,steps=[dict(task=s['task'],status=s['search']['status'],delay=s['search'].get('delay'),labels=s['search']['labels']) for s in answer['steps']]),indent=2))


if __name__=='__main__':main()
