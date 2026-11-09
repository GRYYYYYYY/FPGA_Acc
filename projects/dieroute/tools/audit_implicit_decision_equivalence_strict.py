"""Supplemental exact decision/validation comparison; never certify by exit code alone."""
from pathlib import Path
import copy,hashlib,json,sys
R=Path(__file__).resolve().parents[1]

def signature(step):
 out={k:v for k,v in step.items() if k not in ['wall_ns','native_evidence','validation']}
 if 'validation' in step:
  v=step['validation'];out['validation']={k:x for k,x in v.items() if k!='quality'}
  if 'quality' in v:
   q=v['quality'];out['validation']['quality']={k:q[k] for k in ['legal','total_wirelength','critical_path_delay_ns']}
 return out

def self_check():
 f=R/'work/native_instrumented_compound_repeat_20261016/sweep/ex5p/manifest.json';step=json.loads(f.read_text())['steps'][0]
 for kind in ['labels','accepted','native_delay','cap']:
  changed=copy.deepcopy(step)
  if kind=='labels':changed['searches'][0]['labels']+=1
  if kind=='accepted':changed['accepted']=not changed['accepted']
  if kind=='native_delay':changed['validation']['quality']['critical_path_delay_ns']+=0.001
  if kind=='cap':changed['net_crossing_budget']+=1
  assert signature(step)!=signature(changed),kind
 changed=copy.deepcopy(step);changed['wall_ns']+=1;changed['native_evidence']='different-output-directory'
 assert signature(step)==signature(changed)
 print('Four semantic corruptions detected; wall/output path excluded')

def main():
 D=R/'work/native_implicit_compound_repeat_v2_20261017';B=R/'work/native_instrumented_compound_repeat_20261016'
 state=json.loads((D/'manifest.json').read_text());assert state['status']=='three_case_compound_repeat_terminal_requires_independent_review'
 outcomes=[];refs={}
 def load(f):
  refs[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest();return json.loads(f.read_text())
 for label in ['ex5p','diffeq','alu4']:
  for stage in ['sweep','refresh']:
   a=load(B/stage/label/'manifest.json');b=load(D/stage/label/'manifest.json')
   left=[signature(s) for s in a['steps']];right=[signature(s) for s in b['steps']]
   mismatch=[i for i in range(max(len(left),len(right))) if i>=len(left) or i>=len(right) or left[i]!=right[i]]
   outcomes.append(dict(case=label,stage=stage,reference_steps=len(left),candidate_steps=len(right),equal=not mismatch,mismatch_ranks=mismatch))
 refs[str(Path(__file__))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 P=R/'work/implicit_strict_decision_equivalence_20261017';P.mkdir(exist_ok=False)
 result=dict(status='strict_decision_and_native_candidate_outcome_comparison_complete',all_equal=all(v['equal'] for v in outcomes),outcomes=outcomes,source_sha256=refs,scope='Exact recorded selection,budget,search counters,acceptance and candidate native quality/failure outcomes. Excludes wall time and output path identities; independent native connectivity replay remains required. all_equal false forbids equivalence claim.',research_complete=False,adopted=False)
 (P/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':
 if '--self-check' in sys.argv:self_check()
 else:main()
