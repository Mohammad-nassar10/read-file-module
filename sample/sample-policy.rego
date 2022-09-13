package dataapi.authz

rule[{"action": {"name": "FilterFiles"}}] {
    input.context.role == "manager"
    input.resource.metadata.tags.finance
}
