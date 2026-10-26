CANCELED capacity objective; no rerun tests started

Victor canceled all capacity testing via Genesis at 00:30 CT. The rerun stopped during startup reads.
All seven existing delegates are terminal and settled; the old probe is completed and settled. No new test, probe, cohort, delegate or top-level thread started.
The active board has no ramp plan. Historical evidence is preserved below as canceled and superseded. No capacity limit is claimed.

Current cancellation report: [rerun/CANCELED.md](rerun/CANCELED.md).
Exact receipts: [rerun/cancellation-receipts.json](rerun/cancellation-receipts.json).
Wording provenance: [rerun/PROVENANCE.md](rerun/PROVENANCE.md).
New-episode terminal delivery: [rerun/DELIVERY.md](rerun/DELIVERY.md).

---

## Historical initial result, canceled and superseded

Everything below records the earlier experiment and its earlier conclusion. Its single slow sample is not a capacity limit. It authorizes no continuation.

DONE finite capacity experiment stopped at measured native send-acceptance degradation
---
verdict: DONE
hardware_capacity: undetermined
last_stable_cohort: 2
first_latency_degraded_cohort: 4
peak_measured_total_active_runs: 8
review_required: false
review_reason: Operational measurement and local synthetic evidence only; no code PR or deploy, under review-and-babysit section 1.
---

The finite experiment stopped at four actual diagnostic delegates after native probe acceptance rose to 1,179 ms. Earlier sends took 45, 43 and 176 ms.
Resources remained healthy during the four-delegate window. This proves a measured control-path delay, not F-D hardware saturation.
Seven workers completed 168 synthetic scenarios. All 1,008 numeric checks passed; every worker and the probe have terminal and settle receipts.
No decision is needed to close this experiment. Higher cohorts were not run. Parent callback and Genesis terminal notice receipts are in DELIVERY.md.

## Verdict and limits

- Last stable measured service step: two actual delegates, 5–6 total active runs including this orchestrator, probe when active, and two unrelated-project runs.
- First measured latency-degraded step: four actual delegates, 7–8 total active runs. Cohort native acceptance was 6.7 times c2 and 26.2 times the baseline. Each cohort has one probe send, so no percentile or sustained steady-state latency claim is possible.
- The send was initiated concurrently with cohort dispatch, as requested. Native admission serialization, MCP/tool scheduling and transient launch overhead remain competing explanations. The probe request timestamp is about 1.13 seconds after the client-side send began. This narrows the observed delay to the acceptance/control path; it does not prove its implementation cause.
- Four real delegates overlapped with healthy resource metrics. Hardware capacity is undetermined. Two is the last observed stable service step, not a hardware cap. Eight is the peak sampled whole-environment active count, not an exact machine capacity.
- Stop disposition: conservative measurement stop at the first plainly measurable service-latency increase. No retries, next cohort, repair investigation, caps, throttles or server changes.
- Cohorts 8, 16 and 20 were not run. Neither the 20-delegate thread ceiling nor the 100-agent host ceiling was reached. No provider failure, human prompt or dispatch rejection occurred.

## Concurrent measurements

All metric windows lasted about ten seconds. PSI is the difference of cumulative microsecond totals divided by elapsed monotonic time. Rates aggregate physical whole NVMe namespaces only, using 512-byte diskstats sectors. Swap si/so are cumulative page-count differences; the host page size is 4 KiB. Available memory is the minimum sampled value.

| Window | Actual cohort delegates | All active runs | Other projects active | Accepted send ms | Client send-to-completion s | Load 1m | IO some/full % | Min available GiB | Memory some/full % | Swap used GiB | si/so pages | NVMe write/read MiB/s |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|---:|---:|
| baseline | 0–0 | 3–4 | 2–2 | 45 | 6.541 | 1.15 → 1.13 | 0.957/0.893 | 48.21 | 0.364/0.361 | 7.938 → 7.917 | 3144/20 | 22.553/12.430 |
| baseline-idle | 0–0 | 3–3 | 2–2 | n/a | n/a | 1.49 → 1.88 | 0.449/0.408 | 47.30 | 1.373/1.361 | 7.708 → 7.631 | 20632/505 | 41.275/43.097 |
| c1 | 1–1 | 5–6 | 3–3 | 43 | 3.002 | 1.97 → 1.82 | 0.520/0.485 | 47.82 | 0.033/0.032 | 7.627 → 7.620 | 1318/0 | 18.379/0.753 |
| c2 | 2–2 | 5–6 | 2–2 | 176 | 2.705 | 1.34 → 1.29 | 0.521/0.490 | 47.43 | 0.180/0.176 | 7.588 → 7.579 | 1096/3 | 19.186/1.964 |
| c4 | 4–4 | 7–8 | 2–2 | 1179 | 4.117 | 1.03 → 1.33 | 0.264/0.200 | 47.71 | 0.106/0.094 | 7.556 → 7.547 | 2088/0 | 18.826/0.974 |

The accepted prior near-idle comparison, supplied by the parent at 05:02 UTC, had load 1.98 → 1.78, about 47 GiB available, IO full 0.211/0.035/0.068%, memory full 0.050/0.003/0.003%, writes 10.046/0.186/1.770 MiB/s and reads 0.394/0.005/0.470 MiB/s in its three windows. Six swap-out pages appeared in the first window; swap usage declined 8.879 → 8.874 GiB. This accepted baseline was not replaced with a zero-write or zero-swap gate.

