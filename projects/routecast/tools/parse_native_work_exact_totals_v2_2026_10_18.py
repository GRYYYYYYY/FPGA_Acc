"""Strict exact work counters; infer at most one rounded heap cell from native exact total."""
import re,struct
from audit_mmc_v16_native_iteration_work_v1 import parse as strict_parse

def parse(text):
 totals=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',text);assert len(totals)==1
 nets,conns,heap,pops=map(int,totals[0]);assert pops<=heap
 lines=text.splitlines();known=0;rounded=[]
 for i,line in enumerate(lines):
  w=line.split()
  if len(w)<9 or not w[8].startswith('('):continue
  try:
   for k in [0,3,5,6,7]:int(w[k])
   float(w[1]);float(w[2])
  except ValueError:continue
  if w[4].isdigit():known+=int(w[4])
  else:
   assert re.fullmatch(r'\d+(?:\.\d+)?e[+]\d+',w[4]);rounded.append((i,w))
 assert len(rounded)<=1, 'Multiple rounded heap cells cannot be recovered uniquely'
 reconstruction=[]
 if rounded:
  i,w=rounded[0];exact=heap-known;assert exact>9999999
  rounded_float=struct.unpack('f',struct.pack('f',exact))[0];assert format(rounded_float,'#.2g')==w[4]
  reconstruction.append(dict(iteration=int(w[0]),printed_heap_token=w[4],exact_heap_pushes=exact,native_exact_total=heap,sum_other_exact_rows=known))
  w[4]=str(exact);lines[i]=' '.join(w)
 result=strict_parse('\n'.join(lines));assert result['total_heap_pushes']==heap and result['total_rerouted_NET_operations']==nets and result['total_rerouted_connection_operations']==conns
 result['exact_heap_reconstruction']=reconstruction
 return result
