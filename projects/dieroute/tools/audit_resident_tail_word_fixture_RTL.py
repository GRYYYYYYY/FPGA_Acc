"""Read-only audit of nine reverse scalar-interface fixture RTL calls."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];D=R/'work/resident_tail_word_HLS_v2_20261021'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 protocol=json.loads((D/'protocol.json').read_text())
 for name,h in protocol['source_sha256'].items():assert sha(name)==h,name
 manifest=json.loads((D/'manifest.json').read_text());assert manifest['status']=='HLS_tool_terminal_requires_independent_reports' and manifest['returncode']==0
 log=(D/'run.log').read_text();assert 'C/RTL co-simulation finished: PASS' in log and 'RTL Simulation : 9 / 9' in log
 report=D/'project/solution1/sim/report/dieroute_resident_tail_words_cosim.rpt';text=report.read_text();assert re.search(r'\|\s*Verilog\|\s*Pass\|',text)
 transaction=D/'project/solution1/sim/report/verilog/result.transaction.rpt';rows=[dict(transaction=int(a),latency_cycles=int(b),interval_cycles=None if c=='x' else int(c)) for a,b,c in re.findall(r'transaction\s+(\d+):\s+(\d+)\s+(\d+|x)',transaction.read_text())];assert [v['transaction'] for v in rows]==list(range(9));assert rows[0]['latency_cycles']==4607
 tv=D/'project/solution1/sim/tv';pairs=[];files=[D/'protocol.json',D/'manifest.json',D/'run.log',report,transaction,Path(__file__)]
 for bundle in ['control','scratch','labels','frontier']:
  a=tv/'cdatafile'/f'c.dieroute_resident_tail_words.autotvout_{bundle}.dat';b=tv/'rtldatafile'/f'rtl.dieroute_resident_tail_words.autotvout_{bundle}.dat';assert a.read_bytes()==b.read_bytes(),bundle;pairs.append(dict(bundle=bundle,bytes=a.stat().st_size,equal=True));files.extend([a,b])
 synth=D/'project/solution1/syn/report/dieroute_resident_tail_words_csynth.xml';root=ET.parse(synth).getroot();resources={e.tag:int(e.text) for e in root.find('AreaEstimates/Resources')};estimated=float(root.findtext('PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod'));files.append(synth)
 result=dict(status='nine_declared_reverse_scalar_fixture_Verilog_calls_and_all4output_bundles_verified',fixture_calls=9,valid_workload_calls=1,reject_calls=8,transactions=rows,reported_total_execution_cycles=18608,sum_call_latencies_cycles=sum(v['latency_cycles'] for v in rows),output_bundle_comparisons=pairs,HLS_resources=resources,HLS_estimated_clock_ns=estimated,source_sha256={str(p):sha(p) for p in files},scope='One two-node zero-cost alias reverse job and8reject calls only.4607cycles for valid fixture. RTL outputs equal C bytes; aggregate C differential covers4cases,2000random Ccases separately. HLS estimates are not physical timing. No real-workload RTL,performance,board or asynchronous authority proof; prior aggregate failure retained.',research_complete=False)
 p=D/'independent_RTL_review.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','fixture_calls','reported_total_execution_cycles','HLS_resources','HLS_estimated_clock_ns']}))
if __name__=='__main__':main()
