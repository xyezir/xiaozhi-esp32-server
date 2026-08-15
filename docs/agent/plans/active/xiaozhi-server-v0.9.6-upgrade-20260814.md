# Xiaozhi Server v0.9.6 Upgrade ExecPlan

Acceptance contract: `docs/agent/acceptance/active/xiaozhi-server-v0.9.6-upgrade-20260814.yaml`

## Goal and boundaries

Upgrade the accepted v0.9.6 core-server candidate to the official rolling `main` snapshot verified on 2026-08-15, preserve the OTA trust boundary and security/runtime fixes, add current Volcengine API-key compatibility, synchronize official model/provider configuration, and publish an auditable branch and PR to `xyezir/xiaozhi-esp32-server`. Production service/database writes and billable provider calls remain out of scope.

## Progress

- [x] Confirmed the running core reports 0.9.1 and official stable is v0.9.6.
- [x] Created an isolated v0.9.6 worktree because the current custom branch diverges from an older base and conflicts with the stable tag.
- [x] Port the required security changes and add regression tests.
- [x] Build and smoke the candidate on isolated ports and configuration.
- [x] Record compatibility, model recommendations, rollout and rollback evidence.
- [x] Run adversarial review and acceptance completion validation.
- [x] Diagnose the current one-turn-only device failure: the local wake phrase still works, but the selected Doubao streaming ASR handshake returns HTTP 403 before any user utterance can be transcribed.
- [x] Add bounded exponential retry, audio-buffer trimming and credential-safe diagnostics to the v0.9.6 Doubao streaming provider; pass the expanded offline regression suite and reproduce the rebuilt candidate image twice.
- [x] Re-verify the candidate against the exact live Compose model mounts after the first authorized canary failed closed and rolled back.
- [x] Redeploy the reproducibly rebuilt candidate after the authorized Huoshan probe exposed a placeholder-key log echo; keep the failed TTS relation rolled back.
- [x] Verify that `xyezir/main` exactly matches official `main` at task start while the accepted candidate has 18 local commits and lacks 21 upstream commits.
- [x] Merge the official latest `main` without rewriting shared history and preserve both upstream behavior and local security fixes.
- [x] Add explicit current-console `X-Api-Key` support to the Huoshan double-stream provider while keeping legacy AppID/Access Token compatibility.
- [x] Synchronize and document official model/provider defaults; complete focused, manager and image-level verification.
- [x] Publish the branch and reviewable PR to the fork, record GitHub evidence and close the acceptance contract.
- [ ] Build and deploy a disposable full-stack shadow with no host ports; verify manager migration, Web/API routes and core-to-manager authenticated configuration fetch, then remove all shadow containers and network.

## Surprises and discoveries

- The current custom server is one large commit on an older base; directly pulling v0.9.6 conflicts in manager security, dependencies and mobile files.
- The currently selected live route is Doubao streaming ASR, `qwen-plus` and Doubao TTS. The wake phrase and its fixed acknowledgement are local; every subsequent ASR WebSocket handshake currently fails with HTTP 403, so the first real utterance never reaches the LLM.
- The live 0.9.1 provider logs credential-bearing request diagnostics. No credential value is retained in this plan. The v0.9.6 candidate removes those payload/header logs, bounds errors to status code or exception type and throttles repeated handshakes from per-frame retries to an exponential 1-30 second cooldown.
- The old manager provides the two required core configuration routes. New v0.9.6 correct-word, chat-title and address-book calls are optional and degrade on the old manager, so those features are not part of a core-only rollout.
- The isolated candidate starts successfully with network disabled and without a manager URL or database; HTTP, WebSocket and OTA probes pass.
- The first recorded image ID was not reproducible because nested ignored Python caches still entered the Docker context. Recursive exclusions and embedded source/base provenance now make consecutive builds identical; the superseded image was never deployed.
- The first authorized core-only canary on 2026-08-15 entered a restart loop because the live Compose file mounted only the legacy SenseVoice path while v0.9.6 also requires `silero_vad.onnx`. The rollback restored 0.9.1 in about 30 seconds without restarting manager web/API, MySQL or Redis. The previous isolated smoke had hidden this mismatch by mounting the entire host `models` directory.
- The second core canary passed. The separately authorized Huoshan TTS relation then changed exactly one agent and its matching voice, but the one short provider probe revealed that the configured access token was still a placeholder and returned no audio. The relation rolled back immediately. This path also exposed that `check_model_key` echoed its current value into logs, so the candidate must be rebuilt before the core canary is retained.
- The official latest Release remains v0.9.6, but rolling `main` is 21 commits ahead of the tag. The user's fork already matches that upstream snapshot; the unpublished value is the accepted candidate's 18 security/runtime commits plus the new API-key compatibility.
- Volcengine now exposes a single API Key in its current speech console, while the existing manager schema and adapter only send legacy `X-Api-App-Key` and `X-Api-Access-Key`. Treating an Ark or speech API Key as a legacy access token cannot work reliably.
- The manager test suite defaults to `skipTests=true`; a bare `mvn test` is not evidence. Explicit `-DskipTests=false` plus disposable MySQL/Redis is required for the 127-test integration run.
- The upstream Web build succeeds but retains existing static-asset size warnings. They are not introduced by this provider/configuration change and remain separate performance debt.

