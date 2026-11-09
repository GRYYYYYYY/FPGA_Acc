"""All raw byte prefixes and architecture attribute joins independently checked."""
import json,struct
from pathlib import Path
from fractions import Fraction as F
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_track_aware_features_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'verification.json';v=read(p);assert len(v['rows'])==9 and len(v['columns'])==31 and not v['target_labels_read'] and all(sha(path)==h for path,h in v['bindings'].items());count=0
 for r in v['rows']:
  ids=read(r['resource_ids']);attributes={x['RR']:x for x in map(json.loads,Path(r['track_attributes']).read_text().splitlines())};old=Path(r['original_matrix']).read_bytes();new=Path(r['matrix']).read_bytes();assert len(old)==len(ids)*208 and len(new)==len(ids)*248
  for i,node in enumerate(ids):
   assert new[i*248:i*248+208]==old[i*208:(i+1)*208];a=attributes[node];expected=(float(a['ptc']),float(F(a['ptc'],a['width']-1)),float(a['width']),float(a['segment_id']==0),float(a['segment_id']==1));assert struct.unpack('<5d',new[i*248+208:(i+1)*248])==expected;count+=1
 out=D/'independent_verification_v1.json';out.write_text(json.dumps({'status':'ALL9_ORIGINAL26_BYTE_PREFIXES_AND5_ARCHITECTURE_COLUMNS_VERIFIED','resource_rows':count,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Source-only join correctness, no target/quality claim.'},indent=2)+'\n');print('TRACK_AWARE_PREFIXES_VERIFIED',count)
if __name__=='__main__':main()
