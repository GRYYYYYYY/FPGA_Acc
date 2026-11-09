"""Exact clone of source constraint object; change only one setup target, no I/O reset."""
import pathlib,json,struct,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];O=R/'build/native_reference_setup_export_v1_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);base=R/'build/native_prior_setup_slack_export_v2_2026-10-19';plan=json.loads((base/'protocol.json').read_text());prior=R/'experiments/mmc_prior_setup_slack_export_v1_2026-10-19';proof=prior/'independent_verification_v1.json';v=json.loads(proof.read_text());mapped=prior/'model_connection_setup_slacks.json';assert sha(mapped)==v['bindings'][str(mapped)];rows=json.loads(mapped.read_text());minimum=min(struct.unpack('<f',struct.pack('<I',x['setup_slack_float32_bits']))[0] for x in rows);reference_bits=struct.unpack('<I',struct.pack('<f',-minimum))[0];src=O/'source';src.mkdir();h=(base/'source/routecast_export.h').read_text()
 helper=r'''
#include "tatum/TimingConstraints.hpp"
#include <algorithm>
static std::string routecast_constraint_dump(const tatum::TimingConstraints& c){
 std::ostringstream out;
 for(auto d:c.clock_domains())out<<"D\t"<<size_t(d)<<"\t"<<std::quoted(c.clock_domain_name(d))<<"\t"<<size_t(c.clock_domain_source_node(d))<<"\t"<<c.is_virtual_clock(d)<<"\n";
 for(auto kv:c.setup_constraints())out<<"S\t"<<size_t(kv.first.domain_pair.src_domain_id)<<"\t"<<size_t(kv.first.domain_pair.sink_domain_id)<<"\t"<<size_t(kv.first.capture_node)<<"\t"<<routecast_float_bits(float(kv.second))<<"\n";
 for(auto kv:c.hold_constraints())out<<"H\t"<<size_t(kv.first.domain_pair.src_domain_id)<<"\t"<<size_t(kv.first.domain_pair.sink_domain_id)<<"\t"<<size_t(kv.first.capture_node)<<"\t"<<routecast_float_bits(float(kv.second))<<"\n";
 for(auto type:{tatum::DelayType::MAX,tatum::DelayType::MIN}){
  for(auto kv:c.input_constraints(type))out<<"I\t"<<int(type)<<"\t"<<size_t(kv.first)<<"\t"<<size_t(kv.second.domain)<<"\t"<<routecast_float_bits(float(kv.second.constraint))<<"\n";
  for(auto kv:c.output_constraints(type))out<<"O\t"<<int(type)<<"\t"<<size_t(kv.first)<<"\t"<<size_t(kv.second.domain)<<"\t"<<routecast_float_bits(float(kv.second.constraint))<<"\n";
 }
 for(auto kv:c.setup_clock_uncertainties())out<<"US\t"<<size_t(kv.first.src_domain_id)<<"\t"<<size_t(kv.first.sink_domain_id)<<"\t"<<routecast_float_bits(float(kv.second))<<"\n";
 for(auto kv:c.hold_clock_uncertainties())out<<"UH\t"<<size_t(kv.first.src_domain_id)<<"\t"<<size_t(kv.first.sink_domain_id)<<"\t"<<routecast_float_bits(float(kv.second))<<"\n";
 for(auto type:{tatum::ArrivalType::EARLY,tatum::ArrivalType::LATE})for(auto kv:c.source_latencies(type))out<<"L\t"<<int(type)<<"\t"<<size_t(kv.first)<<"\t"<<routecast_float_bits(float(kv.second))<<"\n";
 std::vector<size_t> constants;for(auto node:c.constant_generators())constants.push_back(size_t(node));std::sort(constants.begin(),constants.end());for(auto node:constants)out<<"C\t"<<node<<"\n";
 return out.str();
}
static void routecast_reference_constraint(){
 auto& ctx=g_vpr_ctx.mutable_timing();const auto& original=*ctx.constraints;
 size_t clocks=0;for(auto d:original.clock_domains()){(void)d;clocks++;}
 auto domain=original.find_clock_domain("clk_i");
 if(clocks!=1||!domain||original.is_virtual_clock(domain)||float(original.setup_constraint(domain,domain))!=0)throw std::runtime_error("reference requires exact original one-clock zero-setup context");
 size_t setups=0;for(auto kv:original.setup_constraints()){(void)kv;setups++;}if(setups!=1)throw std::runtime_error("unexpected setup overrides");
 auto before=routecast_constraint_dump(original);std::ofstream("original_constraints.tsv")<<before;
 auto clone=std::make_shared<tatum::TimingConstraints>(original);
 uint32_t b=REFERENCE_BITS;float target;std::memcpy(&target,&b,4);clone->set_setup_constraint(domain,domain,tatum::Time(target));
 auto after=routecast_constraint_dump(*clone);std::ofstream("reference_constraints.tsv")<<after;
 auto without_setup=[](const std::string& text){std::istringstream in(text);std::string line,result;while(std::getline(in,line))if(line.rfind("S\t",0)!=0)result+=line+"\n";return result;};
 if(without_setup(before)!=without_setup(after))throw std::runtime_error("non-setup constraints changed");
 ctx.constraints=clone;
}
'''.replace('REFERENCE_BITS',str(reference_bits)+'u')
 # Helper functions depend on the float-bit function declared in base header.
 hp=src/'routecast_export.h';hp.write_text(h+'\n'+helper);mainp=src/'main.cpp';maintext=(base/'source/main.cpp').read_text();needle='                    routecast_export(vpr_setup);';assert maintext.count(needle)==1;mainp.write_text(maintext.replace(needle,'                    routecast_reference_constraint();\n'+needle));compile=plan['compile'].copy();compile[compile.index('-c')+1]=str(mainp);compile[compile.index('-o')+1]=str(O/'main.o');compile=[('-I'+str(src)) if x=='-I'+str(base/'source') else x for x in compile];link=[str(O/'main.o') if x==str(base/'main.o') else str(O/'reference_setup_export') if x==str(base/'routecast_prior_slack_export') else x for x in plan['link']];bindings={str(p):sha(p) for p in [proof,mapped,base/'protocol.json',mainp,hp,pathlib.Path(__file__).resolve()]}
 for p,hv in plan['bindings'].items():assert sha(pathlib.Path(p))==hv;bindings[p]=hv
 (O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,compile=compile,link=link,reference_float32_bits=reference_bits,reference_seconds=-minimum,policy='Reference QoR target only, copied native TimingConstraints, exact sole default setup entry0 replaced by prior worst setup-slack magnitude; every domain/I/O/hold/uncertainty/latency/constant entry byte-audited. Not user timing deadline or budget policy.'),indent=2)+'\n')
 for label,cmd in [('compile',compile),('link',link)]:
  print('BUILD',label,flush=True)
  with (O/(label+'.log')).open('x') as out:subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,check=True)
 for p,hv in bindings.items():assert sha(pathlib.Path(p))==hv
 (O/'receipt.json').write_text(json.dumps(dict(status='PRIVATE_NATIVE_REFERENCE_SETUP_EXPORT_BUILT',binary=str(O/'reference_setup_export'),binary_sha256=sha(O/'reference_setup_export'),bindings=bindings,reference_float32_bits=reference_bits,reference_seconds=-minimum),indent=2)+'\n');print('REFERENCE_EXPORT_BUILT',reference_bits,flush=True)
if __name__=='__main__':main()
