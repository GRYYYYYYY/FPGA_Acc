"""Snapshot completed packed-format search evidence while commit remains live."""
import hashlib,json,re,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'work/native_dual_potential_XRT_pipeline_20261015'
O=R/'work/native_dual_potential_XRT_search_stage_20261015'

def main():
 O.mkdir(exist_ok=False);refs={}
 def sha(path):
  path=Path(path).resolve();h=hashlib.sha256()
  with path.open('rb') as stream:
   for block in iter(lambda:stream.read(1048576),b''):h.update(block)
  refs[str(path)]=h.hexdigest();return h.hexdigest()
 protocol=json.loads((P/'protocol.json').read_text())
 assert protocol['label_capacity']==protocol['maximum_expansions']==2097152
 binding=json.loads((P/'image_binding.json').read_text())
 assert sha(protocol['image'])==binding['source_sha256'][protocol['image']]
 gold=R/'work/native_policy_identity_ordering_cpu_20261015/identity_higher_g/artifacts'
 artifacts=[]
 for name in ['attachment.raw','goal.raw','metadata.raw','observations.raw','path_nodes.raw','path_pips.raw','result.raw']:
  actual=P/'artifacts'/name;expected=gold/name
  assert sha(actual)==sha(expected),name
  artifacts.append(dict(name=name,bytes=actual.stat().st_size,sha256=refs[str(actual.resolve())]))
 packed=P/'artifacts/potential8.raw';gold8=R/'work/native_potential8_lossless_storage_20261015/potential8.raw'
 storage=json.loads((gold8.parent/'independent_audit.json').read_text())
 assert sha(gold8)==storage['source_sha256'][str(gold8)]
 assert sha(packed)==sha(gold8) and packed.stat().st_size==91975784
 result=struct.unpack('<8Q',(P/'artifacts/result.raw').read_bytes())
 assert result==(0,43,256,258,214,256,257,0)
 snapshot=O/'run_log_snapshot.txt';snapshot.write_bytes((P/'run.log').read_bytes());log=snapshot.read_text()
 assert 'DIAG snapshot_wait_complete' in log
 selected=re.findall(r'STAGE name=potential_format_selected a=(\d+) b=(\d+)',log)
 assert selected==[('2','91975784')]
 assert 'STAGE name=kernel_wait_begin a=3 b=0' in log
 assert 'STAGE name=kernel_wait_return ' not in log
 for path in [snapshot,P/'protocol.json',P/'image_binding.json',gold8.parent/'independent_audit.json',Path(__file__).resolve()]:sha(path)
 audit=dict(status='packed_format2_full_native_XRT_search7gold_and_potential8dump_match',
  result_words=list(result),artifacts=artifacts,potential_format=2,packed_payload_bytes=packed.stat().st_size,
  commit_completed=False,verified_total_upload_bytes=None,source_sha256=refs,board_result=False,
  adopted=False,research_complete=False,
  scope='Completed search evidence at frozen log snapshot. Actual selectedformat2 and92MBpacked dump match storage gold; this is not an independent device-transfer byte counter or full upload accounting. First proposal wait begins; no commit completion, deadlock, physical performance or end-to-end success claim.')
 with (O/'independent_audit.json').open('x') as stream:json.dump(audit,stream,indent=2);stream.write('\n')
 print(json.dumps({k:v for k,v in audit.items() if k not in ['source_sha256','artifacts','scope']}))
if __name__=='__main__':main()
