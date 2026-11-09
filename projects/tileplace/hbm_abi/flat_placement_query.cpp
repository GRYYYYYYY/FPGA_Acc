#include "flat_placement.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc,char** argv){try{if(argc!=2)return 2;std::ifstream input(argv[1],std::ios::binary);std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(input)),{});tileplace_hbm::FlatPlacement placement(bytes);std::cout<<placement.positions().size()<<'\n';unsigned count;while(std::cin>>count){tileplace_snapshot::Positions changes;while(count--){unsigned id;tileplace_snapshot::Point p;std::cin>>id>>p.x>>p.y>>p.subtile>>p.layer;changes[id]=p;}try{placement.commit(changes);std::cout<<"OK\n";}catch(const std::exception&){std::cout<<"REJECT\n";}for(const auto& [id,p]:placement.positions())std::cout<<id<<' '<<p.x<<' '<<p.y<<' '<<p.subtile<<' '<<p.layer<<'\n';}}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
