# API Endpoints Version 5.5

All endpoints are available under `/api` because `backend/main.py` registers the router with the API prefix.

## Governance

- `GET/POST /api/governance/categories`
- `GET/POST /api/governance/policies`
- `GET/POST /api/governance/policy-versions`
- `GET/POST /api/governance/exceptions`
- `GET/POST /api/governance/acknowledgements`

## SOP

- `GET/POST /api/sops`
- `GET/POST /api/sop-steps`
- `GET /api/sops/{sop_id}/steps`

## Workflows

- `GET/POST /api/workflows/templates`
- `GET/POST /api/workflows/stages`
- `GET/POST /api/workflows/instances`
- `GET/POST /api/workflows/tasks`
- `POST /api/workflows/instances/{record_id}/actions/{action}`

## Approvals

- `GET/POST /api/approvals/matrix`
- `GET/POST /api/approvals/requests`
- `GET/POST /api/approvals/actions`
- `POST /api/approvals/requests/{request_id}/actions/{action}`

## Events, Audit, SLA, IAM, Compliance, Risk, KPI

- `GET/POST /api/events`
- `GET/POST /api/audit/logs`
- `GET/POST /api/sla/policies`
- `GET/POST /api/sla/instances`
- `POST /api/sla/policies/{policy_id}/start`
- `GET/POST /api/escalations`
- `GET/POST /api/iam/access-profiles`
- `GET/POST /api/iam/access-reviews`
- `GET/POST /api/compliance/controls`
- `GET/POST /api/risk/register`
- `GET/POST /api/kpis`
- `GET/POST /api/kpis/results`
- `GET/POST /api/corrective-actions`

## Platform

- `GET /api/automation/resources`
- `GET /api/automation/dashboard`
- `POST /api/automation/seed`

Resource endpoints also support `GET /{id}`, `PUT /{id}`, and `DELETE /{id}` for record retrieval, update, and soft delete.
