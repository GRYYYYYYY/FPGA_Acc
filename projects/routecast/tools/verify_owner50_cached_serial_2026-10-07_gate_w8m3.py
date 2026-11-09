"""Verify complete native outcomes while retaining mux32 nonpublication."""
import json
import re
from pathlib import Path
from pre_route_endpoints import placements,sha
from stream_native_route_audit import audit
from native_route_ledger_import import physical_paths

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/owner50_cached_serial_2026-10-07_gate_w8m3'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==len(p['cases'])==1
assert all(sha(f)==h for group in ('sources','binaries') for f,h in p[group].items())
rows=[]
def paths(path):return {n:sorted(v) for n,v in physical_paths(path).items() if v}
for spec,row in zip(p['cases'],r['rows']):
    width=row['width'];index=spec['index'];assert width==spec['width'] and index==row['index']
    if row['status'] in ('ALLOCATION_NOT_SUBMITTED','INCOMPLETE_NOT_SUBMITTED'):
        assert not (out/f'w{width}_m{index}/run.log').exists();rows.append(dict(width=width,index=index,status=row['status']));continue
    assert row['status']=='RELOADED' and row['error'] is None and row['native_exit_code']==0
    native,reload=row['native'],row['reload'];work=out/f'w{width}_m{index}';graph=Path(spec['source'])/'rr_graph.xml'
    assert all(sha(f)==h for f,h in spec['inputs'].items())
    assert all(sha(f)==h for f,h in native['files'].items()) and all(sha(f)==h for f,h in reload['files'].items())
    text=(work/'run.log').read_text();m=re.search(r'same-target gate predicted_cpd_ns=([0-9.]+) reference_cpd_ns=([0-9.]+) selected=(\w+)',text);assert m
    pred,ref=map(float,m.groups()[:2]);j=re.search(r'joint-qor gate predicted_wire=(\d+) reference_wire=(\d+) selected=(\w+) cpd_regression=(\d+) wire_regression=(\d+)',text);assert j
    predicted_wire,reference_wire=map(int,j.groups()[:2]);assert m[3]==j[3]==('reference' if pred>ref or predicted_wire>reference_wire else 'predicted');assert int(j[4])==int(pred>ref) and int(j[5])==int(predicted_wire>reference_wire)
    assert reload['exit_code']==0 and reload['mismatches']==reload['fixups']==0 and reload['cpd_ns']==native['cpd_ns'] and abs(reload['cpd_ns']-(ref if m[3]=='reference' else pred))<=5.1e-5
    assert sha(reload['command'][0])=='a90dc1b3380ebda705e85f176db0cc3d6be1b71ab9ee887db819febc8b62bafc'
    original=(work/'canonical/reload.log').read_text()
    for marker in ('VPR succeeded','RouterOpts.check_route: FULL','Completed routing consistency check successfully.'):assert marker in original
    assert int(re.search(r'Found (\d+) mismatches',original)[1])==int(re.search(r'Fixed (\d+) routing traces',original)[1])==0
    assert paths(work/'candidate_0.route')==paths(work/'predicted.route') and paths(work/'output.route')==paths(work/'canonical/design.route')
    for name in ('candidate_0.route','loaded_reference.route','canonical/design.route'):
        result=audit(graph,work/name);assert result['overflow_units']==0 and len(result['connections'])=={8:466,16:936,32:1929}[width]
    assert paths(work/'canonical/design.route')==paths(work/('loaded_reference.route' if m[3]=='reference' else 'predicted.route'))
    # Independent originalXML channel geometry, unique printed nodes perNET.
    import xml.etree.ElementTree as ET
    from audit_native_route import NET,NODE
    unions={}
    for name in ('candidate_0.route','loaded_reference.route','canonical/design.route'):
        nets={};net=None
        for line in (work/name).read_text().splitlines():
            match=NET.match(line)
            if match:net=int(match[1]);nets[net]=set()
            match=NODE.match(line)
            if match:
                assert net is not None
                if match[2] in ('CHANX','CHANY'):nets[net].add(int(match[1]))
        unions[name]=nets
    needed=set().union(*(nodes for nets in unions.values() for nodes in nets.values()));lengths={}
    for event,node in ET.iterparse(graph,events=('end',)):
        if node.tag=='node':
            nid=int(node.get('id'))
            if nid in needed:
                loc=node.find('loc');kind=node.get('type');assert kind in ('CHANX','CHANY')
                lengths[nid]=(int(loc.get('xhigh'))-int(loc.get('xlow'))+1) if kind=='CHANX' else (int(loc.get('yhigh'))-int(loc.get('ylow'))+1)
            node.clear()
    assert set(lengths)==needed
    totals={name:sum(sum(lengths[n] for n in nodes) for nodes in nets.values()) for name,nets in unions.items()}
    assert totals['candidate_0.route']==predicted_wire and totals['loaded_reference.route']==reference_wire
    assert totals['canonical/design.route']==(reference_wire if m[3]=='reference' else predicted_wire)
    assert int(re.findall(r'Total wirelength:\s*(\d+)',original)[-1])==totals['canonical/design.route']
    assert placements(work/'accepted.place',sha(work/'design.net'))==placements(work/'identity_probe/design.place',sha(work/'identity_probe/design.net'))
    rows.append(dict(width=width,index=index,status=row['status'],selected=m[3],predicted_cpd_ns=pred,reference_cpd_ns=ref,original_cpd_ns=reload['cpd_ns'],predicted_wire=predicted_wire,reference_wire=reference_wire,selected_wire=totals['canonical/design.route'],physical_connections_checked=3*{8:466,16:936,32:1929}[width]))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Native joint CPD/wire choice independently checked; allthree originalXML NETunion wire totals and exact selected paths; three complete candidate/reference/final physical/capacity audits and original FULL/STA zero-fixup proofs. No wholefamily success, timing/generalization/production benefit.'),indent=2)+'\n')
print('verified focused gate, candidate/reference/final physical audits; selection explicit')
