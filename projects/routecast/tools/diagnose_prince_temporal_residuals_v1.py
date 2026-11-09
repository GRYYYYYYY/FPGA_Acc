"""Post-screen cell/space residual attribution; no fitted or deployable candidate."""
import json,struct,hashlib
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_temporal_stability_v1_2026-10-20';D=E/'prince_temporal_residuals_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def q(w):return Fraction(struct.unpack('<f',struct.pack('<I',w))[0])
def encode(x):return json.loads(json.dumps(x,default=lambda f:dict(numerator=f.numerator,denominator=f.denominator)))
def main():
 D.mkdir(exist_ok=False);vp=S/'verification.json';v=load(vp);frozen=load(S/'frozen_features.json');by={r['case']:r for r in frozen['rows']};bindings={str(vp):sha(vp),str(S/'frozen_features.json'):sha(S/'frozen_features.json'),str(Path(__file__)):sha(__file__)};rows=[]
 for row in v['rows']:
  c=row['case']
  if row['status']!='SCORED':rows.append(dict(case=c,status=row['status']));continue
  fp=S/c/'input_features.jsonl';features={x['id']:x for x in map(json.loads,fp.open())};sp=S/c/'expected_counts.jsonl';scores={x['id']:x for x in map(json.loads,sp.open())};specp=E/'prince_feedback_quality_v1_2026-10-20'/c/'specification.json';spec=load(specp);lp=Path(spec['label_physical_audit']);truth={int(n):y for n,y in load(lp)['node_occupancy'].items()};folder=E/'prince_quality_domains_v1_2026-10-20'/c.split('/')[0];rp=folder/'resources.jsonl';bp=folder/'spatial_bins.json';resources=list(map(json.loads,rp.open()));bins=load(bp);cells=defaultdict(list)
  for n,x in features.items():cells[f"{x['B']},{x['P']},{x['S']}"].append(n)
  cellstats={}
  for key,ns in sorted(cells.items()):
   stats={}
   for name in ['B','BP','BPS']:
    p=[q(scores[n][name]) for n in ns];stats[name]=dict(mean_prediction=sum(p)/len(ns),signed_residual=sum((z-truth.get(n,0) for n,z in zip(ns,p)),Fraction()),squared_error=sum(((z-truth.get(n,0))**2 for n,z in zip(ns,p)),Fraction()))
   cellstats[key]=dict(resources=len(ns),occupied=sum(truth.get(n,0) for n in ns),methods=stats)
  # Resource-onset age from all already observed same-phase RR snapshots, capped at3.
  it=by[c]['iterations'][1];hist=[];src=E/'prince_input_mean_trial_v1_2026-10-20'/c/'identity'
  for t in range(max(1,it-2),it+1):
   p=src/'boundary'/f'iteration_{t}.bin';raw=p.read_bytes();assert raw[:8]==b'RCBND001' and struct.unpack_from('<Q',raw,8)[0]==t;hist.append({n:occ>0 for n,kind,occ,cap,acc in struct.iter_unpack('<QIiiI',raw[24:])});bindings[str(p)]=sha(p)
  agecells=defaultdict(list)
  for n,x in features.items():
   assert hist[-1][n]==bool(x['B']);age=0
   for frame in reversed(hist):
    if frame[n]:age+=1
    else:break
   agecells[f"{x['B']},{x['P']},{x['S']};age{age}"].append(n)
  ages={key:dict(resources=len(ns),occupied=sum(truth.get(n,0) for n in ns)) for key,ns in sorted(agecells.items())}
  adj=defaultdict(list)
  for r in resources:
   for key in r['bins']:adj[tuple(key)].append(r['id'])
  bstats=[]
  for b in bins:
   key=tuple(b['key']);ns=adj[key];cap=b['capacity'];assert len(ns)==cap;ty=Fraction(sum(truth.get(n,0) for n in ns),cap);methods={}
   for name in ['B','BP','BPS']:
    parts={cell:sum((q(scores[n][name])-truth.get(n,0) for n in ns if f"{features[n]['B']},{features[n]['P']},{features[n]['S']}"==cell),Fraction())/cap for cell in cells};pred=sum((q(scores[n][name]) for n in ns),Fraction())/cap;assert sum(parts.values())==pred-ty;methods[name]=dict(prediction=pred,residual=pred-ty,cell_residuals=parts)
   bstats.append(dict(key=list(key),capacity=cap,truth=ty,methods=methods))
  out=D/c;out.mkdir(parents=True);ap=out/'spatial_attribution.json';ap.write_text(json.dumps(encode(bstats),indent=2)+'\n');bindings[str(ap)]=sha(ap)
  for name in ['B','BP','BPS']:
   mae=sum((abs(b['methods'][name]['residual']) for b in bstats),Fraction())/len(bstats);expected=row['metrics'][name]['spatial']['mae'];assert expected==dict(numerator=mae.numerator,denominator=mae.denominator)
  toptruth={tuple(x) for x in row['metrics']['BP']['spatial']['truth_top_k']};boundary={}
  for name in ['BP','BPS']:
   selected={tuple(x) for x in row['metrics'][name]['spatial']['prediction_top_k']};boundary[name]=dict(missed_truth_bins=[b for b in bstats if tuple(b['key']) in toptruth-selected],false_selected_bins=[b for b in bstats if tuple(b['key']) in selected-toptruth]);assert len(selected&toptruth)==row['metrics'][name]['spatial']['top_k_hits']
  rows.append(dict(case=c,status='RESIDUALS_RECONCILED',cells=cellstats,onset_age_cells=ages,spatial_boundary=boundary,spatial_attribution=str(ap),failing_metrics={name:{ctrl:[x['metric'] for x in gate['checks'] if not x['nonregress']] for ctrl,gate in row['checks'][name].items()} for name in ['BP','BPS']}))
  for p in [fp,sp,specp,lp,rp,bp]:bindings[str(p)]=sha(p)
  print(c,'cells',[(k,x['resources'],x['occupied']) for k,x in cellstats.items()],'age',ages,flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'verification.json').write_text(json.dumps(encode(dict(status='CELL_RESIDUALS_SPATIAL_ATTRIBUTION_AND_ONSET_AGE_RECONCILED',rows=rows,bindings=bindings,full9_gate=False,scope='Post-screen exposed diagnostic. No label-fitted correction,retuning,tie-rule change,or candidate promotion. Age capped3 is exploratory stratification,not trained forecast.')),indent=2)+'\n')
if __name__=='__main__':main()
