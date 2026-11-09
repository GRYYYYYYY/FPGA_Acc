#include "atom_netlist_utils.h"
#include <iostream>
#include <string>
#include <vector>
#include <stdexcept>
int main(){
 try {
  std::size_t total; if(!(std::cin>>total)) throw std::runtime_error("header");
  for(std::size_t k=0;k<total;++k){
   std::string name;std::size_t n,w,rows;std::cin>>name>>n>>w>>rows;
   if(n==0||n>w||w>6||rows==0)throw std::runtime_error("dimensions");
   std::vector<int> permutation(n);std::vector<bool> seen(w,false);
   for(auto& p:permutation){std::cin>>p;if(p<0||std::size_t(p)>=w||seen[p])throw std::runtime_error("permutation");seen[p]=true;}
   AtomNetlist::TruthTable table;
   for(std::size_t j=0;j<rows;++j){std::string pattern;int value;std::cin>>pattern>>value;if(pattern.size()!=n||(value!=0&&value!=1))throw std::runtime_error("cube");std::vector<vtr::LogicValue> cube;
    for(char c:pattern){if(c!='0'&&c!='1'&&c!='-')throw std::runtime_error("symbol");cube.push_back(c=='0'?vtr::LogicValue::FALSE:c=='1'?vtr::LogicValue::TRUE:vtr::LogicValue::DONT_CARE);}cube.push_back(value?vtr::LogicValue::TRUE:vtr::LogicValue::FALSE);table.push_back(cube);}
   auto logical=truth_table_to_lut_mask(table,n);auto physical=truth_table_to_lut_mask(permute_truth_table(table,w,permutation),w);
   std::cout<<name<<' ';for(auto x:logical){if(x!=vtr::LogicValue::TRUE&&x!=vtr::LogicValue::FALSE)throw std::runtime_error("undefined logical");std::cout<<(x==vtr::LogicValue::TRUE?'1':'0');}std::cout<<' ';for(auto x:physical){if(x!=vtr::LogicValue::TRUE&&x!=vtr::LogicValue::FALSE)throw std::runtime_error("undefined physical");std::cout<<(x==vtr::LogicValue::TRUE?'1':'0');}std::cout<<'\n';
  }
  std::string extra;if(std::cin>>extra)throw std::runtime_error("trailing input");
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
 return 0;
}
