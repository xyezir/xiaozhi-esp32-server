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

## Surprises and discoveries

- The current custom server is one large commit on an older base; directly pulling v0.9.6 conflicts in manager security, dependencies and mobile files.
- The running dialogue path uses non-streaming `qwen3-asr-flash`, `qwen-plus` and `EdgeTTS`; observed failures were upstream-provider timeouts rather than local CPU or memory pressure.
- The old manager provides the two required core configuration routes. New v0.9.6 correct-word, chat-title and address-book calls are optional and degrade on the old manager, so those features are not part of a core-only rollout.
- The isolated candidate starts successfully with network disabled and without a manager URL or database; HTTP, WebSocket and OTA probes pass.

## Decision log

- 2026-08-14: Use the official v0.9.6 tag, not current `main`, because stable already contains the relevant audio/concurrency fixes while `main` continues to move.
- 2026-08-14: Validate the core server first and leave the combined manager web/API container unchanged; this minimizes database and migration risk.
- 2026-08-14: Do not switch to a paid streaming TTS or a new LLM until account access, price and latency are measured with an explicit small test budget.

## Outcomes and retrospective

The rollback-ready stable candidate is built as `sha256:3665c05953e772881968a114828c2276671448848eb4fb33e8243c9cbf4c07e0`. Security regressions and isolated protocol smoke pass. The current running service remains unchanged; a controlled one-device test-environment deployment is still required before production replacement.
