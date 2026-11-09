#!/usr/bin/env python3
"""Run all four online joint XRT fixtures with source-bound independent audits."""
import argparse,hashlib,json,os,pwd,shlex,shutil,subprocess,sys,time
from pathlib import Path
if not __debug__:raise RuntimeError('verification requires assertions')
ap=argparse.ArgumentParser(description=__doc__)
for name in ('fixture-run','host','link-run','platform-audit','output'):ap.add_argument('--'+name,required=True,type=Path)
args=ap.parse_args();root=Path(__file__).resolve().parents[1];link=args.link_run.resolve();platform_audit=args.platform_audit.resolve();a=json.loads(platform_audit.read_text());assert a['status']=='verified'
out=args.output.resolve();fixture=args.fixture_run.resolve();assert not out.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
xclbin=link/'joint.xclbin';assert sha(xclbin)==a['xclbin_sha256'] and sha(link/'manifest.json')==a['input_manifest_sha256'];assert json.loads((link/'manifest.json').read_text())['status']=='passed'
for name in ('interior_1','interior_3','cross_1','cross_3'):assert (fixture/(name+'_kernel')/'command.json').is_file()
assert args.host.is_file();out.mkdir()
inputs={str(p):sha(p) for p in (xclbin,link/'manifest.json',platform_audit)}
for p in [root/'host/owner_publish_xrt.cpp',root/'host/net_commit_xrt.cpp',root/'host/xrt_device_context.hpp',root/'tools/route_native_parallel.cpp',root/'tools/build_owner_publish_xrt.sh',*sorted((root/'include').glob('*.hpp'))]:
 target=out/'source'/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);inputs[str(p)]=sha(p)
for name in ('audit_native_joint_xrt.py','audit_native_parallel.py','audit_native_net_commit.py','audit_net_commit.py','audit_native_persistent_shadows.py','audit_native_summary_hbm.py','audit_native_owner_publish.py','audit_native_label_transport.py','run_native_case.py'):
 p=root/'tools'/name;shutil.copy2(p,out/'source/tools'/name);inputs[str(p)]=sha(p)
binary=args.host.resolve();shutil.copy2(binary,out/'host');inputs[str(binary)]=sha(binary);inputs[str(out/'host')]=sha(out/'host');assert inputs[str(binary)]==inputs[str(out/'host')]
platform='/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/dev_platform/opt/xilinx/platforms/xilinx_u280_gen3x16_xdma_1_202211_1/xilinx_u280_gen3x16_xdma_1_202211_1.xpfm'
setup='source /inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis/2022.2/settings64.sh && source /inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt/setup.sh >/dev/null && '
config=['emconfigutil','--platform',platform,'--od',str(out),'--nd','1']
with (out/'emconfig.log').open('w') as f:subprocess.run(['bash','-c',setup+shlex.join(config)],cwd=out,stdout=f,stderr=subprocess.STDOUT,check=True)
inputs[str(out/'emconfig.json')]=sha(out/'emconfig.json')
env=dict(os.environ,USER=pwd.getpwuid(os.getuid()).pw_name,XCL_EMULATION_MODE='hw_emu',EMCONFIG_PATH=str(out),DIEROUTE_OWNER_PUBLISH_XCLBIN=str(xclbin),DIEROUTE_NET_COMMIT_XCLBIN=str(xclbin))
env.pop('DIEROUTE_NET_COMMIT_ALLOW_INJECTION',None)
record=dict(schema='dieroute.native_joint_authority_xrt.v1',status='running',started_ns=time.time_ns(),inputs=inputs,emconfig_command=config,mode='hw_emu',runtime_environment={k:env[k] for k in ('USER','XCL_EMULATION_MODE','EMCONFIG_PATH','DIEROUTE_OWNER_PUBLISH_XCLBIN','DIEROUTE_NET_COMMIT_XCLBIN')},explicit_injection_mode=False,board_result=False,cases=[])
def save():
 tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(out/'manifest.json')
producer=Path(__file__).resolve();shutil.copy2(producer,out/'producer.py');inputs[str(producer)]=sha(producer)
sys.path.insert(0,str(out/'source/tools'));from audit_native_joint_xrt import audit_case
for name in ('interior_1','interior_3','cross_1','cross_3'):
 baseline=fixture/(name+'_kernel');case=out/name;case.mkdir();command=json.loads((baseline/'command.json').read_text());command[0]=str(out/'host');command[7]=str(case/'route');(case/'command.json').write_text(json.dumps(command,indent=2)+'\n')
 for folder in command[1:6]:
  for p in Path(folder).rglob('*'):
   if p.is_file():inputs[str(p)]=sha(p)
 for p in (baseline/'route').iterdir():
  if p.is_file():inputs[str(p)]=sha(p)
 invocation=['bash','-c',setup+'exec '+shlex.join(command)];result=dict(name=name,baseline=str(baseline),command=command,invocation=invocation,status='running');record['cases'].append(result)
 try:
  with (case/'run.log').open('w') as f:
   proc=subprocess.Popen(invocation,cwd=case,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True);result['pid']=proc.pid;save();code=proc.wait()
  result['returncode']=code;save();assert code==0,'online XRT router failed'
  evidence,proof=audit_case(case,baseline,command);assert not name.startswith('cross') or evidence['receiver_kernel_calls']>0
  (case/'audit.json').write_text(json.dumps(proof,indent=2)+'\n');result.update(evidence);save()
 except Exception as exc:result.update(status='failed',error=repr(exc));record.update(status='failed',finished_ns=time.time_ns());save();raise
record.update(status='passed',finished_ns=time.time_ns(),inputs_unchanged=all(sha(p)==h for p,h in inputs.items()));save();assert record['inputs_unchanged'];print(json.dumps(dict(status=record['status'],calls={c['name']:{k:c[k] for k in ('net_kernel_calls','publisher_kernel_calls','receiver_kernel_calls')} for c in record['cases']})))
