# Current critical path v105

Original scope, budgets, failed cases and denominators remain fixed:11workloads/311096searches. All eight gates remain open.

G1: Frozen inputs, baseline sources and commands; true layer/SLR metadata; graph and route round trip; in_progress

G2: C++ complete routing closure with exact occupancy, net sharing, corridor release/repair, deterministic transactions and five-repeat hashes; in_progress

G3: At least one credible multi-die workload cohort plus parameterized topology/capacity scaling; microbenchmarks alone insufficient; in_progress

G4: Native legality; route failures do not increase; SLL use, CPD and wirelength do not degrade relative to frozen strong baselines; in_progress

G5: E-DR1 reservation, E-DR2 mapping, E-DR3 shadow, E-DR4 migration, E-DR5 topology ablations; in_progress

G6: HLS csim/csynth/cosim; actual HBM interfaces and connectivity; U280 implementation timing and resource reports; in_progress

G7: Physical board end-to-end >=3x target, energy, repeated runs and statistical evidence; never substitute emulation time; pending_external_hardware

G8: Paper, claim matrix, reproducible artifact bundle and gate-by-gate final audit; in_progress

Inventory correction: original linked platform contains onecommit, oneSeedQueue and oneSnapshotSearch CU, allSLR1. Onlyone newcache instance is needed to replace snapshotsearch while preserving all3CUidentities. Prior3cache replica exclusion does not apply. Base256k192URAM passes necessarySLR1capacity320 arithmetic; integrated fit/timing unproven. Base1M768URAM still exceeds fixedSLR1capacity320. Hypothetical3replica figures remain hypothetical. Evidence:work/original_platform_CU_inventory_correction_20261023/review.json

Native33 completeworkerRTL+Xcanary independentreview passed at fulltemplate/cachedepth, finite4node4arc only. Generationv3actualOOC MCPvivado-20261023-092113-9e5d9c49/native488181/start1700209110/functions2174 stillrunning; await actualsource0, close normally, freshDCPquery and derive actualnewcounts. No inheritedbasecounts.

Existing graph28878 nativeXSim1922718/start1699455310 and joint46600wholeTVauditor4126414/start1699696127 remain live at lastcheck; no timeoutrestart. Original postroute709786/start1697034141 stillrunning; finalfullDCPsignoff required before timingclaim.

G4 two newseq closurecandidates pass fullnativequality, but baseline-heavy restoration718/699nets, separatefromoriginalfixedbudgetfailures and notuniformintegratedpolicy/five-repeat proof. Generic capacityrepair rule+CLI verified25600finitecases/exact2nativecandidateoutputs; contract staged. Threeoldmissingupstreamlaunchreceipt exceptions remain.

G7 physicalboard unavailable under retainedPCI/XRT evidence; no boardtime/energy/>=3xclaims. Frozenpaper/artifacts remain immutable; G8finalaudit incomplete.


v106 actualgenerationv3resources192URAM/48.5BRAM/12DSP/34790LUT/46400FF/0BB/fullcache/AXI independentlyverified. BothOOC/freshMCPs normalclosed. XOexport0 and15args/7ports externalABI match, butactualoriginalHIGHER_G_TIE1 vs currentcache smallerG witness differs. Do notlinkthiscandidateasoriginalalgorithm-preservingreplacement. Rebaseprivatecacheontofrozenoriginalsource+flags, thenC/RTL/resourceproofs forsuccessor. Existingv3proofs remain validscoped. All8gates unchanged.


v107 frozenplatformcachev4 prepared withall50originalsourcefiles+3compileflags unchanged. Actual33CplusfullworkerHIGHER_Gtiecasepass; fullrealCSR freshfrozenref/cache all14artifactseq/341treecensus/42PIPpass. ActualHLS0,full3cachearrays/6AXI/nextcounterandpreprocessedflags verified; all-loopconstraintsnotmet retained. Native34setup/Cgen launched1855238/start1700353728, ZEROv4RTLaccepteduntilactualfullpipelineaudit. Need complete34TVindependentABI thennative34includingtie/Xcanary andnewOOC/freshDCP. Do notinheritv3resourcecounts. Original11/311096/all8gatesunchanged.


v108 v4fullnative34positivepassed717.909s/full104618scratchwords/Cpost/twoactualwraps/higherGtie. Xcanarypending. Actualv4XOexport36.144s andoriginal15args/7ports/3compileflags/42packagedHDL/50frozenheaders verified. ActualOOC457.974/freshDCP37.643s sources0 andbothsessionsnormallyclosed; finalmappingreviewwaiter2803873/start1700452429 waitsactualnative34combinedreview. Fullplatformlinkcontroller2605659/start1700432104 stagedonlysnapshotXOreplacement/original2XOs/all3CUs/HBM/SLR1/300MHz/privateidenticalpostphysopthook; awaitallactualreviews thenserializedlock+36GiBheadroom/24GiBVM-RSS/global72/no timeout. No linkstarted/adoption/signoff yet. Original11/311096/all8gatesunchanged.


