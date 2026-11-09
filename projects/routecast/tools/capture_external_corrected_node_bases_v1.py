"""Fresh corrected-native initialization dump, pernode plus legacy indexed metadata."""
import json,hashlib,shutil,subprocess,os,struct
from pathlib import Path
from fractions import Fraction
from array import array
R=Path(__file__).resolve().parents[1];B=R/'build/native_external_seed_delay_handoff_v1_2026-10-19';N=R/'build/native_external_shared_sink_native_v1_2026-10-19';D=R/'build/native_external_corrected_node_bases_v1_2026-10-19';E=R/'experiments/prospective_external_family_corrected_node_bases_v1_2026-10-19';OLD=R/'experiments/prospective_external_family_width_node_bases_v2_2026-10-19/w160'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 proof=read(OLD/'verification.json');assert all(sha(k)==h for k,h in proof['bindings'].items());b=read(N/'receipt.json');assert sha(b['binary'])==b['binary_sha256'];assert all(sha(k)==h for k,h in b['bindings'].items());D.mkdir(exist_ok=False);E.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source');route=D/'source/route.cpp';s=route.read_text();orig=R/'build/native_indexed_cost_dump_v1_2026-10-10/source/route.cpp';t=orig.read_text();start=t.index('    if(const char* path=std::getenv("ROUTECAST_INDEXED_COST_DUMP"))');end=t.index('    if(const char* manifest=',start);code=t[start:end]
 anchor='        if(std::ferror(fp) || std::fclose(fp))';assert code.count(anchor)==1
 extra=r'''
        FILE* nodes=std::fopen("native_nodes.tsv","wx");if(!nodes)throw std::runtime_error("node dump open");
        std::fprintf(nodes,"node\ttype\tindex\tbase\tsaved\tT_quadratic\n");
        for(auto node:rr.nodes()) {
            const auto& data=device_ctx.rr_indexed_data[rr.node_cost_index(node)];
            std::fprintf(nodes,"%zu\t%d\t%zu\t%.9g\t%.9g\t%.9g\n",size_t(node),int(rr.node_type(node)),size_t(rr.node_cost_index(node)),double(data.base_cost),double(data.saved_base_cost),double(data.T_quadratic));
        }
        if(std::fclose(nodes))throw std::runtime_error("node dump close");
'''
 code=code.replace(anchor,extra+anchor);anchor='    const bool retained_input=routecast_retained_pending;';assert s.count(anchor)==1;route.write_text(s.replace(anchor,code+anchor));p=read(B/'protocol.json');compile=[x.replace(str(B),str(D)) for x in p['compile']];link=read(N/'protocol.json')['link'];link=[str(D/'route.o') if x==str(B/'route.o') else str(D/'sequence_vpr') if x==str(N/'sequence_vpr') else x for x in link];bindings={str(OLD/'verification.json'):sha(OLD/'verification.json'),str(N/'receipt.json'):sha(N/'receipt.json'),str(orig):sha(orig),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for f in (D/'source').rglob('*'):
  if f.is_file():bindings[str(f)]=sha(f)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Corrected-native initialization only, route-free exit. Exact legacy metadata plus every raw node base/saved/Tquadratic captured. Not routing or timing acceptance.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 source=read(R/'experiments/prospective_external_family_corrected_native_epoch_v1_2026-10-19/source_manifest.json')['cases'][0];work=E/'work';work.mkdir();cmd=source['command'].copy();cmd[0]=str(D/'sequence_vpr')
 for k,name in [('blif','design.blif'),('net','design.net'),('place','design.place')]:shutil.copyfile(source['inputs'][k],work/name);bindings[source['inputs'][k]]=sha(source['inputs'][k])
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_INDEXED_COST_DUMP']=str(work/'indexed.tsv');(E/'protocol.json').write_text(json.dumps(dict(command=cmd,bindings=bindings,environment_set={'ROUTECAST_INDEXED_COST_DUMP':str(work/'indexed.tsv')}),indent=2)+'\n')
 with (work/'native.log').open('x') as log:subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert not list(work.glob('*.route'));assert (work/'indexed.tsv').read_bytes()==(OLD/'capture/work/indexed.tsv').read_bytes()
 import csv
 expected=array('Q');expected.frombytes((OLD/'node_base.u64').read_bytes());assert len(expected)==129090;count=0
 for row in csv.DictReader((work/'native_nodes.tsv').open(),delimiter='\t'):
  node=int(row['node']);assert node==count;f=struct.unpack('f',struct.pack('f',float(row['base'])))[0];saved=struct.unpack('f',struct.pack('f',float(row['saved'])))[0];assert f==saved and float(row['T_quadratic'])==0;exact=Fraction(f)*10**18;ceil=(exact.numerator+exact.denominator-1)//exact.denominator;assert ceil==expected[node];count+=1
 assert count==len(expected);assert all(sha(k)==h for k,h in bindings.items());files=[D/'protocol.json',D/'sequence_vpr',E/'protocol.json',work/'indexed.tsv',work/'native_nodes.tsv',work/'native.log',OLD/'node_base.u64'];(E/'verification.json').write_text(json.dumps(dict(status='CORRECTED_NATIVE_ALL129090_NODE_BASES_EXACT_LEGACY_INDEXED_METADATA_IDENTICAL',nodes=count,all_pernode_base_saved_equal=True,all_T_quadratic_zero=True,all_lattice_ceil_bases_equal_cached=True,no_route_generated=True,bindings={**bindings,**{str(f):sha(f) for f in files}},scope='Fresh native initialization. All pernode static costs equal existing cache; original grouped fanout proof remains required. No feedback or final-label scoring.'),indent=2)+'\n');print('ALL129090_NODE_BASES_EXACT')
if __name__=='__main__':main()
