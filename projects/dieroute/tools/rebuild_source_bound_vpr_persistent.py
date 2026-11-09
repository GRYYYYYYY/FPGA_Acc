"""Fork the verified frozen VPR sources and apply the persistent timing FIFO wrapper around the verified strict timing hook."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('vtr',type=Path)
    parser.add_argument('eigen',type=Path)
    parser.add_argument('historical_case',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--persistent-patch',type=Path,required=True)
    parser.add_argument('--historical-build-cache',type=Path,required=True)
    parser.add_argument('--parent-build',type=Path,required=True)
    args=parser.parse_args()
    vtr,eigen,case,output=[p.resolve() for p in (args.vtr,args.eigen,args.historical_case,args.output)]
    output.mkdir(exist_ok=False)
    state=dict(status='freezing_new_build_sources',pid=os.getpid(),steps=[],
               historical_case=str(case),board_result=False,research_complete=False)

    def save():
        temporary=output/'manifest.json.tmp'
        temporary.write_text(json.dumps(state,indent=2)+'\n')
        temporary.replace(output/'manifest.json')

    def run(label,command,cwd=None):
        step=dict(label=label,command=command,status='running')
        state['steps'].append(step)
        state['status']=label+'_running'
        with (output/(label+'.log')).open('w') as log:
            process=subprocess.Popen(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
            step['pid']=process.pid
            save()
            rc=process.wait()
        step.update(returncode=rc,status='passed' if rc==0 else 'failed')
        save()
        assert rc==0,(label,rc)

    save()
    try:
        parent=args.parent_build.resolve()
        inherited=json.loads((parent/'source_manifest.json').read_text())
        records,links={},{}
        for source,label in [(vtr,'source_vtr'),(eigen,'source_eigen')]:
            target=output/label
            target.mkdir()
            for directory,dirs,files in os.walk(source):
                dirs[:]=[d for d in dirs if not d.startswith(('build','.git','__pycache__'))]
                relative=Path(directory).relative_to(source)
                destination=target/relative
                destination.mkdir(parents=True,exist_ok=True)
                for name in list(dirs)+files:
                    original=Path(directory)/name
                    copied=destination/name
                    if original.is_symlink():
                        text=os.readlink(original)
                        copied.symlink_to(text,target_is_directory=original.is_dir())
                        assert inherited['symlinks'][str(copied.relative_to(output))]==text
                        links[str(copied.relative_to(output))]=text
                        if name in dirs:
                            dirs.remove(name)
                    elif original.is_file():
                        before=sha(original)
                        assert before==inherited['files_sha256'][str(copied.relative_to(output))]
                        shutil.copy2(original,copied)
                        assert sha(copied)==before==sha(original),original
                        records[str(copied.relative_to(output))]=before
        patch=output/'applied_persistent_timing.patch'
        shutil.copy2(args.persistent_patch.resolve(),patch)
        assert sha(patch)==sha(args.persistent_patch.resolve())
        run('apply_persistent_patch',['patch','--batch','--forward','--fuzz=0','--no-backup-if-mismatch','-p1','-i',str(patch)],cwd=output/'source_vtr')
        modified={p:sha(output/p) for p,h in records.items() if sha(output/p)!=h}
        assert set(modified)=={'source_vtr/vpr/src/base/vpr_api.cpp'},modified
        pre_patch={p:records[p] for p in modified}
        records.update(modified)
        state.update(parent_build=str(parent),parent_source_manifest_sha256=sha(parent/'source_manifest.json'),
                     persistent_patch_sha256=sha(patch),pre_patch_source_sha256=pre_patch,
                     post_patch_source_sha256=modified)
        old=json.loads((case/'run.json').read_text())
        baseline=Path(old['sources']['vpr']['path'])
        assert sha(baseline)==old['sources']['vpr']['sha256']
        cache=args.historical_build_cache.resolve()
        shutil.copy2(cache,output/'historical_build_cache.txt')
        compiler=Path('/usr/bin/c++').resolve()
        cc1=Path(subprocess.check_output([str(compiler),'-print-prog-name=cc1plus'],text=True).strip()).resolve()
        version=subprocess.check_output([str(compiler),'--version'],text=True)
        (output/'compiler_version.txt').write_text(version)
        source_manifest=dict(status='copied_sources_and_persistent_timing_patch_verified_before_configuration',files_sha256=records,
                             parent_source_manifest=str(parent/'source_manifest.json'),
                             parent_source_manifest_sha256=sha(parent/'source_manifest.json'),
                             persistent_patch_sha256=sha(patch),pre_patch_source_sha256=pre_patch,post_patch_source_sha256=modified,
                             symlinks=links,excluded_directory_prefixes=['build','.git','__pycache__'],
                             scope='Frozen nonexcluded local source tree and Eigen installation. Symlink targets '
                                   'are recorded, including upstream broken benchmark/tool links. Compiled '
                                   'dependency closure and generated inputs require a separate post-build audit.')
        sources=output/'source_manifest.json'
        sources.write_text(json.dumps(source_manifest,indent=2)+'\n')
        state.update(source_manifest_sha256=sha(sources),frozen_regular_files=len(records),
                     historical_baseline_binary=str(baseline),historical_baseline_binary_sha256=sha(baseline),
                     historical_case_manifest_sha256=sha(case/'run.json'),
                     compiler_sha256={str(p):sha(p) for p in [compiler,cc1]},
                     script_sha256=sha(Path(__file__).resolve()),
                     scope='New clean source-bound build only. Does not establish original baseline as-built '
                           'source identity, numerical equivalence, native quality or any physical performance.')
        save()
        command=['cmake','-S',str(output/'source_vtr'),'-B',str(output/'build'),
                 '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                 '-DCMAKE_PREFIX_PATH='+str(output/'source_eigen'),'-DVPR_ANALYTIC_PLACE=ON',
                 '-DVPR_USE_EZGL=off','-DVPR_USE_SERVER=off','-DVPR_USE_SIGNAL_HANDLER=off',
                 '-DVPR_ENABLE_INTERCHANGE=off','-DVTR_ENABLE_CAPNPROTO=OFF',
                 '-DWITH_ODIN=OFF','-DWITH_BLIFEXPLORER=OFF']
        run('configure',command)
        run('build',['cmake','--build',str(output/'build'),'--target','vpr','-j','2'])
        assert all(sha(output/p)==h for p,h in records.items()),'Frozen source changed during build'
        assert all(os.readlink(output/p)==target for p,target in links.items()),'Source symlink changed'
        assert sha(baseline)==state['historical_baseline_binary_sha256']
        binary=output/'build/vpr/vpr'
        state.update(status='new_source_bound_build_completed_dependency_and_native_compatibility_audits_required',
                     binary=str(binary),binary_sha256=sha(binary),frozen_sources_unchanged=True,
                     compile_commands_sha256=sha(output/'build/compile_commands.json'))
    except BaseException as error:
        state.update(status='failed',error=repr(error))
        raise
    finally:
        save()


if __name__=='__main__':
    main()
