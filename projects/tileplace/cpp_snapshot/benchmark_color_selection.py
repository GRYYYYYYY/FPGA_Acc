"""Pinned, alternating CPU color-selection benchmark with exact audit equality.

Initialization/feedback parsing and native closure are excluded. Each sample
queries all four colors at one fixed layout, with empty forbidden sets. The C++
measurement includes IPC, selected-transaction host audit and layout comparison.
"""
import argparse,hashlib,json,os,platform,statistics,time
from pathlib import Path
from compare_proposals import (TilePlaceV2Engine,V2Config,prepare_pressure,prepare_timing,
 load_feedback_from_payload,load_timing_feedback)
from fast_adapter import FastCppEngine


def main():
 p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--cases',nargs='+',default=['diffeq','tseng','apex2']);p.add_argument('--cpu',type=int,default=31);p.add_argument('--repeats',type=int,default=5);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.repeats<3:raise ValueError('at least three measured repetitions required')
 os.sched_setaffinity(0,{a.cpu})
 root=Path(__file__).resolve().parent.parent;FastCppEngine.binary=a.binary.resolve();rows=[];inputs=[]
 for case in a.cases:
  if case=='diffeq':
   baseline=root/'work/cohort_native_baseline_diffeq_2026-09-29';contract=root/'work/cohort_fresh_input_diffeq_2026-09-29/contract'
  else:
   directory=root/'experiments/tileplace_new_cohort_2026-09-29'/case;baseline=directory/'baseline';contract=directory/'inputs/contract'
  files=[baseline/f'{case}.place',baseline/f'{case}.route',baseline/'rr_graph.xml',baseline/'report_timing.setup.rpt',baseline/f'{case}.net']
  pressure=load_feedback_from_payload(prepare_pressure(files[1],files[2]))
  timing=load_timing_feedback(prepare_timing(files[3],files[4],contract/'blocks.jsonl',20))
  config=V2Config(critical_distance_guard_q=0,routed_timing_weight=2)
  reference=TilePlaceV2Engine(contract,files[0],config,pressure,timing)
  fast=FastCppEngine(contract,files[0],config,pressure,timing)
  samples=[]
  try:
   for repetition in range(-1,a.repeats):
    results={};times={}
    order=['python','cpp'] if repetition%2==0 else ['cpp','python']
    for label in order:
     engine=reference if label=='python' else fast;engine._net_cost_cache.clear()
     start=time.perf_counter();selected=[engine.propose_color(color) for color in range(4)];times[label]=time.perf_counter()-start
     results[label]=[([t.audit() for t in transactions],stats) for transactions,stats in selected]
    if results['python']!=results['cpp']:raise RuntimeError(f'benchmark equality failed for {case}')
    if repetition>=0:samples.append({'repetition':repetition,'order':order,**times})
    print(f'{case} sample {repetition}: Python {times["python"]:.4f}s C++ {times["cpp"]:.4f}s',flush=True)
  finally:
   fast.close();fast._server.stdin.close();fast._server.stdout.close()
  py=statistics.median(s['python'] for s in samples);cpp=statistics.median(s['cpp'] for s in samples)
  rows.append({'case':case,'blocks':len(reference.positions),'samples':samples,'python_median_s':py,'cpp_median_s':cpp,'median_wall_speedup':py/cpp,'exact_audits_and_stats':True})
  inputs.extend([*files,*sorted(contract.glob('*'))])
 source=Path(__file__).resolve().parent
 inputs.extend([a.binary,*source.glob('*.hpp'),source/'state_server_fast.cpp',source/'fast_adapter.py',source/'persistent_adapter.py',source/'compare_proposals.py',Path(__file__),*sorted((root/'tools').glob('*.py'))])
 receipt={'status':'pass','scope':'CPU four-color selection at fixed baseline layout and feedback; includes C++ IPC, selected audit and layout verification; excludes initialization, feedback parsing, VPR and layout changes','cpu_affinity':sorted(os.sched_getaffinity(0)),'platform':platform.platform(),'repetitions':a.repeats,'warmups':1,'cases':rows,'files':[{'path':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in inputs if f.is_file()]}
 a.output.write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({'status':'pass','speedups':{r['case']:r['median_wall_speedup'] for r in rows}}))
if __name__=='__main__':main()
