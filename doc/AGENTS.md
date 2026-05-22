# AGENTS

## Scope
- `doc/` is the source-truth Builder spec set.
- Keep it policy-oriented: roles, hard rules, allowed/forbidden behavior, target architecture.

## Highest-value files
- `README.md`: product naming rule.
- `nautilus_builder_spec.md`: main system spec.
- `nautilus_builder_hardguards.md`: strongest contributor constraints.
- `nautilus_builder_directory_architecture.md`: target repo layout, not current files.
- `nautilus_builder_lifecycle_versioning.md`: canonical lifecycle terms.
- `nautilus_builder_repo_dependency_architecture.md`: Builder ↔ NautilusTrader ↔ Daedalus boundary.

## Conventions
- Keep flat `nautilus_builder_*` filenames.
- Prefer declarative policy prose over tutorial prose.
- Prefer Builder-side framing even when discussing Daedalus integration.

## Do not
- Do not describe planned paths as already implemented.
- Do not weaken `UX must not own runtime`.
- Do not turn Builder docs into Daedalus implementation instructions.
- Do not rename domain packages into vague labels.
