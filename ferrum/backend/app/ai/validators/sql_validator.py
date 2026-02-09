"""SQL query validation and sanitization.

Dependencies:
    Requires sqlparse package: pip install sqlparse
"""

import logging
import re
from dataclasses import dataclass

try:
    import sqlparse
    from sqlparse.sql import Identifier, IdentifierList, Token
    from sqlparse.tokens import Keyword, DML
except ImportError:
    raise ImportError(
        "sqlparse is required for SQL validation. Install with: pip install sqlparse"
    )

logger = logging.getLogger(__name__)


# Whitelist of allowed tables
ALLOWED_TABLES = {
    "suppliers",
    "materials",
    "material_categories",
    "capabilities",
    "certifications",
    "supplier_capabilities",
    "supplier_certifications",
    "supplier_materials",
    "prices",
    "compliance_records",
}

# CUI (Controlled Unclassified Information) columns that require authorization
CUI_COLUMNS = {
    "suppliers": ["cage_code", "sam_uei", "duns_number"],
    "compliance_records": ["notes", "audit_findings"],
}


@dataclass
class ValidationResult:
    """Result of SQL validation."""

    is_valid: bool
    sanitized_sql: str | None
    errors: list[str]


class SQLValidator:
    """Validates and sanitizes generated SQL queries."""

    def __init__(self, cui_authorized: bool = False):
        """Initialize the SQL validator.

        Args:
            cui_authorized: Whether the user is authorized to access CUI data
        """
        self.cui_authorized = cui_authorized

    def validate(self, sql: str) -> ValidationResult:
        """Validate a SQL query.

        Args:
            sql: SQL query to validate

        Returns:
            ValidationResult with validation status, sanitized SQL, and errors
        """
        errors = []

        try:
            # Parse the SQL
            parsed = sqlparse.parse(sql)

            if not parsed:
                return ValidationResult(
                    is_valid=False,
                    sanitized_sql=None,
                    errors=["Empty or invalid SQL statement"],
                )

            statement = parsed[0]

            # Check 1: Only SELECT statements allowed
            if not self._is_select_statement(statement):
                errors.append(
                    "Only SELECT statements are allowed. "
                    "DDL/DML operations (INSERT, UPDATE, DELETE, DROP, ALTER) are forbidden."
                )
                return ValidationResult(
                    is_valid=False, sanitized_sql=None, errors=errors
                )

            # Check 2: No semicolons (single statement only)
            if sql.count(";") > 1 or (sql.count(";") == 1 and not sql.rstrip().endswith(";")):
                errors.append("Multiple statements not allowed")

            # Check 3: No subqueries to information_schema or pg_catalog
            if self._has_system_schema_access(sql):
                errors.append(
                    "Access to information_schema and pg_catalog is not allowed"
                )

            # Check 4: Table whitelist validation
            tables = self._extract_tables(statement)
            invalid_tables = [t for t in tables if t not in ALLOWED_TABLES]
            if invalid_tables:
                errors.append(
                    f"Invalid tables referenced: {', '.join(invalid_tables)}. "
                    f"Allowed tables: {', '.join(sorted(ALLOWED_TABLES))}"
                )

            # Check 5: CUI column access validation
            if not self.cui_authorized:
                cui_violations = self._check_cui_access(sql, tables)
                if cui_violations:
                    errors.append(
                        f"Unauthorized access to CUI columns: {', '.join(cui_violations)}"
                    )

            # Check 6: Ensure LIMIT clause exists (add if missing)
            sanitized_sql = self._ensure_limit(sql)

            # Check 7: Verify org_id filter exists
            if not self._has_org_id_filter(sql):
                errors.append(
                    "Query must include org_id filter for multi-tenant security"
                )

            # If there are errors, return invalid
            if errors:
                return ValidationResult(
                    is_valid=False,
                    sanitized_sql=None,
                    errors=errors,
                )

            # All checks passed
            logger.info("SQL validation passed")
            return ValidationResult(
                is_valid=True,
                sanitized_sql=sanitized_sql,
                errors=[],
            )

        except Exception as e:
            logger.error(f"SQL validation error: {e}")
            return ValidationResult(
                is_valid=False,
                sanitized_sql=None,
                errors=[f"Validation error: {str(e)}"],
            )

    def _is_select_statement(self, statement) -> bool:
        """Check if statement is a SELECT query."""
        for token in statement.tokens:
            if token.ttype is DML and token.value.upper() == "SELECT":
                return True
        return False

    def _has_system_schema_access(self, sql: str) -> bool:
        """Check for access to system schemas."""
        sql_lower = sql.lower()
        return "information_schema" in sql_lower or "pg_catalog" in sql_lower

    def _extract_tables(self, statement) -> set[str]:
        """Extract table names from SQL statement."""
        tables = set()

        def extract_from_identifier(identifier):
            """Extract table name from identifier."""
            name = str(identifier).split()[-1]  # Get last part (table name)
            # Remove aliases and clean up
            name = name.split()[0] if " " in name else name
            # Remove quotes if present
            name = name.strip('"').strip("'").strip("`")
            return name

        # Look for FROM and JOIN clauses
        from_seen = False
        for token in statement.tokens:
            if token.ttype is Keyword and token.value.upper() in ("FROM", "JOIN"):
                from_seen = True
            elif from_seen:
                if isinstance(token, Identifier):
                    table = extract_from_identifier(token)
                    tables.add(table)
                    from_seen = False
                elif isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        table = extract_from_identifier(identifier)
                        tables.add(table)
                    from_seen = False
                elif token.ttype is not Keyword and not token.is_whitespace:
                    # Single table name
                    table = str(token).strip().split()[0]
                    table = table.strip('"').strip("'").strip("`")
                    tables.add(table)
                    from_seen = False

        return tables

    def _check_cui_access(self, sql: str, tables: set[str]) -> list[str]:
        """Check for unauthorized CUI column access."""
        violations = []

        for table in tables:
            if table in CUI_COLUMNS:
                for cui_column in CUI_COLUMNS[table]:
                    # Simple pattern matching for column references
                    # Matches: table.column or just column (if table is in FROM)
                    pattern = rf"\b({table}\.{cui_column}|{cui_column})\b"
                    if re.search(pattern, sql, re.IGNORECASE):
                        violations.append(f"{table}.{cui_column}")

        return violations

    def _ensure_limit(self, sql: str) -> str:
        """Ensure SQL has a LIMIT clause, add if missing."""
        sql_upper = sql.upper()

        # Check if LIMIT already exists
        if "LIMIT" in sql_upper:
            return sql

        # Add LIMIT 100 before any trailing semicolon
        sql = sql.rstrip()
        if sql.endswith(";"):
            return sql[:-1] + " LIMIT 100;"
        else:
            return sql + " LIMIT 100"

    def _has_org_id_filter(self, sql: str) -> bool:
        """Check if query includes org_id filter."""
        # Look for org_id in WHERE clause
        return re.search(r"\borg_id\s*=\s*:org_id\b", sql, re.IGNORECASE) is not None
