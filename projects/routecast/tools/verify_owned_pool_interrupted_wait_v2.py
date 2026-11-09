"""An interrupted Future.result still drains its running native owner lane."""
import json,sys
from pathlib import Path
from threading import Event,Timer
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from ordered_owned_search_pool_v2 import SearchPool
from source_binding_v2 import closure
started,release,ended=Event(),Event(),Event()
class Engine:
 def prepare(self,*args):pass
 def search(self,source,targets):
  started.set();assert release.wait(5)
  ended.set();return {0:1},{},{0}
 def close(self):assert ended.is_set()
pool=SearchPool(Engine,workers=1,window=1);pool.prepare({},0)
submit=pool.executors[0].submit
releaser=None
def interrupting_submit(*args):
 global releaser
 future=submit(*args)
 def interrupted_result():
  assert started.wait(5)
  releaser=Timer(.1,release.set);releaser.start()
  raise KeyboardInterrupt('injected wait interruption')
 future.result=interrupted_result
 return future
pool.executors[0].submit=interrupting_submit
try:
 try:next(pool.search_many([(0,{0})]))
 except KeyboardInterrupt:assert ended.is_set() and not pool.active
 else:raise AssertionError('interruption not propagated')
finally:release.set();pool.close()
D=R/'experiments/owned_pool_interrupted_wait_v2_2026-10-10';D.mkdir()
(D/'verification.json').write_text(json.dumps(dict(bindings=closure([Path(__file__)]),interrupted_result_drains_current_running_future_before_clearing_active=True,engine_destroy_after_task_completion=True,scope='Injected Future.result interruption with a live gated worker. Not physical native fault recovery or fullgraph parity.'),indent=2)+'\n')
print('PASS interrupted wait drains current future before engine close')
