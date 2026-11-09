"""One serial native request on the caller's existing immutable RR context."""
import json,time,threading,traceback
from pathlib import Path
from live_search_worker_v8 import produce
class Worker:
 def __init__(self,ctx,inventory,box):
  self.ctx=ctx;self.inventory=inventory;self.box=Path(box);self.box.mkdir();self.error=None;self.stop=threading.Event();self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
 def run(self):
  try:
   request=self.box/'request_0.json';deadline=time.monotonic()+150
   while not request.exists():
    if self.stop.is_set():return
    if time.monotonic()>deadline:raise TimeoutError('native export request missing')
    time.sleep(.02)
   data=json.loads(request.read_text());produce(data['stem'],data['config'],self.ctx,self.inventory);result=dict(ok=True,index=0)
  except Exception:
   self.error=traceback.format_exc();result=dict(ok=False,index=0,error=self.error)
  temp=self.box/'response_0.tmp';temp.write_text(json.dumps(result)+'\n');temp.rename(self.box/'response_0.json')
 def finish(self):
  self.stop.set();self.thread.join(timeout=125)
  if self.thread.is_alive():raise TimeoutError('live worker remains running')
  if self.error:raise RuntimeError(self.error)
