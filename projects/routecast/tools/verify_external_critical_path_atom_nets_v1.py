"""Independent BLIF logical sink/net checks for native-mapped worst path points."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_final_critical_path_attribution_v1_2026-10-19';M=R/'experiments/prospective_external_family_final_atom_mapping_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 v=json.loads((D/'attribution.json').read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings={str(D/'attribution.json'):sha(D/'attribution.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for i in (1,2,3):
  for arm in ('cold','seed'):
   case=f'w160/episode_{i:02d}/{arm}';p=M/case/'design.blif';text=p.read_text().replace('\\\n',' ');nets={}
   for line in text.splitlines():
    x=line.split()
    if not x:continue
    if x[0]=='.names':
     for bit,net in enumerate(x[1:-1]):nets[(x[-1],'in',bit)]=net
    elif x[0]=='.latch':nets[(x[2],'D',0)]=x[1]
    elif x[0]=='.outputs':
     for net in x[1:]:nets[('out:'+net,'outpad',0)]=net
   q=D/case/'worst_path_points.json';points=json.loads(q.read_text());external=0
   for r in points:
    k=(r['atom'],r['port'],r['bit']);assert k in nets,(case,k);assert nets[k]==r['atom_net'],(case,k,nets[k],r['atom_net'])
    if r['classification']=='EXTERNAL_NATIVE_CID':assert r['native_net_name']==r['atom_net'];external+=1
   rows.append(dict(case=case,BLIF_sink_net_checks=len(points),external_atom_native_net_name_checks=external));bindings[str(p)]=sha(p);bindings[str(q)]=sha(q)
 assert all(sha(p)==h for p,h in bindings.items());out=dict(status='ALL6_WORST_PATH_BLIF_ATOM_NET_AND_EXTERNAL_NET_NAMES_VERIFIED',rows=rows,bindings=bindings,limitations='Independent logical net identity check; does not independently reconstruct packed physical pin connectivity or prove causal timing attribution.');(D/'independent_logical_identity_verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
