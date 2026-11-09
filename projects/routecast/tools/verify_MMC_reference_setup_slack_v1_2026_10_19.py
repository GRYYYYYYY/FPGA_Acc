"""Exact constraint-object difference and direct recomputed native slack validation."""
import pathlib,json,hashlib,struct,math
from collections import Counter
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_reference_setup_slack_export_v1_2026-10-19';P=R/'experiments/mmc_prior_setup_slack_export_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def value(b):return struct.unpack('<f',struct.pack('<I',b))[0]
def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def main():
 rp=O/'receipt.json';r=json.loads(rp.read_text());assert r['exit_code']==0 and r['full_pass'] and r['source_route_bytes_identical'] and r['source_packed_post_bytes_identical'];assert r['CPD_ns']==15.7422 and r['wirelength']==661370
 for p,h in r['bindings'].items():assert sha(pathlib.Path(p))==h
 protocol=json.loads((O/'protocol.json').read_text());before=(O/'original_constraints.tsv').read_text().splitlines();after=(O/'reference_constraints.tsv').read_text().splitlines();bs=[x.split('\t') for x in before if x.startswith('S\t')];a=[x.split('\t') for x in after if x.startswith('S\t')];assert len(bs)==len(a)==1 and bs[0][:-1]==a[0][:-1] and int(bs[0][-1])==0 and int(a[0][-1])==protocol['reference_setup_float32_bits'];assert [x for x in before if not x.startswith('S\t')]==[x for x in after if not x.startswith('S\t')];types=Counter(x.split('\t')[0] for x in before);assert types['D']==types['S']==1
 proof=P/'independent_verification_v1.json';pv=json.loads(proof.read_text());assert pv['mapped_model_connections']==115572;oldfile=P/'routecast_cluster_criticality.jsonl';assert sha(oldfile)==pv['bindings'][str(oldfile)];old={(x['net_id'],x['net_pin_index']):x for x in map(json.loads,oldfile.read_text().splitlines())};rows={};stats=Counter();newfile=O/'routecast_cluster_criticality.jsonl'
 for line in newfile.open():
  x=json.loads(line);key=(x['net_id'],x['net_pin_index']);assert key not in rows;previous=old[key]
  for k in ['net','cluster_pin_id','block','port','bit','logical_pin','native_route_delay_s','native_route_delay_float32_bits','clock_sink','ignored_net']:assert x[k]==previous[k]
  assert [(p['atom_pin_id'],p['tatum_node']) for p in x['atom_pins']]==[(p['atom_pin_id'],p['tatum_node']) for p in previous['atom_pins']];minimum=math.inf
  for ap in x['atom_pins']:
   slack=value(ap['setup_slack_float32_bits']);assert (ap['setup_slack_s'] is None)==(not math.isfinite(slack))
   if math.isfinite(slack):assert bits(ap['setup_slack_s'])==ap['setup_slack_float32_bits']
   if slack<minimum:minimum=slack
  assert bits(minimum)==x['setup_slack_float32_bits'];slack=value(x['setup_slack_float32_bits']);assert (x['setup_slack_s'] is None)==(not math.isfinite(slack))
  if math.isfinite(slack):assert bits(x['setup_slack_s'])==x['setup_slack_float32_bits']
  rows[key]=x;stats['rows']+=1
 assert rows.keys()==old.keys();mappedp=P/'model_connection_setup_slacks.json';assert sha(mappedp)==pv['bindings'][str(mappedp)];mapped=json.loads(mappedp.read_text());percid={};counts=Counter();max_deviation=0.;target=value(protocol['reference_setup_float32_bits'])
 for q in mapped:
  x=rows[(q['native_NET_id'],q['native_sink_index'])];slack=value(x['setup_slack_float32_bits']);prior=value(q['setup_slack_float32_bits']);category='nonfinite' if not math.isfinite(slack) else ('negative' if slack<0 else ('zero' if slack==0 else 'positive'));counts[category]+=1;assert not x['ignored_net'];counts['clock']+=x['clock_sink'];percid[q['connection_id']]=dict(connection_id=q['connection_id'],setup_slack_s=x['setup_slack_s'],setup_slack_float32_bits=x['setup_slack_float32_bits'],clock_sink=x['clock_sink'])
  if math.isfinite(slack):max_deviation=max(max_deviation,abs(slack-(prior+target)))
 out=O/'model_connection_reference_slacks.json';out.write_text(json.dumps(list(percid.values()),separators=(',',':'))+'\n');cases=[];C=R/'experiments/mmc_changed_endpoint_prior_budgets_v2_2026-10-19'
 for case in ['episode_01','episode_02','episode_03']:
  changed=json.loads((C/f'{case}.json').read_text());details=[]
  for q in changed['rows']:
   row=percid[q['connection_id']];s=value(row['setup_slack_float32_bits']);valid=math.isfinite(s) and not row['clock_sink'];fraction=Fraction.from_float(max(s,0))*10**18 if valid else Fraction(0);credit=fraction.numerator//fraction.denominator;deficit=q['minimum_necessary_budget_increase'];details.append(dict(connection_id=q['connection_id'],old_actual_shortfall=deficit,local_reference_slack_credit=credit,covered_by_local_reference_credit=valid and credit>=deficit))
  result=dict(case=case,changed_connections=len(details),prior_actual_budget_floor_failures=changed['changed_connections_with_impossible_prior_actual_budget'],remaining_floor_failures_after_local_reference_diagnostic=sum(not d['covered_by_local_reference_credit'] for d in details),new_floor_positive_shortfalls_locally_covered=sum(d['old_actual_shortfall']>0 and d['covered_by_local_reference_credit'] for d in details),rows=details);(O/f'{case}_local_slack_diagnostic.json').write_text(json.dumps(result,indent=2)+'\n');cases.append({k:v for k,v in result.items() if k!='rows'})
 finite=[value(q['setup_slack_float32_bits']) for q in percid.values() if q['setup_slack_s'] is not None];bindings={str(p):sha(p) for p in [rp,O/'protocol.json',proof,oldfile,newfile,mappedp,out,O/'original_constraints.tsv',O/'reference_constraints.tsv',pathlib.Path(__file__).resolve()]}
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='SINGLE_SETUP_REFERENCE_CHANGE_ALL_OTHER_CONSTRAINTS_AND_ALL115572_NATIVE_IDENTITIES_PASS',reference_seconds=target,reference_float32_bits=protocol['reference_setup_float32_bits'],constraint_record_counts=dict(types),all_nonsetup_constraint_records_identical=True,all_native_sink_rows=len(rows),mapped_connections=len(percid),mapped_reference_slack_counts=dict(counts),minimum_reference_slack_s=min(finite),maximum_reference_slack_s=max(finite),max_recomputed_vs_arithmetic_shift_difference_s=max_deviation,local_changed_endpoint_diagnostics=cases,budget_policy_adopted=False,bindings=bindings,scope='One prior-source native recomputation with reference setup target, not a real user timing constraint. Local slack coverage only; simultaneous changed paths can share and consume margin, and floating-point boundary residuals remain explicit. Native/new-layout/quality/full-flow gates unchanged.'),f,indent=2)
 print('REFERENCE NATIVE CONSTRAINT AND SLACK PASS',dict(counts),'minimum',min(finite),'cases',cases,flush=True)
if __name__=='__main__':main()
