"""Archive a stable report snapshot; do not equate it with terminal signoff."""
import argparse
import hashlib
import json
from pathlib import Path
import re

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('report',type=Path);p.add_argument('producer',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();source=a.report.resolve();producer_path=a.producer.resolve();out=a.output.resolve()
    out.mkdir(exist_ok=False);data=source.read_bytes();digest=hashlib.sha256(data).hexdigest();content=data.decode()
    assert 'Device            : xcu280-' in content and 'report_timing_summary' in content
    snapshot=out/'timing_summary_snapshot.rpt';snapshot.write_bytes(data)
    producer=json.loads(producer_path.read_text());pid=producer['pid'];proc=Path('/proc',str(pid),'stat')
    producer_live=proc.exists();identity=proc.read_text().split(')')[-1].split()[19] if producer_live else None
    paths=[]
    pattern=r'\nSlack \((MET|VIOLATED)\)\s*:\s*([-\d.]+)ns[^\n]*\n(.*?)(?=\nSlack \(|\Z)'
    for match in re.finditer(pattern,content,re.S):
        if match[1]!='VIOLATED':continue
        block=match[3]
        if not re.search(r'Path Type:\s+Setup',block):continue
        def field(label):
            result=re.search(r'^\s*'+label+r':\s+(.+)$',block,re.M)
            assert result,label
            return result[1].strip()
        start,end=field('Source'),field('Destination')
        delay=re.search(r'Data Path Delay:\s+([\d.]+)ns\s+\(logic ([\d.]+)ns.*?route ([\d.]+)ns',block)
        assert delay
        paths.append(dict(slack_ns=float(match[2]),source=start,destination=end,
            group=field('Path Group'),requirement_ns=float(field('Requirement').split('ns')[0]),
            data_delay_ns=float(delay[1]),logic_delay_ns=float(delay[2]),route_delay_ns=float(delay[3]),
            route_fraction=float(delay[3])/float(delay[1]),logic_levels=int(field('Logic Levels').split()[0])))
    assert paths,'Expected actual violated setup paths in this diagnostic'
    paths.sort(key=lambda row:row['slack_ns'])
    counts={}
    for key in ('no_clock','unconstrained_internal_endpoints','no_input_delay','no_output_delay'):
        match=re.search(r'checking '+key+r' \((\d+)\)',content);assert match
        counts[key]=int(match[1])
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,'Source report changed during snapshot'
    report=dict(status='stable_routed_timing_report_snapshot_profiled',source_report=str(source),
        source_report_sha256=digest,snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        producer_manifest=str(producer_path),producer_status_at_capture=producer['status'],
        producer_pid=pid,producer_live_at_capture=producer_live,producer_start_ticks=identity,
        displayed_violated_setup_paths=paths,constraint_counts=counts,
        profiler_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Read-only stable text snapshot during or after a hardware build. Displayed worst paths only, not a complete failure distribution. No terminal timing/resource/constraint signoff, board execution, achievable frequency or speedup claim.',
        board_result=False,research_complete=False)
    (out/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],displayed_paths=len(paths),worst=paths[0],producer_live=producer_live)))
