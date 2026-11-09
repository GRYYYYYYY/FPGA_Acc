"""Cold full-graph length-switch transport, no native cost binding or labels."""
import pathlib,json,time,shutil,sys,argparse,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args();front=ROOT/'experiments/adder_tree_family_endpoints_2026-10-06'/args.design;p=json.loads((front/'protocol.json').read_text());out=ROOT/'experiments/adder_tree_family_length_switch_csr_2026-10-06'/args.design;out.mkdir(parents=True);(out/'source').mkdir()
 names=['convert_adder_tree_length_switch.py','streaming_rr_nodes.py','streaming_csr_builder.py','prepare_length_switch_csr.py','prepared_csr.py','pre_route_endpoints.py','path_rc.py','semantic_sketch.py']
 for n in names:shutil.copyfile(ROOT/'tools'/n,out/'source'/n)
 sys.path.insert(0,str(out/'source'));from pre_route_endpoints import sha;from streaming_rr_nodes import read;from streaming_csr_builder import write;from prepare_length_switch_csr import switches,cost
 graph=p['inputs']['rr_graph'];assert sha(graph['path'])==graph['sha256'];sources={n:sha(out/'source'/n) for n in names};protocol={'graph':graph,'frontend_receipt_sha256':sha(front/'receipt.json'),'sources':sources,'cost':'existing rr_length_switch: 1+256*destination channel span+switch Tdel ps ROUND_HALF_UP; capacity0 disabled','scope':'cold full physical graph transport only; no native labels or new model tuning'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
 try:
  fields,_,_,_,_,digest=read(graph['path']);assert digest==graph['sha256'];rank={n:i for i,n in enumerate(fields['node_ids'])};delays=switches(graph['path'])
  def arcs():
   stack=[];eid=0
   for event,e in ET.iterparse(graph['path'],events=('start','end')):
    if event=='start':stack.append(e);continue
    parent=stack[-2].tag if len(stack)>1 else None
    if e.tag=='edge' and parent=='rr_edges':
     a=int(e.get('src_node'));b=int(e.get('sink_node'));sid=int(e.get('switch_id'));i=rank[b]
     value=cost(fields['types'][i],fields['xlow'][i],fields['xhigh'][i],fields['ylow'][i],fields['yhigh'][i],fields['capacities'][i],delays[sid]);yield eid,a,b,sid,value;eid+=1
    if parent in ('rr_nodes','rr_edges','switches','segments','block_types','grid','channels'):stack[-2].remove(e);e.clear()
    stack.pop()
   assert sha(graph['path'])==digest
  context={'graph_sha256':digest,'cost_identity':{'definition':protocol['cost'],'implementation_sha256':sources['semantic_sketch.py'],'preparer_sha256':sources['prepare_length_switch_csr.py']},'scale':1,'normalization':'none','mode':'rr_length_switch'}
  m=write(fields,arcs,out/'csr',context);assert all(sha(out/'source'/n)==h for n,h in sources.items());assert sha(graph['path'])==digest
  receipt={'protocol_sha256':sha(out/'protocol.json'),'nodes':m['nodes'],'edges':m['edges'],'manifest_sha256':sha(out/'csr/manifest.json'),'context_sha256':m['context_sha256'],'wall_s':time.monotonic()-start,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
 except BaseException as error:
  (out/'failure.json').write_text(json.dumps({'error':repr(error),'wall_s':time.monotonic()-start})+'\n');raise
if __name__=='__main__':main()
