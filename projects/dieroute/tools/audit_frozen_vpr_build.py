"""Audit a completed fresh VPR build's frozen sources and actual compiler dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_record',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    base=args.build_record.resolve()
    assert not args.output.exists()
    manifest=base/'manifest.json'
    state=json.loads(manifest.read_text())
    assert state['status']=='new_source_bound_build_completed_dependency_and_native_compatibility_audits_required'
    sources_path=base/'source_manifest.json'
    assert sha(sources_path)==state['source_manifest_sha256']
    sources=json.loads(sources_path.read_text())
    assert all(sha(base/p)==h for p,h in sources['files_sha256'].items())
    assert all(os.readlink(base/p)==target for p,target in sources['symlinks'].items())
    binary=Path(state['binary'])
    assert sha(binary)==state['binary_sha256']
    assert sha(Path(state['historical_baseline_binary']))==state['historical_baseline_binary_sha256']
    assert all(sha(Path(p))==h for p,h in state['compiler_sha256'].items())
    commands_path=base/'build/compile_commands.json'
    assert sha(commands_path)==state['compile_commands_sha256']
    commands=json.loads(commands_path.read_text())
    dependency_paths=set()
    translation_units=[]
    objects={}
    for row in commands:
        tokens=shlex.split(row['command'])
        directory=Path(row['directory'])
        object_path=(directory/tokens[tokens.index('-o')+1]).resolve()
        if not object_path.exists():
            continue  # compile_commands also lists optional targets never requested.
        dependency=Path(str(object_path)+'.d')
        assert dependency.exists(),object_path
        text=dependency.read_text().replace('\\\n',' ')
        target,body=text.split(':',1)
        deps={(directory/p).resolve() for p in shlex.split(body)}
        source=Path(row['file']).resolve()
        assert source in deps and deps
        assert source.is_relative_to(base/'source_vtr') or source.is_relative_to(base/'build'),source
        assert all(p.exists() and p.is_file() for p in deps)
        # All non-system inputs must be in this new snapshot or its generated build tree.
        unexpected=[p for p in deps if not (p.is_relative_to(base) or p.is_relative_to('/usr') or p.is_relative_to('/lib'))]
        assert not unexpected,unexpected
        dependency_paths.update(deps)
        dependency_paths.add(dependency)
        objects[str(object_path)]=sha(object_path)
        translation_units.append(dict(source=str(source),object=str(object_path),
                                      dependency_file=str(dependency),dependency_count=len(deps)))
    assert len(translation_units)>100, 'Insufficient actual clean-build translation-unit evidence'
    link_path=base/'build/vpr/CMakeFiles/vpr.dir/link.txt'
    link_directory=link_path.parents[2]
    link_inputs={}
    for token in shlex.split(link_path.read_text()):
        if token.startswith('-'):
            continue
        path=(link_directory/token).resolve()
        if path.is_file():
            link_inputs[str(path)]=sha(path)
    assert any(p.endswith('.a') for p in link_inputs)
    runtime=subprocess.check_output(['ldd',str(binary)],text=True)
    runtime_file=args.output.with_suffix('.ldd.txt')
    runtime_file.write_text(runtime)
    runtime_inputs={}
    assert 'not found' not in runtime
    for line in runtime.splitlines():
        for token in line.split():
            if token.startswith('/'):
                path=Path(token).resolve()
                assert path.is_file()
                runtime_inputs[str(path)]=sha(path)
    files=[manifest,sources_path,commands_path,link_path,runtime_file,Path(__file__).resolve(),
           base/'build/CMakeCache.txt',base/'compiler_version.txt',base/'configure.log',base/'build.log']
    report=dict(status='new_frozen_vpr_sources_compiler_dependencies_and_link_inputs_audited',
                binary=str(binary),binary_sha256=sha(binary),translation_units=translation_units,
                compiled_object_sha256=objects,
                dependency_sha256={str(p):sha(p) for p in sorted(dependency_paths)},
                explicit_link_input_sha256=link_inputs,runtime_library_sha256=runtime_inputs,
                frozen_source_files_verified=len(sources['files_sha256']),
                source_sha256={str(p):sha(p) for p in files},
                scope='New clean source-bound VPR build with actual compiler .d inputs and explicit '
                      'link operands; unbuilt optional compile_commands entries excluded. System inputs '
                      'are hashed, not vendored. Not a hermetic or bit-for-bit rebuild, historical binary '
                      'source identity, native numerical compatibility, quality acceptance or board evidence.',
                board_result=False,research_complete=False)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],translation_units=len(translation_units),
                          dependencies=len(dependency_paths))))


if __name__=='__main__':
    main()
