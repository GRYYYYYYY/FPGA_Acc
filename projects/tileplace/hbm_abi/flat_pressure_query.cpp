#include "flat_pressure.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc,char** argv) {
 try {
  if(argc!=2)return 2;
  std::ifstream input(argv[1],std::ios::binary);if(!input)throw std::runtime_error("snapshot unavailable");
  std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(input)),{});
  tileplace_hbm::FlatPressure pressure(bytes);
  tileplace_hbm::Location a{},b{};
  while(std::cin>>a.x>>a.y>>b.x>>b.y) {
   auto h=pressure.path(a,b,true),v=pressure.path(a,b,false);
   std::cout<<h<<' '<<v<<' '<<std::min(h,v)<<'\n';
  }
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
