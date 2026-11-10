#!/usr/bin/env python3
"""Prepare isolated sources and frozen inputs. Does not run the pilot."""
from pathlib import Path
import json,hashlib,shutil,difflib,os,platform,subprocess
D=Path(__file__).resolve().parent
ROOT=Path('/inspire/hdd/project/siinovarch-fpga-chip/guoruiyuan-253208540291/FPGA_Acc')
TP=ROOT/'projects/tileplace'; EXP=TP/'experiments'
BASE='b32afa4303a5574dde7171b4ae6e3d07aeb8a06c'; HIST='2fa6e2324a971d8489bba12d49115f91d0a56874c0ee5200224d72e4f8a9f689'
def dump(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
a=json.loads((EXP/'implementation_sources'/HIST/'archive.json').read_text())
patch=[]
for row in a['sources']:
 f=TP/'tools'/row['name']; assert sha(f)==row['sha256'];shutil.copyfile(f,D/'source'/f.name)
p=D/'source/tileplace_v2.py'; old=p.read_text();s=old.replace('import argparse','import os\nimport time\nimport argparse',1)
# This module has no argparse import; insert after future import instead.
if 'import os\n' not in s:s=s.replace('from __future__ import annotations','from __future__ import annotations\n\nimport os\nimport time',1)
s=s.replace('        self.pressure_q16 = pressure_q16 or {}','        self.pressure_prefix = os.environ.get("TILEPLACE_PRESSURE_PREFIX", "1") == "1"\n        self.profile = {"index_build_s": 0.0, "index_builds": 0, "cache_hits": 0, "cache_misses": 0, "cache_invalidations": 0, "path_queries": 0}\n        self.pressure_q16 = pressure_q16 or {}',1)
s=s.replace('        pressure_snapshot = MappingProxyType(dict(values))','        build_start = time.perf_counter()\n        pressure_snapshot = MappingProxyType(dict(values))\n        if not self.pressure_prefix:\n            self._pressure_q16 = pressure_snapshot\n            self._horizontal_pressure = self._vertical_pressure = {}\n            if hasattr(self, "_net_cost_cache"):\n                self._net_cost_cache.clear()\n                self.profile["cache_invalidations"] += 1\n            self.profile["index_build_s"] += time.perf_counter() - build_start\n            self.profile["index_builds"] += 1\n            return',1)
s=s.replace('        self._vertical_pressure = vertical_prefix','        self._vertical_pressure = vertical_prefix\n        self.profile["index_build_s"] += time.perf_counter() - build_start\n        self.profile["index_builds"] += 1',1)
s=s.replace('            self._net_cost_cache.clear()\n\n    @staticmethod','            self._net_cost_cache.clear()\n            self.profile["cache_invalidations"] += 1\n\n    @staticmethod',1)
off=(EXP/'implementation_sources/dc0d7b31b411a03057597d4f215f46cfb4f29a7a2fb1a265185ca9d321996f6d/tileplace_v2.py').read_text();i=off.index('    def _path_pressure');off=off[i:off.index('    def _connection_congestion',i)].replace('def _path_pressure(', 'def _path_pressure_edgewalk(')
s=s.replace('    def _path_pressure(',off+'    def _path_pressure(',1)
start=s.index('    def _path_pressure(');pos=s.index('        x, y = a',start);s=s[:pos]+'        self.profile["path_queries"] += 1\n        if not self.pressure_prefix:\n            return self._path_pressure_edgewalk(a, b, horizontal_first)\n'+s[pos:]
s=s.replace('        if cached is not None:\n            return cached','        if cached is not None:\n            self.profile["cache_hits"] += 1\n            return cached\n        self.profile["cache_misses"] += 1',1)
# Count invalidation at transaction apply/rollback, not alter cache policy.
s=s.replace('        self._net_cost_cache.clear()\n', '        self._net_cost_cache.clear()\n',1)
s=s.replace('    def update_timing_feedback(', '    def update_timing_feedback(',1)
s=s.replace('                self.profile["cache_invalidations"] += 1\n', '').replace('            self.profile["cache_invalidations"] += 1\n', '')
s=s.replace('self._net_cost_cache.clear()', 'self._invalidate_cost_cache()')
s=s.replace('    @staticmethod\n    def _segment_pressure', '    def _invalidate_cost_cache(self):\n        t = time.perf_counter()\n        self._net_cost_cache.clear()\n        self.profile["cache_invalidations"] += 1\n        self.profile["cache_invalidation_s"] = self.profile.get("cache_invalidation_s", 0.0) + time.perf_counter() - t\n\n    @staticmethod\n    def _segment_pressure', 1)
p.write_text(s);patch.extend(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='original/tileplace_v2.py' ,tofile='source/tileplace_v2.py'))
p=D/'source/run_tileplace_v2.py';old=p.read_text();s=old.replace('"search_other_wall_s": search_wall_s - sum(totals.values()),','"search_other_wall_s": search_wall_s - sum(totals.values()),\n                "pressure_prefix": engine.pressure_prefix,\n                "mechanism_profile": engine.profile,',1);p.write_text(s);patch.extend(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='original/run_tileplace_v2.py',tofile='source/run_tileplace_v2.py'));(D/'instrumentation.patch').write_text(''.join(patch))
shutil.copyfile(TP/'tools/run_v4_timing_protocol.py',D/'source/run_v4_timing_protocol.py')
sys_path=str(D/'source');import sys;sys.path.insert(0,sys_path)
from tileplace_provenance import source_snapshot
from prepare_timing_feedback import parser_identity
impl=source_snapshot([D/'source'/r['name'] for r in a['sources']],parser_identity());dump(D/'implementation.json',impl)
fixed=json.loads((EXP/'tileplace_fixed_development_protocol_2026-09-29.json').read_text())
cases=[]; files={}
def record(f,role):
 p=Path(f).resolve()
 if str(p) in files:return
 files[str(p)]={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'role':role,'rehashed_this_round':True,'uploaded':False}
