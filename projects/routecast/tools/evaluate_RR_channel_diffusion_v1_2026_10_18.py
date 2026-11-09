"""Fixed one-step directed RR-channel mass diffusion, a soft forecast only."""
import sys,json,array,math,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from verify_mmc_pressure_risk_v2_2026_10_18 import rank_info

def main():
 E=R/'experiments';root=E/'mmc_pressure_risk_matrix_v1_2026-10-18';manifest=json.loads((root/'vector_manifest.json').read_text());domains=json.loads((root/'domains.json').read_text());nodes=domains['ids']['channels'];N=len(nodes);pos={n:i for i,n in enumerate(nodes)};proofp=E/'mmc_typed_risk_matrix_verification_v1_2026-10-18/verification.json';proof=json.loads(proofp.read_text());idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';index=json.loads(idxp.read_text());out=E/'mmc_RR_channel_diffusion_v1_2026-10-18';out.mkdir(exist_ok=False);(out/'vectors').mkdir();bindings={str(p):sha(p) for p in [Path(__file__),root/'vector_manifest.json',root/'domains.json',proofp,idxp]};start=time.perf_counter();arrays={}
 for key in ['edge_source','edge_destination']:
  desc=index['arrays'][key];assert sha(desc['path'])==desc['sha256'];a=array.array('I');a.frombytes(Path(desc['path']).read_bytes());assert sys.byteorder=='little' and len(a)==desc['values'];arrays[key]=a;bindings[desc['path']]=desc['sha256']
 adj=[set() for _ in nodes]
 for s,t in zip(arrays['edge_source'],arrays['edge_destination']):
  if s in pos and t in pos and s!=t:adj[pos[s]].add(pos[t])
 adj=[tuple(sorted(v)) for v in adj];setup=time.perf_counter()-start;sources=['raw_min_off','raw_min_on','native_retained_off','native_retained_on','previous_native','native_retained_terminal_batch'];cases=['case_01','case_02','case_03'];vm={}
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,rule='One step: half stays, half divided equally among distinct direct channel successors. Self edges excluded; nodes without eligible successor retain all mass. Fixed rule, no fitted weight or step count.',scope='Exposed development diagnostic, soft channel-resource mass only. Not per-NET route support, endpoint-connecting paths, timing legality, probability calibration, heldout qualification or replacement of existing gates.',graph_setup_seconds=setup,channel_nodes=N,distinct_direct_channel_arcs=sum(map(len,adj))),indent=2))
 for case in cases:
  for source in sources:
   v=manifest[case+'__'+source+'__channels'];assert sha(v['path'])==v['sha256']==proof['bindings'][v['path']];a=array.array('d');a.frombytes(Path(v['path']).read_bytes());bindings[v['path']]=v['sha256'];b=array.array('d',[0.0])*N;tick=time.perf_counter()
   for i,value in enumerate(a):
    neighbors=adj[i]
    if neighbors:
     b[i]+=value/2;share=value/(2*len(neighbors))
     for j in neighbors:b[j]+=share
    else:b[i]+=value
   assert abs(math.fsum(b)-math.fsum(a))<1e-8 and all(x>=0 and math.isfinite(x) for x in b);key=case+'__'+source;p=out/'vectors'/(key+'.f64');p.write_bytes(b.tobytes());vm[key]=dict(path=str(p),sha256=sha(p),values=N,source_mass=math.fsum(a),diffused_mass=math.fsum(b),scatter_seconds=time.perf_counter()-tick)
 (out/'vector_manifest.json').write_text(json.dumps(vm,indent=2));rows=[]
 for case in cases:
  vp=E/f'mmc_multiplacement_quality_v1_2026-10-18/{case}/vectors.json';admission=json.loads(vp.with_name('verification.json').read_text());assert sha(vp)==admission['bindings'][str(vp)];truth={r['node']:r['labels']['cold'] for r in json.loads(vp.read_text())['channels']};y=[truth[n] for n in nodes];bindings[str(vp)]=sha(vp);yr=rank_info(y,N//20);truth_top=yr['selected']
  for source in sources:
   key=case+'__'+source;p=vm[key];b=array.array('d');b.frombytes(Path(p['path']).read_bytes());original=manifest[key+'__channels'];a=array.array('d');a.frombytes(Path(original['path']).read_bytes());scores={}
   for name,v in [('source_point',a),('one_step_diffusion',b)]:
    ranks=rank_info(v,N//20);den=math.sqrt(ranks['variance']*yr['variance']);clipped=[min(1,x) for x in v];scores[name]=dict(spearman=sum(x*z for x,z in zip(ranks['center'],yr['center']))/den,deterministic_precision_at_5percent=len(ranks['selected']&truth_top)/(N//20),raw_MAE=math.fsum(abs(x-z) for x,z in zip(v,y))/N,clipped_Brier=math.fsum((x-z)**2 for x,z in zip(clipped,y))/N,clipped_mass=math.fsum(clipped))
   rows.append(dict(case=case,source=source,scores=scores))
 for p,h in bindings.items():assert sha(p)==h
 with (out/'results.json').open('x') as f:json.dump(dict(status='all18_directed_channel_diffusion_diagnostics_computed',bindings=bindings,rows=rows,scope='Only channel diagnostic metrics on exposed cold labels. No original four-metric/full-domain gate, new route or net-time utility claim.'),f,indent=2)
 print(json.dumps([r for r in rows if r['source']=='native_retained_on'],indent=2),flush=True)
if __name__=='__main__':main()
