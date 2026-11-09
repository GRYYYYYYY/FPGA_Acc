"""Verify pinned XSim witness receipts and mapped/exported RAM cell coverage."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/parmys_read_hold_xsim_v1_2026-10-21';P=R/'experiments/standard_parmys_ram_mapping_v2_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 protocol=json.loads((D/'protocol.json').read_text())
 for name,h in protocol['bindings'].items():assert sha(Path(name))==h,name
 result=json.loads((D/'results.json').read_text());assert len(result['rows'])==2;bindings={};checks=[]
 for row in result['rows']:
  n=row['case'];f=D/n;assert row['counterexample_confirmed'];assert len(row['stages'])==3 and all(s['exit_code']==0 for s in row['stages'])
  log=(f/'xsim.log').read_text();assert log.count('EDGE_MATCH ref=')==3;assert 'READ_HOLD_COUNTEREXAMPLE_CONFIRMED' in log and 'clk=0' in log;assert '$finish called at time : 33 ns' in log;assert 'Fatal:' not in log
  m=json.loads((P/n/'mapped.json').read_text())['modules']['probe'];count=sum(c['type']=='dual_port_ram' for c in m['cells'].values());text=(f/'mapped.v').read_text();assert text.count('dual_port_ram #(.ADDR_WIDTH(11),.DATA_WIDTH(1))')==count;assert 'always' not in text and 'initial' not in text
  tb=(f/'tb.v').read_text();assert 'if(refout !==' in tb and 'mappedout !==' in tb and '.we2(1\'b0)' in tb
  for name in ['mapped.v','tb.v','run.tcl','xvlog.log','xelab.log','xsim.log']:bindings[str((f/name).relative_to(R))]=sha(f/name)
  checks.append(dict(case=n,ram_cells_exported=count,three_edge_samples_match=True,no_edge_counterexample_confirmed=True))
 B=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
 for name in ['xvlog','xelab','xsim']:
  for p in [B/name,B/'unwrapped/lnx64.o'/name]:
   if p.is_file():bindings[str(p)]=sha(p)
 out=dict(status='XSIM_CONCRETE_READ_HOLD_COUNTEREXAMPLES_VERIFIED',checks=checks,bindings=bindings,verification_scope='Pinned inputs, complete RAM instance count, successful compile/elaborate/sim receipts and expected concrete trace. HDL export is direct operator translation, not independently proven full netlist equivalence. No physical RAM or full source-family claim.')
 (D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
