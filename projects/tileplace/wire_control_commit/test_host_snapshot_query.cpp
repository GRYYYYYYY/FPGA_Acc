#include "host_snapshot_words.hpp"
#include <fstream>
#include <iterator>
#include <iostream>
int main(int argc,char** argv){if(argc!=2)return 1;std::ifstream f(argv[1],std::ios::binary);std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(f)),{});tileplace_wire_control_commit::HostSnapshotWords snapshot(bytes);auto in=snapshot.input();std::cout<<in.block_count<<" "<<in.unit_count<<" "<<in.site_count<<" "<<in.net_count<<" "<<in.connection_count<<" "<<in.routed_count<<"\n";}
