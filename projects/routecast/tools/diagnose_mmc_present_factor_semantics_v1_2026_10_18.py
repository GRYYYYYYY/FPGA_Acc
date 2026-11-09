"""Read-only prospective present multiplier sensitivity; no target route labels."""
import hashlib,json,struct
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
O=R/'experiments/mmc_present_factor_semantics_v1_2026-10-18'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def main():
 protocol=O/'protocol.json';p=json.loads(protocol.read_text())
 for name,digest in p['bindings'].items():assert sha(name)==digest,name
 nodes={};factor=None
 with (R/'experiments/mmc_dense_post_STA_source_v1_2026-10-18/context.tsv').open() as f:
  for line in f:
   x=line.split()
   if x[0]=='H':factor=float(x[2])
   elif x[0]=='N':
    n,occ,cap,bits=map(int,x[1:5]);history=struct.unpack('<f',struct.pack('<I',bits))[0]
    assert history==float(x[5]) and cap>=0 and 0<=occ<=cap
    nodes[n]=(occ,cap,history)
 assert len(nodes)==904438 and factor==73.0959702
 cases=[]
 for case in ['source','case_01','case_02','case_03']:
  if case=='source':ledger={n:v[0] for n,v in nodes.items() if v[0]}
  else:
   state=json.loads((R/f'experiments/mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained/initial.json').read_text())
   ledger={int(n):int(c) for n,c in state['ledger'].items()}
  assert all(n in nodes and c>0 and nodes[n][1]>0 for n,c in ledger.items())
  enter=Counter();keep=Counter();owner_incidence=Counter();saturated=0;overused=0;overflow=0
  for n,(_,cap,_) in nodes.items():
   if cap<=0:continue
   occ=ledger.get(n,0);m=max(0,occ-cap+1)
   enter[m]+=1
   saturated+=occ==cap;overused+=occ>cap;overflow+=max(0,occ-cap)
   if occ:
    k=max(0,occ-cap);keep[k]+=1;owner_incidence[k]+=occ
    assert k==max(0,(occ-1)-cap+1)
  cases.append(dict(case=case,overflow_units=overflow,saturated_nodes=saturated,overused_nodes=overused,enter_nonowner_m_histogram=dict(sorted(enter.items())),keep_old_owner_m_histogram=dict(sorted(keep.items())),keep_old_owner_incidence_m_histogram=dict(sorted(owner_incidence.items())),enter_sensitive_nodes=sum(v for m,v in enter.items() if m),keep_sensitive_nodes=sum(v for m,v in keep.items() if m)))
 log=(R/'experiments/mmc_dense_post_STA_source_v1_2026-10-18/native.log').read_text()
 for line in ['RouterOpts.first_iter_pres_fac: 0.000000','RouterOpts.initial_pres_fac: 0.500000','RouterOpts.pres_fac_mult: 1.300000']:assert line in log
 result=dict(status='present_factor_initial_state_sensitivity_measured',bindings={**p['bindings'],str(protocol):sha(protocol),str(Path(__file__).resolve()):sha(Path(__file__).resolve())},cases=cases,m1_multiplier_examples={'first_native_iteration':1,'native_second_iteration':1.5,'model_both_rounds':2,'source_last_observed_decimal':1+factor},interpretation='At source feasible saturation a nonowner can still incur a present penalty although there is no overflow; an existing owner sees no present penalty after virtual release. Initial target penalties after release occur only on overused resources. These are potential node-entry costs, not actual search visitation counts or whole-path scores.',native_contract_caveats=['Native get_rr_cong_cost sums non-configurable companions; this diagnostic counts individual RR nodes only.','Native per-NET structural base scaling and floating arithmetic have not been equated to model integer units.','Model adds static channel-span prices; matching present factor alone cannot establish native score equality.','Native history updates after routing except first iteration; model updates before round1 from completed round0, with round0 skipped.','Neither restarting native schedule nor inheriting final source factor is validated by this diagnostic.'],scope='No target cold labels read; no model choices, quality gain, native utility, or runtime gain established.')
 (O/'results.json').open('x').write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'cases':cases},indent=2),flush=True)
if __name__=='__main__':main()