v109 FINALv4native34positive/Xcanarycombinedreview passed andnewOOC/freshDCP finalreview passed:192URAM/48.5BRAM/12DSP/34636LUT/46879FF/0BB/fullarrays/AXI. Allprerequisiteproofs actualcomplete. Fullplatformlinkcontroller2605659/start1700432104 wrote frozenlink_protocol andnowWAIT36GiBtotalheadroom(actual~23GiB), no linkstarted. OnlysnapshotXOchanged; originalother2XOs,threeCUs/SLR1/HBM/300MHz andprivateidenticalpostphysopthook retained. Actualfullplatformtiming andmappedRAMfunctionalproof remain open; no override ofmemoryguard orstopolderjobs. All8gates/original11/311096unchanged.


v110 actualmappedURAMnative34functionaltest added withoutalteringDUTor34oracles. InitialpositivefailedbeforeXSim onHLS-onlylogicalloopprofilingnames;failure retained/noDUTdefectestablished. Privatev2supervisor3774305/start1700555708,positive3775655/start1700555820,auditwaiter3774308/start1700555708: all23moduleportprofilers retained/all14notapplicableHLSloopprobesexplicitlyexcluded/mechanicalinverseproof/noHLSloopCSVclaim. Staticelaborationpassed, runtimecompileongoing/0acceptedworkerRTLcalls. Newnetlist contains192actualURAM288primitives;generationobserveraliasreboundcache_generation_reg only. Fullplatformlink2605659 stillwaiting36GiBheadroom, noneofoldjobsstopped. All8gates/original11/311096unchanged.


v111 jointwholeTVauditor4126414actualterminal0/8749.263s/peak557805568/no guard:all46600/full2144479808000payloadbytes/native256/domain64/24padbytespercall/headersfooterEOF/fiveSHAcomplete. FreshindependentreconciliationchecksallimmutablecachefilemetadataandsmallTVhashes/Cpostidentityonly(no2TBrehash). OriginalcorrectedjointRTLwaiterautolaunchedpositive3991046/start1700578855,actualXSim4039363/start1700583670,512/256/512+3rawX/fullmodelsruntimeconfirmed/intermediate1of46600/notfullacceptance. Preserveall46600/Cpost/reply/rows/canary/unsigned64diagnosticwatchdog. Mappednative34v2kernel3957564/start1700575281stillrunning; originalgraph1922718andpostroute709786alive. Fullplatformcachev4linkstillWAIT36GiBheadroom. All8gates/original11/311096unchanged.


v112 finalsignoffparsernegativecontrolrealreports verified:routecomplete doesnotconcealWNS-3.053/setup72030/8criticalmethodology/7input+3outputmissingdelays. DefaultDRC375actualrows/0waivedcrosschecked;missing/contradictorytimingevidence3mutationsrejected. NewreadonlyqueryextendedallactualDRCproperties/waiverstate, Tclsyntaxcheckedonly; priorquery/preparation/syntaxrecordsv1archivedwithhashidentity. No newnativequery/signoffexecution. Allbackgroundjobidentitieslive/latestnoendstates; v4fulllinkstillWAIT36GiBheadroom. All8gates/original11/311096unchanged.


v113: Uniform frozen-parent capacity repair all9 complete independent native exact whole-tree/sinkpin audit0. All9 capacity/legal/WL/modelcrossing pass; only4jointquality pass,5CPD regressions. Complete original9eligible+3des failures retained. Need unchanged-budget refinement (7eligible for extra sweep;seq1/2budget30exhausted). New uniforminitialcontroller1764212/start1700784485 waits actualreview0/resources; no fullpolicy/freshrepeat claim. Original11/311096/all8gates unchanged.


v114:firstuniformrepairedparentinitial misex3_seed1 independentreplay0,629nets31accepted+1refreshaccepted,WL11423/CPD10.8337/model845 allbaselinepass;1107evidencehashesrechecked. InitialauditmissingVPRhashfailure preserved. SecondcaseinitialCPDfail11377/10.4478 retained; secondaudit1995768 waits20GiB then originalfixedmodes followupwaiter2107122 waitsactualaudit0. Thirdcaseinitialrunning. No freshparent/fiverepeat/fullcohort or gateclosure. All8gates/original11/311096unchanged.


v115: secondmisex3_seed2 originalinitialaudit0 independentlyconfirmsCPD10.4478>10.3296 failure,1275sourcehashesrechecked. Actualnewfixedfollowupguard741505/start1701539062 waits20GiB; remaining5auditsguard685822/start1701533525 waits20GiB. Mainseq_seed3sweepcontinues. No completeuniformpolicy/freshrepeats/gateclosure. Original11/311096/all8gatesunchanged.


v116: secondmisex3_seed2 fixedmodesbothfailthenoriginalcapacityfallback585/629restored=>12074WL/10.3296ns/model907 nativejointpass; all8commands0,noguard,actorreceipt/protocolbindings verified. Thirdmisex3_seed3 initialindependentaudit0=>11967/10.7649/model888.1255recursiveevidencehashesverified. Mainseq_seed3refreshstillmissesbaseline atlatest18335/10.6916, originalinitialoutcome requiredbeforefollowup. Remainingauditscontinue. Fullplatformlinkstillmemoryqueued; oldFPGAexperiments unchanged. All8gates/original11/311096unchanged.
