"""Independent direct-use recount and reset-trace evidence qualification."""
import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';A=E/'ram_read_port_observability_v1_2026-10-21';D=E/'fifo_reset_collision_xsim_v2_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for d in [A,D]:
  for p,h in json.loads((d/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 audited=json.loads((A/'results.json').read_text());assert len(audited['rows'])==16;mods={n:json.loads((E/'preserved_source_ram_mapping_v1_2026-10-21'/n/'preserved_boundary.json').read_text())['modules'][n] for n in ['mcml','mkDelayWorker32B']}
 for r in audited['rows']:
  m=mods[r['source']];c=m['cells'][r['instance']];allinputs={b for cell in m['cells'].values() for p,bs in cell['connections'].items() if cell['port_directions'][p]=='input' for b in bs};external={b for p in m['ports'].values() if p['direction']=='output' for b in p['bits']};assert c['connections']['we2']==['0']
  for p in ['out1','out2']:
   used=set(c['connections'][p])&(allinputs|external);assert bool(used)==(not r['read_ports'][p]['unused_output_proven']);assert len(used)==r['read_ports'][p]['used_bits']
 cases=json.loads((D/'protocol.json').read_text())['cases'];stages=json.loads((D/'results.json').read_text())['rows'];assert len(stages)==3 and all(r['exit_code']==0 for r in stages);assert '--relax' in stages[0]['command'];log=(D/'xsim.log').read_text();assert 'FIFO_RESET_COLLISION_ALL7_COMPLETE' in log
 witnesses=[]
 for i,(suffix,w) in enumerate(cases):
  pattern=rf'FIFO_RESET_COLLISION group={i} writer=1 reader=2 addr=([0-9a-fA-F]+) empty=1 full=0 re=0';match=re.search(pattern,log);assert match and int(match.group(1),16)==0;assert f'FIFO_USED_OWNPORT_MATCH group={i} width={w}' in log;witnesses.append({'module':'generic_fifo_sc_'+suffix,'width':w,'reset_edges':2,'collision_address':0,'enqueue_while_empty_and_not_full':True,'dequeue':False,'used_ownport_matches_written_data':True})
 tb=(D/'tb.v').read_text();assert tb.count('rst=1;we=1;')==7 and tb.count('rst=0,clr=0,we=0,re=0')==7;assert '.we2(' not in tb and 'force ' not in tb # original source retains the disabled second writer; TB does not change it
 out={'status':'7_LOCAL_RESET_REACHABLE_FIFO_COLLISIONS_ON_UNUSED_SECOND_READ_PORTS_VERIFIED','direct_port_use':{'unused_second_read':7,'used_second_read':9},'reset_witnesses':witnesses,'bindings':{str(p.relative_to(R)):sha(p) for p in [A/'results.json',D/'tb.v',D/'xsim.log',D/'results.json']},'scope':'Reset reachability proven by concrete simulation of original local generic_fifo modules with legal first enqueue. Full-top controls abstracted, so not whole-design reachability.7port2 outputs disconnected in preserved whole-source graph, port2 writes0.9used-port2 cases retain collision proof obligation. Not arbitrary source equivalence or FIFO specification proof.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
