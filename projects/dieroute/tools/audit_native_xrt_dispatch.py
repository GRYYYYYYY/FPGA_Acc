"""Bind actual XRT dispatch to an independently verified native protocol proof.

Supports cohorts whose repeat count differs from the C-model baseline.
Pass the proof returned by audit_native_parallel.verify for this same case.
"""
import re,struct
from pathlib import Path


def bind_dispatch(case, proof):
 case=Path(case)
 assert proof['passed'] and proof['net_commit']['verified']
 log=(case/'run.log').read_text();assert log.count('XRT shared device load=1')==1 and 'binary_1/' not in log,'device image reloaded'
 net=[tuple(map(int,r)) for r in re.findall(r'XRT net_commit call=(\d+) op=(\d+) status=(\d+) reads=(\d+) deltas=(\d+) authority_uploads=(\d+) total_authority_uploads=(\d+)',log)]
 frames=(case/'route/net_commit_frames.bin').read_bytes();pos=64;expected=[]
 while pos<len(frames):
  assert len(frames)-pos>=448,'truncated ABI frame'
  h=struct.unpack_from('<16Q',frames,pos);assert h[7]>=56 and pos+h[7]*8<=len(frames),'invalid ABI frame size'
  done=struct.unpack_from('<8Q',frames,pos+320);expected.append((h[0]+1,h[6],done[0],done[2],done[7],0,0));pos+=h[7]*8
 assert pos==len(frames) and net==expected and len(net)==proof['net_commit']['kernel_calls'],'XRT dispatch differs from actual native ABI frames'
 publisher=[tuple(map(int,r)) for r in re.findall(r'XRT publisher die=(\d+) session=(\d+) commands=(\d+) updates=(\d+) visits=(\d+) error=(\d+) state_uploads=(\d+)',log)]
 receiver=[tuple(map(int,r)) for r in re.findall(r'XRT receiver die=(\d+) session=(\d+) commands=(\d+) error=(\d+) state_uploads=(\d+)',log)]
 assert publisher and all(r[-2:]==(0,0) for r in publisher+receiver)
 totals=proof['summary_hbm']['totals'];ops={int(k):v for k,v in proof['summary_hbm']['operation_counts'].items()};expected_receiver=ops.get(3,0)+ops.get(4,0)
 assert len(receiver)==expected_receiver and len(publisher)==totals['commands']-expected_receiver+totals['pump_launches']
 assert sum(r[2] for r in publisher+receiver)==totals['commands'] and sum(r[3] for r in publisher)==totals['published_updates'] and sum(r[4] for r in publisher)==totals['dirty_queue_visits']
 return dict(status='passed',net_kernel_calls=len(net),publisher_kernel_calls=len(publisher),receiver_kernel_calls=len(receiver),net_authority_uploads=0,endpoint_state_uploads=0,device_image_loads=1,net_dispatch_bound_to_native_frames=True)
