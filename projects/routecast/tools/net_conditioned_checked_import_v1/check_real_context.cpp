#include "checked_claim_import.h"
#include <fstream>
#include <iostream>
#include <set>
using namespace routecast_import_v1;
int main(int argc,char** argv) {
 try {
  if(argc!=3)throw FrameError("usage context claims");
  std::ifstream f(argv[1]);Context c;size_t nets,entries;f>>c.graph_sha256>>c.node_count>>c.epoch>>nets>>entries;
  if(!f||nets>1000000||entries>c.node_count)throw FrameError("context header");
  c.net_names.resize(nets);c.ignored.resize(nets);std::set<uint32_t> unit;
  for(size_t i=0;i<nets;++i) {
   size_t id;int ignored;std::string hex;f>>id>>ignored>>hex;
   if(!f||id!=i||(ignored!=0&&ignored!=1)||hex.size()%2)throw FrameError("context NET");
   std::string name;
   for(size_t j=0;j<hex.size();j+=2) {auto digit=[](char x)->unsigned{if(x>='0'&&x<='9')return x-'0';if(x>='a'&&x<='f')return x-'a'+10;throw FrameError("hex");};name+=char(digit(hex[j])*16+digit(hex[j+1]));}
   c.net_names[i]=name;c.ignored[i]=ignored;
  }
  for(size_t i=0;i<entries;++i) {uint32_t n,b;int is_unit;f>>n>>b>>is_unit;if(!f||!c.expected_hint_bits.emplace(n,b).second)throw FrameError("context hints");if(is_unit==1)unit.insert(n);}
  std::string extra;if(f>>extra)throw FrameError("context trailing");
  c.is_unit_channel=[&](uint32_t n){return unit.count(n)>0;};
  std::ifstream input(argv[2]);auto claims=read(input,c);
  // Emit every accepted record for independent exact comparison, not just a count.
  for(auto x:claims)std::cout<<x.node<<' '<<x.net<<' '<<x.hint_bits<<'\n';
  return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
