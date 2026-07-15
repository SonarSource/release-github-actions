# Decisions

* [golden-architecture](golden-architecture.md) - actions as a public API; `@master` on master, frozen SHA on `v1`.
* [vault-blocks-per-action](vault-blocks-per-action.md) - why Vault credential retrieval stays inline per action.
* [env-var-injection-guard](env-var-injection-guard.md) - no user-controlled input interpolated directly into `run:` blocks.
* [pin-external-actions](pin-external-actions.md) - external actions pinned to a full commit SHA, never a tag.
* [architecture-review-2026-07](architecture-review-2026-07.md) - the 2026-07-14 review of the automated-release orchestrator; links to all findings under [risks/](../risks/).
