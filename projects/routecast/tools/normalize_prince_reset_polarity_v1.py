"""Explicit inverter candidate; no reset assumption or native jobs."""
import json
from pathlib import Path
from verify_external_family_cut_v1_2026_10_18 import lines
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_reset_polarity_v1_2026-10-20'
def main():
 proof=E/'prince_async_cut_verification_v1_2026-10-20/verification.json';v=json.loads(proof.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());source=E/'prince_compile_cut_v2_2026-10-20/design.blif';rows=lines(source);wire='routecast_prince_reset_high_v1';assert all(wire not in row for row in rows);result=[];count=0
 for row in rows:
  if row[0]=='.subckt':
   assert row[1] in ['$_DFF_PN0_','$_DFF_PN1_'];pins=dict(pair.split('=',1) for pair in row[2:]);assert pins['R']=='reset_n';row=[row[0],row[1].replace('_PN','_PP'),*[('R='+wire) if pair.startswith('R=') else pair for pair in row[2:]]];count+=1
  if row[0]=='.end':result.extend([['.names','reset_n',wire],['0','1']])
  result.append(row)
 assert count==646;D.mkdir(exist_ok=False);out=D/'design.blif';out.write_text('\n'.join(' '.join(row) for row in result)+'\n');files=[Path(__file__),source,proof,E/'prince_reset_polarity_design_v1_2026-10-20/protocol.json',out];(D/'receipt.json').write_text(json.dumps({'status':'NORMALIZED_CANDIDATE_FROZEN_PENDING_INDEPENDENT_EVENT_AND_PIN_AUDIT','state_cells':count,'added_inverter':wire,'native_labels_generated':False,'bindings':{str(p):sha(p) for p in files}},indent=2)+'\n');print('PRINCE_RESET_CANDIDATE_FROZEN',count)
if __name__=='__main__':main()