for case in ['diffeq','clma','spla']:
 c=next(x['command'] for x in fixed['cases'] if x['case']==case) if case!='spla' else json.loads((EXP/'tileplace_new_cohort_2026-09-29/spla/run_00/refinement_00.command.json').read_text())
 c=[x.replace('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/',str(ROOT)+'/') for x in c]
 c[c.index('--implementation-manifest')+1]=str(D/'implementation.json');c[4]=str(D/'source/run_tileplace_v2.py')
 for flag,name in [('--work','work'),('--output-place','final.place'),('--report','report.json'),('--timing-report','timing.json')]:c[c.index(flag)+1]='{run_dir}/'+name
 for flag in ['--input-place','--baseline-closure','--rr-graph','--preregistration','--vpr','--architecture','--circuit','--netlist','--implementation-manifest']:record(c[c.index(flag)+1],flag)
 contract=Path(c[c.index('--contract')+1]);m=json.loads((contract/'manifest.json').read_text());record(contract/'manifest.json','contract_manifest')
 for n in m['outputs']:record(contract/n,'contract_output')
 for x in m['inputs'].values():record(x['path'],'contract_input')
 baseline=json.loads(Path(c[c.index('--baseline-closure')+1]).read_text())
 for k in ['route','timing_setup_report']:
  if k in baseline['outputs']:record(baseline['outputs'][k]['path'],'initial_'+k)
 if 'timing_setup_report' not in baseline['outputs']:record(Path(baseline['outputs']['stdout']['path']).parent/'report_timing.setup.rpt','initial_timing')
 cases.append({'case':case,'exposure':'development_previously_exposed','command_template':c,'seed':1,'channel_width':200})
