"""Independent actual XML paths and occupancy for partially aligned factors."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from streaming_prediction_audit import verify

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_native_factor_prediction_2026-10-06';receipt=json.loads((out/'receipt.json').read_text());assert sha(out/'protocol.json')==receipt['protocol_sha256'];rows=[]
 for r in receipt['results']:
  d=out/r['design'];assert sha(d/'prediction.json')==r['prediction_sha256'] and sha(r['endpoint_path'])==r['endpoint_sha256'];p=json.loads((d/'prediction.json').read_text());ep=json.loads(Path(r['endpoint_path']).read_text());a=verify(r['graph']['path'],ep,p,topology=True);assert a['all_physical_and_union_checks_passed'] and a['all_type_overuse_units']==r['final']['all_type_overuse_units'];(d/'physical_audit.json').write_text(json.dumps(a)+'\n');rows.append({'design':r['design'],'overuse':a['all_type_overuse_units'],'wall_s':r['wall_s'],'audit_sha256':sha(d/'physical_audit.json'),'internal_reconvergent_nets':a['net_union_topology']['internal_reconvergent_net_count']})
 (out/'audited_summary.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(__file__),'rows':rows},indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
