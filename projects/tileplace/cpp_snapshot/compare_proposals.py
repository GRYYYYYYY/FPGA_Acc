"""Compare complete candidate identities/scores for selected real contract units."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'tools'))
from tileplace_v2 import TilePlaceV2Engine,V2Config,load_timing_feedback
from run_tileplace_v2 import load_feedback_from_payload
from prepare_route_feedback import prepare as prepare_pressure
from prepare_timing_feedback import prepare as prepare_timing

def payload(e,index):
 c=e.config; lines=[]
 nn=max(e.net_members,default=-1)+1
 lines.append(f'{len(e.positions)} {len(e.site_by_loc)} {len(e.units)} {nn} {len(e.pressure_q16)} {len(e.path_edges_q16)} {len(e.guarded)} {index}')
 lines.append(f'{c.page_width} {c.page_height} {c.candidate_limit} {c.chain_candidate_limit} {c.timing_weight} {c.routed_timing_weight} {c.congestion_weight}')
 def put(values):lines.append(' '.join(map(str,values)))
 for id,p in e.positions.items():
  b=e.block_by_id[id]; r=b.get('region'); regions=None
  if r is not None:
   if r and all(isinstance(v,int) for v in r):regions=[[*r[:4],r[4] if len(r)>4 else -2147483648,r[4] if len(r)>4 else 2147483647,-1]]
   else:regions=[[q[k] for k in ['xmin','ymin','xmax','ymax','layer_low','layer_high','subtile']] for q in r]
  put([id,*p,b['logical_type'],-1 if regions is None else len(regions)])
  for q in regions or []:put(q)
  fixed=[None]*4
  if b.get('fixed'):
   if b.get('fixed_location') is not None:fixed=[b['fixed_location'][k] for k in ['x','y','subtile','layer']]
   else:fixed=[b['initial'][k] for k in ['x','y','subtile','layer']]
  put([v for q in fixed for v in (int(q is not None),q if q is not None else 0)])
 for p,s in e.site_by_loc.items():put([*p,s['physical_type']])
 for u in e.units:put([len(u),int(u in e.fixed_units),*u])
 for i in range(nn):
  m=e.net_members.get(i,[]);cs=e.connections.get(i,[]);put([len(m),len(cs)]);put(m)
  for connection in cs:put(connection)
 for edge,w in e.pressure_q16.items():put([*edge,w])
 for edge,w in e.path_edges_q16.items():put([*edge,w])
 for a,b,_,d in e.guarded:put([a,b,d+c.critical_distance_slack])
 return '\n'.join(lines)+'\n'

def parse(text):
 out=[]
 for line in text.splitlines():
  tokens=iter(line.split());kind=next(tokens);score=int(next(tokens));units=[]
  for _ in range(int(next(tokens))):units.append(tuple(int(next(tokens)) for _ in range(int(next(tokens)))))
  trial=[]
  for _ in range(int(next(tokens))):trial.append((int(next(tokens)),tuple(int(next(tokens)) for _ in range(4))))
  out.append(((kind,tuple(units),tuple(trial)),score))
 return sorted(out)

def main():
 p=argparse.ArgumentParser();p.add_argument('contract',type=Path);p.add_argument('place',type=Path);p.add_argument('--binary',type=Path,required=True);p.add_argument('--baseline-dir',type=Path);p.add_argument('--units',type=int,default=20);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 pressure={}; timing=({},set()); extra=[]
 if a.baseline_dir:
  d=a.baseline_dir
  extra=[d/'diffeq.route',d/'rr_graph.xml',d/'report_timing.setup.rpt',d/'diffeq.net']
  pressure=load_feedback_from_payload(prepare_pressure(extra[0],extra[1]))
  timing=load_timing_feedback(prepare_timing(extra[2],extra[3],a.contract/'blocks.jsonl',20))
 e=TilePlaceV2Engine(a.contract,a.place,V2Config(critical_distance_guard_q=0,routed_timing_weight=2 if a.baseline_dir else 0),pressure,timing)
 occupied={loc:id for id,loc in e.positions.items()};rows=[]
 for index,u in enumerate(e.units[:a.units]):
  reference=sorted((t.transaction_id,t.score_q20) for t in e._transactions_for_unit(u,occupied))
  result=subprocess.run([str(a.binary.resolve())],input=payload(e,index),text=True,capture_output=True,check=True)
  actual=parse(result.stdout)
  if actual!=reference:raise RuntimeError(f'candidate mismatch for unit {u}: C++ {len(actual)}, Python {len(reference)}')
  rows.append({'unit':u,'candidates':len(actual)})
  if (index+1)%20==0:print(f'checked {index+1}/{min(a.units,len(e.units))} units',flush=True)
 receipt={'status':'pass','scope':'supplied placement candidate identities/scores with optional static feedback; no feedback-refresh or full trajectory claim','contract':str(a.contract),'place':str(a.place),'pressure_edges':len(pressure),'timing_edges':len(timing[0]),'units':rows,'candidates':sum(r['candidates'] for r in rows)}
 receipt['files']=[{'path':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [a.place,a.binary,*extra,*sorted((Path(__file__).parent.parent/'tools').glob('*.py')),*sorted(a.contract.glob('*')), *sorted(Path(__file__).parent.glob('*.hpp')),Path(__file__),Path(__file__).with_name('proposal_query.cpp')] if f.is_file()]
 a.output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='files'}))
if __name__=='__main__':main()
