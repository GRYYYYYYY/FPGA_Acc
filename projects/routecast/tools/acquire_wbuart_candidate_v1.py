"""Acquire authenticated RTL; only hierarchy checking, no route outcomes."""
import hashlib,json,subprocess,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[1]
O=R/'experiments/wbuart_source_candidate_v1_2026-10-20'
def fetch(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'RouteCast-provenance'}),timeout=40) as f:return f.read()
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 inventory=R/'experiments/next_family_candidate_inventory_v1_2026-10-20/verification.json'
 assert json.loads(inventory.read_text())['status']=='BOUNDED_FILENAME_INVENTORY_AND_SELECTION_ORDER_FROZEN'
 O.mkdir(exist_ok=False)
 api='https://api.github.com/repos/ZipCPU/wbuart32'
 c=fetch(api+'/commits/master'); commit=json.loads(c);rev=commit['sha'];save(O/'commit.json',c)
 b=fetch(api+'/git/trees/'+rev+'?recursive=1');tree=json.loads(b);assert not tree['truncated'];assert tree['sha']==commit['commit']['tree']['sha'];save(O/'tree.json',b)
 entries=[e for e in tree['tree'] if e['type']=='blob' and (e['path'] in ['LICENSE','README.md','wbuart32.core'] or (e['path'].startswith('rtl/') and e['path'].endswith(('.v','.vh','.sv'))))]
 protocol={'repository':'https://github.com/ZipCPU/wbuart32','commit':rev,'top':'wbuart','files':[e['path'] for e in entries],'selection_protocol_sha256':sha(inventory.parent/'protocol.json'),'inventory_sha256':sha(inventory),'scope':'Unmodified RTL hierarchy only. GPL source retained separately. No target labels or performance selection. Strict unseen unproven.'}
 save(O/'protocol.json',(json.dumps(protocol,indent=2)+'\n').encode())
 assets=[]
 for e in entries:
  b=fetch('https://raw.githubusercontent.com/ZipCPU/wbuart32/'+rev+'/'+e['path']);assert len(b)==e['size'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==e['sha']
  p=O/'upstream'/e['path'];save(p,b);assets.append({'path':e['path'],'sha256':sha(p),'git_blob':e['sha']})
 rtl=sorted((O/'upstream/rtl').glob('*.v'))
 script='read_verilog -I'+str(O/'upstream/rtl')+' '+' '.join(str(p) for p in rtl)+'\nhierarchy -check -top wbuart\nstat\n'
 save(O/'hierarchy.ys',script.encode())
 yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys'
 with (O/'hierarchy.log').open('x') as log: rc=subprocess.call([str(yosys),'-Q','-T','-s',str(O/'hierarchy.ys')],cwd=O,stdout=log,stderr=subprocess.STDOUT)
 result={'status':'PINNED_SOURCE_HIERARCHY_PASS' if rc==0 else 'PINNED_SOURCE_HIERARCHY_FAILED','commit':rev,'assets':assets,'hierarchy_exit_status':rc,'strict_unseen_families_certified':0,'new_target_labels_read':False,'synthesis_placement_routing_run':False,'bindings':{'tool':sha(Path(__file__)),'protocol':sha(O/'protocol.json'),'hierarchy_log':sha(O/'hierarchy.log'),'yosys':sha(yosys)}}
 save(O/'verification.json',(json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:result[k] for k in ['status','commit','hierarchy_exit_status']}))
if __name__=='__main__':main()
