"""Check conflict-resource membership of every complete found OPIN alternative."""
import pathlib,json,array,sys,hashlib,bisect,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 matrix=BASE/'fixed_opin_candidate_matrix';complete=BASE/'fixed_opin_candidate_matrix_completion/receipt.json';affected=BASE/'additional_high_fanout_physical_audit/affected_conflict_connections.json';csr=BASE/'streaming_csr_class_cache_v3/csr'
 c=json.loads(complete.read_text());assert c['parent_receipt_sha256']==sha(matrix/'receipt.json');mr=json.loads((matrix/'receipt.json').read_text());assert mr['results_sha256']==sha(matrix/'results.json')
 mp=json.loads((matrix/'protocol.json').read_text());assert sha(affected)==mp['inputs'][str(affected.relative_to(ROOT))]
 m=json.loads((csr/'manifest.json').read_text());assert sha(csr/'manifest.json')==mp['inputs'][str((csr/'manifest.json').relative_to(ROOT))]
 rows=[r for r in json.loads((matrix/'results.json').read_text()) if r['status']=='FOUND'];wanted={eid for r in rows for eid in r['physical_edge_ids']};data={};hashes={}
 for k in ['node_ids','row_offsets','edge_ids','dest_ranks']:
  spec=m['files'][k];p=csr/spec['file'];h=sha(p);assert h==spec['sha256'];hashes[str(p)]=h;a=array.array(spec['type']);a.frombytes(p.read_bytes())
  if sys.byteorder!='little':a.byteswap()
  assert len(a)==spec['elements'];data[k]=a
 records={}
 for i,eid in enumerate(data['edge_ids']):
  if eid in wanted:records[eid]=(data['node_ids'][bisect.bisect_right(data['row_offsets'],i)-1],data['node_ids'][data['dest_ranks'][i]])
 assert set(records)==wanted
 requests={r['connection_id']:r for r in json.loads(affected.read_text())['affected_connections']};results=[]
 for r in rows:
  q=requests[r['connection_id']];nodes=[q['source']]
  for eid in r['physical_edge_ids']:
   a,b=records[eid];assert a==nodes[-1];nodes.append(b)
  assert nodes[-1]==q['sink'] and len(nodes)==len(set(nodes));conflicts=sorted(set(nodes)&set(q['conflict_rr_nodes']))
  results.append({'connection_id':r['connection_id'],'opin':r['opin'],'attributed_conflict_nodes_still_used':conflicts,'avoids_attributed_conflicts':not conflicts})
 out=BASE/'opin_candidate_conflict_membership';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes());(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 result={'matrix_completion_sha256':sha(complete),'matrix_results_sha256':mr['results_sha256'],'affected_sha256':sha(affected),'payload_sha256':hashes,'source_sha256':sha(pathlib.Path(__file__)),'results_sha256':sha(out/'results.json'),'found_candidates':len(rows),'avoids_attributed_conflicts':sum(v['avoids_attributed_conflicts'] for v in results),'scope':'authenticated CSR selected physical-path membership only; full XML candidate audit pending; no candidate acceptance or universal impossibility beyond prior separate proof'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'found_candidates':len(rows),'avoids_attributed_conflicts':result['avoids_attributed_conflicts']}))
if __name__=='__main__':main()
