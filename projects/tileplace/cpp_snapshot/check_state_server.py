"""Exercise persistent state and full feedback rollback on the real diffeq contract."""
import argparse,json,subprocess
from pathlib import Path
from compare_proposals import (TilePlaceV2Engine,V2Config,payload,parse,prepare_pressure,
 prepare_timing,load_feedback_from_payload,load_timing_feedback)

def main():
 p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 root=Path(__file__).resolve().parent.parent
 d=root/'work/cohort_native_baseline_diffeq_2026-09-29';contract=root/'work/cohort_fresh_input_diffeq_2026-09-29/contract'
 pressure=load_feedback_from_payload(prepare_pressure(d/'diffeq.route',d/'rr_graph.xml'))
 timing=load_timing_feedback(prepare_timing(d/'report_timing.setup.rpt',d/'diffeq.net',contract/'blocks.jsonl',20))
 e=TilePlaceV2Engine(contract,d/'diffeq.place',V2Config(critical_distance_guard_q=0,routed_timing_weight=2),pressure,timing)
 proc=subprocess.Popen([str(a.binary.resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
 def send(text):proc.stdin.write(text+'\n');proc.stdin.flush()
 def line():
  value=proc.stdout.readline().strip()
  if not value:raise RuntimeError('state server ended unexpectedly')
  return value
 def ok(text):send(text);assert line()=='OK'
 def color(c):
  send(f'COLOR {c} 0');count=int(line());rows=[line() for _ in range(count)];assert line()=='END';return parse('\n'.join(rows))
 def dump():
  send('DUMP');count=int(line());rows=[tuple(map(int,line().split())) for _ in range(count)];assert line()=='END'
  return {r[0]:r[1:] for r in rows}
 try:
  send(payload(e,0)+' '.join(map(str,[len(e.focus_blocks),*sorted(e.focus_blocks)])));assert line()=='READY'
  initial=dict(e.positions);ok('SAVE 1')
  selected,_=e.propose_color(0);expected=sorted((t.transaction_id,t.score_q20) for t in selected)
  assert color(0)==expected
  changes={id:position for t in selected for id,position in t.trial.items()}
  ok('APPLY '+str(len(changes))+' '+' '.join(str(v) for id,position in sorted(changes.items()) for v in (id,*position)))
  e.apply(selected);assert dump()==e.positions
  # Replace all pressure and timing feedback, then restore one saved version.
  edge=next(iter(pressure));source,sink=next(iter(timing[0]));focus=next(iter(timing[1]))
  ok('FEEDBACK 1 1 1 '+' '.join(map(str,[*edge,123,source,sink,456,focus])))
  e.pressure_q16={edge:123};e.update_timing_feedback(({(source,sink):456},{focus}))
  assert color(1)==sorted((t.transaction_id,t.score_q20) for t in e.propose_color(1)[0])
  ok('RESTORE 1');e.restore(initial);e.pressure_q16=pressure;e.update_timing_feedback(timing)
  assert dump()==initial and color(0)==expected
  send('APPLY 1 0 999999 0 0 0');assert line().startswith('ERROR ')
  assert dump()==initial and color(0)==expected
  ok('QUIT');assert proc.wait(timeout=10)==0
 finally:
  if proc.poll() is None:proc.kill();proc.wait()
 receipt={'status':'pass','checks':['persistent color selection','candidate apply','feedback replacement','placement and feedback snapshot restore','illegal apply atomicity'],'scope':'real diffeq state server diagnostic, no native oracle execution'}
 a.output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
