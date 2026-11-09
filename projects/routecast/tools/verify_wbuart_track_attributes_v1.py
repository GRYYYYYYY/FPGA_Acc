"""Independent XML stream attribute and declared uniform-width reconstruction."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction as F
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_track_attributes_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'verification.json';v=read(p);assert len(v['rows'])==3 and not v['target_labels_read'] and all(sha(path)==h for path,h in v['bindings'].items());count=0
 for r in v['rows']:
  expected={};widths=set();declared=None
  for _,e in ET.iterparse(r['graph']):
   if e.tag=='channel':declared=int(e.get('chan_width_max'))
   elif e.tag in ['x_list','y_list']:widths.add(int(e.get('info')))
   elif e.tag=='node':
    if e.get('type') in ['CHANX','CHANY']:expected[int(e.get('id'))]=(int(e.find('loc').get('ptc')),int(e.find('segment').get('segment_id')))
    e.clear()
  actual=[json.loads(x) for x in Path(r['attributes']).read_text().splitlines()];assert len(actual)==len(expected)==r['resources'] and len({q['RR'] for q in actual})==len(actual) and widths=={declared} and declared==r['channel_width']
  for q in actual:
   ptc,segment=expected[q['RR']];assert q['ptc']==q['relative_ptc_numerator']==ptc and q['width']==declared and q['relative_ptc_denominator']==declared-1 and q['segment_id']==segment and q['features']==[ptc,float(F(ptc,declared-1)),declared,int(segment==0),int(segment==1)];count+=1
 out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL3_XML_TRACK_AND_SEGMENT_ATTRIBUTES_VERIFIED','resources':count,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Physical source attributes only; no target-label/model/quality claim.'},indent=2)+'\n');print('ALL_TRACK_ATTRIBUTES_VERIFIED',count)
if __name__=='__main__':main()
