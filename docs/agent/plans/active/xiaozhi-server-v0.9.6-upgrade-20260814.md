# Xiaozhi Server v0.9.6 Upgrade ExecPlan

Acceptance contract: `docs/agent/acceptance/active/xiaozhi-server-v0.9.6-upgrade-20260814.yaml`

## Goal and boundaries

Build an auditable, rollback-ready v0.9.6 core-server candidate without touching the running service or its database. Preserve the existing OTA trust boundary and sensitive-log redaction. Provider/model changes remain recommendations until their billing and account permissions are explicitly validated.

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
- [ ] Rebuild and redeploy the candidate after the authorized Huoshan probe exposed a placeholder-key log echo; keep the failed TTS relation rolled back.

## Surprises and discoveries

- The current custom server is one large commit on an older base; directly pulling v0.9.6 conflicts in manager security, dependencies and mobile files.
- The currently selected live route is Doubao streaming ASR, `qwen-plus` and Doubao TTS. The wake phrase and its fixed acknowledgement are local; every subsequent ASR WebSocket handshake currently fails with HTTP 403, so the first real utterance never reaches the LLM.
- The live 0.9.1 provider logs credential-bearing request diagnostics. No credential value is retained in this plan. The v0.9.6 candidate removes those payload/header logs, bounds errors to status code or exception type and throttles repeated handshakes from per-frame retries to an exponential 1-30 second cooldown.
- The old manager provides the two required core configuration routes. New v0.9.6 correct-word, chat-title and address-book calls are optional and degrade on the old manager, so those features are not part of a core-only rollout.
- The isolated candidate starts successfully with network disabled and without a manager URL or database; HTTP, WebSocket and OTA probes pass.
- The first recorded image ID was not reproducible because nested ignored Python caches still entered the Docker context. Recursive exclusions and embedded source/base provenance now make consecutive builds identical; the superseded image was never deployed.
- The first authorized core-only canary on 2026-08-15 entered a restart loop because the live Compose file mounted only the legacy SenseVoice path while v0.9.6 also requires `silero_vad.onnx`. The rollback restored 0.9.1 in about 30 seconds without restarting manager web/API, MySQL or Redis. The previous isolated smoke had hidden this mismatch by mounting the entire host `models` directory.
- The second core canary passed. The separately authorized Huoshan TTS relation then changed exactly one agent and its matching voice, but the one short provider probe revealed that the configured access token was still a placeholder and returned no audio. The relation rolled back immediately. This path also exposed that `check_model_key` echoed its current value into logs, so the candidate must be rebuilt before the core canary is retained.

## Decision log

- 2026-08-14: Use the official v0.9.6 tag, not current `main`, because stable already contains the relevant audio/concurrency fixes while `main` continues to move.
- 2026-08-14: Validate the core server first and leave the combined manager web/API container unchanged; this minimizes database and migration risk.
- 2026-08-14: Do not switch to a paid streaming TTS or a new LLM until account access, price and latency are measured with an explicit small test budget.
- 2026-08-15: Do not treat the local wake acknowledgement as a successful server turn. Keep the running provider selection unchanged under the read-only production boundary; a separately authorized one-device ASR canary must either repair the current Doubao entitlement or select one already-configured alternative such as Qwen3-ASR-Flash.
- 2026-08-15: Rotate any credential that may have appeared in legacy logs only after the redacted provider is deployed, so replacement values cannot be leaked by the same code path.
- 2026-08-15: Preserve one-variable rollout semantics by adding a read-only, exact-file VAD mount through a candidate-only Compose override. Do not mutate the base production Compose file or mount the whole models tree.
- 2026-08-15: Treat a placeholder provider token as a failed TTS canary, not a billable success. Redact the value at the shared model-key validation boundary and do not retry another provider without fresh authorization.

## Outcomes and retrospective

The rollback-ready stable candidate is built reproducibly as `sha256:e3f5dabd86232f4830d9374fd370f4fa49260e9366ff5430b1b0b1019abfcc43` from deployment/source revision `3be7f4745c0f516756c46c1f0c82d2fcf703fe28`, source tree `4314d754246c2e4c6b445b3c917f008b86d0a7c3` and deployment manifest `14f3d6ea58075fdda90a7402499047e9f365a21b`. Twenty-six offline security/provider tests, exact-topology isolated HTTP/WebSocket/OTA smoke and two consecutive image builds pass. The first production canary exposed and safely rolled back a missing VAD mount; the corrected candidate-only override now closes that deployment gap. A second one-device server canary remains required before the separately authorized dual-stream TTS canary.

Quality Delta: Improved deployment-to-test fidelity, immutable deployment provenance and fail-fast model-path validation. Introduced one candidate-only read-only bind mount. Deferred repair of the legacy SenseVoice source path, which is currently a directory and is not used by the selected Qwen ASR. Evidence: two identical candidate builds, exact live Compose resolution, 26 offline tests and isolated protocol smoke.
