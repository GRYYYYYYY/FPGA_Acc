"""Exact prospective criterion motivation on the frozen predecessor traces."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_critical_release_online_loop_2026-10-06';out=ROOT/'experiments/mux_detour_score_analysis_2026-10-06';out.mkdir();receipt=json.loads((parent/'receipt.json').read_text());summary=json.loads((parent/'audit_summary.json').read_text());assert summary['receipt_sha256']==sha(parent/'receipt.json');rows=[];bindings={}
for row in receipt['rows']:
 if row['status']=='PRIOR_ALLOCATION_SKIP':continue
 file=parent/f"w{row['width']}_m{row['index']}/result.json";assert sha(file)==row['result_sha256'];bindings[str(file)]=sha(file);d=json.loads(file.read_text());alloc=d['allocations'];seed={cid:F(value) for cid,value in alloc[0]['floor_ns'].items()};cursor=1
 for step,entry in enumerate(d['result']['trace']):
  if 'options' not in entry:continue
  options=alloc[cursor:cursor+len(entry['options'])];cursor+=len(options);scores=[]
  for order,spec in enumerate(options):
   assert spec['restrictions']==entry['options'][order]['restrictions'] and spec['valid']==entry['options'][order]['accepted']
   if spec['valid']:scores.append((F(spec['floor_cpd_ns']),sum(max(F(0),F(value)-seed[cid]) for cid,value in spec['floor_ns'].items()),order,spec['index']))
  old=min(scores,key=lambda x:(x[0],x[2]));new=min(scores,key=lambda x:(x[0],x[1],x[2]));assert d['attempts'][step+1]['allocation_index']==old[3];rows.append(dict(width=row['width'],index=row['index'],step=step,primary_tie=len({x[0] for x in scores})==1,old_selected_index=old[3],secondary_selected_index=new[3],would_change=old[3]!=new[3],scores=[dict(index=x[3],cpd_ns=str(x[0]),increase_ns=str(x[1])) for x in scores]))
 assert cursor==len(alloc)
(out/'receipt.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(parent/'receipt.json'),parent_summary_sha256=sha(parent/'audit_summary.json'),source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,scope='Retrospective exact score-discrimination motivation only; hypothetical secondary selections are not reroute evidence. New trial must start empty and observe its own conflicts.'),indent=2)+'\n');print('groups',len(rows),'primary ties',sum(x['primary_tie'] for x in rows),'changed choices',sum(x['would_change'] for x in rows))
