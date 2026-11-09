"""Compare a separate view-API census to observed validation-journal nodes."""
import csv,hashlib,itertools,struct
from pathlib import Path


def audit(input_prefix,topology_prefix,output_prefix):
    files=[Path(__file__).resolve()]
    def path(suffix):
        p=Path(str(output_prefix)+suffix);files.append(p);return p
    def table(suffix):
        with path(suffix).open() as stream:return list(csv.DictReader(stream))
    tasks_path=Path(str(input_prefix)+'.tasks');owners_path=Path(str(topology_prefix)+'.node_die');files.extend([tasks_path,owners_path])
    tasks={r[0]:r for r in struct.iter_unpack('<IIIIHHIII',tasks_path.read_bytes())}
    owners=[r[0] for r in struct.iter_unpack('<H',owners_path.read_bytes())]
    migration={(int(r['window']),int(r['task_id'])):int(r['execution_die']) for r in table('.task_migration.csv')}
    expected=[]
    for row in table('.transactions.csv'):
        window,task,epoch=[int(row[k]) for k in ['window','task_id','epoch']]
        source=owners[tasks[task][2]];observer=migration.get((window,task),source)
        expected.append(((window,task,epoch,0,observer),int(row['initial_reads'])))
        if int(row['replayed']):expected.append(((window,task,epoch,1,source),int(row['final_reads'])))
    def records(file,layout):
        with file.open('rb') as stream:
            while True:
                block=stream.read(layout.size)
                if not block:return
                assert len(block)==layout.size,'truncated view census record'
                yield layout.unpack(block)
    values=itertools.groupby(records(path('.observed_reads.bin'),struct.Struct('<QIIIIIIHHHHIIQQ')),key=lambda r:r[:5])
    census=itertools.groupby(records(path('.view_access_coverage.bin'),struct.Struct('<QIIIIIIQQ')),key=lambda r:r[:5])
    vgroup=next(values,None);cgroup=next(census,None)
    summaries=table('.view_access_summary.csv');assert len(summaries)==len(expected)
    checked=resource_calls=cost_calls=0
    for raw,(key,count) in zip(summaries,expected):
        row={k:int(v) for k,v in raw.items()}
        assert tuple(row[k] for k in ['window','task_id','epoch','phase','observer_die'])==key
        assert row['unique_nodes']==count
        if not count:
            assert row['resource_calls']==row['cost_calls']==0
            continue
        assert vgroup is not None and cgroup is not None and vgroup[0]==cgroup[0]==key
        value_nodes=[]
        for record in vgroup[1]:
            assert record[5]==len(value_nodes)
            value_nodes.append(record[6])
        assert len(value_nodes)==count and len(set(value_nodes))==count
        coverage_nodes=[];r_total=c_total=0
        for record in cgroup[1]:
            node,reserved,r_calls,c_calls=record[5:]
            assert reserved==0 and r_calls>0 and c_calls>0
            assert not coverage_nodes or node>coverage_nodes[-1]
            coverage_nodes.append(node);r_total+=r_calls;c_total+=c_calls
        assert coverage_nodes==sorted(value_nodes),'view census differs from journal unique nodes'
        assert (r_total,c_total)==(row['resource_calls'],row['cost_calls']),'view census call totals mismatch'
        checked+=count;resource_calls+=r_total;cost_calls+=c_total
        vgroup=next(values,None);cgroup=next(census,None)
    assert vgroup is None and cgroup is None,'unmatched census or journal group'
    def sha(p):
        value=hashlib.sha256()
        with p.open('rb') as stream:
            for block in iter(lambda:stream.read(1<<20),b''):value.update(block)
        return value.hexdigest()
    return dict(status='explicit_view_api_census_exactly_matches_observed_journal_nodes',proposal_phases=len(expected),unique_node_occurrences=checked,resource_api_calls=resource_calls,cost_api_calls=cost_calls,source_sha256={str(p.resolve()):sha(p) for p in files},scope='SeparatelytrackedexplicitRRStateView.resource/cost API calls versusResourceReader journal;exactsets/order/groups andpernode/globalcounts. Costcountsinclude diagnostic snapshot queries. Composewith authority-value/staleness replay. NotgeneralC++pointermemory instrumentation,independentsearchrerun,physicaltrafficorhardwareproof.',board_result=False,research_complete=False)
