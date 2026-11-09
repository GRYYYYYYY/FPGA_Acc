"""Review immutable two-phase/filter composition CPU and synthesis screen."""
import hashlib,json,re,xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_two_phase_key_filter_screen_v2_20261015'
def main():
 refs={}
 def bind(p):refs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 protocol=json.loads((P/'protocol.json').read_text())
 for name,h in protocol['source_sha256'].items():
  p=Path(name);bind(p);assert refs[str(p)]==h,name
 manifest=json.loads((P/'manifest.json').read_text());assert manifest['status']=='CPU_and_synthesis_terminal_requires_review'
 assert len(manifest['steps'])==6 and all(v['returncode']==0 for v in manifest['steps'])
 for flag in (0,1):
  f=P/f'suite{flag}.log';assert 'SHARDED_DIFFERENTIAL calls=75 isolated_owner_banks=3' in f.read_text();bind(f)
 source=(P/'source/net_commit_sharded_hbm.cpp').read_text()
 for c in reversed(json.loads((P/'changes.json').read_text())):
  assert source.count(c['after'])==1;source=source.replace(c['after'],c['before'],1)
 assert source==(R/'work/native_commit_two_phase_boundaries_20261015/source/net_commit_sharded_hbm.cpp').read_text()
 sol=P/'project/solution1';constraint=sol/'.autopilot/db/dieroute_net_commit_sharded_hbm.constraint.tcl'
 block=re.search(r'set clock_constraint\s*\{(.*?)\}',constraint.read_text(),re.S).group(1)
 def number(k):return Decimal(re.search(r'\b'+k+r'\s+([0-9.]+)',block).group(1))
 period,uncertainty=number('period'),number('uncertainty');assert period==Decimal('3.333') and uncertainty==Decimal('0.89991')
 xml=sol/'syn/report/dieroute_net_commit_sharded_hbm_csynth.xml';x=ET.parse(xml).getroot();estimate=Decimal(x.findtext('.//EstimatedClockPeriod'))
 log=P/'HLS_screen.log';assert 'CSim done with 0 errors' in log.read_text()
 for f in [constraint,xml,log,P/'protocol.json',P/'manifest.json',P/'changes.json',Path(__file__).resolve()]:bind(f)
 report=dict(status='CPU150_and_synthesis_screen_reviewed',estimated_ns=str(estimate),effective_budget_ns=str(period-uncertainty),reported_estimate_pass=estimate<=period-uncertainty,resources={v.tag:int(v.text) for v in x.find('.//AreaEstimates/Resources')},warning_emitted='HLS 200-871' in log.read_text(),source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Composition restoration, both CPU flags75calls each and enabled CSIM/synthesis. No RTL/full-native/physical validation of composition.')
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
