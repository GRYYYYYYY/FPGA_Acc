"""Observe original OPIN matrix process; never restart; then authenticate/audit."""
import pathlib,json,time,hashlib,subprocess,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(pid):
 p=pathlib.Path('/proc')/str(pid)
 try:
  stat=(p/'stat').read_text();args=(p/'cmdline').read_bytes().split(b'\0')
  return {'pid':pid,'start_ticks':stat[stat.rfind(')')+2:].split()[19],'argv':[a.decode() for a in args if a]}
 except (OSError,ValueError,IndexError):return None

def main():
 parent=BASE/'fixed_opin_candidate_matrix';matches=[]
 for path in pathlib.Path('/proc').iterdir():
  if path.name.isdigit():
   item=identity(int(path.name))
   if item and 'tools/stereo_fixed_opin_candidate_matrix.py' in item['argv']:matches.append(item)
 assert len(matches)==1;process=matches[0]
 out=BASE/'opin_matrix_completion_chain';out.mkdir(exist_ok=False);(out/'source').mkdir()
 names=['stereo_opin_matrix_completion_chain.py','check_stereo_fixed_opin_candidate_matrix.py','audit_stereo_fixed_opin_matrix_xml.py'];sources={n:sha(ROOT/'tools'/n) for n in names}
 for n in names:shutil.copyfile(ROOT/'tools'/n,out/'source'/n)
 protocol={'original_process':process,'parent_protocol_sha256':sha(parent/'protocol.json'),'source_sha256':sources,'scope':'observe original matrix without restart; complete matrix checks then individual XML audit; no accepted repair'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps({'stage':'waiting_original_matrix','process':process}),flush=True)
 while not (parent/'receipt.json').exists():
  if identity(process['pid'])!=process:raise RuntimeError('original matrix missing/terminal without receipt; no restart')
  time.sleep(10)
 assert sha(parent/'protocol.json')==protocol['parent_protocol_sha256'];stages=[]
 for name in names[1:]:
  assert all(sha(ROOT/'tools'/n)==h for n,h in sources.items());start=time.monotonic();command=['python3','-u','tools/'+name]
  result=subprocess.run(command,cwd=ROOT);stages.append({'command':command,'exit_code':result.returncode,'wall_s':time.monotonic()-start});(out/'stages.json').write_text(json.dumps(stages,indent=2)+'\n')
  if result.returncode:raise RuntimeError('dependent matrix audit failed; no restart')
 assert all(sha(ROOT/'tools'/n)==h for n,h in sources.items())
 receipt={'parent_receipt_sha256':sha(parent/'receipt.json'),'stages':stages,'protocol_sha256':sha(out/'protocol.json'),'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