for p in (D/'source').glob('*.py'):record(p,'source')
protocol={'schema':'PHASE2A_BOUNDED_DIAGNOSTIC_V1','source_baseline_commit':BASE,'accepted_audit_commit':'ec1c5634ea9cbb6f8baf55e94c75cff988bb7b16','historical_source_commit':'unknown','historical_implementation_sha256':HIST,'implementation':impl,'arms':{'A':'TILEPLACE_PRESSURE_PREFIX=1','B':'TILEPLACE_PRESSURE_PREFIX=0'},'only_algorithm_difference':'sparse integer pressure-prefix vs historical per-edge pressure sum; same immutable snapshots, cache invalidation, parser/controller/feedback/acceptance','cases':cases,'run_timeout_s':900,'pilot_wall_budget_s':10800,'cpu':31,'numa_policy':'CPU31 pinned; default first-touch on CPU31 NUMA node; no forced membind; all children inherit affinity','environment':{'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONHASHSEED':'0','PYTHONDONTWRITEBYTECODE':'1'},'schedule':[],'output_root':str(ROOT.parent/'FPGA_Acc_PHASE2A_RUNS_20261110'),'stop_rules':{'failure_or_timeout':'mark remaining runs of that case not_started, no retry; continue other frozen cases within budget','exactness_mismatch':'stop all pilot runs and performance claims immediately','budget':'stop owned group at min(run deadline,pilot deadline); no new pilot start','no_zero_comparison_pass':True},'correctness':['candidate placement SHA','all transaction integer costs','phases','decision/reason','numerical feedback identities and parser','final placement SHA','native legal and exact CPD/WL','nonzero trials'],'timing':{'authoritative':'outer time.monotonic_ns before Popen to return, includes Python startup, all necessary checks, rejected trials, native VPR, feedback, writing','nested':'oracle_driver contains native VPR; index_build_s is nested in preparation/feedback; never add child to parent','cold_deployment':'new pilot uses frozen prepared inputs; historical prep stages retained separately, NOT measured new cold deployment and not free; no divide-by-two of cohort aggregate','offline_audit':'signature comparison and compact evidence packaging timed separately; not search acceptance work'},'acceptance':'native legal; WL<=1.005*original baseline; CPD improvement >=0.001ns or identical CPD and smaller WL','baseline_smoke':{'case':'diffeq','max_runs':1,'timeout_s':900,'semantics':'read_initial_place_file then fresh SA state (placement-seeded reanneal), followed by native route/analysis; NOT checkpoint SA continuation','command_builder':'baseline_smoke.py frozen at pre-run commit','quality_goal':'same timing-first guard evaluated after native closure; executable smoke only, not equal-wall efficacy'},'files':list(files.values())}
for case in cases:
 for j,(kind,pair,arms) in enumerate([('warmup',0,'AB'),('measured',1,'AB'),('measured',2,'BA'),('measured',3,'AB')]):
  for arm in arms:protocol['schedule'].append({'run_id':f"{case['case']}_{kind}_{pair}_{arm}",'case':case['case'],'kind':kind,'pair':pair,'arm':arm,'initial_status':'not_started'})
dump(D/'PILOT_PROTOCOL.json',protocol)
dump(D/'source_manifest.json',{'source_baseline_commit':BASE,'accepted_audit_commit':protocol['accepted_audit_commit'],'historical_source_commit':'unknown','historical_implementation':a,'new_implementation':impl,'modifications':'instrumentation.patch; isolated source only; per-edge reference copied verbatim from dc0d7b archive','files':list(files.values())})
env={'observed_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'uname':list(platform.uname()),'python':sys.version,'affinity_before':sorted(os.sched_getaffinity(0)),'cpu':31,'cpu_numa_nodes':[str(x) for x in Path('/sys/devices/system/cpu/cpu31').glob('node*')],'loadavg':Path('/proc/loadavg').read_text(),'thread_env':protocol['environment'],'numa_policy':protocol['numa_policy']}
for n in ['cpu.max','memory.max']:
 p=Path('/sys/fs/cgroup')/n;env[n]=p.read_text().strip() if p.exists() else 'unknown'
dump(D/'environment.json',env)
print('prepared',len(files),'directly consumed files',sum(x['bytes'] for x in files.values()),'bytes hashed; schedule',len(protocol['schedule']))
