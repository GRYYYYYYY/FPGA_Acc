"""Frozen, bounded native-guided private refinement; never declares research complete."""
from pathlib import Path
from decimal import Decimal
import csv,fcntl,hashlib,json,os,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[1];D=Path(sys.argv[1]).resolve()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def freeze(path,value):
 with Path(path).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def run(command,log):
 with Path(log).open('x') as f:subprocess.run(command,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True)
def bind(files):return {str(Path(f).resolve()):sha(f) for f in files}
def wrapper(directory,module):
 script=directory/'run.py';script.write_text('from pathlib import Path\nimport sys\nsys.path.insert(0,'+repr(str(R/'tools'))+')\nimport '+module+' as job\njob.D=Path(__file__).resolve().parent\njob.main()\n');return script

def main():
 lock=(D/'owner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not (D/'manifest.json').exists(),'No implicit replay'
 p=json.loads((D/'protocol.json').read_text())
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 state={'status':'private_refinement_running','pid':os.getpid(),'stages':[],'research_complete':False,'adopted':False}
 def save(**values):
  state.update(values);tmp=D/'manifest.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(D/'manifest.json')
 current=dict(p['initial_state']);seen={(sha(current['tree']),int(t)) for t in p.get('initial_exhausted_tasks',[])};save(current_state=current)
 try:
  for iteration in range(1,p['maximum_stages']+1):
   stage=D/('stage_'+str(iteration).zfill(3));stage.mkdir();record={'iteration':iteration,'input':current.copy()};state['stages'].append(record);started=time.monotonic_ns();save(active_stage=iteration,phase='native_observation')
   observation=stage/'observation';observation.mkdir();(observation/'parent').mkdir();op=json.loads(Path(p['observation_template']).read_text());case=next(c for c in op['cases'] if c['name']=='parent');case['command'][case['command'].index('--route')+1]=current['route'];case['command'][case['command'].index('--work-dir')+1]=str(observation/'parent/native_validation');case['environment']['PERSISTROUTE_VPR_TIMING_OUTPUT']=str(observation/'parent/native_observations.csv');op.update(cases=[case],parent_tree=current['tree'],scope='Read-only currentprivate state refresh,originalbaselineunchanged.')
   files={Path(s) for s in case['command'] if Path(s).is_file()};files.update([Path(case['environment']['PERSISTROUTE_VPR_TIMING_INPUT']),Path(current['tree']),Path(p['observation_template']),R/'tools/run_native_RC_observations.py']);op['source_sha256']=bind(files);freeze(observation/'protocol.json',op)
   run(['python3',str(R/'tools/run_native_RC_observations.py'),str(observation)],stage/'observe.log');run(['python3',str(R/'tools/audit_native_RC_observations.py'),str(observation)],stage/'observe_audit.log');selection=observation/'selection.json';run(['python3',str(R/'tools/select_regressed_critical_connections.py'),p['baseline_observations'],str(observation/'parent/native_observations.csv'),str(selection)],stage/'select.log');selected=json.loads(selection.read_text())['selected']
   if not selected:record['status']='no_positive_worst_slack_regression';save(status='experiment_terminal_no_selected_regression');return
   available=[v for v in selected if (sha(current['tree']),v['task']) not in seen]
   if not available:record['status']='no_untried_regressed_critical_connection';save(status='experiment_terminal_all_selected_tasks_exhausted');return
   task=available[0]['task'];key=(sha(current['tree']),task);assert key not in seen;seen.add(key);record['selected']=available[0];save(phase='blocker_diagnosis')
   diagnosis=stage/'diagnosis';diagnosis.mkdir();dp=json.loads(Path(p['diagnosis_template']).read_text());dp.update(candidate_tree=current['tree'],critical_tasks=[task],scope='Automaticallyselected currentcriticalpath blockers;privatecapacityinvaliddiagnosticpaths only.');script=wrapper(diagnosis,'run_elliptic_blocked_critical_paths');dp['source_sha256'].update(bind([Path(current['tree']),selection,script]));freeze(diagnosis/'protocol.json',dp);run(['python3',str(script)],stage/'diagnose.log');paths=json.loads((diagnosis/'result.json').read_text())['paths'];path=next(a for a in paths if a['task']==task)
   if path['status']!='optimal_additive_delay_path':record['status']='diagnosis_search_incomplete';save(status='experiment_terminal_diagnosis_incomplete');return
   exchange=stage/'exchange';exchange.mkdir();ep=json.loads(Path(p['exchange_template']).read_text());orders=[path['foreign_conflicting_nets']]
   if orders[0]!=list(reversed(orders[0])):orders.append(list(reversed(orders[0])))
   ep.update(candidate_tree=current['tree'],native_parent_observations=str(observation/'parent/native_observations.csv'),blocked_paths=str(diagnosis/'result.json'),arms=[{'name':'task'+str(task)+('_forward' if i==0 else '_reverse'),'task':task,'order':order} for i,order in enumerate(orders)],scope='Frozenpooled/unboxed/dualcap/8rollbackpolicy,oneautomaticallyselectedtask thisstage;originalbaselineunchanged.')
   ep['connection_ceiling_cpd_ps']=next(csv.DictReader((observation/'parent/native_observations.csv').open()))['critical_path_delay_ps'];ep['connection_ceiling_cpd_ps']=int(ep['connection_ceiling_cpd_ps']);ep['blockers_first']=True;ep['source_sha256'].update(bind([Path(current['tree']),observation/'parent/native_observations.csv',diagnosis/'result.json',selection]));freeze(exchange/'protocol.json',ep);save(phase='exchange_search');run(['python3',str(R/'tools/run_ranked_objective_sink_exchange.py'),str(exchange)],stage/'search.log');generated=json.loads((exchange/'manifest.json').read_text());complete=[a for a in generated['arms'] if a.get('candidate_tree')]
   if not complete:record['status']='no_complete_exchange';save(phase='try_next_selected_task');continue
   save(phase='native_candidate_validation');run(['python3',str(R/'tools/prepare_native_exchange_validation.py'),str(exchange),p['native_template']],stage/'native_prepare.log');queue=exchange/'native_queue';receipt=json.loads((queue/'launch_receipt.json').read_text());pid=receipt['pid']
   while True:
    try:q=json.loads((queue/'manifest.json').read_text())
    except (OSError,json.JSONDecodeError):q={}
    if q.get('status')=='all_native_candidates_terminal_require_independent_review':break
    if q.get('status')=='candidate_supervision_failed_requires_review':raise RuntimeError('Native queue failed')
    proc=Path('/proc')/str(pid)/'cmdline'
    if not proc.exists():raise RuntimeError('Native owner missing before terminal receipt; no restart')
    assert str(queue/'supervise.py').encode() in proc.read_bytes(),'Native owner identity mismatch';time.sleep(3)
   accepted=[];record['candidate_audits']=[]
   for case in json.loads((queue/'protocol.json').read_text())['cases']:
    arm=case['net'];run(['python3',str(R/'tools/audit_protocol_budgeted_exchange_native_v3.py'),str(exchange),arm],stage/('audit_'+arm+'.log'));afile=queue/arm/'independent_native_audit.json';audit=json.loads(afile.read_text());record['candidate_audits'].append(str(afile));checks=audit['checks'];eligible=all(checks[k] for k in ['native_legal','capacity','wirelength','modeled_transitions']) and (Decimal(str(audit['cpd_ns'])),audit['wirelength'],audit['model_crossings'])<(Decimal(str(current['cpd_ns'])),current['wirelength'],current['model_crossings'])
    if eligible:accepted.append((audit,afile,arm))
   if not accepted:record['status']='no_strict_private_lexicographic_improvement';save(phase='try_next_selected_task');continue
   audit,afile,arm=min(accepted,key=lambda v:(v[0]['cpd_ns'],v[0]['wirelength'],v[0]['model_crossings'],v[2]));evaluated=queue/arm/'candidate';current={'tree':str(evaluated/'route.route_trees.csv'),'route':str(evaluated/'native.route'),'cpd_ns':audit['cpd_ns'],'wirelength':audit['wirelength'],'model_crossings':audit['model_crossings'],'audit':str(afile)};record.update(status='strict_private_improvement',output=current.copy(),wall_ns=time.monotonic_ns()-started);save(current_state=current,phase='stage_complete')
   if all(audit['checks'].values()):save(status='experiment_terminal_original_baseline_joint_quality_pass');return
  save(status='experiment_terminal_frozen_stage_budget_exhausted')
 except BaseException:
  save(status='experiment_error_requires_review',error=traceback.format_exc());raise
if __name__=='__main__':main()