## Decision log

- 2026-08-14: Use the official v0.9.6 tag, not current `main`, because stable already contains the relevant audio/concurrency fixes while `main` continues to move.
- 2026-08-14: Validate the core server first and leave the combined manager web/API container unchanged; this minimizes database and migration risk.
- 2026-08-14: Do not switch to a paid streaming TTS or a new LLM until account access, price and latency are measured with an explicit small test budget.
- 2026-08-15: Do not treat the local wake acknowledgement as a successful server turn. Keep the running provider selection unchanged under the read-only production boundary; a separately authorized one-device ASR canary must either repair the current Doubao entitlement or select one already-configured alternative such as Qwen3-ASR-Flash.
- 2026-08-15: Rotate any credential that may have appeared in legacy logs only after the redacted provider is deployed, so replacement values cannot be leaked by the same code path.
- 2026-08-15: Preserve one-variable rollout semantics by adding a read-only, exact-file VAD mount through a candidate-only Compose override. Do not mutate the base production Compose file or mount the whole models tree.
- 2026-08-15: Treat a placeholder provider token as a failed TTS canary, not a billable success. Redact the value at the shared model-key validation boundary and do not retry another provider without fresh authorization.
- 2026-08-15: Use a merge commit to bring official `main` into the accepted branch; do not rebase or force-push the audited local history. Publish only to the user's `xyezir` fork.
- 2026-08-15: Support both current `X-Api-Key` and legacy AppID/Access Token authentication explicitly. Never silently reinterpret a Fireworks/Ark/other-provider key as a speech credential, and never issue a billable provider call during repository validation.
- 2026-08-15: Name the local image `0.9.6-main-20260815-candidate` so its rolling-main provenance is visible; keep the old production image untouched under the read-only boundary.

## Outcomes and retrospective

The mainline candidate is built reproducibly as `sha256:e1e4fb8b6136f7d121863a761d87ab876a456cab8f074610f40cc63c88921645` from build-input revision `40d4fdffdbbc8a27104c1e0ae998f500390206b8`, server tree `04d47042762548a9355fe4646dc47b06c77b55a0` and deployment manifest `14f3d6ea58075fdda90a7402499047e9f365a21b`. Thirty-one offline security/provider tests, 127 manager API tests, 9 manager Web tests, i18n validation, production Web build, exact-topology isolated HTTP/WebSocket/OTA smoke and two consecutive image builds pass. The branch is published to the user's fork with PR `xyezir/xiaozhi-esp32-server#1`; production service and database state were not changed.

Quality Delta: Improved current/legacy speech-auth separation, credential normalization, migration safety, model-source traceability, deployment-to-test fidelity and immutable image provenance. Introduced one additive nullable `api_key` configuration field and no automatic model switch. Deferred realtime Qwen ASR/TTS adapters and existing Web static-asset size debt. Evidence: network-none provider tests, full disposable-database manager suite, Web build and reproducible isolated runtime smoke.
