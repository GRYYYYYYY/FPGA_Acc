"""Real-contract color-phase differential under fixed baseline feedback.

All improving batches are applied for this diagnostic; no native acceptance
oracle is invoked. C++ candidate generation sees an independently updated
placement mirror at every phase.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
from compare_proposals import (TilePlaceV2Engine,V2Config,load_feedback_from_payload,
 prepare_pressure,prepare_timing,load_timing_feedback,payload,parse)

def main():
 p=argparse.ArgumentParser();p.add_argument('contract',type=Path);p.add_argument('baseline',type=Path);p.add_argument('--binary',type=Path,required=True);p.add_argument('--epochs',type=int,default=2);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 d=a.baseline; inputs=[d/'diffeq.place',d/'diffeq.route',d/'rr_graph.xml',d/'report_timing.setup.rpt',d/'diffeq.net']
 pressure=load_feedback_from_payload(prepare_pressure(inputs[1],inputs[2]))
 timing=load_timing_feedback(prepare_timing(inputs[3],inputs[4],a.contract/'blocks.jsonl',20))
 config=V2Config(critical_distance_guard_q=0,routed_timing_weight=2)
 reference=TilePlaceV2Engine(a.contract,inputs[0],config,pressure,timing)
 mirror=TilePlaceV2Engine(a.contract,inputs[0],config,pressure,timing)
 rows=[]
 for epoch in range(a.epochs):
  for color in range(4):
   selected,stats=reference.propose_color(color)
   data=payload(mirror,color)+' '.join(map(str,[len(mirror.focus_blocks),*sorted(mirror.focus_blocks)]))+'\n0\n'
   result=subprocess.run([str(a.binary.resolve()),'--color'],input=data,text=True,capture_output=True,check=True)
   actual=parse(result.stdout); expected=sorted((t.transaction_id,t.score_q20) for t in selected)
   if actual!=expected:raise RuntimeError(f'color selection differs at epoch {epoch}, color {color}')
   reference.apply(selected)
   for identity,score in actual:
    for id,position in identity[2]:mirror.positions[id]=position
   mirror._net_cost_cache.clear()
   if mirror.positions!=reference.positions:raise RuntimeError('placement mirror differs')
   digest=hashlib.sha256(json.dumps(sorted(mirror.positions.items())).encode()).hexdigest()
   rows.append({'epoch':epoch,'color':color,'selected':len(actual),'placement_sha256':digest,'python_stats':stats})
   print(f'epoch {epoch} color {color}: {len(actual)} transactions matched',flush=True)
 files=[*inputs,a.binary,*sorted(a.contract.glob('*')),*sorted(Path(__file__).parent.glob('*.hpp')),
        Path(__file__),Path(__file__).with_name('proposal_query.cpp'),Path(__file__).with_name('compare_proposals.py'),
        *sorted((Path(__file__).parent.parent/'tools').glob('*.py'))]
 receipt={'status':'pass','scope':'fixed-feedback diagnostic, all improving batches applied; no native oracle acceptance or feedback refresh',
          'phases':rows,'matched_transactions':sum(r['selected'] for r in rows),
          'files':[{'path':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files if f.is_file()]}
 a.output.write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({'status':'pass','phases':len(rows),'matched_transactions':receipt['matched_transactions']}))
if __name__=='__main__':main()
