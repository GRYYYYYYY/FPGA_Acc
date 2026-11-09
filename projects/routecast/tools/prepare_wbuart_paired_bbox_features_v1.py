"""Existing paired-NET bbox demand as old/current/delta input, no label reads."""
import json,math,struct,sys
from pathlib import Path
from types import SimpleNamespace as NS
from endpoint_bbox_demand_v1 import predict
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_paired_bbox_features_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 assert sys.byteorder=='little';D.mkdir(exist_ok=False);source=E/'wbuart_owner_delta_features_v1_2026-10-20/verification.json';proof=source.parent/'independent_verification_v1.json';H=E/'wbuart_preroute_heterograph_v1_2026-10-20/verification.json';design=E/'wbuart_paired_bbox_feature_design_v1_2026-10-20/protocol.json'
 for p in [source,proof,H,design]:assert all(sha(path)==h for path,h in read(p)['bindings'].items())
 old=read(source);h=read(H);inputs={r['case']:r for r in h['rows']};graphs={};prior={};rows=[];bindings={str(p):sha(p) for p in [source,proof,H,design,Path(__file__),R/'tools/endpoint_bbox_demand_v1.py']}
 def projection(nodes,values,ids):
  result={}
  for n in ids:
   node=nodes[n];loc=dict(node.location);keys=[(int(loc.get('layer',0)),x,y,node.type,node.segment_id if node.segment_id is not None else -1) for x in range(loc['xlow'],loc['xhigh']+1) for y in range(loc['ylow'],loc['yhigh']+1)];result[n]=math.fsum(values[k] for k in keys)/len(keys)
  return result
 for r in old['rows']:
  info=inputs[r['case']];digest=info['graph_sha256']
  if digest not in graphs:
   raw=[json.loads(x) for x in Path(H.parent/'graphs'/digest/'RR_nodes.jsonl').read_text().splitlines()];graphs[digest]={n['id']:NS(type=n['type'],capacity=n['capacity'],segment_id=n['segment_id'],location=tuple(n['loc'].items())) for n in raw}
  nodes=graphs[digest];ids=read(r['resource_ids'])
  if r['source_frame'] not in prior:
   previous=read(r['source_frame']);assert previous['graph_sha256']==digest;old_cells,_=predict(nodes,previous['records']);prior[r['source_frame']]=(old_cells,projection(nodes,old_cells,ids),{int(n):c for n,c in previous['ledger'].items()})
  old_cells,old_values,ledger=prior[r['source_frame']];queries=[json.loads(x) for x in Path(r['target_incidence']).read_text().splitlines()];current_cells,_=predict(nodes,queries);new_values=projection(nodes,current_cells,ids);before=Path(r['matrix']).read_bytes();assert len(before)==len(ids)*304;directory=D/r['case'];directory.mkdir(parents=True);p=directory/'raw_features.f64';changed=0;unoccupied_changed=0;unoccupied_nonzero=0
  with p.open('xb') as f:
   for i,n in enumerate(ids):
    values=(old_values[n],new_values[n],new_values[n]-old_values[n]);assert all(map(math.isfinite,values));f.write(before[i*304:(i+1)*304]);f.write(struct.pack('<3d',*values));changed+=values[2]!=0;unoccupied_changed+=not ledger.get(n,0) and values[2]!=0;unoccupied_nonzero+=not ledger.get(n,0) and new_values[n]!=0
  witness=directory/'cell_utilities.json';witness.write_text(json.dumps({'old':[{'key':key,'value':value} for key,value in sorted(old_cells.items())],'current':[{'key':key,'value':value} for key,value in sorted(current_cells.items())]},separators=(',',':'))+'\n');rows.append({**r,'matrix':str(p),'columns':41,'original38_matrix':r['matrix'],'cell_utilities':str(witness),'paired_bbox_delta_nonzero_resources':changed,'previously_unoccupied_with_nonzero_delta':unoccupied_changed,'previously_unoccupied_with_nonzero_current_density':unoccupied_nonzero})
  for path in [p,witness,Path(r['source_frame']),Path(r['target_incidence'])]:bindings[str(path)]=sha(path)
  print('PAIRED_BBOX_INPUT',r['case'],changed,unoccupied_changed,flush=True)
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_EXISTING_PAIRED_BBOX_OLD_CURRENT_DELTA41_INPUTS_PRODUCED','rows':rows,'columns':old['columns']+['old paired bbox span mean','current paired bbox span mean','paired bbox mean delta'],'target_labels_read':False,'bindings':bindings,'scope':'Known unfitted paired geometry proxy, not legal paths, calibrated probability, new model or quality gain. Existing helper unchanged; no bbox padding/clipping/variant scan.'},indent=2)+'\n')
if __name__=='__main__':main()
