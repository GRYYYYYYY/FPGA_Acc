"""Input-only four owner flags; fixed mechanism, no target labels opened."""
import array,json,hashlib
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/mmc_resource_owner_context_v1_2026-10-19';out.mkdir(exist_ok=False)
 spec=dict(status='FIXED_OWNER_CONTEXT_PROTOCOL_BEFORE_LABEL_SCORING',cases=['case_01','case_02','case_03'],encoding='extended_code=original216_code*16+flags. bit0:any A owner fanout>1; bit1:any A owner has changed endpoint connection; bit2:any B owner fanout>1; bit3:any B owner has changed endpoint connection. All owners, no NET identity as feature.',model='One primary extension only. Fixed existing leave-one-layout-out folds, Laplace(S+1)/(N+2), quantization1e6, same aggregate expected-L1 NET weights, implication closure and min-B tie rule. No feature selection, threshold/regularization/temperature search. Compare frozen216 primary as control, retain original full cold quality gates.',source_policy='A/B banks and previously verified NET feature metadata only; independently rebuild fanout and endpoint-change flags from original current and before endpoint files. No target native labels read for extraction.',scope='Old exposed layouts, development mechanism test only; no new heldout family or utility evidence. Original upstream full costs retained.')
 (out/'protocol.json').write_text(json.dumps(spec,indent=2)+'\n');cp=R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32';ids=array.array('I');ids.frombytes(cp.read_bytes());fr=R/'experiments/mmc_label_free_NET_features_v1_2026-10-19';receipt=read(fr/'receipt.json');proof=read(fr/'independent_verification_v1.json');bindings={str(p):sha(p) for p in [cp,fr/'receipt.json',fr/'independent_verification_v1.json',Path(__file__).resolve()]};rows=[]
 for case in spec['cases']:
  fp=fr/(case+'.jsonl');assert receipt['bindings'][str(fp)]==sha(fp);features={x['net_id']:x['values'] for x in map(json.loads,fp.open())};assert len(features)==55300
  producer=R/f'experiments/mmc_all_NET_feedback_v1_2026-10-18/{case}/protocol.json';timing=Path(read(producer)['criticality_input_proof']);tp=read(timing);ep=Path(tp['after_endpoint']);before=Path(tp['before_endpoint']);old={q['connection_id']:q for q in read(before)['connections']};current=read(ep)['connections'];fanout=Counter(q['net_id'] for q in current);changed=Counter()
  for q in current:
   o=old[q['connection_id']];changed[q['net_id']]+=((o['source'],o['sink'])!=(q['source'],q['sink']))
  assert sum(fanout.values())==115572 and set(fanout)==set(features)
  for n,f in features.items():assert (fanout[n],changed[n])==(f[0],f[1])
  bank=R/f'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/{case}/banks.jsonl';flags=defaultdict(int);seennets=set()
  for x in map(json.loads,bank.open()):
   n=x['net_id'];seennets.add(n);flag=int(fanout[n]>1)+2*int(changed[n]>0)
   for side,shift in [('A',0),('B',2)]:
    for rr in x[side]:flags[rr]|=flag<<shift
  assert seennets==set(features)
  ctx=R/f'experiments/mmc_resource_context_v1_2026-10-19/{case}.u16';codes=array.array('H');codes.frombytes(ctx.read_bytes());assert len(codes)==len(ids)==258720
  result=array.array('H',(int(c)*16+flags[n] for n,c in zip(ids,codes)));assert all(0<=v<3456 for v in result)
  # Reverse decoding cross-checks every saved feature; NET fields separately
  # recomputed above, not merely trusted from the old feature table.
  target=out/(case+'.u16');target.write_bytes(result.tobytes());reload=array.array('H');reload.frombytes(target.read_bytes());assert all(v//16==c and v%16==flags[n] for n,c,v in zip(ids,codes,reload))
  paths=[fp,producer,timing,ep,before,bank,ctx,target];bindings.update({str(p):sha(p) for p in paths});rows.append(dict(case=case,resources=len(result),NETs=len(features),connections=len(current),occupied_categories=len(set(result)),flag_histogram=dict(sorted(Counter(v%16 for v in result).items()))));print('OWNER_CONTEXT_INPUT_CHECKED',case,len(result),len(set(result)),flush=True)
 (out/'receipt.json').write_text(json.dumps(dict(status='ALL3_OWNER_FLAGS_REBUILT_FROM_ENDPOINTS_AND_RESOURCE_CODES_ROUNDTRIPPED',rows=rows,bindings=bindings,target_labels_read=False,scope=spec['scope']),indent=2)+'\n')
if __name__=='__main__':main()
