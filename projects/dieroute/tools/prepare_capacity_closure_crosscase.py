"""Freeze serial cross-circuit native validation of the generic capacity closure."""
from pathlib import Path
import collections,csv,hashlib,json,mmap,struct
from capacity_restore_closure import restore_closure
R=Path(__file__).resolve().parents[1];D=R/'work/capacity_closure_crosscase_20261020'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):
 t=collections.defaultdict(dict)
 with p.open() as f:
  for row in csv.DictReader(f):t[int(row['net_id'])][int(row['child'])]=(int(row['parent']),int(row['source']))
 return t

def main():
 D.mkdir();cases=[]
 for circuit in ['apex2','frisc','elliptic']:
  label=circuit+'_20x16_cw160_seed1';folder=D/label;folder.mkdir();base=R/'work/width_coverage_roundtrip_20261017'/label;parent=R/'work/width_coverage_parents_20261018/parents'/label
  baseline=base/'native_tree.csv';candidate=parent/'route.route_trees.csv';b=load(baseline);c=load(candidate)
  changed=[n for n in b if b[n]!=c[n]];assert changed
  seed=min(changed,key=lambda n:(-len(set(b[n].items())^set(c[n].items())),n))
  def nodes(t):return {v for child,(par,src) in t.items() for v in [child,par,src]}
  bn={n:nodes(t) for n,t in b.items()};cn={n:nodes(t) for n,t in c.items()};used=set().union(*bn.values(),*cn.values());res=R/'work/width_coverage_native_costs_20261018'/label/'input.resources'
  with res.open('rb') as f:
   m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);cap={v:struct.unpack_from('<H',m,16*v+2)[0] for v in used};m.close()
  closure,waves=restore_closure(bn,cn,cap,{seed})
  review=R/('work/width_coverage_first_parent_review_20261018/protocol.json' if circuit=='apex2' else f'work/width_parent_review_{label}_20261018/protocol.json');steps=json.loads(review.read_text())['steps']
  commands={}
  for name,index in [('writer',2),('native',3)]:
   commands[name]=[s.replace(str(parent/'route.route_trees.csv'),'ARM_TREE').replace(str(parent/'native.route'),'ARM_DIRECTORY/native.route').replace(str(parent/'native_validation'),'ARM_DIRECTORY/native_validation') for s in steps[index]['command']]
  runner=folder/'run.py';runner.write_text('from pathlib import Path\nimport sys\nsys.path.insert(0,'+repr(str(R/'tools'))+')\nimport run_elliptic_critical_net_restore as job\njob.D=Path(__file__).resolve().parent\njob.main()\n')
  p={'status':'frozen_before_launch','baseline_tree':str(baseline),'candidate_tree':str(candidate),'arms':[{'name':'closure','nets':sorted(closure)}],'commands':commands,'selection_rule':'Largest baseline/candidate parent-child tree symmetric difference; tie lowest net ID. Fixed before new native outcome.','selected_seed':seed,'closure_waves':waves,'changed_parent_nets':len(changed),'retained_changed_nets':len(set(changed)-closure),'scope':'Posterior structural and native-quality stress probe, not critical-path-targeted optimization or heldout validation. Preserve original cohort and all failures.'}
  inputs={Path(s) for cmd in commands.values() for s in cmd if Path(s).is_file()};inputs.update([baseline,candidate,res,review,runner,R/'tools/capacity_restore_closure.py',R/'tools/run_elliptic_critical_net_restore.py',Path(__file__).resolve()]);p['source_sha256']={str(f):sha(f) for f in inputs};(folder/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');cases.append({'label':label,'command':['python3',str(runner)],'seed':seed,'closure_nets':len(closure),'retained_changed_nets':p['retained_changed_nets']})
 (D/'protocol.json').write_text(json.dumps({'status':'frozen_before_serial_launch','cases':cases,'source_sha256':{str(D/a['label']/'protocol.json'):sha(D/a['label']/'protocol.json') for a in cases},'scope':'Three posterior circuits,one fixed selection rule,serial native validation. No generalization or hardware claim.'},indent=2)+'\n');print(json.dumps(cases))
if __name__=='__main__':main()
