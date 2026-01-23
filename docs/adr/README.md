# Architecture Decision Records (ADR)

This folder contains Architecture Decision Records (ADRs) for the CSAT Guardian project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences. ADRs help teams:

- Understand why decisions were made
- Onboard new team members quickly
- Avoid revisiting settled discussions
- Track the evolution of the system

## ADR Template

When creating a new ADR, use this template:

```markdown
# ADR NNNN: Title

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXXX]

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?
```

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-azure-government-cloud.md) | Azure Government Cloud Selection | Accepted | 2026-01-23 |
| [0002](0002-key-vault-secrets-management.md) | Azure Key Vault for Secrets Management | Accepted | 2026-01-23 |
| [0003](0003-azure-container-apps-hosting.md) | Azure Container Apps for Application Hosting | Accepted | 2026-01-23 |

## Creating a New ADR

1. Copy the template above
2. Number sequentially (e.g., `0004-descriptive-title.md`)
3. Fill in all sections
4. Submit via PR for team review
5. Update this README index

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [Michael Nygard's ADR Article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
