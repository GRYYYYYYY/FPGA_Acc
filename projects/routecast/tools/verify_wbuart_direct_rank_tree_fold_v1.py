"""Every real node independently rescored by complete affected-case rebuild."""
import json,sys,time
from array import array
from fractions import Fraction as F
from pathlib import Path
from direct_rank_domain_v1 import load_training_domains,training_objective
from direct_rank_rebuild_scan_v1 import scan
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def read(p):return json.loads(Path(p).read_text())
def decode(v):
 if isinstance(v,dict):
  if set(v)=={'numerator','denominator'}:return F(v['numerator'],v['denominator'])
  return {k:decode(x) for k,x in v.items()}
 if isinstance(v,list):return [decode(x) for x in v]
 return v

def main():
 ep=sys.argv[1];D=E/'wbuart_direct_rank_tree_v1_2026-10-20'/ep;fp=D/'predictions_frozen.json';frozen=read(fp);inputp=D/'input_frozen.json';inputs=read(inputp)
 for v in [frozen,inputs]:
  assert not v['heldout_labels_loaded'] and all(sha(p)==h for p,h in v['bindings'].items())
 model=decode(read(D/'model.json'));features={r['case']:r for r in read(E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json')['rows']};specs={r['case']:r['specification'] for r in read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons']};domains,_=load_training_domains(R,model,features,specs);X=[]
 assert model['depth_limit']==8 and model['minimum_child_rows']==64 and model['columns_count']==41
 for case,_ in domains:
  f=features[case];a=array('d');a.frombytes(Path(f['matrix']).read_bytes());X.extend(list(a[i*41:(i+1)*41]) for i in range(f['rows']))
 zero=[[0]*len(d.ids) for _,d in domains];one=[[1]*len(d.ids) for _,d in domains];v0=training_objective(domains,zero);v1=training_objective(domains,one);root=int(v1<v0);fields=one if root else zero;assert tuple(model['initial_objective'])==min(v0,v1);mapping=[(c,i) for c,(_,d) in enumerate(domains) for i in range(len(d.ids))];position=0;candidates=0;seen=set();tick=time.perf_counter()
 def visit(index,members,level,state):
  nonlocal position,candidates
  assert index not in seen;seen.add(index);n=model['nodes'][index];t=model['trace'][position];position+=1;assert t['node']==index and n['state']==state and n['rows']==len(members)
  current=training_objective(domains,fields);assert tuple(t['before'])==current
  result=scan(X,domains,fields,members,64) if level<8 and len(members)>=128 else {'after':current,'choice':None,'candidates':0};candidates+=result['candidates'];expected=None if t['choice'] is None else tuple(t['choice']);assert result['choice']==expected and result['after']==tuple(t['after']);print('REAL_NODE_REBUILD_VERIFIED',ep,index,len(members),result['candidates'],flush=True)
  if expected is None:assert n['feature']==-1 and n['left']==n['right']==-1;return
  f,threshold,a,b=expected;assert n['feature']==f and n['threshold']==threshold;left=[r for r in members if X[r][f]<=threshold];right=[r for r in members if X[r][f]>threshold];assert min(len(left),len(right))>=64
  for members2,bit in [(left,a),(right,b)]:
   for row in members2:c,i=mapping[row];fields[c][i]=bit
  visit(n['left'],left,level+1,a);visit(n['right'],right,level+1,b)
 visit(0,list(range(len(X))),0,root);assert position==len(model['trace'])==len(model['nodes']) and [p for field in fields for p in field]==model['points'] and tuple(model['final_objective'])==training_objective(domains,fields);count=0
 for r in frozen['rows']:
  assert r['case'] in model['test_cases'];f=features[r['case']];a=array('d');a.frombytes(Path(f['matrix']).read_bytes());got=[]
  for i in range(f['rows']):
   index=0
   while model['nodes'][index]['feature']!=-1:
    n=model['nodes'][index];index=n['right'] if a[i*41+n['feature']]>n['threshold'] else n['left']
   got.append(model['nodes'][index]['state'])
  assert got==read(r['point_counts']);count+=len(got)
 assert {r['case'] for r in frozen['rows']}==set(model['test_cases'])
 out=D/'independent_verification_v1.json';assert not out.exists();files=[fp,inputp,Path(__file__),R/'tools/direct_rank_rebuild_scan_v1.py',R/'tools/direct_rank_domain_v1.py',E/'direct_rank_rebuild_scan_contract_v1_2026-10-20/verification.json'];out.write_text(json.dumps({'status':'PASS_ALL_REAL_NODE_CANDIDATES_AND_HELDOUT_INFERENCE','nodes':len(seen),'candidate_objectives':candidates,'heldout_points':count,'seconds':time.perf_counter()-tick,'bindings':{str(p):sha(p) for p in files},'scope':'Same exact metric kernel qualified independently; every candidate rescored without sparse state. No heldout quality evaluated.'},indent=2)+'\n');print('REAL_DIRECT_RANK_FOLD_AUDIT_PASS',ep,len(seen),candidates,count,flush=True)
if __name__=='__main__':main()
