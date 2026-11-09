"""Posthoc worst-path identity and RR sequence comparison, rounded report bounds."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from timing_context import route_pairs,observed_context
root=Path('experiments/frisc_native_sta_pair_v2_2026-10-05');reports={};contexts={};inputs={}
for cid in (0,7):
 native=root/f'candidate_{cid}';receipt=json.loads((native/'receipt.json').read_text());protocol=json.loads((native/'protocol.json').read_text());file=native/'report_timing.setup.rpt';assert receipt['exit_code']==0 and sha(file)==receipt['reports'][file.name] and sha(native/'protocol.json')==receipt['protocol_sha256'];route=Path(protocol['inputs']['route']['path']);assert sha(route)==protocol['inputs']['route']['sha256'];text=file.read_text();contexts[cid]=observed_context(text,route_pairs(route.read_text()));first=text.split('#Path 1\n',1)[1].split('#Path 2\n',1)[0]
 start=re.search(r'^Startpoint:\s*(.*?)\s+\(',first,re.M)[1];end=re.search(r'^Endpoint\s*:\s*(.*?)\s+\(',first,re.M)[1];rr=[(k,int(n)) for k,n in re.findall(r'\((OPIN|IPIN|CHANX|CHANY):(\d+)\b',first)];cpd=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',(native/'stdout.txt').read_text())[1]);reports[cid]={'startpoint':start,'endpoint':end,'rr_sequence':rr,'cpd_ns':cpd,'groups':contexts[cid]['paths'][0]['endpoint_groups']};inputs[str(file)]=sha(file);inputs[str(route)]=sha(route);inputs[str(native/'receipt.json')]=sha(native/'receipt.json')
a,b=reports[0],reports[7];prefix=0
for x,y in zip(a['rr_sequence'],b['rr_sequence']):
 if x!=y:break
 prefix+=1
r={'same_start_and_endpoint':(a['startpoint'],a['endpoint'])==(b['startpoint'],b['endpoint']),'same_worst_path_endpoint_group_sequence':a['groups']==b['groups'],'baseline_critical_groups':len(a['groups']),'critical_rr_sequences_equal':a['rr_sequence']==b['rr_sequence'],'common_rr_prefix_length':prefix,'baseline_rr_sequence_length':len(a['rr_sequence']),'candidate_rr_sequence_length':len(b['rr_sequence']),'baseline_cpd_ns':a['cpd_ns'],'candidate_cpd_ns':b['cpd_ns'],'reports':reports,'input_sha256':inputs,'source_sha256':sha(__file__),'limitations':['same endpoints/group sequence not proof of identical internal logical path','detailed reports rounded to0.001ns; cannot attribute exact1.1ps to individual arc','posthoc native STA, not predictor success or prospective tuning']};(root/'diagnostic.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('reports','input_sha256')}))
