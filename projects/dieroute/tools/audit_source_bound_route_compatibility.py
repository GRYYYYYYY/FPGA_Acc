"""Compare source-bound and legacy native metrics/CSV bytes on frozen routes."""
from pathlib import Path
import csv,hashlib,json,sys
D=Path(sys.argv[1]).resolve()
def main():
 p=json.loads((D/'protocol.json').read_text());native=json.loads((D/'independent_audit.json').read_text());assert native['status']=='native_routed0_observations_provenance_and_quality_reviewed';refs={};results=[]
 def sha(f):
  f=Path(f);h=hashlib.sha256(f.read_bytes()).hexdigest();refs[str(f)]=h;return h
 def table(f):
  with Path(f).open() as s:rows=list(csv.DictReader(s))
  values={int(v['task_id']):{k:int(x) for k,x in v.items()} for v in rows};assert len(rows)==len(values);return values
 for comparison in p['comparisons']:
  legacy_csv=Path(comparison['legacy_csv']);newcase=D/comparison['source_bound_case'];newcsv=newcase/'native_observations.csv';legacy_validation=Path(comparison['legacy_validation']);newvalidation=newcase/'native_validation/validation.json';old=json.loads(legacy_validation.read_text());new=json.loads(newvalidation.read_text());a=table(legacy_csv);b=table(newcsv);assert set(a)==set(b);metrics_equal=all(old[k]==new[k] for k in ['legal','total_wirelength','critical_path_delay_ns']);equal_bytes=sha(legacy_csv)==sha(newcsv);sha(legacy_validation);sha(newvalidation)
  deltas={k:max(abs(b[t][k]-a[t][k]) for t in a) for k in ['delay_ps','slack_ps','criticality_q','critical_path_delay_ps']}
  results.append({'name':comparison['name'],'connections':len(a),'legacy_native_legal':old['legal'],'source_bound_native_legal':new['legal'],'legacy_metrics':{'wirelength':old['total_wirelength'],'cpd_ns':old['critical_path_delay_ns']},'source_bound_metrics':{'wirelength':new['total_wirelength'],'cpd_ns':new['critical_path_delay_ns']},'metrics_identical':metrics_equal,'timing_CSV_bytes_identical':equal_bytes,'maximum_absolute_field_differences':deltas})
 expected=json.loads(Path(p['expected_candidate_validation']).read_text());actual=json.loads((D/'candidate_legacy/native_validation/validation.json').read_text());assert all(expected[k]==actual[k] for k in ['legal','total_wirelength','critical_path_delay_ns']);sha(p['expected_candidate_validation']);sha(D/'protocol.json');sha(D/'independent_audit.json');sha(Path(__file__).resolve())
 result={'status':'all_observed_routes_source_bound_native_and_timing_compatible' if all(r['metrics_identical'] and r['timing_CSV_bytes_identical'] for r in results) else 'observed_route_tool_compatibility_mismatch_requires_review','routes':results,'source_sha256':refs,'scope':'ExactmetricsandroundedpsCSVcompatibilityonlyonthese2frozenroutes. Not historicalbinarysourceidentity,nativefloat-bitidentity,all-inputequivalence,newalgorithmquality,representativevalidationorFPGAperformance. Originalfrozenstudiesunchanged.','research_complete':False,'board_result':False}
 with (D/'compatibility_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
