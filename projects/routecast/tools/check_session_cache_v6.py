"""Frozen-session parity, mutation rejection, closing digest and lifecycle."""
import sys,json,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from remaining_delay_session_cache_v5 import RemainingDelayCache
from remaining_delay_halfns_cache_v3 import RemainingDelayCache as Legacy
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/session_cache_contract_v6_2026-10-07';out.mkdir();sources=closure([Path(__file__)]);(out/'protocol.json').write_text(json.dumps(dict(sources=sources,scope='Software snapshot/session contracts; metadata checks are not per-query cryptographic verification or concurrency security.'))+'\n')
class RC:
 scale=10**10;increments=[2,3]
 def initial(self,n):return 0
f=dict(node_ids=[0,1,2],row_offsets=[0,1,2,2],dest_ranks=[1,2],edge_ids=[0,1],capacities=[1]*3)
def new(name,cls=RemainingDelayCache):
 w=out/name;w.mkdir();g=w/'g';g.write_bytes(b'graph0');return cls(g,sha(g),f,RC(),w/'bounds',max_entries=1)
def rejects(fn):
 try:fn()
 except (ValueError,OSError):return
 raise AssertionError('request accepted')
a=new('parity');b=new('legacy',Legacy)
for sink in (2,2,1,2):assert list(a.get(sink).values)==list(b.get(sink).values)
assert (a.hits,a.misses,a.evictions)==(b.hits,b.misses,b.evictions)
proof=a.finalize();assert proof['initial_and_final_content_digest_equal'] and a.summary()['closed'];rejects(lambda:a.get(2));rejects(a.finalize)
for mode in ('rewrite','replace','restore_mtime','delete','scale','cutoff','reverse','closing_digest'):
 c=new(mode);view=c.get(2);before=dict(c.entries);st=c.graph.stat()
 if mode in ('rewrite','restore_mtime','closing_digest'):
  c.graph.write_bytes(b'graph1')
  if mode=='restore_mtime':os.utime(c.graph,ns=(st.st_atime_ns,st.st_mtime_ns))
  if mode=='closing_digest':c._stamp=c._stat() # deliberately bypass metadata guard; final SHA must reject
 elif mode=='replace':
  temp=c.graph.with_name('replacement');temp.write_bytes(b'graph0');temp.replace(c.graph)
 elif mode=='delete':c.graph.unlink()
 elif mode=='scale':c.rc.scale+=1
 elif mode=='cutoff':c.cutoff+=1
 elif mode=='reverse':c.reverse=tuple(list(row) for row in c.reverse)
 if mode=='closing_digest':rejects(c.finalize);assert c._invalid and not c._closed
 else:rejects(lambda:c.get(2));rejects(c.finalize)
 assert c.entries==before
c=new('deadline');before=dict(c.entries)
try:c.get(2,time.perf_counter()-1)
except TimeoutError:pass
else:raise AssertionError('expired request accepted')
assert c.entries==before and c.misses==0;c.finalize()
assert all(sha(k)==v for k,v in sources.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),parity_queries=4,hit_miss_eviction_parity=True,mutation_modes=['rewrite','replace','restore_mtime','delete','scale','cutoff','reverse','closing_digest'],closing_digest_rejects_metadata_bypass=True,close_blocks_future_get=True,deadline_no_publication=True,scope='No malicious memory protection or concurrent race guarantee; outputs provisional until full digest finalize.'),indent=2)+'\n');print('PASS session lifecycle and legacy parity')
