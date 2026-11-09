#include "checked_claim_import.h"
#include <sstream>
#include <cassert>
#include <iostream>
using namespace routecast_import_v1;
static unsigned rejected=0;
static std::string document(const Context& c) {
 return "RCPREF2 "+c.graph_sha256+" 4 3 17 2 2\nN 0 616c706861\nN 2 62657461\nC 1 0 1073741824\nC 3 2 1077936128\n";
}
static void bad(const std::string& text,const Context& c) {
 std::istringstream s(text);bool caught=false;try{read(s,c);}catch(const FrameError&){caught=true;}assert(caught);++rejected;
}
int main() {
 Context c{std::string(64,'a'),4,17,{"alpha","ignored","beta"},{false,true,false},{{1,1073741824},{3,1077936128}},[](uint32_t n){return n==1||n==3;}};
 auto good=document(c);std::istringstream s(good);auto v=read(s,c);assert(v.size()==2&&v[0].node==1&&v[1].net==2);
 // Every proper token-prefix truncation must reject, including missing final claim word.
 for(size_t i=0;i<good.size();++i)if(i+1<good.size()&&(good[i]==' '||good[i]=='\n'))bad(good.substr(0,i),c);
 auto change=[&](const std::string& old,const std::string& replacement){auto t=good;auto p=t.find(old);assert(p!=std::string::npos);t.replace(p,old.size(),replacement);bad(t,c);};
 change("RCPREF2","RCPREF1");change(std::string(64,'a'),std::string(64,'b'));change("4 3 17","5 3 17");change("4 3 17","4 4 17");change("4 3 17","4 3 18");change("2 2\n","1 2\n");change("2 2\n","2 3\n");change("N 0","N 1");change("N 2","N 0");change("616c706861","616c706862");change("C 1 0","C 1 1");change("C 3 2","C 1 2");change("C 3 2","C 4 2");change("1077936128","1073741824");change("1077936128","4294967296");change("1077936128","18446744073709551616");change("C 1","C -1");change("C 1","C 01");bad(good+"junk",c);
 auto x=c;x.ignored[2]=true;bad(good,x);x=c;x.is_unit_channel=[](uint32_t){return false;};bad(good,x);x=c;x.expected_hint_bits={{0,1073741824},{3,1077936128}};bad(good,x);x=c;x.net_names[2]="renamed";bad(good,x);
 x=c;x.expected_hint_bits.clear();std::istringstream zero("RCPREF2 "+x.graph_sha256+" 4 3 17 0 0\n");assert(read(zero,x).empty());
 std::cout<<"CHECKED_IMPORT_PASS valid=1 zero=1 rejected="<<rejected<<"\n";
}
