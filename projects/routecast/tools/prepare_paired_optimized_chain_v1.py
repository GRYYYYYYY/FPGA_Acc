"""Generate fresh per-arm source copies with explicit experiment-only namespace mapping."""
import json,re
from pathlib import Path
T=Path(__file__).resolve().parent
families=[('adder_step1_from_inputs_checked',[6]),('adder_optimized_step2_checked',[10]),('adder_optimized_step3_checked',[11,12])]
plans=[]
for arm,mode in enumerate(('online','cold','cold','online')):
 mapping={}
 for step,(prefix,versions) in enumerate(families,1):
  for version in versions:
   pattern=re.compile(re.escape(prefix)+r'(?P<suffix>(?:_[a-z_]+)?)_v'+str(version)+r'_2026-10-09')
   mapping[pattern]=f'paired_optimized_chain_v1_arm{arm}_step{step}'
 steps=[]
 for step,(prefix,versions) in enumerate(families,1):
  commands=[];new=f'paired_optimized_chain_v1_arm{arm}_step{step}'
  if mode=='online':
   version=versions[0]
   sources=[f'trial_{prefix}_v{version}.py',f'verify_{prefix}_v{version}.py']
   sources += [f'run_{prefix}_{stage}_v{12 if step==3 and stage!="serialize" else version}.py' for stage in ('serialize','native','canonical','quality')]
   sources += [f'trial_{prefix}_wire_selection_v{version}.py',f'verify_{prefix}_wire_paths_v{version}.py']
   sources += [f'run_{prefix}_wire_{stage}_v{version}.py' for stage in ('serialize','native','canonical','quality')]
   report=f'{new}_wire_native_quality_v1_2026-10-09/verification.json';native=f'{new}_wire_native_v1_2026-10-09';selection=f'{new}_wire_paths_verification_v1_2026-10-09/selection.json'
  else:
   sources=[f'run_paired_checked_v1_arm1_{stage}.py' for stage in ('native','canonical','quality')]
   report=f'{new}_quality_v1_2026-10-09/verification.json';native=f'{new}_native_v1_2026-10-09';selection=None
  for index,source in enumerate(sources):
   text=(T/source).read_text()
   if mode=='online':
    for pattern,replacement in mapping.items():
     text=pattern.sub(lambda match:replacement+match['suffix']+'_v1_2026-10-09',text)
   else:
    for stage in ('native','canonical','quality'):
     text=text.replace(f'paired_checked_v1_arm1_{stage}_2026-10-09',f'{new}_{stage}_v1_2026-10-09')
    text=text.replace('range(3,4)',f'range({step},{step+1})').replace('step_3',f'step_{step}').replace('==3',f'=={step}').replace('step=3',f'step={step}')
    text=text.replace('4.87739',str([4.74739,4.87739,4.87739][step-1])).replace('2646',str([2430,2677,2646][step-1]))
   dst=T/f'run_{new}_stage{index:02d}.py';assert not dst.exists();compile(text,str(dst),'exec');dst.write_text(text);commands.append('tools/'+dst.name)
  steps.append(dict(step=step,commands=commands,report=report,native=native,selection=selection))
 plans.append(dict(arm=arm,mode=mode,steps=steps))
p=T/'paired_optimized_chain_manifest_v1.json';assert not p.exists();p.write_text(json.dumps(dict(plans=plans,spec='tools/optimized_three_step_cost_spec_v1.json',status='PREPARED_NOT_EXECUTED'),indent=2)+'\n')
print('Prepared',sum(len(s['commands']) for p in plans for s in p['steps']),'fresh subprocess scripts')
