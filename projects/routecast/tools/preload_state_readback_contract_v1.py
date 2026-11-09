"""Exact all-node binary32 initial-cost readback for fixed native acc_fac=1."""
import struct,sys,re
from pathlib import Path
from array import array
ONE=1065353216

def verify(state,risk,graph_sha,nodes,native_log):
 assert sys.byteorder=='little'
 lines=Path(risk).read_text().splitlines();header=lines[0].split();assert header[:3]==['RCRISK1',graph_sha,str(nodes)] and len(lines)==int(header[3])+1;updates={};previous=-1;changed=0
 for line in lines[1:]:
  n,bits=map(int,line.split());assert previous<n<nodes and 0<=bits<2**32;previous=n;value=struct.unpack('<f',struct.pack('<I',bits))[0];assert value>0 and value<float('inf');new=struct.unpack('<I',struct.pack('<f',1.0+value))[0];updates[n]=new;changed+=new!=ONE
 with Path(state).open('rb') as f:
  assert f.readline()==f'RCACCBITS1 {nodes}\n'.encode();data=f.read()
 assert len(data)==4*nodes;values=array('I');values.frombytes(data);assert values.itemsize==4 and len(values)==nodes
 for n,bits in enumerate(values):assert bits==updates.get(n,ONE),('initial_cost_mismatch',n,bits,updates.get(n,ONE))
 matches=re.findall(r'initial excess preload entries=(\d+) changed=(\d+) acc_fac=([0-9.eE+-]+)',native_log);assert len(matches)==1 and tuple(map(int,matches[0][:2]))==(len(updates),changed) and float(matches[0][2])==1.0
 return dict(all_nodes_checked=nodes,positive_input_entries=len(updates),changed_initial_costs=changed,all_bits_match_fixed_one_pseudo_iteration=True)
