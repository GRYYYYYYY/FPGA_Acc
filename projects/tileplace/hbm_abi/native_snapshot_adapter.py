"""Checked native host adapter for resident strict-binary snapshot search."""
import subprocess,tempfile
from pathlib import Path
from pack_snapshot import pack
from strict_snapshot_codec import encode
from persistent_adapter import PersistentCppEngine
from compare_proposals import TilePlaceV2Engine,parse
from search_request import query

class NativeSnapshotEngine(PersistentCppEngine):
 def __init__(self,*args,**kwargs):
  TilePlaceV2Engine.__init__(self,*args,**kwargs)
  self._start_snapshot_server()
 def _start_snapshot_server(self):
  self._snapshot_directory=tempfile.TemporaryDirectory(prefix='tileplace_snapshot_')
  path=self._write_snapshot()
  self._server=subprocess.Popen([str(self.binary),str(path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
  self._snapshot_number=0;self.instances.append(self)
  if self._line()!='READY':raise RuntimeError('snapshot service initialization failed')
  self._verify_layout()
 def _write_snapshot(self):
  records,_=pack(self)
  path=Path(self._snapshot_directory.name)/'feedback.bin'
  path.write_bytes(encode(records));return path
 def _ok(self,text):
  command=text.split()[0]
  if command=='APPLY':text='COMMIT'+text[len('APPLY'):]
  expected={'APPLY':'COMMITTED','SAVE':'SAVED','RESTORE':'RESTORED','QUIT':'BYE'}[command]
  self._send(text)
  if self._line()!=expected:raise RuntimeError('snapshot acknowledgement differs')
 def _sync_feedback(self):
  path=self._write_snapshot();self._send(f'FEEDBACK {path}')
  if self._line()!='UPDATED':raise RuntimeError('snapshot feedback rejected')
 def propose_color(self,color,forbidden_ids=None):
  forbidden=forbidden_ids or set()
  reference,stats=TilePlaceV2Engine.propose_color(self,color,forbidden)
  self._send('QUERY\n'+query(self,color,True,forbidden))
  rows=[]
  while True:
   row=self._line()
   if row=='END':break
   rows.append(row)
  actual=parse('\n'.join(rows));expected=sorted((t.transaction_id,t.score_q20) for t in reference)
  if actual!=expected:raise RuntimeError(f'snapshot candidate mismatch color {color}')
  self._verify_layout()
  self.checks.append({'color':color,'selected':len(actual),'forbidden':len(forbidden),'strict_snapshot':True})
  by_id={t.transaction_id:t for t in reference}
  return [by_id[identity] for identity,score in sorted(actual,key=lambda row:(row[1],row[0]))],stats
 def close(self):
  try:super().close()
  finally:self._snapshot_directory.cleanup()
