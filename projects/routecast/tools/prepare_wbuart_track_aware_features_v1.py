"""Append five audited architecture attributes, preserve original26 byte prefix."""
import json,struct,sys
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_track_aware_features_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 assert sys.byteorder=='little';D.mkdir(exist_ok=False);source=E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json';tracks=E/'wbuart_track_attributes_v1_2026-10-20/verification.json';proof=tracks.parent/'independent_verification_v1.json';H=E/'wbuart_preroute_heterograph_v1_2026-10-20/verification.json';design=E/'wbuart_track_aware_CART_design_v1_2026-10-20/protocol.json'
 for p in [source,tracks,proof,design]:assert all(sha(path)==h for path,h in read(p)['bindings'].items())
 old=read(source);t=read(tracks);bindings={str(p):sha(p) for p in [source,tracks,proof,H,design,Path(__file__)]};rows=[];lookup={r['graph_sha256']:r for r in t['rows']};graphs={r['case']:r['graph_sha256'] for r in read(H)['rows']}
 for r in old['rows']:
  metadata=lookup[graphs[r['case']]];attributes={q['RR']:q for q in map(json.loads,Path(metadata['attributes']).read_text().splitlines())};ids=read(r['resource_ids']);blob=Path(r['matrix']).read_bytes();assert len(blob)==len(ids)*26*8 and set(ids)==set(attributes);out=D/r['case'];out.mkdir(parents=True);p=out/'raw_features.f64'
  with p.open('xb') as f:
   for i,node in enumerate(ids):f.write(blob[i*26*8:(i+1)*26*8]);f.write(struct.pack('<5d',*attributes[node]['features']))
  rows.append({**r,'matrix':str(p),'columns':31,'original_matrix':r['matrix'],'track_attributes':metadata['attributes']});bindings[str(p)]=sha(p);bindings[metadata['attributes']]=sha(metadata['attributes'])
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_TRACK_AWARE_31_COLUMN_INPUTS_PRODUCED','rows':rows,'columns':old['columns']+t['columns'],'bindings':bindings,'target_labels_read':False,'scope':'Original26 plus source-only track/segment/width; no learned preprocessing or RR ID feature. Original feature acquisition remains paid.'},indent=2)+'\n');print('TRACK_AWARE_INPUTS_PRODUCED')
if __name__=='__main__':main()
