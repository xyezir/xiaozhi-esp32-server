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

## Surprises and discoveries

- The current custom server is one large commit on an older base; directly pulling v0.9.6 conflicts in manager security, dependencies and mobile files.
- The currently selected live route is Doubao streaming ASR, `qwen-plus` and Doubao TTS. The wake phrase and its fixed acknowledgement are local; every subsequent ASR WebSocket handshake currently fails with HTTP 403, so the first real utterance never reaches the LLM.
- The live 0.9.1 provider logs credential-bearing request diagnostics. No credential value is retained in this plan. The v0.9.6 candidate removes those payload/header logs, bounds errors to status code or exception type and throttles repeated handshakes from per-frame retries to an exponential 1-30 second cooldown.
- The old manager provides the two required core configuration routes. New v0.9.6 correct-word, chat-title and address-book calls are optional and degrade on the old manager, so those features are not part of a core-only rollout.
- The isolated candidate starts successfully with network disabled and without a manager URL or database; HTTP, WebSocket and OTA probes pass.
- The first recorded image ID was not reproducible because nested ignored Python caches still entered the Docker context. Recursive exclusions and embedded source/base provenance now make consecutive builds identical; the superseded image was never deployed.

## Decision log

- 2026-08-14: Use the official v0.9.6 tag, not current `main`, because stable already contains the relevant audio/concurrency fixes while `main` continues to move.
- 2026-08-14: Validate the core server first and leave the combined manager web/API container unchanged; this minimizes database and migration risk.
- 2026-08-14: Do not switch to a paid streaming TTS or a new LLM until account access, price and latency are measured with an explicit small test budget.
- 2026-08-15: Do not treat the local wake acknowledgement as a successful server turn. Keep the running provider selection unchanged under the read-only production boundary; a separately authorized one-device ASR canary must either repair the current Doubao entitlement or select one already-configured alternative such as Qwen3-ASR-Flash.
- 2026-08-15: Rotate any credential that may have appeared in legacy logs only after the redacted provider is deployed, so replacement values cannot be leaked by the same code path.

## Outcomes and retrospective

The rollback-ready stable candidate is built reproducibly as `sha256:a2d7233c6a8e6b3646bec410e34cb53dfbd4c251218637bb3fd5da054c917cb7` from source revision `0761787db1dbe32a786661bdae382cb90bd69784` and source tree `518430602dc8cc1c8e99a61b21874db433bc59af`. Fifteen offline security/provider tests, isolated HTTP/WebSocket/OTA smoke and two consecutive image builds pass. The candidate now fails safely when Doubao rejects authorization, but it cannot make the current invalid provider entitlement succeed. The running service and provider selection remain unchanged; a controlled one-device server canary and a separately authorized ASR canary are still required.
