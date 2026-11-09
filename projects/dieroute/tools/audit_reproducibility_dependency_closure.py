"""Verify hash-bearing dependency references; report scope gaps without gate claims."""
import json,hashlib,re,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1]
O=R/'work/reproducibility_dependency_closure_20261021'
ROOTS=['work/current_research_claim_matrix_v22_20261021/matrix.json','work/power2_delta_quotient_hw_20261021/XO_interface_review.json','work/power2_delta_quotient_candidate_20261021/RTL_cosim_review.json','work/power2_delta_quotient_helper_RTL_20261021/review.json','work/terminal_cohort_evidence_draft_20261021/evidence_update_manifest.json']
def main():
 assert not (O/'audit.json').exists()
 receipt={'pid':os.getpid(),'start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19]}
 (O/'launch_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 queue=[(R/p,None,None) for p in ROOTS];cache={};records={};edges=[];errors=[];parse_errors=[];other_hash_fields=[]
 def write(n,d):
  t=O/(n+'.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(O/n)
 last=0;total_bytes=0
 while queue:
  path,expected,origin=queue.pop();path=path.resolve();name=str(path)
  edges.append({'source':origin,'target':name,'expected_sha256':expected})
  if name in cache:
   if expected and cache[name]!=expected:errors.append({'path':name,'source':origin,'expected':expected,'actual':cache[name]})
   continue
  try:
   before=path.stat();h=hashlib.sha256()
   with path.open('rb') as f:
    for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
   after=path.stat();actual=h.hexdigest();cache[name]=actual
   if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):errors.append({'path':name,'error':'changed_during_read'})
   if expected and actual!=expected:errors.append({'path':name,'source':origin,'expected':expected,'actual':actual})
   records[name]={'sha256':actual,'bytes':after.st_size,'json_dependency_maps':0};total_bytes+=after.st_size
   if path.suffix=='.json':
    try:data=json.loads(path.read_text())
    except (ValueError,UnicodeError) as e:parse_errors.append({'path':name,'error':str(e)});continue
    def visit(v,loc=''):
     if isinstance(v,dict):
      for key,value in v.items():
       if key in ['source_sha256','archived_inputs_sha256','report_sha256','files_sha256'] and isinstance(value,dict):
        records[name]['json_dependency_maps']+=1
        for raw,digest in value.items():
         if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):
          other_hash_fields.append({'source':name,'field':loc+'/'+key,'key':raw,'reason':'nonliteral_sha256'});continue
         q=Path(raw)
         if not q.is_absolute():
          candidates=[R/q,path.parent/q]
          existing=[x.resolve() for x in candidates if x.exists()]
          q=existing[0] if existing else R/q
          if len(set(existing))>1:other_hash_fields.append({'source':name,'key':raw,'reason':'ambiguous_relative_path','candidates':[str(x) for x in existing]})
         queue.append((q,digest,name))
       elif key=='sources' and isinstance(value,dict):
        for entry in value.values():
         if isinstance(entry,dict) and isinstance(entry.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',entry['sha256']) and 'source' in entry:
          q=Path(entry['source']);queue.append((q if q.is_absolute() else R/q,entry['sha256'],name))
       visit(value,loc+'/'+key)
     elif isinstance(v,list):
      for i,item in enumerate(v):visit(item,loc+'/'+str(i))
    visit(data)
  except (OSError,RuntimeError) as e:cache[name]=None;errors.append({'path':name,'source':origin,'error':str(e)})
  if time.monotonic()-last>10:
   write('manifest.json',{'status':'running_readonly_dependency_hash_audit','pid':os.getpid(),'unique_files':len(records),'bytes_hashed':total_bytes,'pending_references':len(queue),'errors':len(errors)});last=time.monotonic()
 write('audit.json',{'status':'hash_dependency_closure_terminal_requires_scope_review','roots':ROOTS,'unique_files':len(records),'bytes_hashed':total_bytes,'reference_edges':len(edges),'errors':errors,'json_parse_errors':parse_errors,'unresolved_hash_field_forms':other_hash_fields,'files':records,'edges':edges,'scope':'Recognized hash-bearing maps only; missing unhashed dependencies, build tools, command portability, licensing, environment, rerun functionality and board data remain separate requirements. This is not a runnable artifact package or G8 completion. Active physical output excluded.','research_complete':False})
 write('manifest.json',{'status':'terminal_requires_interpretation','unique_files':len(records),'errors':len(errors),'json_parse_errors':len(parse_errors),'research_complete':False})
 print(json.dumps({'unique_files':len(records),'errors':len(errors),'bytes_hashed':total_bytes,'json_parse_errors':len(parse_errors)}))
if __name__=='__main__':main()
