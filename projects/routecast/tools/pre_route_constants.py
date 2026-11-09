"""Explicit atom-identity-checked conservative constant policy adapter."""
import argparse,json
from pathlib import Path
import xml.etree.ElementTree as ET
from blif_constants import constants
from pre_route_endpoints import extract,sha


def extract_with_constants(net,place,graph,atom,method,architecture=None):
    if method not in {'global','route'}:raise ValueError('unsupported constant_net_method')
    before=sha(atom)
    if ET.parse(net).getroot().attrib.get('atom_netlist_id')!='SHA256:'+before:
        raise ValueError('atom netlist identity mismatch')
    inferred=constants(atom)
    undriven={}
    architecture_hash=sha(architecture) if architecture is not None else None
    if architecture is not None:
        from blif_undriven_outputs import undriven_outputs
        undriven=undriven_outputs(atom,architecture)
    result,report=extract(net,place,graph)
    names=result['net_names'];excluded=[];kept=[]
    counts={}
    for r in result['connections']:counts[r['net_id']]=counts.get(r['net_id'],0)+1
    for nid,n in names.items():
        if (n in inferred or n in undriven) and int(nid) in counts and method=='global':
            excluded.append({'net':n,'net_id':int(nid),'reason':'explicit constant_net_method global; conservative BLIF inference','constant_value':inferred.get(n),**({'primitive_evidence':undriven[n],'reason':'explicit constant_net_method global; undriven architecture combinational output'} if n not in inferred else {}),'sink_pins':counts[int(nid)]})
    removed={r['net_id'] for r in excluded}
    kept=[r for r in result['connections'] if r['net_id'] not in removed]
    result['connections']=kept;result['excluded_nets'].extend(excluded)
    result['constant_net_method']=method
    result['constant_inference_scope']='.names with all inputs known; no latch/subckt/partial-input inference'
    if architecture is not None:
        result['inputs']['constant_architecture']={'path':str(Path(architecture).resolve()),'sha256':architecture_hash}
        result['undriven_constant_inference_sha256']=sha(Path(__file__).with_name('blif_undriven_outputs.py'))
        result['constant_inference_scope']+='; optional architecture undriven combinational outputs, no value inference'
        if sha(architecture)!=architecture_hash:raise ValueError('architecture changed')
    result['inputs']['atom']={'path':str(Path(atom).resolve()),'sha256':before}
    result['constant_adapter_sha256']=sha(Path(__file__))
    result['constant_inference_sha256']=sha(Path(__file__).with_name('blif_constants.py'))
    if sha(atom)!=before:raise ValueError('atom input changed')
    report.update(connections=len(kept),excluded_nets=result['excluded_nets'],inferred_constants=inferred,constant_net_method=method)
    if architecture is not None:report["undriven_outputs"]=undriven
    return result,report


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('net','place','graph','atom'):p.add_argument(k,type=Path)
    p.add_argument('--constant-net-method',choices=['global','route'],required=True)
    p.add_argument('--architecture',type=Path)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    result,report=extract_with_constants(a.net,a.place,a.graph,a.atom,a.constant_net_method,a.architecture)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    for name,value in [('endpoints',result),('mapping',report)]:
        (a.output_dir/f'{name}.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'connections':len(result['connections']),'excluded':result['excluded_nets']}))
