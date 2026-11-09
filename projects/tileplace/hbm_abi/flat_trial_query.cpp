#include "flat_trial_cost.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc,char** argv) {
 try {
  if(argc!=2)return 2;
  std::ifstream input(argv[1],std::ios::binary);if(!input)throw std::runtime_error("snapshot missing");
  std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(input)),{});
  tileplace_hbm::FlatTrialCosts engine(bytes);unsigned queries;std::cin>>queries;
  while(queries--) {
   unsigned n,m;std::cin>>n>>m;std::set<std::uint32_t> touched;std::map<std::uint32_t,tileplace_hbm::Location> changes;
   while(n--) {unsigned id;std::cin>>id;touched.insert(id);}
   while(m--) {unsigned id;tileplace_hbm::Location p;std::cin>>id>>p.x>>p.y>>p.subtile>>p.layer;changes[id]=p;}
   auto result=engine.cost_pair(touched,changes);
   for(auto v:result.first)std::cout<<v<<' ';
   for(auto v:result.second)std::cout<<v<<' ';
   std::cout<<'\n';
  }
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
