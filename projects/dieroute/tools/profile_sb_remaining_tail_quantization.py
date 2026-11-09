"""Profile quantization of the uncongested cost component on one observed route."""
import collections,csv,hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'work/sb_remaining_tail_cost_quantization_profile_20261015'
def table(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def main():
 c=json.loads((R/'work/sb_remaining_tail_native_delay_calibration_20261015/protocol.json').read_text());inp=c['input_prefix'];route=c['route_prefix']
 files=[Path(inp+'.nodes'),Path(inp+'.edges'),Path(route+'.paths.csv'),Path(c['local_timing_input']),Path(__file__).resolve()]
 nodes=list(struct.iter_unpack('<IHH',files[0].read_bytes()));edges=list(struct.iter_unpack('<IHH',files[1].read_bytes()));timing={int(x['task_id']):x for x in table(files[3])};paths=collections.defaultdict(list)
 for x in table(files[2]):
  v=paths[int(x['task_id'])];assert len(v)==int(x['path_index']);v.append(int(x['resource_id']))
 assert len(paths)==len(timing)==1920
 total=zero=positive=recovered=0;affected=set();hist=collections.Counter()
 for tid,path in paths.items():
  t=timing[tid];n=int(t['source']);q=min(int(t['criticality_q']),64880)
  for dst in path:
   begin,count,_=nodes[n];matches={(b,d) for v,b,d in edges[begin:begin+count] if v==dst};assert len(matches)==1
   base,delay=matches.pop();weight=65535-q;coarse=base*weight//65535;fine=base*weight*256//65535
   total+=1;positive+=base>0
   if base>0 and coarse==0:
    zero+=1;affected.add(tid);hist[base]+=1;recovered+=fine>0
   n=dst
  assert n==int(t['sink'])
 report=dict(status='one_observed_final_route_uncongested_base_component_quantization_profile',connections=len(paths),path_edge_occurrences=total,positive_base_occurrences=positive,positive_base_rounded_to_zero_scale1=zero,connections_with_zeroed_base_component=len(affected),positive_base_recovered_scale256=recovered,zeroed_base_histogram=dict(sorted(hist.items())),source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},scope='Uses actual final route and criticalities presented at iteration8. Evaluates only uncongested multiplicative baseline (acc=present=256); not historical search scores, congestion/ownership history, causal QoR proof, or evidence that costscale256 improves routing. Delays and other cost terms are not classified as zero here. Prior costscale negative results remain applicable within their own scope.',board_result=False,research_complete=False)
 P.mkdir(exist_ok=False);(P/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
