"""Bind packed routing tasks to native logical sink-pin indices in original route order."""
import argparse,csv,json,re,struct
from collections import Counter
from pathlib import Path
from persistent_vpr_timing import sha
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pair',type=Path);p.add_argument('output',type=Path);a=p.parse_args();pair=a.pair.resolve();out=a.output.resolve();out.mkdir(exist_ok=False)
    m=json.loads(pair.read_text());route=Path(m['case'])/'circuit.route';connections=Path(m['reference'])/'connections.csv';tasks_path=pair.parent/'input.tasks';rows=[];net=None;source=None
    for line in route.read_text().splitlines():
        match=re.match(r'^\s*Net\s+(\d+)\s+\((.*)\)\s*$',line)
        if match:net=int(match[1]);source=None;continue
        match=re.match(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b',line)
        if not match or net is None:continue
        node=int(match[1]);kind=match[2]
        if kind=='SOURCE':
            if source is None:source=node
            else:assert source==node
        elif kind=='SINK':
            assert source is not None
            pin=re.search(r'Net_pin_index:\s*(\d+)',line);assert pin is not None and int(pin[1])>0
            rows.append(dict(task_id=len(rows),net_id=net,net_pin_index=int(pin[1]),source_rr=source,sink_rr=node))
    with connections.open() as stream:exported=list(csv.DictReader(stream))
    packed=list(struct.iter_unpack('<IIIIHHIII',tasks_path.read_bytes()));assert len(rows)==len(exported)==len(packed)
    seen=set();triples=Counter()
    for row,connection,task in zip(rows,exported,packed):
        assert tuple(row[k] for k in ['task_id','net_id','source_rr','sink_rr'])==task[:4]
        assert task[:4]==tuple(int(connection[k]) for k in ['id','net_id','source','sink'])
        assert task[4:8]==tuple(int(connection[k]) for k in ['criticality_q','max_hops','priority','epoch']) and task[8]==0
        key=(row['net_id'],row['net_pin_index']);assert key not in seen;seen.add(key);triples[(row['net_id'],row['source_rr'],row['sink_rr'])]+=1
    mapping=out/'task_pin_identity.csv'
    with mapping.open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=['task_id','net_id','net_pin_index','source_rr','sink_rr'],lineterminator='\n');writer.writeheader();writer.writerows(rows)
    proof=dict(status='original_route_logical_sink_pin_order_matches_connections_and_packed_tasks',tasks=len(rows),unique_net_pin_keys=len(seen),duplicate_endpoint_triples=sum(v>1 for v in triples.values()),rows_in_duplicate_endpoint_triples=sum(v for v in triples.values() if v>1),source_sha256={str(p):sha(p) for p in [pair,route,connections,tasks_path,mapping,Path(__file__).resolve()]},scope='Exact original route sink order,explicit Net_pin_index,connection CSV and packed Task identity. Logical pin key disambiguates duplicate RR sink endpoints. No initial timing CSV join,native newbuild compatibility or initialization-policy adoption yet.',board_result=False,research_complete=False)
    (out/'audit.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k not in ['source_sha256','scope']}))
