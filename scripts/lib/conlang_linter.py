"""PolyGlot Conlang Lexicon Importer, Phonotactic Linter & Glossary Compiler (`arcanum conlang-check`).

Bridges external conlang tools like PolyGlot (`.pgd` ZIP/XML dictionaries or raw `.xml` exports)
with Ars Arcanum's `Languages/` World Bible directory and `configs/plugins/speculative_naming/`.

Repository Target: `scripts/lib/conlang_linter.py`
Delegated natively to: `src.arcanum.worldbible.conlang`
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path if needed
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("conlang_linter", "lib.conlang_linter", "scripts.lib.conlang_linter"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.worldbible.conlang import (  # noqa: E402
    ConlangLexeme,
    ConlangViolation,
    PhonotacticSpec,
    audit_conlang_terms,
    compile_glossary_markdown,
    import_polyglot_lexicon,
    main,
    render_etymology_tree_svg,
    validate_word_phonotactics,
)

__all__ = [
    "ConlangLexeme",
    "ConlangViolation",
    "PhonotacticSpec",
    "audit_conlang_terms",
    "compile_glossary_markdown",
    "import_polyglot_lexicon",
    "main",
    "render_etymology_tree_svg",
    "validate_word_phonotactics",
]

if __name__ == "__main__":
    raise SystemExit(main())
