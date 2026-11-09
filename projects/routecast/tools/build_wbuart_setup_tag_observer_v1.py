"""Owned read-only full-node Tatum tag export before/after frozen perturbations."""
import json,hashlib,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R/'build/native_external_delay_components_v1_2026-10-19';O=R/'build/wbuart_setup_tag_observer_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);shutil.copytree(OLD/'source',O/'source');p=O/'source/route.cpp';s=p.read_text();s='#include "tatum/analyzers/SetupTimingAnalyzer.hpp"\n#include "tatum/tags/TimingTag.hpp"\n#include <cstring>\n'+s
 anchor='        dump_components("components_before.tsv");';assert s.count(anchor)==1
 code=r'''
        auto dump_setup_tags=[&](const char* path) {
            FILE* f=std::fopen(path,"wx");if(!f)throw std::runtime_error("tag export open");
            auto analyzer=timing_info->setup_analyzer();
            auto id=[](auto v)->long long{return v?static_cast<long long>(size_t(v)):-1;};
            std::fprintf(f,"node\tkind\tlaunch\tcapture\tvalid\tseconds\tbits\tconstant\n");
            for(auto node:g_vpr_ctx.timing().graph->nodes()) {
                for(auto type:{tatum::TagType::DATA_ARRIVAL,tatum::TagType::DATA_REQUIRED,tatum::TagType::CLOCK_LAUNCH,tatum::TagType::CLOCK_CAPTURE}) {
                    const char* kind=type==tatum::TagType::DATA_ARRIVAL?"A":type==tatum::TagType::DATA_REQUIRED?"R":type==tatum::TagType::CLOCK_LAUNCH?"CL":"CC";
                    for(const auto& tag:analyzer->setup_tags(node,type)) {
                        float v=tag.time();unsigned int word;std::memcpy(&word,&v,4);
                        std::fprintf(f,"%zu\t%s\t%lld\t%lld\t%d\t%.9g\t%08x\t%d\n",size_t(node),kind,id(tag.launch_clock_domain()),id(tag.capture_clock_domain()),int(tag.time().valid()),double(v),word,int(tatum::is_const_gen_tag(tag)));
                    }
                }
                for(const auto& tag:analyzer->setup_slacks(node)) {
                    float v=tag.time();unsigned int word;std::memcpy(&word,&v,4);
                    std::fprintf(f,"%zu\tS\t%lld\t%lld\t%d\t%.9g\t%08x\t%d\n",size_t(node),id(tag.launch_clock_domain()),id(tag.capture_clock_domain()),int(tag.time().valid()),double(v),word,int(tatum::is_const_gen_tag(tag)));
                }
            }
            if(std::fclose(f))throw std::runtime_error("tag export close");
        };
        dump_setup_tags("setup_tags_before.tsv");
'''
 s=s.replace(anchor,code+anchor);anchor2='        dump_components("components_after.tsv");';assert s.count(anchor2)==1;s=s.replace(anchor2,anchor2+'\n        dump_setup_tags("setup_tags_after.tsv");');p.write_text(s)
 old=json.loads((OLD/'protocol.json').read_text());compile=[x.replace(str(OLD),str(O)) for x in old['compile']];link=[x.replace(str(OLD),str(O)) for x in old['link']];bindings={str(Path(__file__)):sha(Path(__file__)),str(OLD/'protocol.json'):sha(OLD/'protocol.json')}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(Path(x))
 for f in (O/'source').rglob('*'):
  if f.is_file():bindings[str(f)]=sha(f)
 (O/'protocol.json').write_text(json.dumps({'compile':compile,'link':link,'bindings':bindings,'scope':'Read-only public setup analyzer tag export at all nodes, no routing search. Extra exports only; source capture outputs must reproduce prior component/graph/atom/constraints snapshots.'},indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (O/(name+'.log')).open('x') as f:rc=subprocess.call(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
  assert rc==0
 for n,h in bindings.items():assert sha(Path(n))==h
 (O/'receipt.json').write_text(json.dumps({'exit_status':0,'binary':str(O/'sequence_vpr'),'binary_sha256':sha(O/'sequence_vpr'),'bindings':{str(p):sha(p) for p in [O/'protocol.json',O/'compile.log',O/'link.log']}},indent=2)+'\n');print('SETUP_TAG_OBSERVER_BUILD_PASS',flush=True)
if __name__=='__main__':main()
