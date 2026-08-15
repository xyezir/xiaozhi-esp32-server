# Xiaozhi Server v0.9.6 Upgrade Report

## Current state

- Official stable remains `v0.9.6`. This branch also contains the official rolling `main` snapshot `17560a7d295a0a7f3e46add30bb584d486b651c3`, merged without rewriting the accepted local security history.
- `xyezir/main` matched official `main` at the start of this delivery. The release branch adds the previously accepted OTA/logging/provider hardening, current Volcengine speech authentication and a verified model/provider baseline.
- Candidate image: `xiaozhi-server:0.9.6-main-20260815-candidate`.
- Candidate image ID: `sha256:e1e4fb8b6136f7d121863a761d87ab876a456cab8f074610f40cc63c88921645`.
- Candidate source revision: `40d4fdffdbbc8a27104c1e0ae998f500390206b8`.
- Candidate source tree: `04d47042762548a9355fe4646dc47b06c77b55a0`.
- Candidate base image ID: `sha256:130bb55b34acabc3d43bf8d1af3d4cf01b53404d04550434992f0b7c486d8a1d`.
- Candidate deployment manifest: `14f3d6ea58075fdda90a7402499047e9f365a21b`.
- Two consecutive builds produced the same candidate image ID. Embedded labels bind the image to the committed source tree, Dockerfile, ignore policy, deployment manifest and base image.
- The isolated smoke used Docker network mode `none`, no manager URL, no database and no published host ports. HTTP, WebSocket, OTA and live-Compose mount-contract probes passed.
- The production core remains the previously deployed `0.9.6` redaction build `sha256:7e6b3cfde68a261ea1c070255806d8d8e8f4a78949191b784044d3f1b8559cf9`; this repository release did not replace it, mutate its database or call a billable provider. `xiaozhi-server:20260813-secure` remains the core rollback image.
- Historical `0.9.1` findings and canary rollback evidence remain relevant only as provenance: the old route exposed repeated ASR/TTS 403 failures and a missing VAD mount, both of which informed the accepted hardening and topology verifier.

## Compatibility boundary

- The Huoshan double-stream provider now supports two explicit modes. A configured `api_key` sends only `X-Api-Key`; otherwise a complete legacy `appid` plus `access_token` pair sends `X-Api-App-Key` and `X-Api-Access-Key`. An explicit current-console key wins if both modes are present.
- Credentials are normalized before header construction. Missing values and repository placeholders fail before any network connection; provider response metadata, session identifiers, user text and credential-bearing exceptions remain redacted.
- Liquibase change set `202608151730` exposes the new speech API-key field in the shared manager provider and adds an empty `api_key` to the two existing double-stream model configurations. It does not enable a model, replace a credential or alter an agent relation.
- The manager already treats `api_key` as sensitive in API and Web form paths. Legacy AppID/Access Token installations continue to work without data conversion.
- Current-console speech API keys and Volcengine Ark LLM API keys are distinct credentials. The server never reinterprets one as the other.
- The source-of-truth recommendations and protocol limits are documented in `docs/model-provider-baseline.md`. Unsupported realtime Qwen ASR/TTS protocols are listed as future adapters rather than being presented as working configurations.

## Model recommendation

- ASR: keep the stable `qwen3-asr-flash` alias for the existing synchronous adapter. A dated snapshot may be used only after account-region verification; realtime ASR requires a separate WebSocket adapter.
- Low-latency LLM: evaluate `qwen3.5-flash` through the existing OpenAI-compatible Chat Completions adapter. Do not select a Responses-only model in this path.
- DeepSeek: use `deepseek-v4-flash`; the upstream default migration is included in this branch. Legacy `deepseek-chat` and `deepseek-reasoner` should not be treated as current defaults.
- VLLM: use `qwen3.5-flash` where image/video input and current OpenAI-style compatibility are required.
- TTS: prefer the `seed-tts-2.0` resource only after the speech product is enabled in the same Volcengine account. Use the speech-console API key in `api_key`; keep `volc.service_type.10029` plus legacy AppID/Access Token only for an already-entitled legacy voice.
- No model selection is changed automatically by this release. Continue one-device, one-variable canaries and compare authorization success, ASR completion, LLM first-token latency, TTS first-audio latency and ordered-turn completion.

## Verification

- Python core: 31 network-isolated security/provider tests passed, including both Huoshan authentication modes, explicit-key precedence, credential normalization, placeholder rejection, OTA trust-boundary validation, bounded provider timeouts and log redaction.
- Manager API: 127 tests passed against disposable MySQL 9.6 and Redis 8 containers. Liquibase migrated an empty database through the new change set; the disposable containers were removed afterward.
- Manager Web: 9 unit tests passed; all 6 locale files contain 1,526 keys; the production build completed. Existing large static assets generated only size warnings.
- Candidate runtime: two identical image builds and two isolated HTTP/WebSocket/OTA smoke runs passed. The resolved live-Compose overlay contains the exact read-only `silero_vad.onnx` mount and does not create the host path implicitly.
- Repository: Python syntax, YAML parsing, Bash syntax, report validation and `git diff --check` passed. No production credential was added to the branch.

## Rollout

This delivery publishes source and a reviewable PR only. Production remains read-only.

1. Review the branch diff and GitHub checks. Confirm the PR head contains official `main` and the accepted local commits without a force-push.
2. Rebuild locally with `bash scripts/verify-server-upgrade-candidate.sh`; inspect provenance with `docker image inspect xiaozhi-server:0.9.6-main-20260815-candidate`.
3. In a later explicitly authorized test deployment, resolve the candidate-only overlay before startup and replace only the core service with `XIAOZHI_SERVER_IMAGE=xiaozhi-server:0.9.6-main-20260815-candidate XIAOZHI_VAD_MODEL_PATH=/absolute/path/to/silero_vad.onnx docker compose -f docker-compose_all.yml -f deploy/docker-compose.server-v0.9.6-canary.yml up -d --no-deps xiaozhi-esp32-server`.
4. Keep ASR, LLM and TTS relations unchanged during the server-version smoke. Only then run separately authorized one-device provider canaries.

## Observation gates

- No crash loop, manager restart, database mutation outside the reviewed Liquibase change set or credential-bearing log entry.
- OTA and WebSocket connect without retry storms; missing optional manager endpoints degrade without terminating the audio session.
- Invalid provider entitlement produces bounded status/type-only diagnostics and does not retry per PCM frame or per generated segment.
- Ten manual half-duplex turns complete in order before promotion: no spontaneous abort, duplicate transcript, answer reordering or missing return to idle.
- Record ASR completion, LLM first token, TTS first audio and total answer latency. A material regression blocks promotion.

## Rollback

The repository release is reverted by closing the PR or reverting its commits; it does not require a production rollback.

For a later core canary, restore only the prior core with `XIAOZHI_SERVER_IMAGE=xiaozhi-server:20260813-secure docker compose -f docker-compose_all.yml up -d --no-deps xiaozhi-esp32-server`. Then verify the image, OTA response, WebSocket connection and one manual conversation. The manager web/API, MySQL and Redis are not replaced by either action.
