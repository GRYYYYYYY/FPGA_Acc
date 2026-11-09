#!/usr/bin/env python3
"""Seal the complete 13-case execution plan before observing new outcomes."""
import json
from pathlib import Path
from tileplace_vpr import sha256

project=Path(__file__).resolve().parents[1]
exp=project/'experiments'
work=project/'work'
repo=project.parents[1]
design=json.loads((exp/'tileplace_new_cohort_design_2026-09-29.json').read_text())
dep=json.loads((exp/'tileplace_new_cohort_input_dependencies_2026-09-29.json').read_text())
basecmd=json.loads((work/'cohort_native_baseline_diffeq_2026-09-29/command.json').read_text())
packcmd=json.loads((work/'cohort_fresh_input_diffeq_2026-09-29/contract_command.json').read_text())
refcmd=json.loads((work/'cohort_fresh_input_diffeq_2026-09-29/refinement/command.json').read_text())
settings=json.loads((work/'cohort_input_smoke_diffeq_2026-09-29/launch.json').read_text())['settings']
timing_settings=json.loads((work/'cohort_timing_chain_diffeq_2026-09-29/launch.json').read_text())['settings']
root=exp/'tileplace_new_cohort_2026-09-29'
tools=repo/'projects/persistroute/tools'
files={v['path']:v for v in dep['files']}
def bind(path):
 path=Path(path).resolve();files[str(path)]={'path':str(path),'sha256':sha256(path)}
def updated(command,changes):
 result=command.copy()
 for flag,value in changes.items():result[result.index(flag)+1]=str(value)
 return result
def stage(name,cwd,command,env=None):return {'name':name,'cwd':str(cwd),'command':[str(x) for x in command],'env':env or {}}
cases=[]
for case in design['cases']:
 name=case['design'];circuit=Path(case['blif']);bind(circuit)
 folder=root/name;base=folder/'baseline';inputs=folder/'inputs'
 c=basecmd.copy();c[5]=str(circuit);c[c.index('--write_rr_graph')+1]=str(base/'rr_graph.xml')
 stages=[stage('baseline',base,c),stage('connections',inputs,['python3',tools/'vpr_route_connections.py',base/(name+'.route'),inputs/'connections.csv']),stage('pack',inputs,['python3',tools/'pack_hls_inputs.py',base/'rr_graph.xml',inputs/'connections.csv',inputs/'vpr_input','--base-cost-q','64']),stage('paths',inputs,['taskset','-c','31',work/'cohort_input_build_2026-09-29/persistroute_accelerated_cmodel',inputs/'vpr_input',inputs/name],settings),stage('proxy',inputs,['python3',project/'tools/paths_to_proxy_timing.py','--input-prefix',inputs/'vpr_input','--paths',inputs/(name+'.paths.csv'),'--output',inputs/'timing.input.csv'])]
 env=timing_settings.copy();env['PERSISTROUTE_VPR_CIRCUIT']=str(circuit)
 for key,suffix in [('NET',name+'.net'),('PLACE',name+'.place'),('ROUTE',name+'.route'),('RR_GRAPH','rr_graph.xml')]:env['PERSISTROUTE_VPR_'+key]=str(base/suffix)
 stages.append(stage('timing',inputs,['taskset','-c','31','python3',tools/'vpr_timing_analyzer.py','0',inputs/'timing.input.csv',inputs/'timing.output.csv'],env))
 packed=updated(packcmd,{'--netlist':base/(name+'.net'),'--place':base/(name+'.place'),'--rr-graph':base/'rr_graph.xml','--native-macros':base/'place_macros.echo','--connections':inputs/'connections.csv','--timing':inputs/'timing.output.csv','--output':inputs/'contract','--vpr-command':' '.join(c)})
 stages.append(stage('contract',inputs,packed));refs=[]
 for i in range(2):
  run=folder/f'run_{i:02d}'
  command=updated(refcmd,{'--contract':inputs/'contract','--input-place':base/(name+'.place'),'--baseline-closure':base/'baseline.json','--rr-graph':base/'rr_graph.xml','--netlist':base/(name+'.net'),'--circuit':circuit,'--work':run/'work','--output-place':run/'final.place','--report':run/'report.json','--timing-report':run/'timing.json'})
  refs.append(stage(f'refinement_{i:02d}',run,command))
 cases.append({'design':name,'stages':stages,'refinements':refs})
for path in [basecmd[3],basecmd[4],timing_settings['PERSISTROUTE_VPR_BIN'],work/'cohort_input_build_2026-09-29/persistroute_accelerated_cmodel',exp/'tileplace_feedback_rollback_implementation_2026-09-29.json',exp/'tileplace_v4_preregistration_2026-09-03.json',project/'tools/run_new_cohort.py',Path(__file__),project/'tools/audit_fixed_development.py',project/'tools/run_fixed_development.py',project/'tools/run_v4_timing_protocol.py',project/'tools/prepare_tileplace_v4_heldout_matrix.py',exp/'tileplace_candidate_exposure_review_2026-09-29.json']:
 bind(path)
manifest=json.loads((exp/'tileplace_feedback_rollback_implementation_2026-09-29.json').read_text())
for v in manifest['sources']:bind(v['path'])
for v in files.values():
 if sha256(Path(v['path']))!=v['sha256']:raise RuntimeError('dependency changed: '+v['path'])
protocol={'schema':'TILEPLACE_NEW_COHORT_EXECUTION_PROTOCOL_V1','output_root':str(root),'implementation_sha256':design['implementation_sha256'],'cases':cases,'files':list(files.values()),'failure_policy':'Retain every case failure, continue remaining cases, no retries or parameter changes; report completion denominator 13 and successful subset separately','repetitions':2,'path_generation_scope':'Completed CPU cmodel paths with fixed 30-iteration limit; static timing uses proxy edge delays, native VPR decides final QoR','scope':'Prospective source-sealed local logic-oriented cohort; exposure review has limitations, strict historical blindness and architecture generalization not established'}
p=exp/'tileplace_new_cohort_protocol_2026-09-29.json'
with p.open('x') as out:out.write(json.dumps(protocol,indent=2)+'\n')
print(str(p));print(sha256(p))
