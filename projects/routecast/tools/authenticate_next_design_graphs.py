"""Authenticate read-only local graph archive contents before frontend work."""
import pathlib,json,hashlib,time,concurrent.futures
ROOT=pathlib.Path(__file__).resolve().parents[1];INPUT=ROOT/'experiments/next_design_input_inventory_2026-10-06/inventory.json'
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def check(row):
 graph=row['inputs']['rr_graph'];p=pathlib.Path(graph['path']);start=time.monotonic();before=p.stat();actual=sha(p);after=p.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns);assert actual==graph['declared_sha256'],row['archive']
 return {'archive':row['archive'],'graph_path':str(p),'graph_sha256':actual,'bytes':after.st_size,'wall_s':time.monotonic()-start,'read_only':True}
def main():
 initial=sha(INPUT);data=json.loads(INPUT.read_text());out=ROOT/'experiments/next_design_graph_authentication_2026-10-06';out.mkdir();(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes());source=sha(pathlib.Path(__file__))
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures=[pool.submit(check,r) for r in data['archives']]
  for future in concurrent.futures.as_completed(futures):
   result=future.result();results.append(result);print(json.dumps(result),flush=True);(out/'progress.json').write_text(json.dumps(results,indent=2)+'\n')
 assert sha(INPUT)==initial and sha(pathlib.Path(__file__))==source
 receipt={'inventory_sha256':initial,'source_sha256':source,'graphs':sorted(results,key=lambda v:v['archive']),'scope':'graph archive byte authentication only; not topology audit, full frontend, family split or prediction validation'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
