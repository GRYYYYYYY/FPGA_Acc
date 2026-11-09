import argparse,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_native_label_transport import crc64
p=argparse.ArgumentParser();p.add_argument('--checker',required=True);a=p.parse_args()
with tempfile.TemporaryDirectory() as tmp:
 path=Path(tmp)/'input'
 for payload,expected in ((b'',0),(b'123456789',0x6c40df5f0b497347),(bytes(range(256))*8193,None)):
  path.write_bytes(bytes(64)+payload);r=subprocess.run([a.checker,str(path),'64'],check=True,capture_output=True,text=True);assert int(r.stdout,16)==(crc64(payload) if expected is None else expected)
 assert subprocess.run([a.checker,str(path),str(path.stat().st_size+1)],capture_output=True).returncode!=0
print('CRC64: known ECMA vector, empty payload, multi-buffer differential and offset bounds passed')
