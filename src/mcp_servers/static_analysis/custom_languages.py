"""
Custom Language Loader for Tree-Sitter
=======================================

Loads custom tree-sitter grammars that are not included in tree-sitter-languages.
Currently supports:
- Smalltalk (Squeak variant)
- Smalltalk-Cincom (Cincom VisualWorks variant)

This module provides a unified interface similar to tree_sitter_languages.get_parser()
but includes custom-built grammars.
"""

import os
from pathlib import Path
from typing import Optional
from tree_sitter import Language, Parser


# Paths to custom grammar libraries
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BUILD_DIR = PROJECT_ROOT / "build"

# Custom language configurations
CUSTOM_LANGUAGES = {
    "smalltalk": {
        "library_path": BUILD_DIR / "tree-sitter-smalltalk" / "smalltalk.so",
        "language_name": "smalltalk",
        "variants": ["squeak", "pharo", "gnu-smalltalk"]
    },
    "smalltalk-cincom": {
        "library_path": BUILD_DIR / "tree-sitter-smalltalk" / "smalltalk.so",
        "language_name": "smalltalk",  # Same grammar, different entity extraction
        "variants": ["visualworks", "cincom"]
    }
}


class CustomLanguageLoader:
    """Loader for custom tree-sitter grammars"""

    def __init__(self):
        self._loaded_languages = {}
        self._parsers = {}

    def get_language(self, language: str) -> Optional[Language]:
        """
        Get a Language object for a custom grammar.

        Args:
            language: Language name (e.g., "smalltalk", "smalltalk-cincom")

        Returns:
            Language object or None if not available
        """
        # Return cached if already loaded
        if language in self._loaded_languages:
            return self._loaded_languages[language]

        # Check if it's a custom language
        if language not in CUSTOM_LANGUAGES:
            return None

        config = CUSTOM_LANGUAGES[language]
        library_path = config["library_path"]

        # Check if library exists
        if not library_path.exists():
            print(f"Warning: Custom language library not found: {library_path}")
            print(f"Run: python scripts/build_smalltalk_grammar.py")
            return None

        try:
            # Load the language
            lang = Language(str(library_path), config["language_name"])
            self._loaded_languages[language] = lang
            return lang

        except Exception as e:
            print(f"Error loading custom language {language}: {e}")
            return None

    def get_parser(self, language: str) -> Optional[Parser]:
        """
        Get a Parser configured for a custom grammar.

        Args:
            language: Language name

        Returns:
            Parser object or None if not available
        """
        # Return cached if already exists
        if language in self._parsers:
            return self._parsers[language]

        # Load the language
        lang = self.get_language(language)
        if not lang:
            return None

        # Create parser
        parser = Parser()
        parser.set_language(lang)

        # Cache and return
        self._parsers[language] = parser
        return parser

    def is_available(self, language: str) -> bool:
        """
        Check if a custom language is available.

        Args:
            language: Language name

        Returns:
            True if available, False otherwise
        """
        if language not in CUSTOM_LANGUAGES:
            return False

        config = CUSTOM_LANGUAGES[language]
        return config["library_path"].exists()

    def list_available(self) -> list[str]:
        """
        List all available custom languages.

        Returns:
            List of language names
        """
        available = []
        for lang in CUSTOM_LANGUAGES:
            if self.is_available(lang):
                available.append(lang)
        return available

    def get_variants(self, language: str) -> list[str]:
        """
        Get variant names for a language.

        Args:
            language: Language name

        Returns:
            List of variant names
        """
        if language in CUSTOM_LANGUAGES:
            return CUSTOM_LANGUAGES[language]["variants"]
        return []


# Global instance
_custom_loader = CustomLanguageLoader()


# Public API (similar to tree_sitter_languages)
def get_language(language: str) -> Optional[Language]:
    """Get a Language object for a custom grammar"""
    return _custom_loader.get_language(language)


def get_parser(language: str) -> Optional[Parser]:
    """Get a Parser configured for a custom grammar"""
    return _custom_loader.get_parser(language)


def is_available(language: str) -> bool:
    """Check if a custom language is available"""
    return _custom_loader.is_available(language)


def list_available() -> list[str]:
    """List all available custom languages"""
    return _custom_loader.list_available()


def get_variants(language: str) -> list[str]:
    """Get variant names for a language"""
    return _custom_loader.get_variants(language)


# Convenience function to check if language is custom
def is_custom_language(language: str) -> bool:
    """Check if a language is a custom (non-standard) language"""
    return language in CUSTOM_LANGUAGES
