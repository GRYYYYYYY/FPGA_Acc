"""Independent bitset bin extrema and printed-target topK exclusion witnesses."""
import json,hashlib,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as F
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_map_spatial_rank_bounds_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=D/'verification.json';v=read(source);assert all(sha(p)==h for p,h in v['bindings'].items());rows=[];graphs={};bindings={str(source):sha(source),str(Path(__file__)):sha(__file__)}
 for row in v['rows']:
  ep=read(row['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.get('sink_node')) for _,e in ET.iterparse(g) if e.tag=='edge']
  dest=graphs[g];resources=[json.loads(x) for x in Path(row['resources']).read_text().splitlines()];ids=[r['id'] for r in resources];masks={n:1<<i for i,n in enumerate(ids)};binsfile=Path(row['resources']).parent/'spatial_bins.json';bins=read(binsfile);keys=[tuple(b['key']) for b in bins];assert keys==sorted(keys);caps=[b['capacity'] for b in bins];binmask=[0]*len(bins);index={k:i for i,k in enumerate(keys)}
  for r in resources:
   for key in r['bins']:binmask[index[tuple(key)]]|=masks[r['id']]
  def support(rs):
   value=0
   for q in rs:
    for eid in q['answer']['physical_edge_ids']:value|=masks.get(dest[eid],0)
   return value
  out=Path(row['output']);initial=defaultdict(list);final=defaultdict(list);pools=defaultdict(set)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for q in read(out/'round1.json')['records']:final[q['net_id']].append(q)
  for n,rs in initial.items():pools[n].add(support(rs))
  for rnd in read(out/'receipt.json')['rounds']:
   for e in rnd['events']:
    for name in ['records','rejected_records']:
     if name in e:pools[e['net_id']].add(support(e[name]))
  lower=[0]*len(bins);upper=[0]*len(bins)
  for pool in pools.values():
   union=0
   for mask in pool:union|=mask
   for i,mask in enumerate(binmask):
    if not union&mask:continue
    counts=[(choice&mask).bit_count() for choice in pool];lower[i]+=min(counts);upper[i]+=max(counts)
  fvalues=[sum((support(rs)&mask).bit_count() for rs in final.values()) for mask in binmask];names={name:int(n) for n,name in ep['net_names'].items()};target=defaultdict(int);net=None
  for line in Path(row['target_route']).read_text().splitlines():
   m=re.match(r'Net\s+\d+\s+\((.*?)\)',line)
   if m:net=names.get(m[1]);continue
   m=re.match(r'\s*Node:\s*(\d+)',line)
   if m and net in initial:target[net]|=masks.get(int(m[1]),0)
  truth=[sum((choice&mask).bit_count() for choice in target.values()) for mask in binmask];p=read(row['payload']);assert lower==p['lower'] and upper==p['upper'] and fvalues==p['final'] and truth==p['truth'];assert [list(k) for k in keys]==p['keys'] and caps==p['capacity'];k=row['k'];tt=sorted(range(len(bins)),key=lambda i:(-F(truth[i],caps[i]),keys[i]))[:k];ft=sorted(range(len(bins)),key=lambda i:(-F(fvalues[i],caps[i]),keys[i]))[:k];assert tt==p['truth_topK'] and ft==p['final_topK'];excluded=[];guaranteed=[]
  lo=[F(a,c) for a,c in zip(lower,caps)];hi=[F(a,c) for a,c in zip(upper,caps)]
  for t in tt:
   certain=[i for i in range(len(bins)) if i!=t and (lo[i]>hi[t] or lo[i]==hi[t] and keys[i]<keys[t])];possible=[i for i in range(len(bins)) if i!=t and (hi[i]>lo[t] or hi[i]==lo[t] and keys[i]<keys[t])];r=p['rank_bounds'][t];assert r['certain_outrankers']==certain and r['best_rank_lower_bound']==len(certain)+1 and r['worst_rank_upper_bound']==len(possible)+1
   if len(certain)>=k:excluded.append(t)
   if len(possible)<k:guaranteed.append(t)
  assert excluded==row['truth_bins_excluded_even_by_intervals'] and guaranteed==row['truth_bins_guaranteed_by_intervals'];assert row['actual_hits']==len(set(tt)&set(ft)) and row['optimistic_hits_upper_bound']==k-len(excluded);rows.append({key:row[key] for key in ['case','initializer','timing_policy','priority','actual_hits','optimistic_hits_upper_bound']});print(row['case'],row['initializer'],row['timing_policy'],row['priority'],'INDEPENDENT_RANK_INTERVAL_PASS',flush=True)
  for path in [Path(row['endpoint']),Path(g),Path(row['resources']),binsfile,Path(row['target_route']),out/'initial.json',out/'round1.json',out/'receipt.json']:bindings[str(path)]=sha(path)
 assert len(rows)==72
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL72_BIN_INTERVALS_AND1440_TRUE_TOPK_RANK_WITNESSES_INDEPENDENTLY_VERIFIED','rows':rows,'bindings':bindings,'scope':'Independent bitset extrema for every bin, direct printed native target unions, final/truth ranks and all20 target-bin bound witnesses/arm. Interval optimism is not joint choice feasibility or a predictor.'},indent=2)+'\n');print('SPATIAL_RANK_INTERVALS_VERIFIED',len(rows))
if __name__=='__main__':main()
