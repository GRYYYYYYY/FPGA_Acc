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
