"""Verify no-op/capture parity and native RR float words at every boundary."""
import json,struct,sys,xml.etree.ElementTree as ET,math
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_resident_phase_trial_v1_2026-10-20'
def main():
 assert sys.byteorder=='little';vp=D/'verification.json';v=json.loads(vp.read_text());assert len(v['rows'])==18 and all(x['all_iteration_snapshots_complete'] and x['all_iteration_summary_fields_match_except_clocks'] and x['final_physical_sequences_identical'] for x in v['rows']);bindings={str(vp):sha(vp),str(Path(__file__)):sha(__file__)};cases=[];cache={};total=0;channels=0;allrows=0;full_occ_diff=0
 for x in v['rows']:
  case,mode=x['case'].rsplit('/',1);d=D/x['case'];rp=d/'receipt.json';receipt=json.loads(rp.read_text());assert all(sha(p)==h for p,h in receipt['files'].items());original=E/'prince_native_trajectory_v1_2026-10-20'/case
  for iteration in range(1,x['iterations']+1):
   a=d/f'iteration_{iteration:03d}.route';b=original/a.name;assert sha(a)==sha(b);bindings[str(b)]=sha(b)
  if mode=='disabled':assert not (d/'boundary').exists();continue
  width=case.split('/')[0];graph=E/'prince_native_cohort_v1_2026-10-20'/width/'source/rr_graph.xml'
  if width not in cache:
   nodes={};kinds={'SOURCE':0,'SINK':1,'IPIN':2,'OPIN':3,'CHANX':4,'CHANY':5}
   for event,node in ET.iterparse(graph):
    if node.tag=='node':nodes[int(node.get('id'))]=(kinds[node.get('type')],int(node.get('capacity')))
    node.clear()
   cache[width]=nodes
  nodes=cache[width];times=(d/'boundary/boundary_times.tsv').read_text().splitlines();assert len(times)==x['iterations'];assert len(list((d/'boundary').glob('iteration_*.bin')))==x['iterations'];percase=[]
  for iteration,line in enumerate(times,1):
   i,n,begin,printed,end=map(int,line.split());assert i==iteration and n==len(nodes) and begin<=printed<=end;p=d/'boundary'/f'iteration_{i}.bin';raw=p.read_bytes();assert raw[:8]==b'RCBND001' and struct.unpack_from('<QQ',raw,8)==(i,n) and len(raw)==24+24*n
   occp=original/f'iteration_{i:03d}_occupancy.json';occ=json.loads(occp.read_text())['node_occupancy'];hp=E/'prince_checkpoint_state_audit_v2_2026-10-20'/case/f'iteration_{i:03d}_derived_CHANNEL_acc_cost.json';history=json.loads(hp.read_text())['derived_costs'];mismatch=0;nonchannel_occ=0;channel_count=0
   for index,(nid,kind,count,cap,bits) in enumerate(struct.iter_unpack('<QIiiI',raw[24:])):
    assert nid==index and (kind,cap)==nodes[nid] and count>=0;value=struct.unpack('<f',struct.pack('<I',bits))[0];assert math.isfinite(value) and value>=1
    if kind in [4,5]:
     assert count==occ.get(str(nid),0);assert bits==struct.unpack('<I',struct.pack('<f',history.get(str(nid),1)))[0];channel_count+=1
    elif count!=occ.get(str(nid),0):nonchannel_occ+=1
   channels+=channel_count;allrows+=n;full_occ_diff+=nonchannel_occ;total+=1;percase.append(dict(iteration=i,native_RR_nodes=n,CHANNEL_words_occupancy_and_acc_bits_exact=channel_count,nonCHANNEL_occupancy_differences_from_printed_union=nonchannel_occ,original_writer_ns=printed-begin,RR_capture_and_binary_write_ns=end-printed));bindings.update({str(q):sha(q) for q in [p,occp,hp]})
  proof=d/'boundary_verification_v1.json';proof.write_text(json.dumps(dict(case=case,rows=percase),indent=2)+'\n');cases.append(dict(case=case,boundaries=len(percase),proof=str(proof),sha256=sha(proof),capture_write_ns=sum(r['RR_capture_and_binary_write_ns'] for r in percase)))
  for q in [rp,graph,d/'boundary/boundary_times.tsv']:bindings[str(q)]=sha(q)
 assert total==227 and all(sha(p)==h for p,h in bindings.items());(D/'boundary_verification_v1.json').write_text(json.dumps(dict(status='ALL18_NATIVE_ARMS_AND227_CAPTURE_BOUNDARIES_VERIFIED',cases=cases,captured_boundaries=total,native_RR_rows=allrows,CHANNEL_rows_exact=channels,nonCHANNEL_occupancy_difference_observations=full_occ_diff,bindings=bindings,scope='Every disabled/capture snapshot byte-identical to original trajectory; terminal physical traces and all nonclock iteration summaries unchanged. Every captured RR id/type/capacity domain and acc float validity checked. CHANNEL occupancy and exact acc float words match derived native prefix recurrence. NonCHANNEL occupancy differences retained, not forced to printed union. No restore/stop-policy or generic full-state serialization proof. RR capture subclock includes RR binary writes but excludes subsequent box, phase and metadata writes; full process cost reported separately, no speedup claim.'),indent=2)+'\n');print('RESIDENT_BOUNDARY_PASS',total,allrows,channels,'nonchannel occupancy differences',full_occ_diff)
if __name__=='__main__':main()
