"""Verify completed explicit-API coverage repeats and current evidence-file integrity."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'work/rr_view_access_coverage_variant_20261015'
cache={};bytes_hashed=0

def sha(path):
 global bytes_hashed
 path=Path(path).resolve();key=str(path)
 if key not in cache:
  h=hashlib.sha256()
  with path.open('rb') as stream:
   for b in iter(lambda:stream.read(1048576),b''):h.update(b);bytes_hashed+=len(b)
  cache[key]=h.hexdigest()
 return cache[key]

def refs(obj):
 for f,h in obj.get('source_sha256',{}).items():assert sha(f)==h,f

def main():
 result=json.loads((p/'native_result.json').read_text());assert result['status']=='ten_native_view_access_coverage_runs_and_independent_audits_complete'
 protocol=json.loads((p/'native_protocol.json').read_text());refs(protocol);refs(result)
 for f in result['source_sha256']:
  if f.endswith('.json'):refs(json.loads(Path(f).read_text()))
 total=dict(proposal_phases=0,unique_node_occurrences=0,resource_api_calls=0,cost_api_calls=0,stale_replays=0);rows=[];previous=None;comparisons=0
 for i in range(5):
  control=p/f'native_runs/control_{i}';covered=p/f'native_runs/covered_{i}'
  a={f.name:f for f in control.glob('route.*')};b={f.name:f for f in covered.glob('route.*')}
  assert set(b)-set(a)=={'route.view_access_coverage.bin','route.view_access_summary.csv'} and not set(a)-set(b)
  for name,f in a.items():
   if name=='route.json':
    left,right=json.loads(f.read_text()),json.loads(b[name].read_text());left.pop('wall_ms');right.pop('wall_ms');assert left==right
   else:assert sha(f)==sha(b[name]),(i,name)
   comparisons+=1
  coverage=json.loads((covered/'view_coverage_audit.json').read_text());reads=json.loads((covered/'observed_read_audit.json').read_text());report=json.loads((covered/'route.json').read_text())
  assert coverage['status']=='explicit_view_api_census_exactly_matches_observed_journal_nodes'
  assert coverage['proposal_phases']==report['speculative_proposals']
  assert coverage['unique_node_occurrences']==reads['observed_read_rows_checked']==report['speculative_read_entries']
  assert reads['fresh_replays_checked']==reads['stale_proposals_checked']==report['speculative_replays']
  assert reads['final_resources_and_costs_byte_equivalent'] and reads['cpu_legal']
  assert (covered/'route.observed_reads.bin').stat().st_size==64*coverage['unique_node_occurrences']
  assert (covered/'route.view_access_coverage.bin').stat().st_size==48*coverage['unique_node_occurrences']
  counts={k:coverage[k] for k in ['proposal_phases','unique_node_occurrences','resource_api_calls','cost_api_calls']};counts['stale_replays']=reads['fresh_replays_checked']
  hashes={name:sha(f) for name,f in b.items() if name!='route.json'}
  if previous is not None:assert previous==(counts,hashes)
  previous=(counts,hashes)
  for key,value in counts.items():total[key]+=value
  rows.append(dict(repeat=i,counts=counts))
 quality={}
 for arm in ['control','covered']:
  q=result['outcomes'][arm]['native_qor'];assert q['legal'] and q['vpr_exit_status']==0
  quality[arm]=dict(wirelength=q['total_wirelength'],cpd_ns=q['critical_path_delay_ns'],joint_quality_pass=q['total_wirelength']<=q['baseline_wirelength'] and q['critical_path_delay_ns']<=q['baseline_cpd_ns'])
 assert quality['control']==quality['covered'] and not quality['covered']['joint_quality_pass']
 files=[p/'native_result.json',p/'native_protocol.json',Path(__file__).resolve()]
 digests={str(f):sha(f) for f in files}
 report=dict(status='ten_native_explicit_api_coverage_runs_integrity_and_counts_reviewed_quality_failed',covered_repeats=5,control_repeats=5,covered_runs=rows,covered_totals=total,quality=quality,matched_control_artifacts=comparisons,verified_unique_files=len(cache),streamed_bytes_hashed=bytes_hashed,source_sha256=digests,scope='Current unique referenced files,includinglargevalue/censuslogs,stream-hashedonce. All5covered explicitAPIcensuses composewithfrozen independent value/staleness/resource/tree/sessionreplays. Control/coveredbytes andcoveredrepeatdeterminism checked. Per-armnativevalidationonewithrepeatartifactsverified. APIcostcountsinclude diagnostic snapshotqueries;notarbitrarypointerinstrumentation,searchrerun,physicaltrafficorqualitywaiver.',board_result=False,research_complete=False)
 with (p/'independent_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(json.dumps({k:report[k] for k in ['status','covered_totals','quality','matched_control_artifacts','verified_unique_files','streamed_bytes_hashed']}))

if __name__=='__main__':main()
