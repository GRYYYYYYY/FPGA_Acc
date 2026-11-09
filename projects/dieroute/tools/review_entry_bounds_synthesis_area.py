"""Compare immutable completed OOC kernel synthesis reports, not routed designs."""
from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 o=R/'work/entry_bounds_pipeline_synthesis_area_review_20261021';o.mkdir();paths={name:R/'work'/folder/'link_temp/link/vivado/vpl/prj/prj.runs/ulp_net_commit_0_synth_1/ulp_net_commit_0_utilization_synth.rpt' for name,folder in [('H','execute_opcode_split_hw_20261020'),('pipelined_bounds','entry_bounds_pipeline_hw_20261021')]};rows={}
 for name,p in paths.items():
  text=p.read_text();assert re.search(r'Design State\s*:\s*Synthesized',text) and 'xcu280-fsvh2892-2L-e' in text and 'Vivado v.2022.2' in text
  metrics={}
  for key,label in [('LUTs','CLB LUTs*'),('registers','CLB Registers'),('BRAM_tiles','Block RAM Tile'),('DSPs','DSPs')]:
   m=re.search(r'^\|\s*'+re.escape(label)+r'\s*\|\s*([0-9.]+)\s*\|',text,re.M);assert m,(name,label);metrics[key]=float(m[1]) if '.' in m[1] else int(m[1])
  rows[name]=metrics
 delta={k:rows['pipelined_bounds'][k]-rows['H'][k] for k in rows['H']}
 result=dict(status='matched_kernel_completed_synthesis_area_reports_reviewed',kernel='ulp_net_commit_0',rows=rows,pipelined_minus_H=delta,source_sha256={str(p):sha(p) for p in [*paths.values(),Path(__file__)]},scope='Matched named OOC kernel synthesis block and Vivado2022.2/XCU280 reports only. Excludes platform infrastructure and physical optimization. Not routed area,timing closure,device performance or all-path improvement. H is known setup-failing;new implementation still running.',research_complete=False)
 (o/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
