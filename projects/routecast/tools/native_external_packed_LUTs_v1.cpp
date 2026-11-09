#include "vpr_api.h"
#include "atom_netlist_utils.h"
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
int main(int argc,char** argv){
 try{
  if(argc<4)throw std::runtime_error("output architecture circuit required");
  std::vector<const char*> args{argv[0]};for(int i=2;i<argc;++i)args.push_back(argv[i]);
  t_options options;t_vpr_setup setup;t_arch arch;
  vpr_init(int(args.size()),args.data(),&options,&setup,&arch);
  vpr_load_packing(setup,arch); // Direct load only; no pack/place/route flow invocation.
  const auto& atom=g_vpr_ctx.atom();std::ofstream out(argv[1]);if(!out)throw std::runtime_error("output open");std::size_t count=0;
  for(auto blk:atom.nlist.blocks()){
   if(atom.nlist.block_model(blk)->name!=std::string(".names"))continue;
   const auto* pb=atom.lookup.atom_pb(blk);if(!pb)throw std::runtime_error("unmapped LUT");auto* gn=pb->pb_graph_node;if(gn->num_input_ports!=1)throw std::runtime_error("LUT ports");int w=gn->num_input_pins[0];std::vector<int> permutation(w,-1);std::vector<std::string> signals(w,"open");
   const t_pb* top=pb;while(top->parent_pb)top=top->parent_pb;
   auto ports=atom.nlist.block_input_ports(blk);if(ports.size()!=1)throw std::runtime_error("logical port");auto port=*ports.begin();
   for(int i=0;i<w;++i){const auto* pin=&gn->input_pins[0][i];int idx=pin->pin_count_in_cluster;auto found=top->pb_route.find(idx);if(found==top->pb_route.end()||!found->second.atom_net_id)continue;
    auto logical=pb->atom_pin_bit_index(pin);auto net=atom.nlist.port_net(port,logical);if(net!=found->second.atom_net_id)throw std::runtime_error("route/logical mismatch");int j=int(logical);if(j<0||j>=w||permutation[j]!=-1)throw std::runtime_error("logical index");permutation[j]=i;signals[i]=atom.nlist.net_name(net);
   }
   std::set<int> used(permutation.begin(),permutation.end());int next=0;for(auto& v:permutation)if(v==-1){while(used.count(next))++next;v=next;used.insert(next);}
   auto table=atom.nlist.block_truth_table(blk);auto mask=truth_table_to_lut_mask(permute_truth_table(table,w,permutation),w);
   out<<atom.nlist.block_name(blk)<<'\t'<<w<<'\t';for(int i=0;i<w;++i){if(i)out<<',';out<<signals[i];}out<<'\t';for(auto v:mask){if(v!=vtr::LogicValue::FALSE&&v!=vtr::LogicValue::TRUE)throw std::runtime_error("undefined mask");out<<(v==vtr::LogicValue::TRUE?'1':'0');}out<<'\n';++count;
  }
  if(count!=6483||!out)throw std::runtime_error("LUT coverage/output");std::cout<<"NATIVE_PACKED_LUTS_EXPORTED "<<count<<'\n';
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
 return 0;
}
