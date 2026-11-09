"""Conservative token comparison permitting only generated internal ID renaming."""
import hashlib,json,re
from pathlib import Path
from zipfile import ZipFile
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_large_traffic_RTL_identifier_audit_20261015';D=R/'work/native_commit_42path_256reads_RTL_diagnostic_v2_20261015'
def tokens(s):
 out=[];i=0;ops=['<<<','>>>','===','!==','&&&','<<','>>','<=','>=','==','!=','&&','||','~&','~|','~^','^~','**','+:','-:','=>','*>']
 while i<len(s):
  c=s[i]
  if c.isspace():i+=1;continue
  if s.startswith('//',i):
   j=s.find('\n',i);i=len(s) if j<0 else j+1;continue
  if s.startswith('/*',i):j=s.find('*/',i+2);assert j>=0;i=j+2;continue
  if c=='"':
   j=i+1
   while j<len(s):
    if s[j]=='\\':j+=2;continue
    if s[j]=='"':break
    j+=1
   assert j<len(s);out.append(('string',s[i:j+1]));i=j+1;continue
  if c=='\\':
   j=i+1
   while j<len(s) and not s[j].isspace():j+=1
   out.append(('escaped',s[i:j]));i=j;continue
  if c.isalpha() or c in '_$':
   j=i+1
   while j<len(s) and (s[j].isalnum() or s[j] in '_$'):j+=1
   out.append(('identifier',s[i:j]));i=j;continue
  if c.isdigit() or c=="'":
   j=i+1
   while j<len(s) and (s[j].isalnum() or s[j] in "_'?"):j+=1
   out.append(('number',s[i:j]));i=j;continue
  op=next((v for v in ops if s.startswith(v,i)),None)
  if op:out.append(('operator',op));i+=len(op)
  else:out.append(('punctuation',c));i+=1
 return out
def declarations(text):return [re.sub(r'\s+',' ',v.strip()) for v in text.splitlines() if re.match(r'^(input|output|inout|parameter)\s',v)]
def shape(name):
 name=re.sub(r'(_fu_|_reg_|^reg_)(\d+)',lambda m:m[1]+'#',name)
 return re.sub(r'(ap_predicate_op)(\d+)',lambda m:m[1]+'#',name)
def compare(old,new,protected):
 if declarations(old)!=declarations(new):return dict(passed=False,reason='interface_declarations_differ')
 a=tokens(old);b=tokens(new)
 if len(a)!=len(b):return dict(passed=False,reason='token_counts_differ',old_tokens=len(a),new_tokens=len(b))
 forward={};back={}
 for i,(left,right) in enumerate(zip(a,b)):
  if left==right:continue
  kind,x=left;other,y=right
  if kind!='identifier' or other!='identifier' or x in protected or y in protected or shape(x)==x or shape(x)!=shape(y):return dict(passed=False,reason='nonpermitted_token_difference',index=i,old=left,new=right)
  if forward.get(x,y)!=y or back.get(y,x)!=x:return dict(passed=False,reason='nonbijective_or_inconsistent_rename',index=i,old=x,new=y)
  forward[x]=y;back[y]=x
 for i,((kind,x),(other,y)) in enumerate(zip(a,b)):
  if (kind,forward.get(x,x) if kind=='identifier' else x)!=(other,y):return dict(passed=False,reason='rename_not_consistent_at_all_occurrences',index=i,old=x,new=y)
 return dict(passed=True,tokens=len(a),renamed_identifiers=len(forward),mapping=forward)
def main():
 P.mkdir(exist_ok=False);xo=R/'work/native_higher_g_hw_emu_link_20261015/commit.xo';candidate=D/'project/solution1/syn/verilog';report=json.loads((D/'independent_audit.json').read_text());assert report['RTL_calls']==45
 with ZipFile(xo) as z:old={Path(n).name:z.read(n).decode() for n in z.namelist() if '/hdl/verilog/' in n and n.endswith('.v')}
 new={f.name:f.read_text() for f in candidate.glob('*.v')};assert old.keys()==new.keys() and len(old)==39
 protected=set()
 for text in list(old.values())+list(new.values()):
  for decl in declarations(text):protected.update(value for kind,value in tokens(decl) if kind=='identifier')
  protected.update(re.findall(r'\bmodule\s+(\w+)',text))
 results={};mapping={}
 for name in sorted(old):
  result=compare(old[name],new[name],protected);mapping[name]=result.pop('mapping',{});results[name]=result
 unresolved={k:v for k,v in results.items() if not v['passed']}
 negatives={}
 top='dieroute_net_commit_sharded_hbm.v';needle="64'd0";assert needle in new[top]
 negatives['numeric_constant_change_rejected']=not compare(old[top],new[top].replace(needle,"64'd1",1),protected)['passed']
 negatives['external_clock_port_rename_rejected']=not compare(old[top],re.sub(r'\bap_clk\b','changed_external_clock',new[top]),protected)['passed']
 assert all(negatives.values())
 (P/'identifier_maps.json').write_text(json.dumps(mapping,indent=2)+'\n')
 files=[xo,D/'independent_audit.json',P/'identifier_maps.json',Path(__file__).resolve()]+list(candidate.glob('*.v'))
 result=dict(status='all39_RTL_token_streams_match_under_generated_identifier_bijections' if not unresolved else 'RTL_identifier_comparison_unresolved',modules=results,unresolved=unresolved,negative_controls=negatives,protected_identifiers=len(protected),source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},scope='Direct comparison of packaged waiting-image commit XO versus enlarged-marshalling diagnostic HDL. All operators/numeric and string literals/module interfaces and parameters remain exact; only bijective generated fu/reg/predicate ID renaming is allowed, with consistent use across each complete module. Whitespace/comments excluded. This is syntactic identifier isomorphism, not solver-based formal equivalence, package/system/interconnect verification, timing signoff or fullnativegraph XRT success.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=result['status'],modules=len(results),unresolved=unresolved,negative_controls=negatives)))
if __name__=='__main__':main()
