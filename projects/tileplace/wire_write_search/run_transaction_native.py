"""Run native Python orchestration with independently checked C++ proposals."""
import argparse,json,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent.parent/"array_transactions"),str(Path(__file__).resolve().parent.parent/"hbm_abi")]
from fast_transaction_adapter import FastTransactionEngine as CheckedCppEngine
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
 hbm=root.parent/'hbm_abi';cpp=root.parent/'cpp_snapshot'
 extra=[Path(__file__),hbm/'native_snapshot_adapter.py',hbm/'search_request.py',hbm/'pack_snapshot.py',hbm/'strict_snapshot_codec.py',hbm/'snapshot_codec.py',root/'transaction_native_server.cpp',root.parent/'array_transactions'/'fast_transaction_adapter.py',*sorted(root.glob('*.hpp')),*sorted((root.parent/'wire_pipeline').glob('*.hpp')),*sorted((root.parent/'wire_checks').glob('*.hpp')),*sorted((root.parent/'wire_candidates').glob('*.hpp')),*sorted((root.parent/'wire_transactions').glob('*.hpp')),*sorted((root.parent/'wire_search').glob('*.hpp')),*sorted((root.parent/'wire_legality').glob('*.hpp')),*sorted((root.parent/'array_costs').glob('*.hpp')),*sorted((root.parent/'wire_costs').glob('*.hpp')),*sorted((root.parent/'wire_pressure').glob('*.hpp')),*sorted((root.parent/'array_transactions').glob('*.hpp')),*sorted(hbm.glob('*.hpp')),*sorted(cpp.glob('*.hpp')),cpp/'persistent_adapter.py',cpp/'compare_proposals.py',binary]
 runner.source_snapshot=lambda paths,parser:original([*paths,*extra],parser)
 sys.argv=[sys.argv[0],*remaining]
 try:
  status=runner.main()
 finally:
  for engine in CheckedCppEngine.instances:engine.close()
 report=Path(remaining[remaining.index('--report')+1])
 receipt={'status':'pass' if status==0 else 'failed','returncode':status,
          'scope':'Strict binary snapshot search with external ABI word-array write-site union and change detection, touched-net discovery, guards, occupancy, shape, roots, macro translation, legality, net/delta costs, Q20 score and external-word full-identity transaction selection with selected-only Python audit and C++ phase statistics; no full Python candidate enumeration; resident layout and feedback mirrored; host owns native closure and feedback parsing',
          'checks':CheckedCppEngine.checks}
 report.with_name('cpp_checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return status
if __name__=='__main__':raise SystemExit(main())
