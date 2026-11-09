"""Reproducible driver for read-only archived RR/route integrity audits."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
from audit_native_route import audit
from rr_graph import read_rr_graph


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',nargs=3,action='append',required=True,metavar=('NAME','GRAPH','ROUTE'))
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    records=[]
    for name,graph,route in args.case:
        if not name.replace('_','').isalnum(): raise ValueError('unsafe case name')
        graph,route=Path(graph),Path(route)
        audit_summary=read_rr_graph(graph).summary(); audit_summary['source_path']=str(graph.resolve())
        graph_out=args.output_dir/f'{name}_audit.json'
        graph_out.write_text(json.dumps(audit_summary,indent=2)+'\n')
        result=audit(graph,route)
        if result['graph_sha256']!=audit_summary['sha256'] or sha(graph)!=result['graph_sha256'] or sha(route)!=result['route_sha256']:
            raise ValueError('input changed during audit')
        route_out=args.output_dir/f'{name}_route_audit.json'
        route_out.write_text(json.dumps(result,indent=2)+'\n')
        record={'name':name,'nodes':audit_summary['node_count'],'edges':audit_summary['edge_count'],
                'connections':len(result['connections']),'nets':result['routed_nets'],
                'occupied_nodes':result['occupied_nodes'],'overflow_nodes':len(result['overflow_nodes']),
                'shared_node_occurrences_saved':result['shared_node_occurrences_saved'],
                'graph_path':str(graph.resolve()),'graph_sha256':result['graph_sha256'],
                'route_path':str(route.resolve()),'route_sha256':result['route_sha256'],
                'graph_audit_sha256':sha(graph_out),'route_audit_sha256':sha(route_out)}
        records.append(record);print(json.dumps(record),flush=True)
    sources=[Path(__file__),Path(__file__).with_name('rr_graph.py'),Path(__file__).with_name('rr_occupancy.py'),
             Path(__file__).with_name('audit_native_route.py'),Path(__file__).with_name('connection_golden.py')]
    receipt={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':records,
             'source_sha256':{p.name:sha(p) for p in sources},'all_checks_passed':True,
             'scope':'Read-only archive import/replay and node accounting; no new router execution or predictor QoR'}
    (args.output_dir/'native_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__': main()
