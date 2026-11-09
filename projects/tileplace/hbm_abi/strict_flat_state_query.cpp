#include "strict_flat_state.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc,char** argv){try{
 if(argc!=2)return 2;
 std::ifstream input(argv[1],std::ios::binary);std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(input)),{});
 tileplace_hbm::StrictFlatState state(bytes);auto initial=state.snapshot();std::string command;
 while(std::cin>>command){
  if(command=="RESTORE"){state.restore(initial);std::cout<<"OK\n";continue;}
  unsigned count;std::cin>>count;std::set<std::uint32_t> nets;
  if(command=="EVAL"){while(count--){unsigned id;std::cin>>id;nets.insert(id);}std::cin>>count;}
  tileplace_snapshot::Positions changes;while(count--){unsigned id;tileplace_snapshot::Point p;std::cin>>id>>p.x>>p.y>>p.subtile>>p.layer;changes[id]=p;}
  if(command=="COMMIT"){try{state.commit(changes);std::cout<<"OK\n";}catch(const std::exception&){std::cout<<"REJECT\n";}}
  else if(command=="EVAL"){auto values=state.evaluate(nets,changes);for(auto v:values.first)std::cout<<v<<' ';for(auto v:values.second)std::cout<<v<<' ';std::cout<<'\n';}
  else throw std::invalid_argument("unknown command");
 }
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
