"""Isolated whole-net replacement simulation; never publishes original state."""
import json,collections,shutil
from pathlib import Path
from array import array
from prepared_csr import read
from pre_route_endpoints import sha

def run():
 base=Path('experiments');original=base/'conv_layer_length_switch_prediction_v2_2026-10-06';search=base/'conv_layer_no_worsening_lex_search_2026-10-06';audit=base/'conv_layer_no_worsening_lex_candidate_xml_audit_2026-10-06';budget=base/'conv_layer_no_worsening_lex_candidate_xml_budget_audit_2026-10-06'
 pp=json.loads((original/'protocol.json').read_text());pr=json.loads((original/'receipt.json').read_text());ar=json.loads((audit/'receipt.json').read_text());br=json.loads((budget/'receipt.json').read_text())
 assert ar['result']['all_physical_and_union_checks_passed'] and br['all_candidates_within_original_exact_path_budget']
 assert ar['protocol_sha256']==sha(audit/'protocol.json') and br['protocol_sha256']==sha(budget/'protocol.json')
 assert pr['protocol_sha256']==sha(original/'protocol.json') and pr['prediction_sha256']==sha(original/'prediction.json')
 sr=json.loads((search/'receipt.json').read_text());sp=json.loads((search/'protocol.json').read_text());ap=json.loads((audit/'protocol.json').read_text());bp=json.loads((budget/'protocol.json').read_text())
 assert sr['protocol_sha256']==sha(search/'protocol.json') and sr['journal_sha256']==sha(search/'queries.jsonl') and sr['queries']==75
 assert ap['parent_receipt_sha256']==sha(search/'receipt.json') and ap['graph']==pp['inputs']['graph'] and bp['inputs']['graph']==pp['inputs']['graph']
 assert bp['physical_receipt_sha256']==sha(audit/'receipt.json') and br['budgets_sha256']==sha(budget/'budgets.json')
 assert all(sha(path)==h for path,h in sp['inputs_sha256'].items()) and all(sha(path)==h for path,h in bp['selection_sha256'].items())
 assert all(sha(audit/'source'/name)==h for name,h in ap['source_sha256'].items())
 for name,h in sp['source_sha256'].items():assert sha(search/'source'/name)==h
 paths=[original/'prediction.json',original/'receipt.json',search/'receipt.json',search/'queries.jsonl',audit/'receipt.json',budget/'receipt.json'];inputs={str(p):sha(p) for p in paths}
 m,f=read(base/'conv_layer_length_switch_csr_2026-10-06/csr',pp['inputs']['graph']['sha256']);assert sha(base/'conv_layer_length_switch_csr_2026-10-06/csr/manifest.json')==pp['csr_manifest_sha256']
 slots=array('Q',[0])*m['edges']
 for slot,eid in enumerate(f['edge_ids']):slots[eid]=slot
 def nodes(row):
  current=row['source'];used={current}
  for eid in row['physical_edge_ids']:
   slot=slots[eid];assert f['row_offsets'][current]<=slot<f['row_offsets'][current+1];current=f['dest_ranks'][slot];assert current not in used;used.add(current)
  assert current==row['sink'];return used
 def span(used):return sum(max(f['xhigh'][n]-f['xlow'][n],f['yhigh'][n]-f['ylow'][n])+1 for n in used if f['types'][n] in (4,5))
 topology={r['net_id']:r for r in ar['result']['net_union_topology']['nets']}
 candidates={r['connection_id']:r for r in [json.loads(line) for line in (search/'queries.jsonl').read_text().splitlines()] if r['result']['status']=='FOUND'}
 eligible={net for net in ar['whole_net_all_connections_found'] if not topology[net]['internal_multi_incoming_nodes'] and not topology[net]['cyclic_union'] and not topology[net]['source_has_incoming'] and topology[net]['all_nodes_source_reachable'] and not topology[net]['terminal_multi_incoming_nodes']}
 pred=json.loads((original/'prediction.json').read_text());old=collections.defaultdict(set);new=collections.defaultdict(set);replacement=[]
 for row in pred['connections']:
  net=row['net_id']
  if net in eligible:
   old[net].update(nodes(row));candidate=candidates[row['connection_id']];row={**row,'physical_edge_ids':candidate['result']['physical_edge_ids']};new[net].update(nodes(row))
  replacement.append(row)
 before=collections.Counter({int(n):v for n,v in pred['node_occupancy'].items()});after=before.copy()
 for net in eligible:
  after.subtract(old[net]);after.update(new[net])
 after=collections.Counter({n:v for n,v in after.items() if v});assert all(v>0 for v in after.values())
 rebuilt=collections.defaultdict(set)
 for row in replacement:rebuilt[row['net_id']].update(nodes(row))
 full=collections.Counter(n for used in rebuilt.values() for n in used);assert full==after
 overflow=lambda counts:sum(max(0,v-f['capacities'][n]) for n,v in counts.items())
 worsened=[{'node':n,'old':before[n],'new':after[n],'old_overflow':max(0,before[n]-f['capacities'][n]),'new_overflow':max(0,after[n]-f['capacities'][n])} for n in sorted(set(before)|set(after)) if max(0,after[n]-f['capacities'][n])>max(0,before[n]-f['capacities'][n])]
 report={'inputs_sha256':inputs,'eligible_whole_net_ids':sorted(eligible),'excluded_incomplete_or_structurally_unsupported_nets':49-len(eligible),'overflow_before':overflow(before),'overflow_after':overflow(after),'worsened_resources':worsened,'net_span_changes':[{'net_id':n,'old':span(old[n]),'new':span(new[n])} for n in sorted(eligible)],'incremental_equals_full_rebuild':True,'repair_committed':False,'scope':'isolated whole-net predicted occupancy simulation; zero overflow/native STA/QoR and global route legality not proven'}
 assert all(sha(p)==h for p,h in inputs.items())
 out=base/'conv_layer_no_worsening_lex_whole_net_candidate_impact_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['inputs_sha256','worsened_resources','net_span_changes','eligible_whole_net_ids']}),flush=True)
if __name__=='__main__':run()
