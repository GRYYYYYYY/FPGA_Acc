"""Full original XML topology/metadata and independent scalar formula CSR audit."""
import json,time,csv,io,resource
from pathlib import Path
from fractions import Fraction
from array import array
import xml.etree.ElementTree as ET
from prepared_csr import read,TYPES,DIRECTIONS,SIDES,U64
from bound_indexed_cost import parse_bound_table
from path_rc import number
from pre_route_endpoints import sha

def audit(base):
    root=Path(base);receipt=json.loads((root/'receipt.json').read_text());p=json.loads((root/'protocol.json').read_text())
    assert receipt['manifest_sha256']==sha(root/'csr/manifest.json') and receipt['protocol_sha256']==sha(root/'protocol.json')
    assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values())
    start=time.monotonic();m,f=read(root/'csr',p['identity']['graph_sha256'])
    # Stereo inventory proves contiguous IDs; use ranks only after checking here.
    assert all(n==i for i,n in enumerate(f['node_ids']))
    indices=array('Q',[U64])*m['nodes']
    for row in csv.DictReader(io.StringIO(Path(p['inputs']['bindings']['path']).read_text())):
        n=int(row['node_id']);assert 0<=n<len(indices) and indices[n]==U64;indices[n]=int(row['cost_index'])
    assert U64 not in indices
    norm,rows=parse_bound_table(Path(p['inputs']['table']['path']).read_text());norm=Fraction(norm);bases={i:Fraction(r['base']) for i,r in rows.items()}
    resistance=[None]*m['nodes'];capacitance=[None]*m['nodes'];switches={};cache={};cursors=array('Q',f['row_offsets'][:-1]);stack=[];nodes=edges=0
    for event,e in ET.iterparse(p['inputs']['graph']['path'],events=('start','end')):
        if event=='start':stack.append(e);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='switch' and parent=='switches':
            t=e.find('timing');assert e.get('type') in ('mux','tristate','buffer') and t is not None
            switches[int(e.get('id'))]=tuple(number(t.get(k,'0')) for k in ('R','Tdel','Cinternal'))
        elif e.tag=='node' and parent=='rr_nodes':
            n=int(e.get('id'));assert n==nodes;nodes+=1;loc=e.find('loc');seg=e.find('segment');t=e.find('timing')
            expected={'types':TYPES[e.get('type')],'directions':DIRECTIONS[e.get('direction','NONE')],'sides':SIDES[loc.get('side','NONE')],'capacities':int(e.get('capacity')),'segments':U64 if seg is None else int(seg.get('segment_id'))}
            expected.update({k:int(loc.get(k,'0')) for k in ('xlow','xhigh','ylow','yhigh','layer','ptc')})
            for k,v in expected.items():assert f[k][n]==v,(n,k)
            resistance[n]=number(t.get('R','0'));capacitance[n]=number(t.get('C','0'))
        elif e.tag=='edge' and parent=='rr_edges':
            assert nodes==m['nodes'];a=int(e.get('src_node'));b=int(e.get('sink_node'));s=int(e.get('switch_id'));slot=cursors[a]
            assert slot<f['row_offsets'][a+1];assert f['edge_ids'][slot]==edges and f['dest_ranks'][slot]==b and f['switch_ids'][slot]==s
            key=(s,resistance[a],resistance[b],capacitance[b],indices[b])
            if key not in cache:
                sr,intrinsic,internal=switches[s];r=resistance[b];c=capacitance[b]
                delay=intrinsic+(sr+r/2)*c+(sr+r-resistance[a]/2)*internal
                assert delay>=0;cache[key]=round((delay+bases[indices[b]])/norm*p['scale']/2)
            expected=cache[key] if f['capacities'][b] else U64
            assert f['costs'][slot]==expected,(edges,'cost');cursors[a]+=1;edges+=1
        if (e.tag,parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')):stack[-2].remove(e);e.clear()
        stack.pop()
    assert nodes==m['nodes'] and edges==m['edges'];assert all(cursors[i]==f['row_offsets'][i+1] for i in range(nodes))
    assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values())
    result={'nodes':nodes,'edges':edges,'all_node_fields_and_raw_edges_exact':True,'all_scalar_costs_exact':True,'formula_cache_entries':len(cache),'wall_s':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'inputs_unchanged':True,'conversion_receipt_sha256':sha(root/'receipt.json'),'audit_source_sha256':sha(__file__),'scope':'full original XML vs CSR including independent zero-upstream exact cost formula; not path optimality or tree STA'}
    (root/'physical_cost_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':
    import sys
    audit(sys.argv[1])
