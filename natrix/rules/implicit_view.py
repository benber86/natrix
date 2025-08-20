from __future__ import annotations

from typing import TYPE_CHECKING

from natrix.rules.common import BaseRule, RuleRegistry, _get_staticcall_function_mutability

if TYPE_CHECKING:
    from natrix.ast_node import FunctionDefNode


@RuleRegistry.register
class ImplicitViewRule(BaseRule):
    """
    Implicit View Decorator Check

    Detect when view functions are missing the '@view' decorator.
    """

    CODE = "NTX4"
    MESSAGE = "Function '{}' reads contract state but is not marked as 'view'."

    def __init__(self) -> None:
        super().__init__(
            severity="style",
            code=self.CODE,
            message=self.MESSAGE,
        )

    def visit_FunctionDef(self, node: FunctionDefNode) -> None:
        if (
            node.is_constructor
            or "view" in node.modifiers
            or "pure" in node.modifiers
            or node.is_from_interface
        ):
            return

        accesses = node.memory_accesses
        read = any(access.type == "read" for access in accesses)
        write = any(access.type == "write" for access in accesses)
        extcalls = node.get_descendants(node_type="ExtCall")
        staticcalls = node.get_descendants(node_type="StaticCall")

        # Check if all staticcalls are to pure functions
        # If so, this should be handled by the implicit_pure rule instead
        if staticcalls:
            all_pure = True
            for staticcall in staticcalls:
                mutability = _get_staticcall_function_mutability(staticcall)
                if mutability != "pure":
                    all_pure = False
                    break
            
            # If all staticcalls are pure, let implicit_pure handle this
            if all_pure:
                return

        if read and not (write or extcalls):
            self.add_issue(node, node.get("name"))
