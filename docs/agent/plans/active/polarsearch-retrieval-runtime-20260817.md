# ExecPlan: PolarSearch Retrieval Runtime

This is a living plan. Keep it self-contained and update it whenever evidence or decisions change.

## Purpose

复用 `cyjdata-index` 已有的 PolarSearch 语义检索、重排和权限控制，为小智语音助手提供低延迟、可引用、可安全降级的检索层。先在本机完成实现与真实只读 smoke，再把同一候选部署到 ACK 非生产环境。

## Execution Mandate

- Autonomy profile: `nonprod-auto`; production read-only.
- Authoritative workspace: `/home/luban/codebase/aiot/xiaozhi-esp32-server`.
- Branch: `codex/polarsearch-retrieval-runtime`.
- In scope: production contract read-only inspection, local Harness, xiaozhi plugin, local verification, ACK nonprod deploy and smoke.
- Out of scope: production writes, raw PolarSearch credential replication, restricted entitlement bypass, router mutation, corpus ingestion.
- Acceptance contract path: `docs/agent/acceptance/active/polarsearch-retrieval-runtime-20260817.yaml`.
- Acceptance contract status: `in_progress`.
- Stop conditions: production mutation or secret weakening becomes required; conflicting writer appears.

## Progress

- [x] Milestone 1: inspect current workspace, ACK reachability and cyjdata production retrieval contract without exposing secrets.
- [x] Milestone 2: implement the local Retrieval Runtime and xiaozhi adapter.
- [x] Milestone 3: pass unit, contract, security and local container smoke checks.
- [ ] Milestone 4: deploy the immutable candidate to ACK nonprod and pass live smoke.
- [ ] Milestone 5: quality review, commit, push and close acceptance evidence.

## Current State

- Completed: production contract inspection; local Runtime, xiaozhi plugin and manager provider migration; 6 Runtime tests, 10 isolated plugin/security tests, disposable MySQL migration verification and real container smoke.
- In progress: immutable image publication and ACK nonprod deployment.
- Remaining: ACK nonprod smoke, final review, commit/push and acceptance closeout.
- Blocked by: public `117.186.231.98:80/443` still times out from ACK, but this does not block the HTTPS `data-admin.petsengine.cn` retrieval path.
- Next action: commit the locally accepted candidate, publish an immutable registry image and deploy only the new ACK nonprod resources.

## Surprises And Discoveries

- Finding: the production service already has mature product and entitlement-aware knowledge APIs.
  Evidence: `/api/v2/internal/ai/search` and `/api/v2/internal/ai/knowledge/search` running in `cyjdata-prod`.
  Impact on plan: the Harness becomes a small anti-corruption and latency boundary, not a second search implementation.
- Finding: product search is live but all three knowledge indices are absent and aggregate knowledge status reports zero documents.
  Evidence: read-only count/status probes on 2026-08-17.
  Impact on plan: product retrieval can be accepted now; knowledge must report degraded until a separate corpus-ingestion milestone.
- Finding: ACK still cannot reach the supplied public IP on 80/443 after the user reported port deployment.
  Evidence: TCP and HTTP probes from `chongyejia-dev` on 2026-08-17.
  Impact on plan: retain this as an independent network issue; do not couple it to Retrieval Runtime delivery.

## Decision Log

- Decision: local Runtime calls the existing HTTPS cyjdata-v2 API and never stores raw PolarSearch/MySQL credentials.
  Reason: preserves least privilege, model reuse, score thresholds, rerank behavior and entitlement boundary.
  Evidence: current production API contract and read-only smoke.
  Date: 2026-08-17.
- Decision: reject `restrictedKnowledge` at the Runtime public contract until a signed internal assertion integration is explicitly designed.
  Reason: a generic API key is not an entitlement authority.
  Evidence: production knowledge router signature verification.
  Date: 2026-08-17.

## Verification And Delivery

- Acceptance execution check: passed.
- Acceptance completion check: pending.
- Local tests: 6 Runtime tests and 10 isolated xiaozhi plugin/security tests pass; manager migration passed on disposable MySQL 9.6.
- Review: pending.
- Commit / push: pending.
- MR: pending.
- Pipeline: pending.
- Deploy: pending ACK nonprod only.
- Live smoke: product query pending; knowledge expected degraded until corpus exists.
- Human acceptance: pending later device conversation test; not required for service-level contract.

## Quality Baseline And Delta

- Existing reusable abstractions: cyjdata-v2 product and knowledge APIs; xiaozhi function registry; `httpx`.
- Generated/vendor boundaries: do not edit generated clients, database data, model binaries, role assets or production ConfigMaps.
- Protected delivery mode: no; normal bounded Q0/Q1 applies.
- Q0 completed: unsafe upstream reason forwarding, malformed list handling, image file permissions and non-executing smoke heredoc were found and fixed before acceptance.
- Q1 completed: persistent HTTP clients, bounded TTL cache, API-key file support, trusted-host allowlist, prompt-injection labeling and reversible manager provider migration.
- Q2 deferred or scheduled: Redis-backed shared cache and full observability may follow after local latency measurements.
- Q3 separate governance scope: production network topology and secret-management consolidation.
- Quality evidence: Ruff, 16 focused tests, real HTTPS contract probe, hardened container smoke, disposable MySQL idempotence/rollback test and git diff check.
- New debt introduced: none yet.

## Recovery And Idempotence

All local artifacts are isolated by branch and compose service. The Runtime is stateless and retries are bounded. ACK nonprod uses a separate namespace/config/secret and an immutable image tag; rollback is the previous Deployment image or deletion of only the new nonprod resources. Production resources are read-only.

## Outcomes And Retrospective

- Delivered: pending.
- Not delivered: knowledge corpus ingestion and public 80/443 connectivity are separate follow-ups.
- Evidence: pending.
- Follow-up: populate approved knowledge documents, then enable public knowledge retrieval and later design signed restricted-entitlement forwarding.
