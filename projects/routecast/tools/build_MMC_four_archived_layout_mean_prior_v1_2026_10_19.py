"""Historical ledger arithmetic only; target labels never opened."""
import pathlib,json,hashlib,time
from collections import Counter
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_four_archived_layout_mean_prior_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 t=time.perf_counter();pp=O/'protocol.json';p=json.loads(pp.read_text());assert p['weights']==[1]*4 and p['denominator']==4 and len(p['historical_states'])==4
 for f,h in p['bindings'].items():assert sha(pathlib.Path(f))==h
 total=Counter();rows=[];graphs=set();bindings={str(pp):sha(pp),str(pathlib.Path(__file__).resolve()):sha(pathlib.Path(__file__).resolve())}
 for x in p['historical_states']:
  sp=pathlib.Path(x['state']);vp=pathlib.Path(x['verification']);v=json.loads(vp.read_text());assert sha(sp)==x['state_sha256']==v['bindings'][str(sp)];s=json.loads(sp.read_text());assert s['overflow_units']==0;ledger={int(k):n for k,n in s[x['ledger_key']].items()};assert all(type(n) is int and n>0 for n in ledger.values())
  if x['tag']=='source':assert v['all_native_paths_exact'] and v['all_uniqueNET_occupancy_matches_full_printed_audit'];assert s['completed_connections']==s['required_connections']==len(s['records'])==115572
  else:assert v['all_native_physical_and_canonical_pass'] and s['all_printed_branch_arc_switch_and_union_checks_pass'] and s['routed_nets']==55300 and len(s['connections'])==115572;graphs.add(s['inputs_sha256']['graph'])
  total.update(ledger);rows.append(dict(tag=x['tag'],nonzero_nodes=len(ledger),occupancy_sum=sum(ledger.values())));bindings[str(sp)]=sha(sp);bindings[str(vp)]=sha(vp)
 assert len(graphs)==1;digest=next(iter(graphs));assert any(h==digest for h in json.loads(pathlib.Path(p['historical_states'][0]['verification']).read_text())['bindings'].values());fp=O/'occupancy_sum.json';fp.open('x').write(json.dumps(dict(denominator=4,graph_sha256=digest,summed_unique_NET_occupancy={str(n):total[n] for n in sorted(total)},historical_states=rows),separators=(',',':'))+'\n');seconds=time.perf_counter()-t
 receipt=dict(status='FOUR_FIXED_HISTORICAL_LEDGER_SUMS_PRODUCED_INDEPENDENT_AUDIT_PENDING',bindings=bindings,prior_file=str(fp),prior_sha256=sha(fp),production_seconds=seconds,target_label_files_read=0,target_specific_changes=0,scope='Equal mean of four archived native ledgers only; no proposed RouteCast innovation, current-layout model adaptation, heldout admission or speedup claim.')
 (O/'production_receipt.json').open('x').write(json.dumps(receipt,indent=2)+'\n');print({k:v for k,v in receipt.items() if k!='bindings'},flush=True)
if __name__=='__main__':main()
