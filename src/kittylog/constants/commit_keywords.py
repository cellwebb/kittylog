"""Keywords for categorizing commits."""


class CommitKeywords:
    """Keywords for categorizing commits."""

    FEATURE_KEYWORDS = ["feat:", "feature:", "add", "new", "implement", "introduce"]
    FIX_KEYWORDS = ["fix:", "bugfix:", "hotfix:", "fix", "bug", "issue", "problem", "error"]
    BREAKING_KEYWORDS = ["break:", "breaking:", "BREAKING CHANGE"]
    REMOVE_KEYWORDS = ["remove:", "delete:", "drop", "remove", "delete"]
    DEPRECATE_KEYWORDS = ["deprecate:", "deprecate"]
    SECURITY_KEYWORDS = ["security:", "sec:", "security", "vulnerability", "cve"]
    CHANGE_KEYWORDS = ["update", "change", "modify", "improve", "enhance", "refactor"]
