"""Read completed new-variant parent counters without rerunning or editing routing."""
from pathlib import Path
import json,hashlib,argparse

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('parent',type=Path);p.add_argument('reference',type=Path);p.add_argument('recipe',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 assert not a.output.exists();manifest=json.loads((a.parent/'manifest.json').read_text());assert manifest['status']=='online_router_completed_equivalence_audit_required' and manifest['returncode']==0
 recipe=json.loads(a.recipe.read_text());step=recipe['steps'][0];env=step['routing_environment'];assert env['DIEROUTE_SPECULATIVE_WORKERS']=='0' and step['command'][-1]=='downstream_bounded'
 actual=json.loads((a.parent/'route.json').read_text());reference=json.loads((a.reference/'route.json').read_text());assert actual['mode']=='downstream_bounded' and actual['execution']=='serial_cpp_reference' and actual['cost_state_bits']==64;assert 0<actual['iterations']<=30 and actual['flat_searches']>=actual['fallbacks']
 result={'status':'completed_new_variant_parent_aggregate_work_counters_reviewed','conditional_capacity_searches':actual['flat_searches']-actual['fallbacks'],'parent_router_legal_flag':actual['legal'],'actual':{k:actual[k] for k in ['iterations','expanded','edge_visits','flat_searches','fallbacks','wall_ms','overused_resources']},'reference':{k:reference[k] for k in ['iterations','expanded','edge_visits','flat_searches','fallbacks','wall_ms','overused_resources']},'source_sha256':{str(p.resolve()):sha(p) for p in [a.parent/'manifest.json',a.parent/'route.json',a.reference/'route.json',a.recipe,Path(__file__)]},'scope':'Serial hierarchical variant only; flat_searches minus fallback calls counts conditional searches in this version. Aggregate work, not a paired speedup or stage-time decomposition. Router legal flag requires independent tree/native validation; parent only, no complete quality or full-policy acceleration claim.','research_complete':False}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'conditional_capacity_searches':result['conditional_capacity_searches'],'research_complete':False}))
if __name__=='__main__':main()
