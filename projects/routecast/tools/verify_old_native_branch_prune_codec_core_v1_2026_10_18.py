"""Manual-tree branch pruning codec coverage and rejection tests."""
import json,sys,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from old_native_branch_prune_codec_v1 import scan,render
from native_route_ledger_import_compact import physical_paths
D=R/'experiments/old_native_branch_prune_codec_core_v1_2026-10-18';D.mkdir();kinds={0:'SOURCE',1:'OPIN',2:'CHANX',3:'IPIN',4:'SINK',5:'CHANY',6:'IPIN',7:'SINK',8:'CHANX',9:'IPIN',10:'SINK'};pins={4:1,7:2,10:3};walk=[(0,0),(1,1),(2,2),(3,3),(4,-1),(2,4),(5,5),(6,6),(7,-1),(1,7),(8,8),(9,9),(10,-1)];lines=[]
for node,switch in walk:
 kind=kinds[node];label='Class' if kind in ['SOURCE','SINK'] else 'Track' if kind.startswith('CHAN') else 'Pin';line=f'Node: {node} {kind} ({node},1,0) {label}: 0 Switch: {switch}'
 if kind=='SINK':line+=f' Net_pin_index: {pins[node]}'
 lines.append(line)
head=['Placement_File: design.place Placement_ID: SHA256:fixture','Array size: 15 x 3 logic blocks.','','Routing:',''];text='\n'.join(head+['Net 0 (unit)','']+lines+['','Net 1 (g): global net connecting:','Block fixture (#0) at (0,0,0), Pin class 0.'])+'\n';old=D/'old.route';old.write_text(text);paths=[((0,None),(1,0),(2,1),(3,2),(4,3)),((0,None),(1,0),(2,1),(5,4),(6,5),(7,6)),((0,None),(1,0),(8,7),(9,8),(10,9))];assert physical_paths(old)['unit']==paths;header,sections,templates=scan(text);assert header==head and set(sections)=={'unit'} and not any('Block ' in l for l in sections['unit']);checked=0
for mask in range(1,8):
 selected=[p for i,p in enumerate(paths) if mask&(1<<i)];out=D/f'subset_{mask}.route';out.write_text('\n'.join(head+['Net 0 (unit)','']+render(selected,templates['unit']))+'\n');assert physical_paths(out)['unit']==selected;assert {n for p in selected for n,_ in p}<={n for p in paths for n,_ in p};checked+=1
negative=0
for bad in [[],[paths[0],((0,None),(1,0),(8,7),(2,1),(6,5),(7,6))],[((0,None),(1,0),(2,1),(1,1),(4,3))]]:
 try:render(bad,templates['unit'])
 except ValueError:negative+=1
 else:raise AssertionError('invalid branch accepted')
t=dict(templates['unit']);t.pop((5,5))
try:render([paths[1]],t)
except KeyError:negative+=1
else:raise AssertionError('missing template accepted')
with (D/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=closure([Path(__file__)]),nonempty_subsets_exact_manual_paths=checked,invalid_cases_rejected=negative,global_Block_envelope_excluded=True,scope='Synthetic branch codec only, not an actual RRgraph/capacity/native importer proof. Real old paths must be separately admitted.'),f,indent=2)
print('PASS branch codec7subsets and4rejects',flush=True)
