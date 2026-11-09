"""Offline exact NET-union wire decomposition; cold never selects candidates."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_global_wire_deficit_2026-10-07';out.mkdir(exist_ok=False);vf=ROOT/'experiments/native_resume_branch_exchange_comparison_2026-10-07/verification.json';v=json.loads(vf.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings={str(vf):sha(vf),str(Path(__file__)):sha(Path(__file__))};rows=[]
for r in v['rows']:
 w=r['width'];i=1 if w==16 else 3;graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml';span={}
 for _,node in ET.iterparse(graph,events=('end',)):
  if node.tag=='node':
   if node.get('type') in ('CHANX','CHANY'):
    loc=node.find('loc');span[int(node.get('id'))]=1+int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))
   node.clear()
 candidate=ROOT/f'experiments/native_resume_branch_exchange_materialized_w{w}_m{i}_2026-10-07/canonical/design.route';cold=ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_cold_2026-10-07/canonical/design.route';wire=[];fanouts={}
 for file in (candidate,cold):
  ps=physical_paths(file);wire.append({name:sum(span.get(n,0) for n in {n for path in paths for n,_ in path}) for name,paths in ps.items() if paths});fanouts.update({name:len(paths) for name,paths in ps.items() if paths})
 assert set(wire[0])==set(wire[1]);assert sum(wire[0].values())==r['wirelength'] and sum(wire[1].values())==r['matched_cold_wire']
 nets=[dict(net=name,fanout=fanouts[name],candidate_wire=wire[0][name],cold_wire=wire[1][name],delta=wire[0][name]-wire[1][name],on_selected_worst_path=name in r['selected_net_names']) for name in wire[0]];positive=sorted([x for x in nets if x['delta']>0],key=lambda x:(-x['delta'],x['net']));negative=[x for x in nets if x['delta']<0]
 rows.append(dict(width=w,net_count=len(nets),global_wire_deficit=sum(x['delta'] for x in nets),positive_net_count=len(positive),negative_net_count=len(negative),positive_excess=sum(x['delta'] for x in positive),negative_savings=-sum(x['delta'] for x in negative),selected_net_delta=sum(x['delta'] for x in nets if x['on_selected_worst_path']),outside_selected_delta=sum(x['delta'] for x in nets if not x['on_selected_worst_path']),largest_excess=positive[:20],all_nets=nets))
 bindings.update({str(f):sha(f) for f in (graph,candidate,cold)});print(w,{k:rows[-1][k] for k in ('global_wire_deficit','positive_net_count','negative_net_count','positive_excess','negative_savings','selected_net_delta','outside_selected_delta')},flush=True)
assert all(sha(f)==h for f,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Offline diagnostic against matched cold; all NET channel unions exactly match native totals. Not permitted as online candidate selection or prediction feature. Not independent native FULL/STA; relies on existing complete proof.'),indent=2)+'\n')
