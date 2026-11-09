"""Observe original conv_layer span evidence chain process; never restart; then authenticate/audit."""
import pathlib,json,time,hashlib,subprocess,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(pid):
 p=pathlib.Path('/proc')/str(pid)
 try:
  stat=(p/'stat').read_text();args=(p/'cmdline').read_bytes().split(b'\0')
  return {'pid':pid,'start_ticks':stat[stat.rfind(')')+2:].split()[19],'argv':[a.decode() for a in args if a]}
 except (OSError,ValueError,IndexError):return None

def main():
 parent=BASE/'conv_layer_span_completion_chain_2026-10-06';matches=[]
 for path in pathlib.Path('/proc').iterdir():
  if path.name.isdigit():
   item=identity(int(path.name))
   if item and 'tools/conv_layer_span_completion_chain.py' in item['argv']:matches.append(item)
 assert len(matches)==1;process=matches[0]
 out=BASE/'conv_layer_candidate_comparison_chain_2026-10-06';out.mkdir(exist_ok=False);(out/'source').mkdir()
 names=['conv_layer_candidate_comparison_chain.py','compare_conv_layer_candidate_objectives.py','pre_route_endpoints.py'];sources={n:sha(ROOT/'tools'/n) for n in names}
 for n in names:shutil.copyfile(ROOT/'tools'/n,out/'source'/n)
 protocol={'original_process':process,'parent_protocol_sha256':sha(parent/'protocol.json'),'source_sha256':sources,'scope':'observe original span evidence chain without restart; matched candidate objective comparison after physical/electrical/global-impact stages; no accepted repair'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps({'stage':'waiting_original_span evidence chain','process':process}),flush=True)
 while not (parent/'receipt.json').exists():
  if identity(process['pid'])!=process:raise RuntimeError('original span evidence chain missing/terminal without receipt; no restart')
  time.sleep(10)
 assert sha(parent/'protocol.json')==protocol['parent_protocol_sha256'];stages=[]
 for name in ['compare_conv_layer_candidate_objectives.py']:
  assert all(sha(ROOT/'tools'/n)==h for n,h in sources.items());start=time.monotonic();command=['python3','-u','tools/'+name]
  result=subprocess.run(command,cwd=ROOT);stages.append({'command':command,'exit_code':result.returncode,'wall_s':time.monotonic()-start});(out/'stages.json').write_text(json.dumps(stages,indent=2)+'\n')
  if result.returncode:raise RuntimeError('dependent full CSR audit failed; no restart')
 assert all(sha(ROOT/'tools'/n)==h for n,h in sources.items())
 receipt={'parent_receipt_sha256':sha(parent/'receipt.json'),'stages':stages,'protocol_sha256':sha(out/'protocol.json'),'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
