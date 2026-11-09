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
