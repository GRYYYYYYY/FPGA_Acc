"""Independent retained-checkpoint checks; never equate link success with signoff."""
import collections,csv,hashlib,json,re
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1]
B=R/'work/lean_start_traffic_read_buffer_hw_20261017'
P=R/'work/traffic_read_buffer_postlink_readonly_20261017'
O=R/'work/traffic_read_buffer_routed_review_20261017'

def timing(text):
 block=text.split('Design Timing Summary',1)[1]
 names=['wns_ns','tns_ns','setup_failing','setup_total','whs_ns','ths_ns','hold_failing','hold_total','wpws_ns','tpws_ns','pulse_failing','pulse_total']
 for line in block.splitlines():
  tokens=line.split()
  if len(tokens)!=12 or not all(tokens[i].isdigit() for i in (2,3,6,7,10,11)):continue
  row={k:int(v) if 'failing' in k or 'total' in k else float(Decimal(v)) for k,v in zip(names,tokens)}
  assert all(row[k]>=0 for k in names if 'failing' in k or 'total' in k)
  return row
 raise ValueError('No complete twelve-field design timing summary')

def routing(text):
 def number(label):
  found=re.findall(re.escape(label)+r'\.*\s*:\s*(\d+)\s*:',text)
  assert len(found)==1,(label,found)
  return int(found[0])
 routable,fully,errors=[number(v) for v in ['# of routable nets','# of fully routed nets','# of nets with routing errors']]
 assert 0<=fully<=routable and routable>0
 return dict(routable=routable,fully_routed=fully,routing_errors=errors,complete=fully==routable and errors==0)

def main():
 refs={}
 def sha(f):
  p=Path(f);key=str(p)
  if key not in refs:
   h=hashlib.sha256()
   with p.open('rb') as stream:
    for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
   refs[key]=h.hexdigest()
  return refs[key]
 post=json.loads((P/'manifest.json').read_text());link=json.loads((B/'manifest.json').read_text())
 assert post['status']=='readonly_reports_complete_signoff_interpretation_required' and post['returncode']==0 and post['checkpoint_unchanged']
 assert link['status']=='linked_requires_independent_routed_signoff' and link['link_returncode']==0
 assert sha(B/'joint.xclbin')==link['xclbin_sha256']==post['xclbin_sha256']
 archive=Path(post['command'][post['command'].index('-tclargs')+1]);assert sha(archive)==sha(post['named_checkpoint_path'])==post['checkpoint_sha256']
 for f,h in post['report_sha256'].items():assert sha(f)==h,f
 d=P/'reports';summary=timing((d/'timing_summary.rpt').read_text());route=routing((d/'route_status.rpt').read_text())
 metrics=dict(v.split('\t',1) for v in (d/'metrics.tsv').read_text().splitlines())
 assert float(metrics['setup_worst_slack_ns'])==summary['wns_ns'] and float(metrics['hold_worst_slack_ns'])==summary['whs_ns']
 clocks=list(csv.DictReader((d/'kernel_clocks.tsv').open(),delimiter='\t'));assert {v['cu'] for v in clocks}=={'net_commit','search_worker','snapshot_search'}
 assert all(Decimal(v['period_ns'])==Decimal('3.333') for v in clocks)
 topology=json.loads((P/'clock_freq_topology.json').read_text())['clock_freq_topology']['m_clock_freq']
 frequencies={v['m_name']:int(v['m_freq_Mhz']) for v in topology};assert len(frequencies)==len(topology) and 'DATA_CLK' in frequencies
 drc=(d/'drc.rpt').read_text();rules=re.findall(r'^\|\s*([A-Z][A-Z0-9-]+)\s*\|\s*(Error|Critical Warning|Warning|Advisory)\s*\|[^\n]*?\|\s*(\d+)\s*\|',drc,re.M)
 assert rules or 'No violations found' in drc
 severity=collections.Counter()
 for _,kind,count in rules:severity[kind]+=int(count)
 check=(d/'check_timing.rpt').read_text();categories={}
 for name in ['no_clock','unconstrained_internal_endpoints','multiple_clock','loops','latch_loops','no_input_delay','no_output_delay']:
  found=re.findall(r'checking '+name+r' \((\d+)\)',check);assert found and len(set(found))==1,name;categories[name]=int(found[0])
 bus=post['bus_skew'];unmeasured=bus['unmeasured_constraints']
 checks=dict(setup=summary['wns_ns']>=0 and summary['setup_failing']==0,
             hold=summary['whs_ns']>=0 and summary['hold_failing']==0,
             pulse=summary['wpws_ns']>=0 and summary['pulse_failing']==0,
             route=route['complete'],drc_no_error_or_critical=severity['Error']==severity['Critical Warning']==0,
             bus_numeric=bus['numeric_violations']==0,
             bus_unmeasured_only_single_endpoint=all(v['endpoints']==1 for v in unmeasured),
             no_unconstrained_internal_clock_or_loops=all(categories[v]==0 for v in ['no_clock','unconstrained_internal_endpoints','multiple_clock','loops','latch_loops']))
 for f in [B/'manifest.json',P/'manifest.json',P/'protocol.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='retained_requested_clock_report_checks_pass_engineering_review_still_required' if all(checks.values()) else 'retained_requested_clock_report_checks_failed',design_timing_summary=summary,route=route,checks=checks,drc_severity_counts=dict(severity),check_timing_counts=categories,bus_skew=bus,retained_checkpoint_CU_clocks=clocks,final_clock_topology_mhz=frequencies,worst_setup_startpoint=metrics['setup_startpoint'],worst_setup_endpoint=metrics['setup_endpoint'],source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Hash-bound completed image and read-only retained requested-clock checkpoint. Numeric report checks only; warnings and external IO delay exceptions remain visible, not waived. Final-bitstream/checkpoint correspondence, adjusted-clock signoff, physical board performance and adoption unproven. Final topology names alone do not identify final CU clocks.')
 with (O/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','bus_skew','retained_checkpoint_CU_clocks']}))
if __name__=='__main__':main()
