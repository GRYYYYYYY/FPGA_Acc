"""Run native Python orchestration with independently checked C++ proposals."""
import argparse,json,sys
from pathlib import Path
from native_snapshot_adapter import NativeSnapshotEngine as CheckedCppEngine
import run_tileplace_v2 as runner

def main():
 p=argparse.ArgumentParser(add_help=False);p.add_argument('--cpp-binary',type=Path,required=True)
 args,remaining=p.parse_known_args()
 binary=args.cpp_binary.resolve()
 if not binary.is_file():raise RuntimeError('C++ binary missing')
 CheckedCppEngine.binary=binary;CheckedCppEngine.checks=[]
 runner.TilePlaceV2Engine=CheckedCppEngine
 original=runner.source_snapshot
 root=Path(__file__).resolve().parent
 extra=[Path(__file__),root/'native_snapshot_adapter.py',root/'search_request.py',root/'pack_snapshot.py',root/'strict_snapshot_codec.py',root/'snapshot_codec.py',root/'array_shape_native_server.cpp',*sorted(root.glob('*.hpp')),*sorted((root.parent/'cpp_snapshot').glob('*.hpp')),root.parent/'cpp_snapshot/persistent_adapter.py',root.parent/'cpp_snapshot/compare_proposals.py',binary]
 runner.source_snapshot=lambda paths,parser:original([*paths,*extra],parser)
 sys.argv=[sys.argv[0],*remaining]
 try:
  status=runner.main()
 finally:
  for engine in CheckedCppEngine.instances:engine.close()
 report=Path(remaining[remaining.index('--report')+1])
 receipt={'status':'pass' if status==0 else 'failed','returncode':status,
          'scope':'Strict binary snapshot search with array roots, legality, macro translation, guards, occupancy and shape checked against Python candidates; resident layout and feedback mirrored; host owns native closure and feedback parsing',
          'checks':CheckedCppEngine.checks}
 report.with_name('cpp_checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return status
if __name__=='__main__':raise SystemExit(main())
