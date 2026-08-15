# Xiaozhi Server v0.9.6 Upgrade Report

## Current state

- The running core container reports `0.9.1` and uses the pinned image `xiaozhi-server:20260813-secure`.
- Official stable `v0.9.6` is the candidate baseline. The official rolling `main` has additional unreleased commits, so it is not used as the replacement target.
- The current custom branch is based on an older upstream revision and conflicts with `v0.9.6` in server, manager and dependency files. The candidate therefore starts at the exact stable tag and ports only the locally required security changes.
- Candidate image: `xiaozhi-server:0.9.6-candidate-20260814`.
- Candidate image ID: `sha256:e3f5dabd86232f4830d9374fd370f4fa49260e9366ff5430b1b0b1019abfcc43`.
- Candidate source revision: `3be7f4745c0f516756c46c1f0c82d2fcf703fe28`.
- Candidate source tree: `4314d754246c2e4c6b445b3c917f008b86d0a7c3`.
- Candidate base image ID: `sha256:130bb55b34acabc3d43bf8d1af3d4cf01b53404d04550434992f0b7c486d8a1d`.
- Candidate deployment manifest: `14f3d6ea58075fdda90a7402499047e9f365a21b`.
- Two consecutive builds produced the same image ID. The build excludes generated Python caches and verifies source, Dockerfile, ignore-policy, deployment-manifest and base-image provenance labels before smoke testing.
- The isolated smoke runs with Docker network mode `none`, no manager URL, no database, no published host ports and only the exact read-only VAD model file used by the deployment manifest. HTTP, WebSocket and OTA probes pass.
- The prior live route used Doubao streaming ASR, `qwen-plus` and Doubao TTS. Its ASR WebSocket handshakes returned HTTP 403. An explicitly authorized one-device canary now selects Qwen3-ASR-Flash while retaining the running 0.9.1 core, `qwen-plus`, Doubao TTS and firmware 2.3.11; manager configuration and a provider sample pass, but a real device conversation still needs human confirmation.
- The running 0.9.1 provider has emitted credential-bearing request diagnostics. No credential value is reproduced here. The candidate removes those request/header/body logs and rate-limits repeated failed handshakes; affected credentials should be rotated only after the redacted implementation is deployed.
- The candidate also moves the synchronous Qwen3-ASR-Flash SDK call off the asyncio event loop, applies a 20-second default SDK/coroutine bound and passes the API key per request instead of mutating DashScope global state. This removes a candidate-only event-loop stall; it has not been deployed to the running 0.9.1 core.
- The first live connection after the ASR canary produced no ASR error or transcript, but Doubao TTS returned ten HTTP 403 failures: two generated segments were each retried five times. The candidate now treats 403 as permanent, stops after one attempt, adds a request timeout and logs only status/type metadata. This prevents the retry stall and removes reply text/response bodies from logs, but valid TTS entitlement or a separately authorized provider is still required for audible replies.
- A later read-only aggregate reached fifteen HTTP 403 attempts and three terminal segment failures. Every sanitized provider response carries code `3001` and a resource-class marker. The configured AppID and access token are present, so this evidence points to a resource entitlement or AppID/token/resource mismatch; it does not prove that a generic LLM SK is wrong, and no credential value is retained here.
- The enabled `HuoshanDoubleStreamTTS` configuration has a credential set distinct from the failing Doubao TTS route and is the lowest-risk configured dual-stream canary candidate. Before any rollout, its v0.9.6 adapter was hardened to bound WebSocket open/close operations and redact text, session/file/connection identifiers, provider metadata and exception payloads. No provider request or billable call was made, so entitlement and real first-audio latency remain unknown.
- The first authorized 0.9.6 core canary on 2026-08-15 failed closed: the process entered a restart loop because the live Compose topology did not mount `silero_vad.onnx`. The old core image was restored in about 30 seconds; manager web/API, MySQL and Redis kept the same container IDs and start times. No TTS relation or provider call was attempted after this failed gate.

## Compatibility boundary

- The required old-manager calls, `/config/server-base` and `/config/agent-models`, are unchanged between the old upstream base and `v0.9.6`; both routes exist in the currently deployed manager source.
- `v0.9.6` adds optional calls for correct words, chat titles and the device address book. The current manager web/API does not provide all of these routes. Their client wrappers catch failures and degrade without stopping the audio session, but those optional features remain unavailable until the manager is upgraded separately.
- The candidate changes only the Python core. The combined manager web/API container, MySQL, Redis and data volume remain unchanged. A candidate-only Compose override adds one exact read-only `silero_vad.onnx` bind mount because the base production Compose file exposes only the legacy SenseVoice path.
- The isolated smoke proves process and protocol startup, not real-device compatibility with the live manager configuration. A controlled test-environment deployment and one-device conversation smoke remain mandatory before any production replacement.

