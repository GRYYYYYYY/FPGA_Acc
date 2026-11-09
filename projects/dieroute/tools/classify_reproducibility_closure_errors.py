"""Describe terminal closure exceptions and exact-byte alternatives without repair."""
from pathlib import Path
import json,collections,hashlib
R=Path(__file__).resolve().parents[1]
O=R/'work/reproducibility_dependency_closure_20261021'
def main():
 source=O/'audit.json'
 if not source.exists():
  print(json.dumps({'status':'original_scan_not_terminal_no_classification'}));return
 data=json.loads(source.read_text());byhash=collections.defaultdict(list);parents=collections.defaultdict(set)
 for path,row in data['files'].items():byhash[row['sha256']].append(path)
 for edge in data['edges']:
  if edge['source']:parents[edge['target']].add(edge['source'])
 roots={str((R/p).resolve()) for p in data['roots']};rows=[]
 for error in data['errors']:
  path=error['path'];seen={path};pending=[path]
  while pending:
   child=pending.pop()
   for parent in parents[child]:
    if parent not in seen:seen.add(parent);pending.append(parent)
  alternatives=byhash.get(error.get('expected'),[])
  rows.append({'original_exception':error,'kind':'recorded_digest_mismatch' if 'expected' in error else 'read_or_stability_exception','roots_with_dependency_path':sorted(roots&seen),'same_digest_paths_observed_in_scan':alternatives,'alternatives_rehashed_now':False,'interpretation':'Dependency reachability is not proof that scientific outputs are wrong. Alternative paths require current hash verification and provenance review; original exception is retained.'})
 out=O/'exception_classification.json'
 with out.open('x') as f:json.dump({'status':'terminal_exceptions_classified_without_source_mutation','scan_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'unique_files':data['unique_files'],'reference_edges':data['reference_edges'],'exceptions':rows,'unresolved_hash_field_forms':data['unresolved_hash_field_forms'],'json_parse_errors':data['json_parse_errors'],'scope':'Structural dependency tracing and observed same-byte alternatives only. No restored source, fixed provenance, full portability or gate closure claim.','research_complete':False},f,indent=2);f.write('\n')
 print(json.dumps({'exceptions':rows,'unresolved_hash_field_forms':len(data['unresolved_hash_field_forms'])}))
if __name__=='__main__':main()
