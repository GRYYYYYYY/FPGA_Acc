"""Frozen first rejected net: test in-search crossing constraint on real graph."""
import collections,csv,hashlib,json,struct,xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from shared_tree_budget_repair import repair
R=Path(__file__).resolve().parents[1];P=R/'work/first_crossing_rejection_repair_20261015'
def main():
 refs={}
 def read(f):
  f=Path(f);data=f.read_bytes();refs[str(f)]=hashlib.sha256(data).hexdigest();return data
 def load(f):return json.loads(read(f))
 def rows(f):return list(csv.DictReader(read(f).decode().splitlines()))
 protocol=load(P/'protocol.json')
 for f,h in protocol['source_sha256'].items():read(f);assert refs[str(Path(f))]==h,f
 producer=R/'work/native_slack_guided_net_repair_v1_20261015';original=load(producer/'protocol.json')
 snapshot=load(R/'work/native_slack_repair_first_WL_milestone_20261015/manifest_snapshot.json');step=next(v for v in snapshot['steps'] if v['status']=='baseline_crossing_limit_rejected');net=step['net']
 before=[v for v in snapshot['steps'] if v['rank']<step['rank'] and v.get('accepted')];directory=Path(before[-1]['native_evidence']) if before else producer/'ex5p/initial'
 case=next(v for v in original['cases'] if v['label']=='ex5p');quality=load(directory/'native_validation/validation.json');observation={int(v['task_id']):v for v in rows(directory/'observation.output.csv')}
 nodes=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.nodes')));edges=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.edges')));resources=list(struct.iter_unpack('<HHHHII',read(case['input_prefix']+'.resources')));dies=[v[0] for v in struct.iter_unpack('<H',read(case['topology_prefix']+'.node_die'))]
 all_rows=rows(directory/'route.route_trees.csv');owners=[set() for _ in nodes];old_parent={};fixed_cross=0
 for row in all_rows:
  n=int(row['net_id']);v=int(row['child']);u=int(row['parent'])
  if n==net:old_parent[v]=u
  else:owners[v].add(n);fixed_cross+=dies[v]!=dies[u]
 allowance=snapshot['baseline_crossings']-fixed_cross;assert allowance>=0
 allowed=[len(values)<resources[v][1] for v,values in enumerate(owners)];length=[0]*len(nodes);rr=Path(case['native_case'])/'rr_graph.xml';read(rr)
 for _,e in ET.iterparse(rr,events=('end',)):
  if e.tag=='node':
   a=e.attrib;l=e.find('loc')
   if a['type'] in ['CHANX','CHANY'] and a.get('direction')!='NONE':length[int(a['id'])]=1+int(l.attrib['xhigh'])-int(l.attrib['xlow'])+int(l.attrib['yhigh'])-int(l.attrib['ylow'])
   e.clear()
  elif e.tag=='edge':e.clear()
 connections=[v for v in rows(case['connections']) if int(v['net_id'])==net];source=int(connections[0]['source']);limit=int(max(Decimal(str(case['baseline_cpd_ns'])),Decimal(str(quality['critical_path_delay_ns'])))*Decimal(1000))
 ordered=sorted(connections,key=lambda v:(-int(observation[int(v['id'])]['criticality_q']),int(v['id'])))
 tasks=[dict(id=int(v['id']),sink=int(v['sink']),max_hops=int(v['max_hops']),delay_budget=max(0,int(observation[int(v['id'])]['delay_ps'])+limit+int(observation[int(v['id'])]['slack_ps']))) for v in ordered]
 result=repair(nodes,edges,allowed,length,dies,source,tasks,allowance,maximum_labels=2097152)
 if result['complete']:
  parent=result['parent'];assert result['crossings']+fixed_cross<=snapshot['baseline_crossings']
  for task in tasks:
   path=result['paths'][task['id']];assert path[-1]==task['sink'] and len(path)<=task['max_hops'];cost=0;u=source
   for v in path:
    assert len(owners[v])+1<=resources[v][1];start,count,_=nodes[u];cost+=min(w for dst,_,w in edges[start:start+count] if dst==v);u=v
   assert cost<=task['delay_budget']
  with (P/'candidate.route_trees.csv').open('w') as stream:
   writer=csv.DictWriter(stream,fieldnames=['net_id','source','parent','child']);writer.writeheader();writer.writerows(row for row in all_rows if int(row['net_id'])!=net);writer.writerows(dict(net_id=net,source=source,parent=u,child=v) for v,u in sorted(parent.items()))
 for f in [Path(__file__).resolve(),Path(__file__).with_name('shared_tree_budget_repair.py'),Path(__file__).with_name('delay_crossing_bounded_wire_search.py')]:read(f)
 report=dict(status='first_crossing_rejected_net_joint_constraint_probe_complete',rank=step['rank'],net=net,parent_native_directory=str(directory),crossing_allowance=allowance,fixed_other_crossings=fixed_cross,
  old_net_crossings=sum(dies[v]!=dies[u] for v,u in old_parent.items()),old_native_wire=sum(length[v] for v in old_parent),result=result,source_sha256=refs,adopted=False,research_complete=False,scope='First cross-limit rejection in immutable milestone snapshot,not chosen for outcome. Fixed earlier private state;one greedy sinkorder and2Mlabels. No nativeSTA/publication/adoption;currentlivecohort untouched.')
 (P/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(net=net,status=result['status'],cross_budget=allowance,old_wire=report['old_native_wire'],new_wire=result.get('wire'),new_crossings=result.get('crossings'))),flush=True)
if __name__=='__main__':main()