## Model recommendation

- The known Doubao authorization blocker has been removed from one device by the authorized Qwen3-ASR-Flash canary. Wi-Fi association, the LLM and TTS remain unchanged; human end-to-end turns are still required before attributing any remaining latency or ordering problem.
- Keep `qwen-plus` and Doubao TTS unchanged while validating the ASR canary. Measure authorization success, end-of-utterance latency and transcript accuracy before keeping it.
- Do not interpret the TTS hardening as a working voice provider. Repair Doubao TTS entitlement or authorize a one-device dual-stream TTS canary only after the current ASR observation; keep the LLM and server version fixed during that measurement.
- `qwen-plus` is not the newest available Qwen family. For a voice companion, first-token latency and consistent streaming matter more than selecting the largest model. Evaluate a current low-latency Qwen Flash model supported by the account, then compare p50/p95 first-token time and answer quality against `qwen-plus`.
- Keep the device in manual push-to-talk mode during the first server rollout. This removes false full-duplex interruptions while server AEC and streaming providers are evaluated independently.
- Evaluate `cosyvoice-v2` or another dual-stream TTS only in a later separately budgeted test, after ASR and server behavior are stable. Measure first-audio latency, timeout rate and sentence ordering before adoption.
- Do not change ASR, LLM and TTS in the same deployment as the server version. One variable per stage preserves causal evidence and a reliable rollback.

## Rollout

This is a proposed test-environment procedure; it has not been run against the current service.

1. Record the running image and container configuration with `docker image inspect xiaozhi-server:20260813-secure` and `docker inspect xiaozhi-esp32-server`.
2. Keep the existing data volume and legacy model mount unchanged, and add the exact read-only VAD model file through the committed override. Run only the core with `XIAOZHI_SERVER_IMAGE=xiaozhi-server:0.9.6-candidate-20260814 XIAOZHI_VAD_MODEL_PATH=/home/luban/codebase/aiot/xiaozhi-esp32-server/main/xiaozhi-server/models/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx docker compose -f /home/luban/codebase/aiot/xiaozhi-esp32-server/main/xiaozhi-server/docker-compose_all.yml -f /home/luban/codebase/aiot/.worktrees/xiaozhi-server-v0.9.6-eval/deploy/docker-compose.server-v0.9.6-canary.yml up -d --no-deps xiaozhi-esp32-server`.
3. Confirm the image ID, process health, OTA response and one WebSocket session before enabling a device: `docker image inspect xiaozhi-server:0.9.6-candidate-20260814`.
4. With provider selection unchanged, verify that an expected Doubao authorization failure is bounded, does not expose credential-bearing diagnostics and does not create a per-audio-frame retry storm. This validates the server candidate but is not a successful dialogue canary.
5. Only after explicit provider authorization, change ASR for one bound device/agent and run ten manual half-duplex turns: connect, tap to listen, speak one short request, tap to end, receive one ordered reply and return to idle. Keep LLM and TTS unchanged.

## Observation gates

- No crash loop, database migration or manager web/API restart.
- OTA and WebSocket connect without retry storms.
- No authorization header, device identifier, client identifier or bind code appears in logs.
- An invalid ASR entitlement produces a bounded status-only error and a 1-30 second retry cooldown rather than one handshake per PCM frame; a permanent TTS 403 stops after one status-only failure instead of five content-bearing retries.
- For at least ten manual turns: no spontaneous abort, no answer reordering, no duplicated user utterance, and no provider timeout.
- Record ASR completion, LLM first token, TTS first audio and total answer latency. A regression from the existing baseline blocks promotion.
- Missing optional manager endpoints may log a bounded warning but must not terminate a conversation.

## Rollback

From the existing compose directory, restore only the core with:

`XIAOZHI_SERVER_IMAGE=xiaozhi-server:20260813-secure docker compose -f docker-compose_all.yml up -d --no-deps xiaozhi-esp32-server`

Then verify `docker image inspect xiaozhi-server:20260813-secure`, OTA response, WebSocket connectivity and one manual conversation. The manager web/API, MySQL and Redis are not replaced by either rollout or rollback.
