"""Invocation path membership, owner-count/occupancy reconciliation, read-only transition."""
import json,csv,hashlib,sys
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from zero_rc_budget_certificate_graph_v1 import load_graph
D=R/'experiments/prospective_external_family_native_growth_owner_observer_v1_2026-10-19';G=R/'experiments/prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/rr_graph.xml'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def nodeids(q):return {int(x.split(':')[0]) for x in q['path_sink_to_source_node_switch_occ_hist_pres'].strip(',').split(',') if x}
def main():
 v=read(D/'trace_verification_v1.json');assert all(sha(p)==h for p,h in v['bindings'].items());g=load_graph(G);bindings={str(D/'trace_verification_v1.json'):sha(D/'trace_verification_v1.json'),str(G):sha(G),str(Path(__file__).resolve()):sha(__file__)};results=[];selected=[]
 for i in (1,2,3):
  for arm in ('cold','seed'):
   case=f'w160/episode_{i:02d}/{arm}';out=D/case/'native';p=out/'growth_owners.tsv';groups={}
   for line in p.open():
    x=line.rstrip('\n').split('\t');kind,phase,it,order,net=x[:5];key=(phase,int(it),int(net));row=groups.setdefault(key,dict(order=int(order),nodes={},owners=defaultdict(dict)));assert row['order']==int(order)
    if kind=='Q':assert 'pin' not in row;row.update(pin=int(x[5]),delay=float(x[6]),criticality=float(x[7]),pres=float(x[8]))
    elif kind=='N':node=int(x[5]);assert node not in row['nodes'];row['nodes'][node]=dict(occ=int(x[6]),cap=int(x[7]),history=float(x[8]),present=float(x[9]));assert int(x[7])==g['caps'][node]
    elif kind=='O':node,owner=int(x[5]),int(x[6]);assert owner not in row['owners'][node];row['owners'][node][owner]=x[7]
    else:raise ValueError(kind)
   assert len(groups)==18
   tp=out/'target_iterations.tsv';traces={}
   for q in csv.DictReader(tp.open(),delimiter='\t'):
    if int(q['iteration']) in (36,38,50) and int(q['net']) in (83,90,368):traces[(q['phase'],int(q['iteration']),int(q['net']),int(q['pin']))]=q
   resources=residuals=0
   for it in (36,38,50):
    for net,pin in ((83,40),(90,19),(368,2)):
     before,after=groups['B',it,net],groups['A',it,net];old,new=traces['BEFORE',it,net,pin],traces['AFTER',it,net,pin];oldnodes,newnodes=nodeids(old),nodeids(new);assert set(before['nodes'])==oldnodes;assert set(after['nodes'])==oldnodes|newnodes;assert before['delay']==float(old['delay_s']) and after['delay']==float(new['delay_s']);assert before['criticality']==float(old['criticality'])==after['criticality']
     for phase,row in [('B',before),('A',after)]:
      for node,n in row['nodes'].items():
       owners=row['owners'][node];assert n['occ']==len(owners),(case,phase,it,net,node,n,owners);resources+=1
     for node in oldnodes:
      a,b=before['nodes'][node],after['nodes'][node];oa,ob=before['owners'][node],after['owners'][node];assert a['history']==b['history'];assert {k:v for k,v in oa.items() if k!=net}=={k:v for k,v in ob.items() if k!=net};assert b['occ']-a['occ']==int(net in ob)-int(net in oa)
     wanted={1:(50,90),2:(36,83),3:(38,368)}[i]
     if (it,net)==wanted:
      over=[]
      for node,n in before['nodes'].items():
       if n['occ']>n['cap']:over.append(dict(node=node,type=g['types'][node],**n,owners=before['owners'][node],after=after['nodes'][node],after_owners=after['owners'][node]))
      selected.append(dict(case=case,iteration=it,net=net,pin=pin,order=before['order'],before_delay_ns=before['delay']*1e9,after_delay_ns=after['delay']*1e9,input_raw_criticality=before['criticality'],oldpath_overuse_at_actual_call=over))
   bindings[str(p)]=sha(p);bindings[str(tp)]=sha(tp);results.append(dict(case=case,invocation_snapshots=len(groups),resources_reconciled=resources,owner_count_occupancy_residuals=0,non_target_owners_invariant_on_old_path=True));print(json.dumps(results[-1]),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'owner_verification_v1.json').write_text(json.dumps(dict(status='ALL6_INVOCATION_SNAPSHOTS_PATH_AND_OWNER_OCCUPANCY_RECONCILED',rows=results,selected_growth_invocations=selected,bindings=bindings,limitations='O rows are native all-tree census; count/transition reconciliation checked, but not independent full owner tree export replay. Pre-call before own ripup; not inner search frontier. No causality or mechanism acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
