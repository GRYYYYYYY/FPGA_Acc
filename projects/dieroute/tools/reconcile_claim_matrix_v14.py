"""Freeze local-exchange successes, transfer failures and fresh board availability."""
from pathlib import Path
import hashlib,json,time
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 previous=R/'work/current_research_claim_matrix_v13_20261020/matrix.json';d=json.loads(previous.read_text())
 for name,h in d['source_sha256'].items():assert sha(R/name)==h,name
 out=R/'work/current_research_claim_matrix_v14_20261020';out.mkdir();plan=R/'experiments/research_plan.json';(out/'plan_snapshot.json').write_bytes(plan.read_bytes())
 added=['work/elliptic_local_exchange_20261020/native_summary.json','work/elliptic_local_exchange_repeats_20261020/audit.json','work/elliptic_local_exchange_20261020/automatic_task_selection.json','work/apex2_seed1_local_exchange_20261020/native_queue/task239_forward/independent_native_audit.json','work/apex2_seed1_dual_cap_crossing_20261020/native_queue/task239_forward/independent_native_audit.json','work/apex2_seed1_native_exchange_refinement_20261020/independent_audit.json','work/apex2_seed1_stage3_alternate_targets_20261020/terminal_review.json','work/apex2_seed1_stage3_current_ceiling_20261020/native_queue/task1289_forward/independent_native_audit.json','work/apex2_seed1_stage3_current_ceiling_20261020/private_acceptance_review.json','work/physical_u280_recheck_20261020/audit.json','work/insert_lookup_boundary_hw_20261020/compiled_XO_review.json']
 summary=json.loads((R/added[0]).read_text());assert summary['joint_passes']==3
 transfer=json.loads((R/added[7]).read_text());assert transfer['checks']['native_legal'] and not transfer['checks']['CPD'];assert transfer['cpd_ns']==11.0409
 board=json.loads((R/added[9]).read_text());assert board['xilinx_devices']==[] and board['pci_devices']==344
 d['claims'].append({'id':'Q4','gates':['G2','G4'],'claim':'Small local exchanges repair all baseline quality metrics on one posterior elliptic case','status':'supported_in_declared_scope','evidence':added[:3],'measurements':summary['quality_points'],'limits':'Four order arms,three unique candidate trees on ONEcase;allnativelegal/jointpass. Five search-only replays byte-identical. No original12cohort replacement,full-router repeat proof,independent validation orFPGAacceleration.'})
 d['claims'].append({'id':'Q5','gates':['G3','G4'],'claim':'Local exchange establishes cross-circuit baseline quality guarantee','status':'not_supported_transfer_failure_retained','evidence':added[3:9],'measurements':{'latest_apex2_private_wirelength':transfer['wirelength'],'latest_apex2_private_cpd_ns':transfer['cpd_ns'],'baseline_cpd_ns':transfer['baseline_cpd_ns'],'latest_apex2_private_crossings':transfer['model_crossings'],'baseline_crossings':transfer['baseline_model_crossings']},'limits':'Already-observed apex2seed1 used asposterior transfer. PrivateCPDprogress andcrossingreduction do notpass10.8372nsbaseline. Originalreserved3of5jointpasses and15attempt denominator retained. Plateau0.3psprogress notsignificance.'})
 b1=next(c for c in d['claims'] if c['id']=='B1');b1['evidence'].append(added[9]);b1['limits']='Fresh2026-10-20samehostPCI344devices,noXilinxvendor;XRT2.14.354reports0devices. Physicalspeed,energy,3xrepeatedend-to-end targets unproven.'
 h2=next(c for c in d['claims'] if c['id']=='H2');h2['evidence'].append(added[10]);h2['limits']+=' Latestinsertlookupcandidate actualXO29args8ports/embeddedsource/callerregistercaptureverified;physical link still running in frozen owner observation,not finaltiming oradoption.'
 observations=[]
 for pid in [1119774,1143696]:
  proc=Path('/proc')/str(pid);stat=(proc/'stat').read_text();fields=stat[stat.rfind(')')+2:].split();assert fields[0]!='Z';cmdline=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode();assert 'insert_lookup_boundary' in cmdline;observations.append({'pid':pid,'state':fields[0],'start_ticks':fields[19],'cmdline':cmdline})
 (out/'live_owner_snapshot.json').write_text(json.dumps({'recorded_ns':time.time_ns(),'owners':observations,'scope':'Point-in-time live handles,not terminal orsignoff proof.'},indent=2)+'\n')
 d.update(schema='dieroute.claim_matrix.v14',recorded_ns=time.time_ns(),predecessor={'path':str(previous.relative_to(R)),'sha256':sha(previous)})
 for f in added+[str((out/'plan_snapshot.json').relative_to(R)),str((out/'live_owner_snapshot.json').relative_to(R)),str(Path(__file__).resolve().relative_to(R))]:d['source_sha256'][f]=sha(R/f)
 assert len(d['gates'])==8 and all(g['status']!='complete' for g in d['gates']);target=out/'matrix.json'
 with target.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
 p=json.loads(plan.read_text());p['current_claim_matrix']={'path':str(target.relative_to(R)),'sha256':sha(target),'status':d['status'],'research_complete':False};p['latest_physical_board_check']='work/physical_u280_recheck_20261020/audit.json';plan.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'claims':len(d['claims']),'open_gates':len(d['gates']),'sources':len(d['source_sha256']),'research_complete':False}))
if __name__=='__main__':main()
