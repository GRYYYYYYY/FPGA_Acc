"""Compare completed out-of-context CU synthesis, separately from HLS estimates."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/negotiate_scan_CU_synthesis_review_20261020'
SUFFIX='link_temp/link/vivado/vpl/prj/prj.runs/ulp_net_commit_0_synth_1'
def read_run(folder):
 directory=ROOT/'work'/folder/SUFFIX
 report=directory/'ulp_net_commit_0_utilization_synth.rpt'
 log=directory/'ulp_net_commit_0.vds'
 text=report.read_text();stdout=log.read_text()
 assert 'synth_design completed successfully' in stdout and 'Exiting Vivado' in stdout
 assert '| Design State : Synthesized' in text and '| Design       : ulp_net_commit_0' in text
 assert '| Device       : xcu280-fsvh2892-2L-e' in text
 resources={}
 for key,label in [('LUT','CLB LUTs*'),('registers','CLB Registers'),('BRAM_tiles','Block RAM Tile'),('DSP','DSPs')]:
  resources[key]=int(re.search(r'^\|\s*'+re.escape(label)+r'\s*\|\s*(\d+)\s*\|',text,re.M)[1])
 return resources,[report,log]
def main():
 parent,ap=read_run('ripup_predecessor_helper_hw_20261018')
 candidate,bp=read_run('negotiate_scan_helper_hw_20261020')
 assert parent==dict(LUT=67531,registers=87978,BRAM_tiles=145,DSP=45)
 assert candidate==dict(LUT=70256,registers=91970,BRAM_tiles=147,DSP=42)
 OUT.mkdir(exist_ok=False)
 audit=dict(status='completed_actual_net_commit_CU_synthesis_resources_compared',parent=parent,candidate=candidate,candidate_minus_parent={k:candidate[k]-parent[k] for k in parent},scope='Vivado out-of-context net_commit CU synthesis only, not HLS estimates or final placed/routed design. Full implementation remains in progress; no timing closure, adoption, representative workload or board performance claim.',source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*ap,*bp,Path(__file__).resolve()]},research_complete=False,adopted=False)
 (OUT/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
