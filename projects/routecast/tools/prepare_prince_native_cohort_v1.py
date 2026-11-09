"""Freeze development-only layout perturbations and native cold routing profiles."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 o=E/'prince_native_cohort_v1_2026-10-20';o.mkdir(exist_ok=False);src=E/'prince_development_place_v1_2026-10-20';proof=src/'independent_verification_v1.json';v=json.loads(proof.read_text())
 for p,h in v['bindings'].items():assert sha(p)==h
 lines=(src/'source.place').read_text().splitlines();rows=[]
 for i,line in enumerate(lines):
  t=line.split()
  if len(t)==6 and not t[0].startswith('#'):rows.append((i,t))
 import xml.etree.ElementTree as ET
 blocks=ET.parse(src/'design.net').getroot().findall('block');clbs=sorted((t for i,t in rows if blocks[int(t[-1][1:])].get('instance').startswith('clb[')),key=lambda t:int(t[-1][1:]));assert len(clbs)==134
 pairs=[(clbs[2*i][0],clbs[2*i+1][0]) for i in range(3)];frames={};selections=[]
 for episode in range(4):
  name='source' if episode==0 else f'episode_{episode:02d}';d=o/'placements'/name;d.mkdir(parents=True);out=lines.copy();pair=None if episode==0 else pairs[episode-1];lookup={t[0]:(i,t) for i,t in rows}
  if pair:
   ia,a=lookup[pair[0]];ib,b=lookup[pair[1]];aa=a.copy();bb=b.copy();aa[1:5]=b[1:5];bb[1:5]=a[1:5];out[ia]='\t'.join(aa);out[ib]='\t'.join(bb)
  place=d/'design.place';place.write_text('\n'.join(out)+'\n');frames[name]=str(place);selections.append(dict(frame=name,pair=pair))
  observed={t[0]:t for line in out if len(t:=line.split())==6 and not t[0].startswith('#')};assert len(observed)==210
  assert {tuple(t[1:5]) for t in observed.values()}=={tuple(t[1:5]) for i,t in rows}
  changed={t[0] for i,t in rows if observed[t[0]][1:5]!=t[1:5]};assert changed==set(pair or [])
 binary=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_vpr/vpr/vpr';arch=E/'prince_direct_pn_arch_v1_2026-10-20/architecture.xml';jobs=[]
 for width in [96,128,160]:
  for frame,place in frames.items():
   directory=o/f'w{width:03d}'/frame;graph=directory/'rr_graph.xml';cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--write_rr_graph',str(graph),'--route_chan_width',str(width),'--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
   jobs.append(dict(case=f'w{width:03d}/{frame}',directory=str(directory),width=width,frame=frame,place=place,command=cmd))
 paths=[Path(__file__),proof,src/'design.blif',src/'design.net',binary,arch,*map(Path,frames.values()),E/'prince_grounded_packed_cut_v1_2026-10-20/receipt.json',E/'prince_loaded_packing_sim_v1_2026-10-20/receipt.json'];p=dict(jobs=jobs,selections=selections,bindings={str(p):sha(p) for p in paths},staging={'design.blif':str(src/'design.blif'),'design.net':str(src/'design.net')},policy='All12 fixed cases retained: widths96/128/160 times source and 3 independent swaps selected by ascending CLB block ID first6, each relative to source. No tuning/retries/replacement; source failure does not remove target jobs. Cold routing max100, seed1, worker1, native default early exit policy unchanged. No predictor trained or promoted from these labels.',scope='Development-exposed PRINCE only. Direct PN experimental architecture with uncharacterized reset timing; diagnostic timing only. Grounded functional certificate is separate explicit export convention, no default-X equivalence. Full original nine-case prediction and native/full-paid utility gates remain required. This is baseline availability acquisition, not full workflow admission or strict unseen.',strict_unseen_admitted=False)
 (o/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');print('FROZEN',len(jobs),selections)
if __name__=='__main__':main()
