# ESP adversarial delivery ExecPlan

Status: blocked on current physical-device acceptance
Updated: 2026-08-13 14:50 +08:00
Acceptance contract: `/home/luban/codebase/aiot/xiaozhi-esp32-server/docs/agent/acceptance/active/esp-project-adversarial-delivery-20260813.yaml`

## Goal

Close the adversarial-review findings across the Nezuko firmware, Xiaozhi server/manager/mobile, and the non-gating Brookesia prototype; produce reproducible Linux artifacts, deploy the current non-production services, and stop only at evidence-backed physical gates.

## Context and constraints

- The release track is Nezuko plus Xiaozhi server/manager; Brookesia is an experiment and cannot block the main release.
- The environment is `nonprod-auto`; production changes, destructive data operations, secret output, force pushes and history rewrites are out of scope.
- One existing Waveshare 1.75C device may be used after a full flash backup. Brookesia must not be flashed without preserving/restoring the main firmware.
- Build success, an old artifact, HTTP 200, a running container and visual acceptance are separate evidence levels.
- Device identifiers, account data, tokens, activation codes and Wi-Fi details must not be copied into plans, logs or final reports.

## Done when

- AC-01 through AC-09 pass with current-source evidence.
- The current Nezuko artifact is installed and HW-01 through HW-04 pass.
- Every old plan is explicitly classified as complete, built, blocked or deferred.
- Current-source artifacts, images, rollback points, limitations and Quality Delta are recorded.

## Progress

- [x] Establish source recovery snapshot and acceptance contract.
- [x] Remove request-derived OTA origins and sensitive Python request/bind logs; add five OTA security tests.
- [x] Make manager binding codes atomic with a ten-minute TTL, enforce agent ownership and remove sensitive identifiers from debug logs.
- [x] Add a unique activation-consume lock token and Lua compare-and-delete release.
- [x] Make Java OTA fail closed, keep MQTT optional when WebSocket is configured, and pass nine targeted manager tests.
- [x] Remove the false `cute-v1` shortcut and build manager web.
- [x] Replace the mobile initialization flow with truthful six-language copy; pass `vue-tsc` and H5 build; retain the original product identity.
- [x] Add explicit Nezuko UI thinking interaction on STT completion and build version 2.2.6 from the current Linux path.
- [x] Fix and build Brookesia label lifetime, 17-icon capacity, bounds, reverse destruction and Linux instructions.
- [x] Build and deploy current Python and Web/API images; pass HTTP/TCP, configured-origin and OTA download smoke tests.
- [x] Identify the ESP32-S3, save a 32 MiB full-flash backup, flash 2.2.5 and observe boot/network/activation/idle evidence.
- [x] Publish Nezuko 2.2.6 to local non-production OTA for both the current and legacy transition board names.
- [x] Reconcile the 2026-08-05, 2026-08-10, Cute UI and Brookesia plan states.
- [ ] Restore device USB/power and install 2.2.6; repeat boot/network/bind/OTA/idle checks.
- [ ] Have a person complete one `listening → thinking → speaking → idle` voice turn.
- [ ] Have a person record all six Cute UI visual checks.

## Surprises and Discoveries

- Python OTA was already deployed but is not the active OTA route when `read_config_from_api=true`; Java manager OTA is the active trust boundary in this topology. Both modes were fixed because standalone Python mode remains supported.
- Manager API and web are one container, so replacing either necessarily causes one short shared interruption; database and Redis remain independent.
- Generic Jackson Redis values require JSON encoding. A raw cache edit produced a transient 500 and was immediately repaired with the expected encoded representation.
- The device originally preferred a stale MQTT gateway over the valid WebSocket route. MQTT was cleared so the response truthfully advertises WebSocket only; the health endpoint was corrected to accept either transport.
- The original 2.2.4/2.2.5 firmware reported the legacy 1.75 board name. A temporary dual OTA registration bridges it to the corrected 1.75C report name.
- Independent standards review found unsafe lock release, a host-local compose pin, and macOS-only Brookesia instructions; all three were corrected.
- Independent spec review found that network connecting was being used as the only thinking motion. Version 2.2.6 now switches the UI to thinking when STT completes.
- USB was available for identification, backup and the 2.2.5 flash, then disappeared before the 2.2.6 follow-up. This is a new physical blocker, not evidence that the earlier checks failed.

## Decision Log

- 2026-08-13: Treat `.225` as the current local-nonproduction trusted origin; never derive OTA URLs from Host, Forwarded headers or local interface discovery.
- 2026-08-13: Fail closed by preserving current firmware version and emitting the invalid download URL when trusted OTA configuration is absent.
- 2026-08-13: Keep Brookesia as built/deferred because visual controls have no real board callbacks.
- 2026-08-13: Scope mobile AC-05 to the initialization surface introduced by F-10/R-05. Repository-wide legacy mobile internationalization is a separate Q3 effort, not a hidden expansion of this delivery.
- 2026-08-13: Keep device transport state as listening during inference, but use an explicit UI interaction state driven by the STT protocol event; this avoids changing the transport state machine while making thinking real and testable.
- 2026-08-13: Bump the terminal-review firmware to 2.2.6 so a device on 2.2.5 cannot treat the new artifact as already current.
- 2026-08-13: Keep portable pullable images in the base compose and pin current local images in `docker-compose.local-secure.yml`.

## Outcomes and Retrospective

The software delivery is complete: all nine automated criteria pass, the current services are deployed, and both firmware targets build reproducibly on Linux. Hardware identification also passed. The release is not fully accepted because the current 2.2.6 artifact has not run on the board and no human completed the voice/visual observations. The acceptance contract therefore remains `in_progress` with HW-02 through HW-04 blocked.

The most important process correction was separating implemented, built, deployed and accepted. That prevented old binaries, healthy containers and the first 2.2.5 flash from masking terminal-review changes introduced afterward.

## Quality Delta

- Improved: trusted OTA origins in Python and Java; fail-closed behavior; sensitive-log removal; atomic code reservation; token-safe Redis lock release; ownership checks; truthful WebSocket-only transport; explicit UI thinking; type-safe mobile build; portable compose; reproducible Linux builds and regression tests.
- Introduced: a temporary legacy/current dual OTA registration for the 1.75-to-1.75C transition and local dated image tags in a dedicated override. Both are explicit, reversible operational compatibility layers.
- Deferred: F-17 activation enumeration/MAC validation and rate limiting (P2); the five full-suite Spring tests that require a hermetic database fixture; repository-wide legacy mobile i18n; Brookesia real quick-control callbacks; current device install plus human voice/visual checks.
- Evidence: Python tests 5/5; manager targeted tests 9/9; web/mobile builds; Nezuko and Brookesia builds and hashes; live image IDs; HTTP/TCP/OTA smoke; full-flash backup; 2.2.5 serial boot evidence; structured acceptance contract.

## Recovery and next action

- Service rollback tags: `xiaozhi-server-rollback:20260813-1109` and `xiaozhi-web-rollback:20260813-1109`.
- Device backup: `/home/luban/migration/esp-device-pre-2.2.5-20260813-1418.bin`.
- On device reconnection, install `/home/luban/codebase/aiot/esp32-nezuko/build-current/xiaozhi.bin`, verify 2.2.6 boot and OTA latest, then perform HW-03 and HW-04. Do not flash Brookesia as part of this acceptance.
