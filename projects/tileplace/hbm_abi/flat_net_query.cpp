#include "flat_net_cost.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc,char** argv) {
 try {
  if(argc!=2)return 2;
  std::ifstream input(argv[1],std::ios::binary);if(!input)throw std::runtime_error("snapshot missing");
  std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(input)),{});
  tileplace_hbm::FlatNetCosts engine(bytes);
  for(const auto& net:engine.nets()) {auto cost=engine.cost(net);std::cout<<net.id<<' '<<cost[0]<<' '<<cost[1]<<' '<<cost[2]<<'\n';}
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
