"""Execute the preregistered complete cold label after audited model completion."""
import json
import argparse
import datetime
import gc
import os
import resource
import shutil
import subprocess
import time
from pathlib import Path
from pre_route_endpoints import sha

R = Path(__file__).resolve().parents[1]

def reclaim_verified_cache(paths):
    """Advise away clean RC data cache, excluding files used by live processes."""
    candidates = {str(Path(p).resolve()) for p in paths
                  if Path(p).resolve().is_relative_to(R)
                  and Path(p).is_file() and Path(p).stat().st_size >= 2**20}
    busy = set()
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            for line in (proc / 'maps').read_text().splitlines():
                fields = line.split(None, 5)
                if len(fields) == 6:
                    busy.add(fields[5].removesuffix(' (deleted)'))
            for fd in (proc / 'fd').iterdir():
                try:
                    busy.add(os.readlink(fd).removesuffix(' (deleted)'))
                except FileNotFoundError:
                    pass
        except FileNotFoundError:
            continue
        except PermissionError as error:
            raise RuntimeError('Cannot establish live-file exclusions') from error
    before = int(Path('/sys/fs/cgroup/memory.current').read_text())
    advised = []
    for filename in sorted(candidates - busy):
        fd = os.open(filename, os.O_RDONLY)
        try:
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
            advised.append(dict(path=filename, file_bytes=os.fstat(fd).st_size))
        finally:
            os.close(fd)
    after = int(Path('/sys/fs/cgroup/memory.current').read_text())
    return dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                cgroup_before_bytes=before, cgroup_after_bytes=after,
                advised=advised, skipped_busy=sorted(candidates & busy),
                scope='POSIX_FADV_DONTNEED for verified RC data only. File bytes are not freed bytes; shared cgroup measurements include concurrent activity. No file deletion or process termination.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reclaim-verified-cache', action='store_true',
                        help='Return clean RC data cache after integrity checks')
    args = parser.parse_args()
    prereg = R / 'experiments/titan23_neuron_native_label_prereg_v2_2026-10-13/protocol.json'
    policy = json.loads(prereg.read_text())
    pipeline = R / 'experiments/titan23_neuron_compact_wide_retained_pipeline_v3_2026-10-13'
    terminal = json.loads((pipeline / 'pipeline_terminal.json').read_text())
    assert terminal['exit_status'] == 0 and terminal['all_stages_completed']
    for stage in ('model','initial_audit','sketch_audit','event_audit'):
        assert json.loads((pipeline / (stage+'_terminal.json')).read_text())['exit_status'] == 0
    bindings = dict(policy['bindings'])
    for name in ('initial_physical_verification.json', 'sketch_physical_verification.json', 'verification.json'):
        proof = json.loads((pipeline / 'model' / name).read_text())
        assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
        assert proof['completed'] == policy['original_connections']
        for path, expected in proof['bindings'].items():
            assert path not in bindings or bindings[path] == expected, path
            bindings[path] = expected
        bindings[str(pipeline / 'model' / name)] = sha(pipeline / 'model' / name)
    receipt = json.loads((pipeline / 'model/receipt.json').read_text())
    for group in (receipt['bindings'],receipt['files']):
        for path, expected in group.items():
            assert path not in bindings or bindings[path] == expected, path
            bindings[path] = expected
    del receipt, proof
    gc.collect()
    for p, expected in bindings.items():
        assert sha(p) == expected, p
    cache_report = None
    if args.reclaim_verified_cache:
        cache_report = reclaim_verified_cache([*bindings, pipeline/'model/receipt.json'])
        (pipeline/'native_cache_reclaim_latest.json').write_text(json.dumps(cache_report,indent=2)+'\n')
        print('RC CACHE RECLAIM', json.dumps({k:v for k,v in cache_report.items() if k not in ('advised','skipped_busy')}), flush=True)
    limit = 24 * 2**30
    margin = 8 * 2**30
    maximum = int(Path('/sys/fs/cgroup/memory.max').read_text())
    current = int(Path('/sys/fs/cgroup/memory.current').read_text())
    if maximum - current < limit + margin:
        report = dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      shared_memory_max_bytes=maximum, shared_memory_current_bytes=current,
                      required_free_bytes=limit+margin, native_launched=False,
                      bindings_verified=True, prereg_sha256=sha(prereg), driver_sha256=sha(__file__))
        (pipeline / 'native_resource_denial_latest.json').write_text(json.dumps(report,indent=2)+'\n')
        raise RuntimeError('Shared memory admission unavailable; native not launched')
    out = R / 'experiments/titan23_neuron_native_cold_label_v1_2026-10-14'
    out.mkdir(exist_ok=False)
    if cache_report is not None:
        (out/'cache_reclaim.json').write_text(json.dumps(cache_report,indent=2)+'\n')
    source = Path(policy['source_directory'])
    for name in policy['local_copies']:
        shutil.copyfile(source / name, out / name)
        assert sha(out / name) == bindings[str(source / name)]
    copied_bindings = {str(out / name):sha(out / name) for name in policy['local_copies']}
    (out / 'input_bindings.json').write_text(json.dumps(dict(original=bindings,copies=copied_bindings),indent=2)+'\n')
    env = {k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
    (out / 'launch.json').write_text(json.dumps(dict(prereg_sha256=sha(prereg),driver_sha256=sha(__file__),command=policy['native_command'],child_address_space_limit_bytes=limit,shared_memory_max_bytes=maximum,shared_memory_current_bytes=current,margin_bytes=margin,no_elapsed_timeout=True,label_accepted=False),indent=2)+'\n')
    def bounded():
        resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
    start = time.perf_counter()
    peak = 0
    with (out/'native.log').open('x') as log, (out/'memory.jsonl').open('x') as memory:
        child = subprocess.Popen(policy['native_command'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=bounded)
        (out/'process.json').write_text(json.dumps(dict(pid=child.pid,args=child.args))+'\n')
        print('NATIVE START',child.pid,flush=True)
        while child.poll() is None:
            try:
                lines = Path(f'/proc/{child.pid}/status').read_text().splitlines()
                sample = {k:int(v.split()[0]) for line in lines if ':' in line for k,v in [line.split(':',1)] if k in ('VmRSS','VmHWM','VmSize')}
                peak = max(peak,sample.get('VmHWM',0))
                memory.write(json.dumps(dict(seconds=time.perf_counter()-start,**sample))+'\n');memory.flush()
            except FileNotFoundError:
                pass
            time.sleep(5)
    (out/'terminal.json').write_text(json.dumps(dict(exit_status=child.returncode,seconds=time.perf_counter()-start,sampled_peak_rss_kib=peak,label_accepted=False,independent_physical_and_canonical_audits_pending=True),indent=2)+'\n')
    mismatches = []
    for path, expected in {**bindings,**copied_bindings}.items():
        if not Path(path).exists() or sha(path) != expected:
            mismatches.append(path)
    (out/'input_postcheck.json').write_text(json.dumps(dict(all_inputs_unchanged=not mismatches,mismatches=mismatches,label_accepted=False),indent=2)+'\n')
    print('NATIVE END',child.returncode,flush=True)

if __name__ == '__main__':
    main()
