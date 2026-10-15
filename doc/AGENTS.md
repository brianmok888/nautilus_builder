# Product specification knowledge base

## OVERVIEW
Primary Builder policy/specification set; retained distinct domain, measured structural score 0.

## WHERE TO LOOK
| Task | File | Meaning |
|---|---|---|
| Product identity | README.md | Naming and product boundaries |
| System behavior | nautilus_builder_spec.md | Main specification |
| Contributor limits | nautilus_builder_hardguards.md | Hard rules |
| Target layout | nautilus_builder_directory_architecture.md | Intended architecture |
| Lifecycle vocabulary | nautilus_builder_lifecycle_versioning.md | Canonical state terms |
| Repository boundaries | nautilus_builder_repo_dependency_architecture.md | Builder, engine and runtime roles |
| Planned delivery | nautilus_builder_implementation_plan.md | Plan, not completion evidence |
| Implementation prompts | nautilus_builder_implementation_prompts.md | Task guidance |

## CONVENTIONS
- Keep flat nautilus_builder_* snake_case filenames.
- Write declarative product policy rather than implementation tutorials.
- Frame integrations from Builder's side of the contract.
- Label target architecture separately from source-verified current layout.
- Check packages/, services/ and tests/ before describing implemented behavior.
- Keep the lifecycle terms aligned across specifications and validation models.
- Derived execution notes under docs/ do not supersede this policy set.

## ANTI-PATTERNS
- Do not describe planned paths as implemented modules.
- Do not weaken the rule that UX must not own runtime.
- Do not turn Builder policy into instructions to modify Daedalus.
- Do not replace domain package names with vague architectural labels.
- Do not cite an implementation prompt as proof that its work has shipped.
