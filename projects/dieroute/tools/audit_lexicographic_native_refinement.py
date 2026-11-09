"""Independently audit private refinement acceptance chain and terminal reason."""
from pathlib import Path
from decimal import Decimal
import csv,hashlib,json,sys
from select_regressed_critical_connections import select
D=Path(sys.argv[1]).resolve()
def main():
 refs={}
 def sha(f):
  f=Path(f)
  if str(f) not in refs:
   h=hashlib.sha256()
   with f.open('rb') as s:
    for b in iter(lambda:s.read(1048576),b''):h.update(b)
   refs[str(f)]=h.hexdigest()
  return refs[str(f)]
 def observations(f):
  with Path(f).open() as s:return {int(v['task_id']):{k:int(x) for k,x in v.items()} for v in csv.DictReader(s)}
 p=json.loads((D/'protocol.json').read_text());m=json.loads((D/'manifest.json').read_text());assert m['status'].startswith('experiment_terminal_');assert len(m['stages'])<=p['maximum_stages']
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 baseline=observations(p['baseline_observations']);current=p['initial_state'];accepted=[]
 for record in m['stages']:
  assert record['input']==current
  stage=D/('stage_'+str(record['iteration']).zfill(3));oa=stage/'observation/independent_audit.json';selection=stage/'observation/selection.json';s=json.loads(selection.read_text());computed=select(baseline,observations(stage/'observation/parent/native_observations.csv'));assert computed==s['selected'];sha(oa);sha(selection)
  if computed:assert record['selected']==computed[0]
  if record['status']=='strict_private_improvement':
   eligible=[]
   for f in record['candidate_audits']:
    a=json.loads(Path(f).read_text());sha(f)
    c=a['checks'];ok=all(c[k] for k in ['native_legal','capacity','wirelength','modeled_transitions']) and (Decimal(str(a['cpd_ns'])),a['wirelength'],a['model_crossings'])<(Decimal(str(current['cpd_ns'])),current['wirelength'],current['model_crossings'])
    if ok:eligible.append((a,f))
   chosen_path=record['output']['audit'];chosen=next(a for a,f in eligible if f==chosen_path);best=min((a['cpd_ns'],a['wirelength'],a['model_crossings'],Path(f).parent.name) for a,f in eligible);assert (chosen['cpd_ns'],chosen['wirelength'],chosen['model_crossings'],Path(chosen_path).parent.name)==best
   output=record['output'];assert (output['cpd_ns'],output['wirelength'],output['model_crossings'])==(chosen['cpd_ns'],chosen['wirelength'],chosen['model_crossings']);qfile=Path(output['tree']).parent/'native_validation/validation.json';q=json.loads(qfile.read_text());assert q['legal'] and q['critical_path_delay_ns']==output['cpd_ns'];assert sha(output['route'])==q['inputs']['route_sha256'];sha(output['tree']);sha(qfile)
   accepted.append({'iteration':record['iteration'],'selected_task':record['selected']['task'],'cpd_ns':output['cpd_ns'],'wirelength':output['wirelength'],'model_crossings':output['model_crossings'],'stage_wall_ns':record['wall_ns']});current=output
  elif record['status']=='no_complete_exchange':
   gfile=stage/'exchange/manifest.json';g=json.loads(gfile.read_text());assert g['status']=='budgeted_exchange_arms_terminal_require_review' and not any(a.get('candidate_tree') for a in g['arms']);sha(gfile);assert record is m['stages'][-1]
  else:assert record['status'] in ['no_positive_worst_slack_regression','diagnosis_search_incomplete','no_strict_private_lexicographic_improvement']
 assert m['current_state']==current
 terminal=m['stages'][-1]['status'];assert terminal=='no_complete_exchange' if m['status']=='experiment_terminal_no_complete_exchange' else True
 final_audit=json.loads(Path(current['audit']).read_text());final_pass=all(final_audit['checks'].values())
 for f in [D/'protocol.json',D/'manifest.json',D/'launch_receipt.json',Path(__file__).resolve()]:sha(f)
 result={'status':'private_refinement_monotone_native_acceptance_and_stop_reviewed','termination':m['status'],'stages_attempted':len(m['stages']),'accepted_stages':accepted,'initial_cpd_ns':p['initial_state']['cpd_ns'],'final_private_cpd_ns':current['cpd_ns'],'final_original_baseline_joint_pass':final_pass,'final_private_state':current,'source_sha256':refs,'scope':'Frozenboundedposterior experiment,strictlexicographic(CPD,WL,crossing)improvementswithnativelegalityandoriginalWL/crossingcaps. Terminalincompleteexchange retained;originalbaselineCPDgate remains required. No originalreservedcohort replacement,generalization,FPGAclaimorfullresearchcompletion.','research_complete':False,'adopted':False}
 with (D/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','final_private_state']}))
if __name__=='__main__':main()
