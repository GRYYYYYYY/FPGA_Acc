"""Pack a reference engine into explicit ABI arrays, preserving sparse IDs."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'cpp_snapshot'))
from compare_proposals import (TilePlaceV2Engine,V2Config,prepare_pressure,prepare_timing,
 load_feedback_from_payload,load_timing_feedback)
from snapshot_codec import FORMATS,encode,decode


def pack(engine,generation=1):
 s={name:[] for name in FORMATS};s['generation']=generation
 types=sorted({b['logical_type'] for b in engine.block_by_id.values()}|
              {site['physical_type'] for site in engine.site_by_loc.values()})
 type_ids={name:i for i,name in enumerate(types)}
 units={id:i for i,u in enumerate(engine.units) for id in u}
 for id,b in sorted(engine.block_by_id.items()):
  region=b.get('region');regions=[]
  if region is not None:
   if region and all(isinstance(v,int) for v in region):
    regions=[(*region[:4],region[4] if len(region)>4 else -2147483648,
              region[4] if len(region)>4 else 2147483647,-1,0)]
   else:regions=[tuple(item[k] for k in ['xmin','ymin','xmax','ymax','layer_low','layer_high','subtile'])+(0,) for item in region]
  offset=len(s['regions']);s['regions'].extend(regions)
  fixed=[None]*4
  if b.get('fixed'):
   source=b.get('fixed_location') or b['initial'];fixed=[source[k] for k in ['x','y','subtile','layer']]
  mask=sum(1<<i for i,v in enumerate(fixed) if v is not None)|(0x80000000 if region is not None else 0)
  initial=tuple(b['initial'][k] for k in ['x','y','subtile','layer'])
  s['blocks'].append((id,type_ids[b['logical_type']],*initial,offset,len(regions),
                      *(v if v is not None else 0 for v in fixed),mask,units[id]))
  s['positions'].append(tuple(engine.positions[id]))
 for loc,site in sorted(engine.site_by_loc.items()):s['sites'].append((*loc,type_ids[site['physical_type']],0,0,0))
 for id,members in sorted(engine.net_members.items()):
  m=len(s['net_members']);c=len(s['connections']);connections=engine.connections.get(id,[])
  s['net_members'].extend((id,) for id in members);s['connections'].extend(tuple(row) for row in connections)
  s['nets'].append((id,0,0,0,m,len(members),c,len(connections)))
 for unit in engine.units:
  offset=len(s['unit_members']);s['unit_members'].extend((id,) for id in unit)
  s['units'].append((offset,len(unit),int(unit in engine.fixed_units),0,0,0))
 for axis,lines in enumerate([engine._horizontal_pressure,engine._vertical_pressure]):
  for line,(coordinates,sums) in sorted(lines.items()):
   offset=len(s['prefix_entries']);s['prefix_entries'].extend((coordinate,0,value) for coordinate,value in zip(coordinates,sums))
   s['prefix_lines'].append((axis,line,sums[-1],offset,len(coordinates)))
 s['routed_edges']=[(*edge,weight) for edge,weight in sorted(engine.path_edges_q16.items())]
 s['focus']=[(id,) for id in sorted(engine.focus_blocks)]
 return s,types


def main():
 p=argparse.ArgumentParser();p.add_argument('contract',type=Path);p.add_argument('baseline',type=Path);p.add_argument('--design',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 d=a.baseline;name=a.design
 inputs=[d/f'{name}.place',d/f'{name}.route',d/'rr_graph.xml',d/'report_timing.setup.rpt',d/f'{name}.net']
 pressure=load_feedback_from_payload(prepare_pressure(inputs[1],inputs[2]))
 timing=load_timing_feedback(prepare_timing(inputs[3],inputs[4],a.contract/'blocks.jsonl',20))
 engine=TilePlaceV2Engine(a.contract,inputs[0],V2Config(critical_distance_guard_q=0,routed_timing_weight=2),pressure,timing)
 snapshot,types=pack(engine);blob=encode(snapshot)
 if decode(blob)!=snapshot:raise RuntimeError('snapshot round trip differs')
 a.output.mkdir(exist_ok=False);(a.output/'snapshot.bin').write_bytes(blob)
 metadata={'status':'pass','design':name,'scope':'reference engine to flat snapshot exact record round trip; no C++/HLS query claim',
           'types':types,'bytes':len(blob),'snapshot_sha256':hashlib.sha256(blob).hexdigest(),
           'records':{name:len(snapshot[name]) for name in FORMATS}}
 files=[*inputs,*a.contract.glob('*'),Path(__file__),Path(__file__).with_name('snapshot_codec.py'),
        Path(__file__).with_name('snapshot_abi.hpp'),*sorted((Path(__file__).parent.parent/'tools').glob('*.py'))]
 metadata['files']=[{'path':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files if f.is_file()]
 (a.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
 print(json.dumps({k:v for k,v in metadata.items() if k!='files'}))
if __name__=='__main__':main()
