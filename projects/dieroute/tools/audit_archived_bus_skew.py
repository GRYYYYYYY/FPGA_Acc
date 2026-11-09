"""Audit numeric and NA bus-skew constraints without silently waiving missing paths."""
import hashlib,json,re
from pathlib import Path


def parse(text):
    a=list(re.finditer(r'^1\. Bus Skew Report Summary',text,re.M))[-1].start()
    b=list(re.finditer(r'^2\. Bus Skew Report Per Constraint',text,re.M))[-1].start()
    summary=text[a:b];starts=list(re.finditer(r'^(\d+)\s+(\d+)\s+',summary,re.M))
    details=list(re.finditer(r'^Id:\s+(\d+)\s*$',text[b:],re.M));detail={}
    for i,m in enumerate(details):
        detail[int(m[1])]=text[b+m.start():b+details[i+1].start() if i+1<len(details) else len(text)]
    assert starts and len(starts)==len(detail)
    result=[]
    for i,m in enumerate(starts):
        cid=int(m[1]);block=summary[m.start():starts[i+1].start() if i+1<len(starts) else len(summary)]
        assert cid in detail
        numbers=re.findall(r'^\s+(Slow|Fast)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*$',block,re.M)
        d=detail[cid]
        if numbers:
            assert len(numbers)==1
            corner,requirement,actual,slack=numbers[0];requirement,actual,slack=map(float,[requirement,actual,slack])
            matched=re.findall(r'^Slack \((MET|VIOLATED)\)\s*:\s*(-?[\d.]+)ns',d,re.M)
            assert len(matched)==1 and abs(float(matched[0][1])-slack)<0.0001
            assert abs(requirement-actual-slack)<0.0011
            assert (matched[0][0]=='MET')==(slack>=0)
            result.append(dict(id=cid,position=int(m[2]),corner=corner,requirement_ns=requirement,actual_ns=actual,slack_ns=slack,status=matched[0][0]))
        else:
            na=re.findall(r'^\s+NA\s+([\d.]+)\s+NA\s+NA\s*$',block,re.M);assert len(na)==1
            assert 'No bus skew paths found.' in d and not re.search(r'^Slack ',d,re.M)
            endpoints=re.search(r'^Endpoints:\s+(\d+)\s*$',d,re.M);assert endpoints
            result.append(dict(id=cid,position=int(m[2]),requirement_ns=float(na[0]),status='NA',endpoints=int(endpoints[1]),reason='No bus skew paths found.'))
    assert len({r['id'] for r in result})==len(result) and set(detail)=={r['id'] for r in result}
    return result


def main():
    root=Path(__file__).resolve().parents[1];p=root/'work/archived_sharded_bus_skew_audit_20261015'
    manifest=json.loads((p/'manifest.json').read_text());assert manifest['status']=='bus_skew_report_generated_requires_independent_review' and manifest['returncode']==0 and manifest['checkpoint_unchanged']
    raw=(p/'bus_skew.rpt').read_bytes();assert hashlib.sha256(raw).hexdigest()==manifest['report_sha256'];text=raw.decode();rows=parse(text)
    numeric=[r for r in rows if r['status']!='NA'];missing=[r for r in rows if r['status']=='NA'];assert len(rows)==230 and len(numeric)==229 and len(missing)==1
    assert all(r['status']=='MET' for r in numeric) and missing[0]['id']==163
    # Verify that a false status or missing NA justification cannot be accepted.
    rejected=[]
    for name,bad in [('forged_status',text.replace('Slack (MET)','Slack (VIOLATED)',1)),('missing_NA_reason',text.replace('No bus skew paths found.','',1))]:
        try:parse(bad)
        except AssertionError:rejected.append(name)
        else:raise AssertionError('corrupted bus report accepted '+name)
    protocol=json.loads((p/'protocol.json').read_text());checkpoint=[f for f in protocol['inputs'] if f.endswith('.dcp')];assert len(checkpoint)==1
    files=[p/'protocol.json',p/'manifest.json',p/'bus_skew.rpt',Path(__file__).resolve()]
    result=dict(status='archived_bus_skew_229_numeric_met_one_constraint_NA',constraints=len(rows),numeric_constraints=len(numeric),numeric_violations=sum(r['status']=='VIOLATED' for r in numeric),minimum_numeric_slack_ns=min(r['slack_ns'] for r in numeric),unmeasured_constraints=missing,rows=rows,rejected_report_corruptions=rejected,checkpoint_sha256=protocol['inputs'][checkpoint[0]],source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},scope='Actual read-only old archived DCP bus-skew report;all summary IDs matched per-constraint details.229numericconstraintsMET;oneNA/endpoints1/no paths. NA is not silently waived. Not full timing signoff,finalbitstream correspondence,newcandidate timing orphysical operation.',board_result=False,research_complete=False)
    with (p/'independent_audit.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps({k:result[k] for k in ['status','constraints','numeric_constraints','numeric_violations','minimum_numeric_slack_ns','unmeasured_constraints']}))


if __name__=='__main__':main()
