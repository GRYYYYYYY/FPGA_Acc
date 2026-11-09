"""Differential rejection contracts for original and indexed serializers."""
import copy,json,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from serialize_whole_net_subset_v1 import serialize_subset as original
from serialize_whole_net_subset_pin_index_v2 import serialize_subset as indexed
D=R/'experiments/seed_serializer_rejections_v1_2026-10-08';D.mkdir()
class Inventory:
 def __init__(self,p):
  self.path=p;self.digest=sha(p)
  self.nodes={i:(kind,dict(xlow=str(i),xhigh=str(i),ylow='0',yhigh='0',layer='0',ptc='0')) for i,kind in enumerate(['SOURCE','CHANX','SINK'])}
  self.edges=[(0,1,0),(1,2,0)]
 def validate(self,p,d):assert Path(p)==self.path and d==self.digest and sha(p)==d
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp);g=t/'graph';g.write_text('fixture graph');inv=Inventory(g)
 ep=dict(inputs=dict(graph=dict(path=str(g))),graph_sha256=sha(g),connections=[dict(connection_id=7,net_id=0,source=0,sink=2)],net_names={'0':'n'})
 pins=[dict(index=0,x=0,y=0,layer=0,**{'class':0}),dict(index=1,x=2,y=0,layer=0,**{'class':0})]
 identity=dict(name='n',net_id=0,pins=pins)
 candidate=dict(records=[dict(**ep['connections'][0],answer=dict(physical_edge_ids=[0,1]))])
 place=t/'place';place.write_text('Placement\nArray size: 3 x 1\n');rows=[]
 for case in ['valid','duplicate_source','duplicate_sink_site','missing_sink','wrong_source_site','duplicate_connection','wrong_endpoint','cyclic_path','incomplete_path']:
  e=copy.deepcopy(ep);n=copy.deepcopy(identity);c=copy.deepcopy(candidate)
  if case=='duplicate_source':n['pins'].append(copy.deepcopy(pins[0]))
  if case=='duplicate_sink_site':n['pins'].append(dict(pins[1],index=2))
  if case=='missing_sink':n['pins']=n['pins'][:1]
  if case=='wrong_source_site':n['pins'][0]['x']=9
  if case=='duplicate_connection':c['records']*=2
  if case=='wrong_endpoint':c['records'][0]['sink']=1
  if case=='cyclic_path':c['records'][0]['answer']['physical_edge_ids']=[0,0]
  if case=='incomplete_path':c['records'][0]['answer']['physical_edge_ids']=[0]
  ef=t/'ep.json';ef.write_text(json.dumps(e));nf=t/'identity.jsonl';nf.write_text(json.dumps(n)+'\n')
  outcomes=[]
  for fn in [original,indexed]:
   try:outcomes.append(('PASS',fn(c,ef,nf,place,inv)))
   except ValueError as error:outcomes.append(('REJECT',str(error)))
  assert outcomes[0]==outcomes[1],(case,outcomes)
  assert outcomes[0][0]==('PASS' if case=='valid' else 'REJECT'),(case,outcomes)
  rows.append(dict(case=case,status=outcomes[0][0]))
result=dict(bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/serialize_whole_net_subset_v1.py',R/'tools/serialize_whole_net_subset_pin_index_v2.py']},all_differential_contracts_pass=True,rows=rows,scope='Crafted rejection contracts complement full MMC parity; no physical runtime or performance claim.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(rows),'differential contracts')
