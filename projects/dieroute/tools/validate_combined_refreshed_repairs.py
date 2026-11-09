"""Capacity-check and native-validate the combination of two isolated net repairs."""
import csv,hashlib,json,struct,subprocess,sys
from pathlib import Path

root=Path('work/native_joint_budget_net_repair_v2_20261016');protocolfile=root/'protocol.json'
protocol=json.loads(protocolfile.read_text());case=protocol['cases'][0]
parent=Path('work/native_joint_budget_ex5p_baseline_target_probe_20261016/route.route_trees.csv')
repairs=[Path('work/native_refreshed_baseline_target_task895_20261016/result.json'),Path('work/native_refreshed_baseline_target_task318_20261016/result.json')]
D=Path('work/native_combined_refreshed_repairs_20261016').resolve();D.mkdir(exist_ok=False)
rows=list(csv.DictReader(parent.open()));sources={int(r['net_id']):int(r['source']) for r in rows}
changed=[]
for p in repairs:
    r=json.loads(p.read_text());assert r['answer']['complete'];net=r['net_id'];changed.append(net)
    rows=[r for r in rows if int(r['net_id'])!=net]
    rows += [dict(net_id=net,source=sources[net],parent=u,child=v) for v,u in r['answer']['parent'].items()]
resourcefile=Path(case['input_prefix']+'.resources');diefile=Path(case['topology_prefix']+'.node_die')
resources=list(struct.iter_unpack('<HHHHII',resourcefile.read_bytes()));dies=[r[0] for r in struct.iter_unpack('<H',diefile.read_bytes())]
owners={};cross=0
for r in rows:
    net,u,v=int(r['net_id']),int(r['parent']),int(r['child']);owners.setdefault(v,set()).add(net);cross+=dies[u]!=dies[v]
overflow=[v for v,o in owners.items() if len(o)>resources[v][1]]
baselinecross=sum(dies[int(r['parent'])]!=dies[int(r['child'])] for r in csv.DictReader(open(case['native_tree'])))
inputs=[protocolfile,parent,*repairs,resourcefile,diefile,Path(case['native_tree']),Path(__file__)]
receipt=dict(status='combined_capacity_and_crossing_check',changed_nets=changed,overflow_nodes=overflow,crossings=cross,baseline_crossings=baselinecross,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},adopted=False,research_complete=False)
(D/'preflight.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert not overflow and cross<=baselinecross
with (D/'route.route_trees.csv').open('x') as stream:
    writer=csv.DictWriter(stream,fieldnames=['net_id','source','parent','child']);writer.writeheader();writer.writerows(rows)
native=Path(case['native_case']);route=D/'native.route'
commands=[[sys.executable,protocol['writer'],str(native/'circuit.route'),str(native/'rr_graph.xml'),case['connections'],str(D/'route.route_trees.csv'),str(route)]]
command=[sys.executable,protocol['validator'],'--vpr',protocol['vpr'],'--device','DieRouteSBScale3']
for flag,f in [('arch','architecture.xml'),('circuit','circuit.blif'),('net','circuit.net'),('place','circuit.place'),('rr-graph','rr_graph.xml')]:command+=['--'+flag,str(native/f)]
command+=['--route',str(route),'--channel-width','80','--work-dir',str(D/'native_validation'),'--baseline-wirelength',str(case['baseline_wirelength']),'--baseline-cpd-ns',str(case['baseline_cpd_ns'])]
commands.append(command)
(D/'launch.json').write_text(json.dumps(dict(commands=commands),indent=2)+'\n')
for i,command in enumerate(commands):
    with (D/('stage_'+str(i)+'.log')).open('x') as stream:rc=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT).returncode
    assert rc==0,rc
q=json.loads((D/'native_validation/validation.json').read_text());assert q['legal']
receipt.update(status='combined_repair_native_legal_requires_independent_review',wirelength=q['total_wirelength'],cpd_ns=q['critical_path_delay_ns'],joint_baseline_pass=q['total_wirelength']<=case['baseline_wirelength'] and q['critical_path_delay_ns']<=case['baseline_cpd_ns'])
(D/'result.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
