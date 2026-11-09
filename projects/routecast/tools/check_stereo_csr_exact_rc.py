"""Independent budget parity on 1157 previously XML-audited predictor paths."""
import json,time,shutil
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from prepared_csr import read
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'csr_exact_rc_budget_parity';out.mkdir();(out/'source').mkdir()
 names=('check_stereo_csr_exact_rc.py','csr_exact_buffered_rc.py','buffered_rc_context.py','buffered_rc_node_classes.py','prepared_csr.py','pre_route_endpoints.py')
 sources={n:sha(Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
 exact=b/'exact_buffered_rc_classes_v2';csr=b/'streaming_csr_class_cache_v3'/'prepared'
 # Resolve prepared payload location from the frozen experiment manifest.
 if not (csr/'manifest.json').exists():
  matches=list((b/'streaming_csr_class_cache_v3').rglob('manifest.json'))
  if len(matches)!=1:raise ValueError('ambiguous CSR manifest')
  csr=matches[0].parent
 graph=json.loads((exact/'protocol.json').read_text())['graph']['sha256']
 bound={};jobs=[]
 for folder,count in [('first_high_fanout_exact_budgets',486),('additional_high_fanout_exact_budgets',671)]:
  r=b/folder;receipt=json.loads((r/'receipt.json').read_text());p=json.loads((r/'protocol.json').read_text())
  if sha(r/'protocol.json')!=receipt['protocol_sha256'] or sha(r/'budgets.json')!=receipt['budgets_sha256']:raise ValueError('budget authentication failed')
  if p['inputs']['graph']['sha256']!=graph:raise ValueError('budget graph mismatch')
  budgets={x['connection_id']:Fraction(x['delay_seconds_numerator'],x['delay_seconds_denominator']) for x in json.loads((r/'budgets.json').read_text())}
  if len(budgets)!=count:raise ValueError('budget coverage mismatch')
  rows=[]
  for path,h in p['inputs']['snapshots'].items():
   if sha(path)!=h:raise ValueError('snapshot changed')
   bound[path]=h;d=json.loads(Path(path).read_text())
   for row in d['connections']:rows.append((row,d['net_result']['result']['paths'][str(row['sink'])]))
  if len(rows)!=count or {x['connection_id'] for x,_ in rows}!=set(budgets):raise ValueError('snapshot coverage mismatch')
  jobs.append((rows,budgets));bound[str(r/'receipt.json')]=sha(r/'receipt.json');bound[str(r/'budgets.json')]=sha(r/'budgets.json');bound[str(r/'protocol.json')]=sha(r/'protocol.json')
 for p in [exact/'receipt.json',exact/'protocol.json',csr/'manifest.json']:bound[str(p)]=sha(p)
 (out/'protocol.json').write_text(json.dumps({'inputs':bound,'sources':sources,'graph_sha256':graph,'expected_connections':1157,'scope':'exact original path delay parity, not repair, global legality or STA'},indent=2)+'\n')
 start=time.monotonic();m,fields=read(csr,graph);ids,classes,switches=load(exact,graph);rc=ExactBufferedRC(fields,ids,classes,switches);checked=0
 for rows,budgets in jobs:
  for row,path in rows:
   if rc.path(row['source'],row['sink'],path)!=budgets[row['connection_id']]:raise ValueError('exact budget mismatch')
   checked+=1
 assert checked==1157
 if any(sha(p)!=h for p,h in bound.items()) or any(sha(Path('tools')/n)!=h for n,h in sources.items()):raise ValueError('input or source changed')
 result={'connections':checked,'exact_fraction_parity':True,'delay_classes_used':len(rc.cache),'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'scope':'original predictor paths only; no repair or STA claim'}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':run()
