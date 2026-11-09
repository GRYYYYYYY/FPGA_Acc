"""All3 baseline criticality exactness plus all6 corrected warm path snapshots."""
import csv,json,hashlib
from pathlib import Path
from fixed_nominal_timing_feedback_v2 import FixedNominalTimingFeedback
from zero_rc_budget_certificate_graph_v1 import load_graph
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_fixed_nominal_feedback_contract_v2_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);graph=E/'prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/rr_graph.xml';g=load_graph(graph);bindings={str(graph):sha(graph)};results=[]
 for episode in ('episode_01','episode_02','episode_03'):
  case='w160/'+episode;base=E/'prospective_external_family_clock_constraints_v1_2026-10-19'/case;comp=E/'prospective_external_family_delay_components_v1_2026-10-19'/case/'scaled/components_before.tsv';mp=E/'prospective_external_family_current_timing_graph_v1_2026-10-19'/case/'external_edge_CID_bindings_v1.json';initial=E/'prospective_external_family_frame_timings_v1_2026-10-19'/case/'initial_connection_criticalities.json';meta=read(initial);model=FixedNominalTimingFeedback(base,comp,read(mp),base/'timing_atoms.tsv',meta,g)
  RR={(int(x['net']),int(x['pin'])):float(x['delay_s']) for x in csv.DictReader((base/'initial_connections.tsv').open(),delimiter='\t')};rows=model.analyze_rr(RR)
  fields=('criticality_bits','raw_criticality_bits','slack_bits','criticality_numerator','criticality_denominator');bad=[m['connection_id'] for m in meta if any(rows[m['connection_id']][k]!=m[k] for k in fields)];assert not bad,bad[:10]
  result=dict(case=case,baseline_connections=len(rows),baseline_mismatches=len(bad),warm=[])
  for init in ('raw_min','native_retained'):
   p=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19/warm'/case/init/'initial.json';records=read(p)['records'];updated=model.from_records(records);changed=sum(updated[cid]['criticality_bits']!=rows[cid]['criticality_bits'] for cid in rows);out=D/case/init;out.mkdir(parents=True);payload=out/'criticalities.json';payload.write_text(json.dumps(list(updated.values()))+'\n');result['warm'].append(dict(initializer=init,connections=len(updated),changed_from_nominal=changed));bindings[str(p)]=sha(p);bindings[str(payload)]=sha(payload)
  for p in [comp,mp,initial,*base.glob('*.tsv')]:bindings[str(p)]=sha(p)
  results.append(result);print(json.dumps(result),flush=True)
 for p in [Path(__file__),R/'tools/fixed_nominal_timing_feedback_v2.py',R/'tools/nominal_component_timing_bridge_v1.py',R/'tools/zero_rc_native_float_delay_v1.py',R/'tools/native_setup_reference_v1.py',R/'tools/load_native_clock_constraints_v1.py']:bindings[str(p.resolve())]=sha(p)
 assert all(sha(Path(k))==v for k,v in bindings.items())
 (D/'verification.json').write_text(json.dumps(dict(status='ALL3_BASELINE_CRITICALITY_EXACT_AND_ALL6_WARM_PHYSICAL_PATH_FEEDBACK_COMPLETE',rows=results,bindings=bindings,scope='Fixed nominal local components; warm snapshots internally calculated, not claimed equal native remapped packing timing.'),indent=2)+'\n')
if __name__=='__main__':main()
