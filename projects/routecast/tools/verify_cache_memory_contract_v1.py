"""Independently audit tracked-memory transition, alignment and collision-hit SAT inputs."""
import json,hashlib
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'cache_memory_relation_sat_v1_2026-10-21';SRC=E/'preserved_source_ram_mapping_v1_2026-10-21/mkDelayWorker32B/preserved_boundary.json';STUDIES=['cache_memory_relation_sat_v1_2026-10-21','message_read_alignment_sat_v1_2026-10-21','message_collision_cache_hit_sat_v1_2026-10-21']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 original=json.loads(SRC.read_text())['modules']['mkDelayWorker32B'];ram={n:c for n,c in original['cells'].items() if c['type'].endswith('dual_port_ram')};assert len(ram)==9;oldbits={b for v in original['netnames'].values() for b in v['bits'] if isinstance(b,int)};oldbits|={b for c in original['cells'].values() for bits in c['connections'].values() for b in bits if isinstance(b,int)};checks=[]
 for study in STUDIES:
  root=E/study
  for p,h in json.loads((root/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
  result=json.loads((root/'results.json').read_text())['rows'];assert len(result)==(10 if study==STUDIES[0] else 4)
  for row in result:
   f=R/row['folder'];obj=json.loads((f/'proof.json').read_text())['modules']['mkDelayWorker32B'];cut=json.loads((f/'cutpoints.json').read_text());assert {c['cell'] for c in cut}==set(ram)
   for n,c in original['cells'].items():
    if n not in ram:assert obj['cells'][n]==c
    else:assert n not in obj['cells']
   for n,v in original['ports'].items():assert obj['ports'][n]==v
   for n,v in original['netnames'].items():assert obj['netnames'][n]==v
   free={b for n,p in obj['ports'].items() if n not in original['ports'] and p['direction']=='input' for b in p['bits']};assert free=={b for c in ram.values() for p,bits in c['connections'].items() if c['port_directions'][p]=='output' for b in bits if isinstance(b,int)}
   added={n:c for n,c in obj['cells'].items() if n not in original['cells']};fresh=set()
   for c in added.values():
    for p,bits in c['connections'].items():
     if c['port_directions'][p]=='output':
      for b in bits:assert b not in oldbits and b not in fresh;fresh.add(b)
   prefix=row['prefix'];target=ram['dpram1' if prefix=='mesgRF' else 'dpram2'];cache=original['netnames'][prefix+'_rCache']['bits'];getter=original['netnames'][prefix+'_wDataOut__wget']['bits'];mode=row['mode']
   if study in STUDIES[:2]:
    fixed=added['$rc_fixed_row'];assert fixed['type']=='$dff' and fixed['connections']['D']==fixed['connections']['Q'] and len(fixed['connections']['Q'])==10 and not fixed['attributes'];memory=added['$rc_tracked_memory'];assert memory['type']=='$dffe' and len(memory['connections']['Q'])==256 and not memory['attributes'] and set(memory['connections'])=={'CLK','D','EN','Q'};assert memory['connections']['CLK']==target['connections']['clk'];assert added['$rc_write_row']['connections']['A']==target['connections']['addr1'] and added['$rc_write_row']['connections']['B']==fixed['connections']['Q']
    if mode=='no_memory_write_negative':assert memory['connections']['EN']==['0']
    else:assert memory['connections']['EN']==added['$rc_write_enable']['connections']['Y'] and added['$rc_write_enable']['connections']['A']==target['connections']['we1']
    if mode=='wrong_memory_data_negative':assert added['$rc_bad_data']['connections']['A']==target['connections']['data1'] and memory['connections']['D']==added['$rc_bad_data']['connections']['Y']
    else:assert memory['connections']['D']==target['connections']['data1']
    if study==STUDIES[0]:assert added['$rc_tag_match']['connections']['A']==cache[256:266] and added['$rc_valid_match']['connections']['A']==[cache[267]] and added['$rc_data_equal']['connections']=={'A':cache[:256],'B':memory['connections']['Q'],'Y':added['$rc_data_equal']['connections']['Y']}
    else:
     sampled=added['$rc_sampled_address'];assert sampled['connections']['D']==(target['connections']['addr2'] if mode=='read_alignment' else original['netnames'][prefix+'_rRdPtr']['bits'][:10]);assert added['$rc_read_aligned']['connections']['A']==original['netnames'][prefix+'_rRdPtr']['bits'][:10] and added['$rc_read_aligned']['connections']['B']==sampled['connections']['Q']
   else:
    mux=next(c for c in original['cells'].values() if c['type']=='$mux' and c['connections'].get('Y')==getter);assert added['$rc_equal']['connections']['A']==mux['connections']['S'] and added['$rc_equal']['connections']['B']==(['0'] if mode=='wrong_hit_negative' else ['1'])
   log=(f/'yosys.log').read_text();cmd=(f/'commands.ys').read_text();assert 'Found and reported 0 problems.' in log and '-seq 2' in cmd and '-prove-skip 1' in cmd and '-ignore_unknown_cells' not in cmd and '-set-init-zero' not in cmd
   positive=mode in ['reset_base','induction','read_alignment','hit_after_collision']
   if positive:assert row['exit_code']==0 and row['proof_passed'] and 'no model found: SUCCESS' in log
   else:assert row['exit_code']==1 and row['proof_failed'] and 'proof did fail' in log
   if mode=='reset_base':assert '-set wciS0_MReset_n 0' in cmd
   if mode=='induction':assert '-set-at 1 rc_relation 1' in cmd
   checks.append({'study':study,'prefix':prefix,'mode':mode,'positive':positive,'bindings':{str(p.relative_to(R)):sha(p) for p in [f/'proof.json',f/'commands.ys',f/'yosys.log']}})
 # Candidate's two changed reductions must have no fanout to source state/transaction logic.
 policy=E/'aux_word_forward_policy_v1_2026-10-21';obj=json.loads((policy/'candidate_boundary.json').read_text())['modules']['mkDelayWorker32B'];users=defaultdict(set)
 for n,c in obj['cells'].items():
  for p,bits in c['connections'].items():
   if c['port_directions'][p]=='input':
    for b in bits:users[b].add(n)
 isolation=[]
 for change in json.loads((policy/'change_manifest.json').read_text())['changes']:
  todo=obj['cells'][change['cell']]['connections']['Y'][:];seen=set();reachable=set()
  while todo:
   b=todo.pop();reachable.add(b)
   for n in users[b]:
    if n not in seen:seen.add(n);c=obj['cells'][n];assert c['type']=='$and';todo.extend(b for p,bits in c['connections'].items() if c['port_directions'][p]=='output' for b in bits)
  outputs=[n for n,p in obj['ports'].items() if p['direction']=='output' and set(p['bits'])&reachable];assert outputs==['prevent_hanging_nodes'];isolation.append({'prefix':change['prefix'],'only_output':outputs[0],'downstream_AND_cells':len(seen)})
 out={'status':'CACHE_MEMORY_RELATION_READ_ALIGNMENT_AND_COLLISION_HIT_VERIFIED','positive_proofs':sum(r['positive'] for r in checks),'negative_controls_expected_failures':sum(not r['positive'] for r in checks),'checks':checks,'auxiliary_policy_sink_isolation':isolation,'quantification':'Tracked row is arbitrary and self-held, not initialized to0. Reset base has invalid cache and unconstrained tracked memory. One-edge induction therefore lifts pointwise to all1024rows under exact sampled writer/data/address recurrence.','scope':'Binary synchronous source IR and explicit tracked RAM update using same event input tuple as cache. Does not prove literal HDL active-event scheduling agreement, arbitrary four-state behavior, physical port/I-O word correspondence, original raw observer equivalence or full policy composition.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status']);print(out['positive_proofs'],out['negative_controls_expected_failures'])
if __name__=='__main__':main()
