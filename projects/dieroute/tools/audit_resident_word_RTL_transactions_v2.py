"""Audit declared scalar resident operator cosimulation counts and output bytes."""
from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as ET,sys

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=Path(sys.argv[1]).resolve();p=json.loads((d/'protocol.json').read_text());count=p['fixture_calls']
 for name,h in p['source_sha256'].items():assert sha(name)==h,name
 m=json.loads((d/'manifest.json').read_text());assert m['returncode']==0 and m['status']=='HLS_tool_terminal_requires_independent_reports'
 log=(d/'run.log').read_text();assert 'C/RTL co-simulation finished: PASS' in log and f'RTL Simulation : {count} / {count}' in log
 summary=ET.parse(d/'project/solution1/syn/report/csynth.xml').getroot();declared_top=summary.findtext('UserAssignments/TopModelName');assert re.search(r'^set_top\s+'+re.escape(declared_top)+r'\s*$',(d/'run.tcl').read_text(),re.M);syn=[d/f'project/solution1/syn/report/{declared_top}_csynth.xml'];assert syn[0].is_file()
 root=ET.parse(syn[0]).getroot();top=root.findtext('UserAssignments/TopModelName');report=d/f'project/solution1/sim/report/{top}_cosim.rpt';line=next(l for l in report.read_text().splitlines() if re.search(r'\|\s*Verilog\|',l));fields=[x.strip() for x in line.split('|')[1:-1]];assert fields[:2]==['Verilog','Pass'];numbers=[int(x) for x in fields[2:]];assert len(numbers)==7;total=numbers[-1]
 transaction=d/'project/solution1/sim/report/verilog/result.transaction.rpt';rows=[dict(transaction=int(a),latency_cycles=int(b),interval_cycles=None if c=='x' else int(c)) for a,b,c in re.findall(r'transaction\s+(\d+):\s+(\d+)\s+(\d+|x)',transaction.read_text())];assert [x['transaction'] for x in rows]==list(range(count));assert total==sum(x['interval_cycles'] for x in rows if x['interval_cycles'] is not None)+rows[-1]['latency_cycles']
 files=[Path(__file__).resolve(),d/'protocol.json',d/'manifest.json',d/'run.log',report,transaction,syn[0]];pairs=[]
 for bundle in ['control','scratch','labels','frontier']:
  a=d/f'project/solution1/sim/tv/cdatafile/c.{top}.autotvout_{bundle}.dat';b=d/f'project/solution1/sim/tv/rtldatafile/rtl.{top}.autotvout_{bundle}.dat';assert a.read_bytes()==b.read_bytes(),bundle;pairs.append(dict(bundle=bundle,bytes=a.stat().st_size,equal=True));files.extend([a,b])
 expected=json.loads((d/'C_differential.stdout').read_text());actual=[json.loads(s) for s in log.splitlines() if s.startswith('{"graphs":')][-1];assert actual==expected and actual['graphs']==count
 result=dict(status='all_declared_synthetic_scalar_RTL_transactions_and4output_bundles_verified',declared_calls=count,C_and_RTL_postcheck_status_counts=actual['status_counts'],reported_total_execution_cycles=total,min_latency_cycles=min(x['latency_cycles'] for x in rows),max_latency_cycles=max(x['latency_cycles'] for x in rows),transactions=rows,output_bundles=pairs,HLS_resources={e.tag:int(e.text) for e in root.find('AreaEstimates/Resources')},HLS_estimated_clock_ns=float(root.findtext('PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod')),source_sha256={str(p):sha(p) for p in files},scope='Fixed synthetic small-job suite including failure/rejection states, not representative real-workload RTL or throughput. C original reference and byte output equality; not independent algorithm correctness proof, requested-clock closure, physical U280 performance or asynchronous authority.',research_complete=False)
 target=d/'independent_random_RTL_review.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','declared_calls','reported_total_execution_cycles']}))
if __name__=='__main__':main()
