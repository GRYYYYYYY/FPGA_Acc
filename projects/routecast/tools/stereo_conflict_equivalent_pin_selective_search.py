"""Five conflict diagnostics under original actual physical pins; no commit."""
import json,time,shutil
from pathlib import Path
from fractions import Fraction
from prepared_csr import read,TYPES
from pre_route_endpoints import sha
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from csr_exact_budget_search_pruned import query
from csr_reverse_delay_bound import incoming,prepare
import xml.etree.ElementTree as ET
from pre_route_endpoints import PIN

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'conflict_equivalent_pin_selective_search';out.mkdir();(out/'source').mkdir()
 reqpath=b/'additional_high_fanout_physical_audit/conflict_repair_requests.json';requests=json.loads(reqpath.read_text())
 exact=b/'exact_buffered_rc_classes_v2';csr=b/'streaming_csr_class_cache_v3/csr';graph=json.loads((exact/'protocol.json').read_text())['graph']['sha256']
 names=('stereo_conflict_equivalent_pin_selective_search.py','csr_exact_budget_search_pruned.py','csr_reverse_delay_bound.py','csr_exact_buffered_rc.py','buffered_rc_context.py','buffered_rc_node_classes.py','prepared_csr.py','pre_route_endpoints.py')
 sources={n:sha(Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
 inputs={str(p):sha(p) for p in [reqpath,exact/'receipt.json',csr/'manifest.json',b/'additional_high_fanout_exact_budgets/budgets.json',b/'additional_high_fanout_physical_audit/affected_conflict_connections.json',b/'conflict_pin_equivalence_binding/binding.json']}
 assert inputs[str(b/'additional_high_fanout_exact_budgets/budgets.json')]==requests['budget_sha256']
 assert inputs[str(b/'additional_high_fanout_physical_audit/affected_conflict_connections.json')]==requests['affected_sha256']
 protocol={'inputs':inputs,'sources':sources,'graph_sha256':graph,'blocked_nodes':'per request: only directly attributed conflicting resources','max_labels':100000,'max_reverse_settled':100000,'reverse_bound':'settled exact distances; unfinished frontier admissible fallback','objective':'sum destination CHAN Manhattan span including unit length','pins':'fixed SOURCE, all class OPINs and architecture-bound full IPINs; optimistic occupancy-relaxed diagnostic','scope':'per-resource conflict ownership diagnostic; all equivalent pins, occupancy relaxed, other conflicting resource may be retained by this net; no commit'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
 _,f=read(csr,graph);ids,classes,switches=load(exact,graph);rc=ExactBufferedRC(f,ids,classes,switches);blocked=set();results=[];rs=time.monotonic();reverse=incoming(f);reverse_setup_s=time.monotonic()-rs
 declarations=json.loads((b/'conflict_pin_equivalence_binding/binding.json').read_text());declarations={x['connection_id']:x for x in declarations['requests']}
 graphpath=json.loads((exact/'protocol.json').read_text())['graph']['path'];types={};grid={}
 for event,e in ET.iterparse(graphpath,events=('start','end')):
  if event=='start' and e.tag=='rr_nodes':break
  if event!='end':continue
  if e.tag=='block_type':
   types[int(e.get('id'))]=(e.get('name'),[[(int(pin.get('ptc')),PIN.fullmatch(pin.text.strip()).groups()) for pin in cls.findall('pin')] for cls in e.findall('pin_class')]);e.clear()
  elif e.tag=='grid_loc':grid[(int(e.get('x')),int(e.get('y')),int(e.get('layer','0')))]=int(e.get('block_type_id'));e.clear()
 candidate_records=[]
 for row in requests['requests']:
  blocked=set(row['conflict_rr_nodes'])
  source=row['source'];sink=row['sink'];current=source;nodes=[source]
  for eid in row['physical_edge_ids']:
   matches=[i for i in range(f['row_offsets'][current],f['row_offsets'][current+1]) if f['edge_ids'][i]==eid]
   assert len(matches)==1;current=f['dest_ranks'][matches[0]];nodes.append(current)
  assert current==sink
  opins=[n for n in nodes if f['types'][n]==TYPES['OPIN']];ipins=[n for n in nodes if f['types'][n]==TYPES['IPIN']];assert len(opins)==len(ipins)==1
  opin=opins[0];ipin=ipins[0];budgetrow=row['original_exact_budget'];budget=Fraction(budgetrow['delay_seconds_numerator'],budgetrow['delay_seconds_denominator']);assert rc.path(source,sink,row['physical_edge_ids'])==budget
  declaration=declarations[row['connection_id']];assert declaration['logical_equivalent']==declaration['tile_equivalent']=='full'
  tid=grid[(f['xlow'][sink],f['ylow'][sink],f['layer'][sink])];tile,physical_classes=types[tid];assert tile==declaration['tile']
  members=physical_classes[f['ptc'][sink]];expected={ptc for ptc,parts in members}
  assert len(expected)==declaration['num_pins'] and all(parts[2]==declaration['mapping']['port'] for ptc,parts in members)
  rrrows,rrindices,rrparents=reverse
  targets={rrparents[j] for j in range(rrrows[sink],rrrows[sink+1])}
  assert all(f['types'][n]==TYPES['IPIN'] for n in targets) and {f['ptc'][n] for n in targets}==expected
  source_pins={f['dest_ranks'][i] for i in range(f['row_offsets'][source],f['row_offsets'][source+1])}
  assert source_pins and all(f['types'][n]==TYPES['OPIN'] for n in source_pins)
  targets-=blocked;source_pins-=blocked
  candidate_records.append({'connection_id':row['connection_id'],'source_opins':sorted(source_pins),'target_ipins':sorted(targets),'target_ptcs':sorted({f['ptc'][n] for n in targets}),'scope':'class candidates only; actual ownership not filtered'})
  def allowed(n,i):
   dest=f['dest_ranks'][i]
   if dest in blocked or f['capacities'][dest]<=0:return False
   if n==source:return dest in source_pins
   if n in targets:return dest==sink
   return (n in source_pins or f['types'][n] in (TYPES['CHANX'],TYPES['CHANY'])) and (dest in targets or f['types'][dest] in (TYPES['CHANX'],TYPES['CHANY']))
  def cost(n,i):
   d=f['dest_ranks'][i]
   return abs(f['xhigh'][d]-f['xlow'][d])+abs(f['yhigh'][d]-f['ylow'][d])+1 if f['types'][d] in (TYPES['CHANX'],TYPES['CHANY']) else 0
  qs=time.monotonic()
  lower=prepare(rc,reverse,sink,allowed,100000)
  result=query(rc,source,sink,budget,allowed,cost,100000,lower=lower);result['reverse']=lower.counters
  if isinstance(result.get('delay'),Fraction):result['delay']=[result['delay'].numerator,result['delay'].denominator]
  result.update(blocked_nodes=sorted(blocked),connection_id=row['connection_id'],net_id=row['net_id'],original_opin=opin,original_ipin=ipin,wall_s=time.monotonic()-qs)
  results.append(result);print(json.dumps(result),flush=True);(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 (out/'candidates.json').write_text(json.dumps(candidate_records,indent=2)+'\n')
 if any(sha(p)!=h for p,h in inputs.items()) or any(sha(Path('tools')/n)!=h for n,h in sources.items()):raise ValueError('inputs/source changed')
 receipt={'reverse_setup_s':reverse_setup_s,'queries':len(results),'status_counts':{s:sum(x['status']==s for x in results) for s in sorted({x['status'] for x in results})},'results_sha256':sha(out/'results.json'),'protocol_sha256':sha(out/'protocol.json'),'wall_s':time.monotonic()-start,'scope':protocol['scope']}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()
