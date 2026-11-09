"""Actual full-array expiry invariants; no route quality inference."""
import struct,pathlib,re

def verify(initial_path,before_path,after_path,risk_path,log):
 def words(path):
  h,b=pathlib.Path(path).read_bytes().split(b'\n',1);assert h==b'RCACCBITS1 904438' and len(b)==904438*4;return [x[0] for x in struct.iter_unpack('<I',b)]
 entries={}
 for line in pathlib.Path(risk_path).read_text().splitlines()[1:]:
  n,b=map(int,line.split());assert n not in entries;v=struct.unpack('<f',struct.pack('<I',b))[0];entries[n]=struct.unpack('<I',struct.pack('<f',1+v))[0]
 initial,before,after=map(words,[initial_path,before_path,after_path]);changed=0
 for n in range(904438):
  if n in entries:assert initial[n]==before[n]==entries[n] and after[n]==0x3f800000
  else:assert before[n]==after[n]
  changed+=before[n]!=after[n]
 assert changed==sum(x!=0x3f800000 for x in entries.values());assert re.findall(r'ROUTECAST first iteration hint expired entries=(\d+)',log)==[str(len(entries))]
 return dict(all_nodes_checked=904438,hint_entries=len(entries),changed_cost_words=changed,initial_hint_bits_unchanged_before_expiry=True,hint_bits_exact_one_after_expiry=True,all_nonhint_words_preserved=True,scope='Expiry state invariants only, no original quality/utility acceptance.')
