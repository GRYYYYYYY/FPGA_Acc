"""Native full-design validation of the private baseline-target diagnostic."""
import csv,json,subprocess,sys,hashlib
from pathlib import Path

root=Path('work/native_joint_budget_net_repair_v2_20261016')
protocol=json.loads((root/'protocol.json').read_text());case=protocol['cases'][0]
D=Path('work/native_serial_baseline_target_task'+sys.argv[1]+'_20261016').resolve()
probe=json.loads((D/'result.json').read_text());assert probe['answer']['complete']
original=Path('work/native_refreshed_baseline_target_task895_20261016/route.route_trees.csv')
rows=list(csv.DictReader(original.open()));net=probe['net_id'];source=next(r['source'] for r in rows if int(r['net_id'])==net)
rows=[r for r in rows if int(r['net_id'])!=net]
rows += [dict(net_id=net,source=source,parent=u,child=v) for v,u in probe['answer']['parent'].items()]
tree=D/'route.route_trees.csv'
with tree.open('x') as stream:
    writer=csv.DictWriter(stream,fieldnames=['net_id','source','parent','child']);writer.writeheader();writer.writerows(rows)
native=Path(case['native_case']);route=D/'native.route'
commands=[[sys.executable,protocol['writer'],str(native/'circuit.route'),str(native/'rr_graph.xml'),case['connections'],str(tree),str(route)]]
command=[sys.executable,protocol['validator'],'--vpr',protocol['vpr'],'--device','DieRouteSBScale3']
for flag,f in [('arch','architecture.xml'),('circuit','circuit.blif'),('net','circuit.net'),('place','circuit.place'),('rr-graph','rr_graph.xml')]:command+=['--'+flag,str(native/f)]
command+=['--route',str(route),'--channel-width','80','--work-dir',str(D/'native_validation'),'--baseline-wirelength',str(case['baseline_wirelength']),'--baseline-cpd-ns',str(case['baseline_cpd_ns'])]
commands.append(command)
(D/'native_launch.json').write_text(json.dumps(dict(commands=commands,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'result.json',original,tree,Path(__file__)]}),indent=2)+'\n')
for i,command in enumerate(commands):
    with (D/('validation_stage_'+str(i)+'.log')).open('x') as stream:
        rc=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT).returncode
    if rc:raise SystemExit(rc)
print((D/'native_validation/validation.json').read_text())
