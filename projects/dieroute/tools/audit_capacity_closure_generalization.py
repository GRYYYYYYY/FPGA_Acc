"""Replay general closure implementation against frozen real restoration probes."""
from pathlib import Path
import csv,collections,hashlib,json,mmap,struct,subprocess,sys
from capacity_restore_closure import restore_closure
R=Path(__file__).resolve().parents[1]
def main():
 D=R/'work/elliptic_capacity_restore_closure_20261020';p=json.loads((D/'protocol.json').read_text());construction=json.loads((D/'construction.json').read_text())
 def allocation(path):
  t=collections.defaultdict(set)
  with open(path) as f:
   for row in csv.DictReader(f):t[int(row['net_id'])].update(int(row[k]) for k in ['source','parent','child'])
  return t
 base=allocation(p['baseline_tree']);cand=allocation(p['candidate_tree']);nodes=set().union(*base.values(),*cand.values());res=R/'work/width_coverage_native_costs_20261018/elliptic_28x22_cw320_seed1/input.resources'
 with res.open('rb') as f:
  m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);cap={n:struct.unpack_from('<H',m,16*n+2)[0] for n in nodes};m.close()
 for a in construction['arms']:
  restored,waves=restore_closure(base,cand,cap,a['seed_nets']);assert restored==set(a['closure_net_ids']) and waves==a['waves']
 checker=R/'tools/check_capacity_restore_closure.py';checks=json.loads(subprocess.check_output([sys.executable,str(checker)],text=True))
 files=[R/'tools/capacity_restore_closure.py',checker,Path(__file__).resolve(),D/'construction.json',D/'independent_native_audit.json']
 result={'status':'general_capacity_closure_reproduces_all_three_real_probes','real_probes':3,'restored_nets_each':2220,'exhaustive_checks':checks,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'scope':'General reusable capacity algorithm reproduces frozen posterior outputs. This is not cross-circuit native quality generalization, minimal restoration or an FPGA implementation.','research_complete':False,'adopted':False}
 with (D/'general_algorithm_review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
