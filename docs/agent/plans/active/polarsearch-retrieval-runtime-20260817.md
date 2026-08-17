# ExecPlan: PolarSearch Retrieval Runtime

This is a living plan. Keep it self-contained and update it whenever evidence or decisions change.

## Purpose

复用 `cyjdata-index` 已有的 PolarSearch 语义检索、重排和权限控制，为小智语音助手提供低延迟、可引用、可安全降级的检索层。先在本机完成实现与真实只读 smoke，再把同一候选部署到 ACK 非生产环境。

## Execution Mandate

- Autonomy profile: `nonprod-auto`; production read-only.
- Authoritative workspace: `/home/luban/codebase/aiot/xiaozhi-esp32-server`.
- Branches: `codex/polarsearch-retrieval-runtime` and `codex/retrieval-ack-closeout`.
- In scope: production contract read-only inspection, local Harness, xiaozhi plugin, local verification, ACK nonprod deploy and smoke.
- Out of scope: production writes, raw PolarSearch credential replication, restricted entitlement bypass, router mutation, corpus ingestion.
- Acceptance contract path: `docs/agent/acceptance/active/polarsearch-retrieval-runtime-20260817.yaml`.
- Acceptance contract status: `passed`.
- Stop conditions: production mutation or secret weakening becomes required; conflicting writer appears.

## Progress

- [x] Milestone 1: inspect current workspace, ACK reachability and cyjdata production retrieval contract without exposing secrets.
- [x] Milestone 2: implement the local Retrieval Runtime and xiaozhi adapter.
- [x] Milestone 3: pass unit, contract, security and local container smoke checks.
- [x] Milestone 4: deploy the immutable candidate to ACK nonprod and pass live smoke.
- [x] Milestone 5: quality review, commit, push and close acceptance evidence.

## Current State

- Completed: production contract inspection; local Runtime, xiaozhi plugin and manager provider migration; 7 Runtime tests, 11 isolated plugin/security tests, disposable MySQL migration verification, real local container smoke and ACK nonprod deployment.
- In progress: none for the service-level acceptance contract.
- Remaining: approved knowledge-corpus ingestion and device-level conversational use are separate follow-ups.
- Blocked by: none for Retrieval Runtime delivery. Public `117.186.231.98:80/443` still times out from ACK, but the Runtime uses the independent HTTPS `data-admin.petsengine.cn` path.
- Next action: configure the xiaozhi ACK consumer with the mounted retrieval token when that consumer is deployed; then ingest approved public knowledge documents.

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
- Finding: the ACK CNI accepted a request from a Pod excluded by the standard NetworkPolicy selector.
  Evidence: live negative probe on 2026-08-17 reached the ClusterIP before application authentication was added.
  Impact on plan: NetworkPolicy remains defense in depth, while a Secret-mounted application token is now the effective authorization boundary and unauthenticated retrieval returns HTTP 401.
- Finding: a first-time GHCR pull took 15m56s on an ACK node and a second node encountered a blob CDN TLS handshake timeout.
  Evidence: Kubernetes pull events for the Debian and Alpine candidates.
  Impact on plan: the default image was reduced from 134 MiB to 63 MiB locally, the ACK progress deadline was extended to 20 minutes, and the already cached authenticated candidate was retained for final smoke.

## Decision Log

- Decision: local Runtime calls the existing HTTPS cyjdata-v2 API and never stores raw PolarSearch/MySQL credentials.
  Reason: preserves least privilege, model reuse, score thresholds, rerank behavior and entitlement boundary.
  Evidence: current production API contract and read-only smoke.
  Date: 2026-08-17.
- Decision: reject `restrictedKnowledge` at the Runtime public contract until a signed internal assertion integration is explicitly designed.
  Reason: a generic API key is not an entitlement authority.
  Evidence: production knowledge router signature verification.
  Date: 2026-08-17.
