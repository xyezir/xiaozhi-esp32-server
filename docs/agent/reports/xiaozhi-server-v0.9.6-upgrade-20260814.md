# Xiaozhi Server v0.9.6 Upgrade Report

## Current state

- The running core container reports `0.9.1` and uses the pinned image `xiaozhi-server:20260813-secure`.
- Official stable `v0.9.6` is the candidate baseline. The official rolling `main` has additional unreleased commits, so it is not used as the replacement target.
- The current custom branch is based on an older upstream revision and conflicts with `v0.9.6` in server, manager and dependency files. The candidate therefore starts at the exact stable tag and ports only the locally required security changes.
- Candidate image: `xiaozhi-server:0.9.6-candidate-20260814`.
- Candidate image ID: `sha256:a2d7233c6a8e6b3646bec410e34cb53dfbd4c251218637bb3fd5da054c917cb7`.
- Candidate source revision: `0761787db1dbe32a786661bdae382cb90bd69784`.
- Candidate source tree: `518430602dc8cc1c8e99a61b21874db433bc59af`.
- Candidate base image ID: `sha256:130bb55b34acabc3d43bf8d1af3d4cf01b53404d04550434992f0b7c486d8a1d`.
- Two consecutive builds produced the same image ID. The build excludes generated Python caches and verifies source, Dockerfile, ignore-policy and base-image provenance labels before smoke testing.
- The isolated smoke runs with Docker network mode `none`, no manager URL, no database, and no published host ports. HTTP, WebSocket and OTA probes pass.
- The currently selected live route is Doubao streaming ASR, `qwen-plus` and Doubao TTS. The local wake phrase can still play its fixed acknowledgement, but the following utterance cannot be transcribed because every current Doubao ASR WebSocket handshake returns HTTP 403.
- The running 0.9.1 provider has emitted credential-bearing request diagnostics. No credential value is reproduced here. The candidate removes those request/header/body logs and rate-limits repeated failed handshakes; affected credentials should be rotated only after the redacted implementation is deployed.

## Compatibility boundary

- The required old-manager calls, `/config/server-base` and `/config/agent-models`, are unchanged between the old upstream base and `v0.9.6`; both routes exist in the currently deployed manager source.
- `v0.9.6` adds optional calls for correct words, chat titles and the device address book. The current manager web/API does not provide all of these routes. Their client wrappers catch failures and degrade without stopping the audio session, but those optional features remain unavailable until the manager is upgraded separately.
- The candidate changes only the Python core. The combined manager web/API container, MySQL, Redis, data volume and model volume remain unchanged during a core-only rollout.
- The isolated smoke proves process and protocol startup, not real-device compatibility with the live manager configuration. A controlled test-environment deployment and one-device conversation smoke remain mandatory before any production replacement.

## Model recommendation

- The live blocker is the selected Doubao streaming ASR authorization failure, not Wi-Fi association and not the LLM. Fixing the UI or upgrading the LLM cannot restore a dialogue turn until ASR succeeds.
- Keep `qwen-plus` and Doubao TTS unchanged while validating ASR. For the first one-device ASR canary, either repair the current Doubao account entitlement or select the already-configured Qwen3-ASR-Flash alternative after explicit authorization; measure authorization success, end-of-utterance latency and transcript accuracy before keeping it.
- `qwen-plus` is not the newest available Qwen family. For a voice companion, first-token latency and consistent streaming matter more than selecting the largest model. Evaluate a current low-latency Qwen Flash model supported by the account, then compare p50/p95 first-token time and answer quality against `qwen-plus`.
- Keep the device in manual push-to-talk mode during the first server rollout. This removes false full-duplex interruptions while server AEC and streaming providers are evaluated independently.
- Evaluate `cosyvoice-v2` or another dual-stream TTS only in a later separately budgeted test, after ASR and server behavior are stable. Measure first-audio latency, timeout rate and sentence ordering before adoption.
- Do not change ASR, LLM and TTS in the same deployment as the server version. One variable per stage preserves causal evidence and a reliable rollback.

## Rollout

This is a proposed test-environment procedure; it has not been run against the current service.

1. Record the running image and container configuration with `docker image inspect xiaozhi-server:20260813-secure` and `docker inspect xiaozhi-esp32-server`.
2. Keep the existing data and model volumes unchanged. From the current compose directory, run the core only with `XIAOZHI_SERVER_IMAGE=xiaozhi-server:0.9.6-candidate-20260814 docker compose -f docker-compose_all.yml up -d --no-deps xiaozhi-esp32-server`.
3. Confirm the image ID, process health, OTA response and one WebSocket session before enabling a device: `docker image inspect xiaozhi-server:0.9.6-candidate-20260814`.
4. With provider selection unchanged, verify that an expected Doubao authorization failure is bounded, does not expose credential-bearing diagnostics and does not create a per-audio-frame retry storm. This validates the server candidate but is not a successful dialogue canary.
5. Only after explicit provider authorization, change ASR for one bound device/agent and run ten manual half-duplex turns: connect, tap to listen, speak one short request, tap to end, receive one ordered reply and return to idle. Keep LLM and TTS unchanged.

## Observation gates

- No crash loop, database migration or manager web/API restart.
- OTA and WebSocket connect without retry storms.
- No authorization header, device identifier, client identifier or bind code appears in logs.
- An invalid ASR entitlement produces a bounded status-only error and a 1-30 second retry cooldown rather than one handshake per PCM frame.
- For at least ten manual turns: no spontaneous abort, no answer reordering, no duplicated user utterance, and no provider timeout.
- Record ASR completion, LLM first token, TTS first audio and total answer latency. A regression from the existing baseline blocks promotion.
- Missing optional manager endpoints may log a bounded warning but must not terminate a conversation.

## Rollback

From the existing compose directory, restore only the core with:

`XIAOZHI_SERVER_IMAGE=xiaozhi-server:20260813-secure docker compose -f docker-compose_all.yml up -d --no-deps xiaozhi-esp32-server`

Then verify `docker image inspect xiaozhi-server:20260813-secure`, OTA response, WebSocket connectivity and one manual conversation. The manager web/API, MySQL and Redis are not replaced by either rollout or rollback.
