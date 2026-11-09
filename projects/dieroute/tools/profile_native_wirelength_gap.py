"""Decompose native wirelength gap into exact per-net channel-node span sums."""
import argparse,csv,json,re,struct
from pathlib import Path
from collections import defaultdict
from persistent_vpr_timing import sha

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pair',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    pair=a.pair.resolve();out=a.output.resolve();out.mkdir(exist_ok=False)
    m=json.loads(pair.read_text());mode,=m['modes'];base=pair.parent;native=Path(m['case'])
    nodes_path=base/'input.nodes';spans=[row[2] for row in struct.iter_unpack('<IHH',nodes_path.read_bytes())]
    original=defaultdict(set);current=None;route=native/'circuit.route'
    for line in route.read_text().splitlines():
        match=re.match(r'Net (\d+) ',line)
        if match:current=int(match[1])
        match=re.match(r'Node:\s*(\d+)\s+',line)
        if match:
            assert current is not None
            original[current].add(int(match[1]))
    candidate=defaultdict(set);trees=base/(mode+'_0.route_trees.csv')
    with trees.open() as stream:
        for row in csv.DictReader(stream):
            net=int(row['net_id']);candidate[net].update(int(row[k]) for k in ['source','parent','child'])
    rows=[]
    for net in sorted(set(original)|set(candidate)):
        old=sum(spans[n] for n in original[net]);new=sum(spans[n] for n in candidate[net])
        rows.append(dict(net_id=net,baseline_wirelength=old,candidate_wirelength=new,delta=new-old,baseline_channel_nodes=sum(spans[n]>0 for n in original[net]),candidate_channel_nodes=sum(spans[n]>0 for n in candidate[net])))
    old=sum(r['baseline_wirelength'] for r in rows);new=sum(r['candidate_wirelength'] for r in rows)
    metrics=m['modes'][mode]['native_validation']
    # The paired manifest stores native metrics in a separate subsection on some versions.
    (out/'raw_decomposition.json').write_text(json.dumps(dict(baseline_wirelength=old,candidate_wirelength=new,rows=rows),indent=2)+'\n')
    baseline_log=native/'vpr_stdout.log'
    expected_old=int(re.findall(r'Total wirelength:\s+(\d+)',baseline_log.read_text())[-1]);assert old==expected_old,(old,expected_old)
    assert metrics is not None,'Need explicit recorded native QoR before accepting decomposition'
    assert new==metrics['total_wirelength'],(new,metrics)
    report=dict(status='native_wirelength_gap_exact_per_net_decomposition',baseline_wirelength=old,candidate_wirelength=new,net_delta=new-old,worsened_nets=sum(r['delta']>0 for r in rows),improved_nets=sum(r['delta']<0 for r in rows),positive_delta=sum(max(0,r['delta']) for r in rows),negative_delta=sum(min(0,r['delta']) for r in rows),largest_regressions=sorted(rows,key=lambda r:(-r['delta'],r['net_id']))[:20],source_sha256={str(p):sha(p) for p in [pair,nodes_path,route,trees,baseline_log,Path(__file__).resolve()]},scope='Unique channel-node native span sums per net;aggregate must equal both native wirelength metrics. Descriptive decomposition,not CPD causality or algorithm tuning/heldout result.',board_result=False,research_complete=False)
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','largest_regressions']}))