- Decision: require `X-Retrieval-Token` in addition to ClusterIP and NetworkPolicy.
  Reason: the live cluster did not enforce the standard NetworkPolicy negative case; the upstream API key alone must not authorize arbitrary in-cluster callers.
  Evidence: unauthenticated ACK request returns 401 and an authorized consumer Pod returns three product results.
  Date: 2026-08-17.

## Verification And Delivery

- Acceptance execution check: passed.
- Acceptance completion check: passed.
- Local tests: 7 Runtime tests and 11 isolated xiaozhi plugin/security tests pass; manager migration passed on disposable MySQL 9.6; final local product-plus-public-knowledge smoke returned four items in 755 ms.
- Review: adversarial negative probes found and closed the missing application-auth boundary; source formatting, lint and diff checks pass.
- Commit / push: feature commits merged through PRs 15 and 16; ACK/auth closeout is tracked by PR 17.
- MR: GitHub PR 17 is the durable delivery record; GitHub remains authoritative for its merge state.
- Pipeline: GitHub Actions run 32031005592 passed; the immutable authenticated Alpine candidate was additionally published after local verification.
- Deploy: ACK `chongyejia-dev`, ClusterIP only, image `retrieval_48f1757a935999a5ab36f86bb72b22d8de18f06a`, digest `sha256:86e4d3c9805b3f4f98255eec97651bc7fcbe33862e981da36fe9ad94de4e2929`.
- Live smoke: Ready with zero restarts; unauthenticated request returns 401; authorized Service-path smoke returns three products, and a measured live query completed in 592 ms with `degraded=false`.
- Human acceptance: later device conversation testing is not required for this service-level contract.

## Quality Baseline And Delta

- Existing reusable abstractions: cyjdata-v2 product and knowledge APIs; xiaozhi function registry; `httpx`.
- Generated/vendor boundaries: do not edit generated clients, database data, model binaries, role assets or production ConfigMaps.
- Protected delivery mode: no; normal bounded Q0/Q1 applies.
- Q0 completed: unsafe upstream reason forwarding, malformed list handling, image file permissions and non-executing smoke heredoc were found and fixed before acceptance.
- Q1 completed: persistent HTTP clients, bounded TTL cache, API-key/token file support, application-layer authentication, trusted-host allowlist, prompt-injection labeling, smaller Alpine image, extended pull deadline and reversible manager provider migration.
- Q2 deferred or scheduled: Redis-backed shared cache and full observability may follow after local latency measurements.
- Q3 separate governance scope: production network topology and secret-management consolidation.
- Quality evidence: Ruff, 18 focused tests, real HTTPS contract probe, hardened container smoke, application-auth negative smoke, authorized ACK Service smoke, disposable MySQL idempotence/rollback test and git diff check.
- New debt introduced: cross-border GHCR cold-pull latency remains an operational constraint; it is bounded by the 20-minute progress deadline and does not affect an already-running replica.

## Recovery And Idempotence

All local artifacts are isolated by branch and compose service. The Runtime is stateless and retries are bounded. ACK nonprod uses a separate namespace/config/secret and an immutable image tag; rollback is `kubectl rollout undo deployment/xiaozhi-retrieval-runtime -n chongyejia-dev` or removal of only these new nonprod resources. Production resources remained read-only.

## Outcomes And Retrospective

- Delivered: provider-neutral Retrieval Runtime, xiaozhi function adapter, manager provider migration, local hardened container path, authenticated ACK nonprod Deployment/Service/Secret boundary and live product retrieval.
- Not delivered: knowledge corpus ingestion, device-level agent enablement and public 80/443 connectivity are separate follow-ups.
- Evidence: acceptance contract `passed`; PRs 15, 16 and 17; workflow run 32031005592; immutable image digest and ACK live-smoke results above.
- Follow-up: populate approved knowledge documents, then enable public knowledge retrieval and later design signed restricted-entitlement forwarding.
