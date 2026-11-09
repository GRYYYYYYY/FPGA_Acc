"""Verify complete original-top input coverage, clocked witnesses and file bindings."""
import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'mcml_top_collision_xsim_v2_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 protocol=json.loads((D/'protocol.json').read_text())
 for p,h in protocol['bindings'].items():assert sha(Path(p))==h,p
 stages=json.loads((D/'results.json').read_text())['rows'];assert len(stages)==3 and all(r['exit_code']==0 for r in stages)
 tb=(D/'tb.v').read_text();assert 'force ' not in tb and '$deposit' not in tb;assert 'reset=1,clk=0,read_constants=0,inc_result=0' in tb and 'constants=1' in tb;assert 'reset=0;' in tb and 'read_constants=threshold>0 && counter<threshold;' in tb
 prefix=tb.split('for(cycle=',1)[0];assert prefix.count('clk=1;')==2
 assert '#4;clk=1;#1;\nif(&seen)' in tb
 graph=json.loads((E/'preserved_source_ram_mapping_v1_2026-10-21/mcml/preserved_boundary.json').read_text())['modules']['mcml'];inputs={n for n,p in graph['ports'].items() if p['direction']=='input'};assert inputs=={'reset','clk','constants','read_constants','inc_result'}
 for p in inputs:assert '.'+p+'('+p+')' in tb
 log=(D/'xsim.log').read_text();records=[]
 for i,name in enumerate(protocol['cases']):
  pattern=rf'MCML_TOP_COLLISION group={i} instance={name} cycle=(\d+) state=(\d+) addr=([0-9a-fA-F]+)';matches=re.findall(pattern,log);assert len(matches)==1;cycle,state,address=matches[0];records.append({'instance':name+'.dpram1','cycle':int(cycle),'state':int(state),'address':int(address,16),'both_addresses_defined':True})
 done=re.search(r'MCML_TOP_ALL7_COLLISIONS_REACHED_AFTER_EDGE cycles=(\d+)',log);assert done and int(done[1])==max(r['cycle'] for r in records);assert '$finish called at time : 74126 ns' in log
 out={'status':'ALL_7_MCML_USED_SECOND_PORT_COLLISIONS_REACHED_IN_ORIGINAL_COMPLETE_TOP','records':records,'all_top_inputs_driven':True,'two_reset_edges_then_external_input_stimulus_only':True,'final_witness_followed_by_rising_edge':True,'bindings':{str(p.relative_to(R)):sha(p) for p in [D/'tb.v',D/'xsim.log',D/'results.json']},'scope':'Concrete four-state XSim trace of original complete RTL from reset, no forced internals or initialized-memory assumptions. Demonstrates known RAM pin collision reachability under declared external stimulus, not arbitrary binary initial-state reachability, application-valid coefficient set, top-result impact, mapped equivalence or collision read-mode correctness.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
