#include "canonical_snapshot.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc,char** argv){try{if(argc!=2)return 2;std::ifstream input(argv[1],std::ios::binary);std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(input)),{});tileplace_hbm::validate_canonical_snapshot(bytes);std::cout<<"pass\n";}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
