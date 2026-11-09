"""New independently classified global-net frontend; preserve original artifacts."""
import pathlib,json,shutil,collections,hashlib
from nonclock_global_pins import classify
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 old=ROOT/'experiments/conv_layer_frozen_frontend_2026-10-06';p=json.loads((old/'protocol.json').read_text());r=json.loads((old/'receipt.json').read_text())
 assert r['protocol_sha256']==sha(old/'protocol.json')
 for n,h in r['outputs'].items():assert sha(old/n)==h
 e=json.loads((old/'endpoints.json').read_text());m=json.loads((old/'mapping.json').read_text());inputs=p['inputs']
 for v in inputs.values():assert sha(v['path'])==v['sha256']
 bound=classify(m,inputs['packed_netlist']['path'],inputs['architecture']['path'],inputs['rr_graph']['path']);nets={v['net_id'] for v in bound};previous={v['net_id'] for v in e['excluded_nets']};new=nets-previous;counts=collections.Counter(v['net_id'] for v in e['connections']);removed=sum(counts[n] for n in new)
 e['connections']=[v for v in e['connections'] if v['net_id'] not in new]
 for n in sorted(new):e['excluded_nets'].append({'net_id':n,'net':e['net_names'][str(n)],'sink_pins':counts[n],'reason':'explicit architecture non-clock-global receiver pin; entire net global per frozen VPR semantics','global_receiver_bindings':[v for v in bound if v['net_id']==n]})
 e['nonclock_global_policy']='exclude entire nets with explicitly bound architecture is_non_clock_global receiver';m['connections']=len(e['connections']);m['excluded_nets']=e['excluded_nets'];out=ROOT/'experiments/conv_layer_global_frontend_v2_2026-10-06';out.mkdir();(out/'source').mkdir()
 for n in ['revise_conv_layer_global_endpoints.py','nonclock_global_pins.py']:shutil.copyfile(ROOT/'tools'/n,out/'source'/n)
 protocol={'inputs':inputs,'parent_frontend_receipt_sha256':sha(old/'receipt.json'),'source_sha256':{v.name:sha(v) for v in (out/'source').iterdir()},'revision_provenance':'after native cohort defect discovery; classification independently from packed/architecture/RR declarations; no native route input'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 for n,v in [('endpoints.json',e),('mapping.json',m),('global_bindings.json',bound)]:(out/n).write_text(json.dumps(v)+'\n')
 assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 receipt={'protocol_sha256':sha(out/'protocol.json'),'connections':len(e['connections']),'retained_nets':len({v['net_id'] for v in e['connections']}),'newly_excluded_nets':sorted(new),'removed_connections':removed,'bound_global_receiver_pins':len(bound),'outputs':{n:sha(out/n) for n in ['endpoints.json','mapping.json','global_bindings.json']},'scope':'architecture bound frontend revision only; native alignment and classifier regression tests still required'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
