"""Actual distinct-net pin ownership inventory, excluding reservations not inferred."""
import pathlib,json,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=BASE/'full_path_pin_witness';decomp=BASE/'full_occupancy_type_diagnosis';eq=BASE/'full_pin_equivalence_binding';parent=BASE/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host'
 inputs={str(p):sha(p) for p in [src/'witness.json',src/'receipt.json',decomp/'report.json',decomp/'completion.json',eq/'report.json',parent/'prediction.json']}
 sr=json.loads((src/'receipt.json').read_text());dr=json.loads((decomp/'report.json').read_text());dc=json.loads((decomp/'completion.json').read_text());er=json.loads((eq/'report.json').read_text())
 assert sha(src/'witness.json')==sr['witness_sha256']
 assert sha(decomp/'report.json')==dc['report_sha256'] and dc['all_receipt_bindings_and_aggregate_checks_pass']
 assert sha(parent/'prediction.json')==dr['prediction_sha256']
 assert er['inputs_sha256'][str(src/'witness.json')]==sha(src/'witness.json')
 owners=collections.defaultdict(set);net_outputs=collections.defaultdict(set);meta={};pairs=set()
 for row in json.loads((src/'witness.json').read_text()):
  pair=(row['connection_id'],row['role']);assert pair not in pairs;pairs.add(pair)
  pin=row['actual_pin_node'];net=row['net_id'];owners[pin].add(net)
  identity=(row['role'],row['class_node'],row['block_id'],row['port'],row['actual_ptc'])
  if pin in meta:assert meta[pin]==identity
  meta[pin]=identity
  if row['role']=='SOURCE':net_outputs[net].add(pin)
 assert len(pairs)==163220 and len(net_outputs)==61314
 occupancy=json.loads((parent/'prediction.json').read_text())['node_occupancy'];reports={}
 for role,kind in [('SOURCE','OPIN'),('SINK','IPIN')]:
  selected={pin:nets for pin,nets in owners.items() if meta[pin][0]==role}
  assert all(occupancy[str(pin)]==len(nets) for pin,nets in selected.items())
  totals={'occupied_nodes':len(selected),'net_node_touches':sum(map(len,selected.values())),'overused_nodes':sum(len(v)>1 for v in selected.values()),'overflow_units':sum(max(0,len(v)-1) for v in selected.values())}
  assert all(value==dr['reports']['prediction'][kind][key] for key,value in totals.items())
  reports[kind]=totals
 hist=collections.Counter(map(len,net_outputs.values()));multi=[{'net_id':n,'opin_nodes':sorted(pins)} for n,pins in sorted(net_outputs.items()) if len(pins)>1]
 out=BASE/'full_pin_ownership_inventory';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 rows=[{'pin_node':pin,'role':meta[pin][0],'class_node':meta[pin][1],'block_id':meta[pin][2],'port':meta[pin][3],'ptc':meta[pin][4],'net_ids':sorted(nets)} for pin,nets in sorted(owners.items())]
 (out/'owners.json').write_text(json.dumps(rows)+'\n');(out/'multi_opin_nets.json').write_text(json.dumps(multi)+'\n')
 assert all(sha(pathlib.Path(p))==h for p,h in inputs.items())
 result={'inputs_sha256':inputs,'source_sha256':sha(pathlib.Path(__file__)),'owners_sha256':sha(out/'owners.json'),'multi_opin_nets_sha256':sha(out/'multi_opin_nets.json'),'reports':reports,'opin_count_per_net_histogram':dict(sorted(hist.items())),'multi_opin_nets':len(multi),'scope':'retained predicted cohort actual ownership only; excluded clock/constant/undriven reservations not supplied; multiple OPINs not by itself declared illegal'}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'reports':reports,'opin_count_per_net_histogram':result['opin_count_per_net_histogram'],'multi_opin_nets':len(multi)}))
if __name__=='__main__':main()