Our baseline includes the real probe launch and metadata measurements. The following baseline-idle window excludes an active probe, but has background activity and paging. Both are retained. Cohort writes of 18–19 MiB/s exceed parts of the earlier near-idle baseline but are below our two current baseline windows. IO pressure did not rise with cohort size. Swap used declined throughout; no memory shortage appeared.

The measurement API workload is material. Every metadata sample paginates all projects and each project's active threads including subagents, about 41 project lists per sample. Counts are not atomic across projects; timestamps bracket each scan. The table uses only scans fully contained inside the proc window, excluding scans that finished after it. No continuous-count claim is made between samples. Launch and terminal receipts separately confirm the cohort workers overlapped. All observed queued counts were zero.

Only aggregate counts were saved for other projects. No titles or messages from those projects were printed or saved. Native task status was read only after named completion notices and once in the final reconciliation. No metadata database was opened.

## Probe timing and lifecycle

The dedicated probe is [Sol 6.1 High probe · F-D capacity send timing](t3-thread://v1/thread:mcp:e5e926c4-b8db-45a6-8639-8faf6d3fc2fe:capacity-probe-create-20261026:0). It performed finite arithmetic and latency interpretation on each send. Accepted-send timings are client wall time around the native send call and are distinct from provider run duration and send-to-completion time. Detailed admission, runtime and timestamps are in metrics/window-counts.json and lifecycle/probe-*-terminal.json.

The probe was settled after each terminal run. All own helper configurations read back codex_auto, gpt-6.1-sol, reasoningEffort high, serviceTier default, runtimeMode full-access and interactionMode default. AUTO_CODEX is derived from the provider-instance mapping. Underlying served account and upstream service tier are unverified because no live DB or provider-log content was read.

## Native helper receipts

| Logical task | Native task ID | Child thread ID | Terminal state | Settle readback |
|---|---|---|---|---|
| c1-w1 | `node:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c1-w1-20261026` | `thread:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c1-w1-20261026` | completed | true |
| c2-w1 | `node:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c2-w1-20261026` | `thread:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c2-w1-20261026` | completed | true |
| c2-w2 | `node:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c2-w2-20261026` | `thread:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c2-w2-20261026` | completed | true |
| c4-w1 | `node:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c4-w1-20261026` | `thread:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c4-w1-20261026` | completed | true |
| c4-w2 | `node:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c4-w2-20261026` | `thread:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c4-w2-20261026` | completed | true |
| c4-w3 | `node:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c4-w3-20261026` | `thread:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c4-w3-20261026` | completed | true |
| c4-w4 | `node:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c4-w4-20261026` | `thread:delegated-task:command%3Amcp%3Ae5e926c4-b8db-45a6-8639-8faf6d3fc2fe%3Adelegate-task%3Acapacity-c4-w4-20261026` | completed | true |

Each helper analyzed its distinct 24-case fixture and wrote one unique output. No sleeps or shell load simulated occupancy, and no helper launched children. All seven native tasks reported completed with no pending child runs in lifecycle/final-reconciliation.json. Final paginated metadata showed only this master active in this project, plus two active runs in other projects and zero queued runs.

## Checker and artifacts

- checker.json: PASS, 7 files, 168 unique scenario rows, 1,008 exact-rational numeric comparisons, plus required diagnosis and next-check fields. Initial float-round comparisons rejected seven valid half-up ties; the checker was corrected to accept either nearest value at exact half-unit ties. No worker output changed.
- fixtures/ and outputs/: distinct synthetic inputs and completed diagnostic answers. Unused planned fixtures remain as evidence; they ran no agents.
- sample.py and metrics/*.json: one-shot authorized proc sampler, raw ten-second snapshots, physical rates and process IO/fd symlink metadata. It never reads DB contents. The summaries retain process IO deltas without argv or private process messages.
- counts/*.json: timestamped paginated aggregate counts across all native projects with subagents; own thread metadata and no other-project titles/messages.
- lifecycle/*.json: every native launch, full configuration readback, named terminal readback, settle receipt and probe run timestamp.
- BOARD.md: ownership, launch decisions, receipts and stop decision. Canon source pin is canon/SOURCE.txt; task-triggered owners were fetched from fresh GitHub main. No canon was edited.
- DELIVERY.md and delivery-*.json: parent callback, metadata-only readback, installed Genesis notice and exact delivery limits.

No installs, builds, DB content reads, credential creation or renewal, upstream writes, SSH, shared-server changes, new caps or throttles occurred. Only the explicitly authorized existing MBP bearer is used in memory for the final internal callback. No forbidden lane was sent, steered or read. No other machines were measured. This newly registered project and all local evidence are preserved.

## Root row suggestion

`F-D real-agent ramp | DONE, conservative latency stop | actual cohorts 1/2/4; last stable 2; first latency-degraded 4; peak total active 8; 1179 ms native acceptance, healthy hardware metrics; 7 helpers terminal and settled | /home/victor/work/fd-capacity-20261026/RESULT.md`

Root owns any canon or registry update. A future steady-state or admission-path experiment requires a separately scoped assignment; this finite experiment does not start it.
