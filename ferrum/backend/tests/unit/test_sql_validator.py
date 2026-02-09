import pytest
from app.ai.validators.sql_validator import SQLValidator, ValidationResult


@pytest.fixture
def validator():
    """Create SQLValidator instance."""
    return SQLValidator(cui_authorized=False)


@pytest.fixture
def cui_validator():
    """Create SQLValidator with CUI authorization."""
    return SQLValidator(cui_authorized=True)


class TestSQLValidator:
    """Test suite for SQL query validation."""

    def test_valid_select_query(self, validator):
        """Test that valid SELECT queries pass validation."""
        query = "SELECT id, name FROM suppliers WHERE org_id = :org_id LIMIT 10"
        result = validator.validate(query)
        assert result.is_valid
        assert result.sanitized_sql is not None
        assert "SELECT" in result.sanitized_sql.upper()

    def test_simple_select_with_limit_and_org(self, validator):
        """Test SELECT query with required org_id and LIMIT."""
        query = "SELECT name, material_type FROM materials WHERE org_id = :org_id LIMIT 5"
        result = validator.validate(query)
        assert result.is_valid

    def test_reject_insert_query(self, validator):
        """Test that INSERT queries are rejected."""
        query = "INSERT INTO suppliers (name) VALUES ('Acme Corp')"
        result = validator.validate(query)
        assert not result.is_valid
        assert any("SELECT" in e or "not allowed" in e.lower() for e in result.errors)

    def test_reject_update_query(self, validator):
        """Test that UPDATE queries are rejected."""
        query = "UPDATE suppliers SET name = 'New Name' WHERE id = 1"
        result = validator.validate(query)
        assert not result.is_valid
        assert any("SELECT" in e or "not allowed" in e.lower() for e in result.errors)

    def test_reject_delete_query(self, validator):
        """Test that DELETE queries are rejected."""
        query = "DELETE FROM suppliers WHERE id = 1"
        result = validator.validate(query)
        assert not result.is_valid
        assert any("SELECT" in e or "not allowed" in e.lower() for e in result.errors)

    def test_reject_drop_query(self, validator):
        """Test that DROP statements are rejected."""
        query = "DROP TABLE suppliers"
        result = validator.validate(query)
        assert not result.is_valid
        assert any("SELECT" in e or "not allowed" in e.lower() for e in result.errors)

    def test_reject_query_without_org_filter(self, validator):
        """Test that queries without org_id = :org_id filter are rejected."""
        query = "SELECT * FROM suppliers LIMIT 10"
        result = validator.validate(query)
        assert not result.is_valid
        assert any("org_id" in e.lower() for e in result.errors)

    def test_adds_limit_if_missing(self, validator):
        """Test that LIMIT is added to queries without one."""
        query = "SELECT * FROM suppliers WHERE org_id = :org_id"
        result = validator.validate(query)
        assert result.is_valid
        assert "LIMIT" in result.sanitized_sql.upper()

    def test_preserves_existing_limit(self, validator):
        """Test that existing LIMIT clause is preserved."""
        query = "SELECT * FROM suppliers WHERE org_id = :org_id LIMIT 50"
        result = validator.validate(query)
        assert result.is_valid
        assert "LIMIT 50" in result.sanitized_sql

    def test_reject_information_schema_access(self, validator):
        """Test that queries to information_schema are rejected."""
        query = "SELECT * FROM information_schema.tables WHERE org_id = :org_id"
        result = validator.validate(query)
        assert not result.is_valid
        assert any("information_schema" in e.lower() or "not allowed" in e.lower() for e in result.errors)

    def test_reject_pg_catalog_access(self, validator):
        """Test that queries to pg_catalog are rejected."""
        query = "SELECT * FROM pg_catalog.pg_tables WHERE org_id = :org_id"
        result = validator.validate(query)
        assert not result.is_valid

    def test_reject_table_not_in_whitelist(self, validator):
        """Test that queries to non-whitelisted tables are rejected."""
        query = "SELECT * FROM users WHERE org_id = :org_id LIMIT 10"
        result = validator.validate(query)
        assert not result.is_valid
        assert any("users" in e.lower() or "not allowed" in e.lower() for e in result.errors)

    def test_allow_whitelisted_tables(self, validator):
        """Test that all whitelisted tables are allowed."""
        for table in ["suppliers", "materials", "compliance_records", "prices"]:
            query = f"SELECT * FROM {table} WHERE org_id = :org_id LIMIT 10"
            result = validator.validate(query)
            assert result.is_valid, f"Table {table} should be allowed but got errors: {result.errors}"

    def test_reject_multiple_statements(self, validator):
        """Test that multiple statements in one query are rejected."""
        query = "SELECT * FROM suppliers; DROP TABLE suppliers;"
        result = validator.validate(query)
        assert not result.is_valid

    def test_case_insensitive_validation(self, validator):
        """Test that validation is case-insensitive for SQL keywords."""
        query = "select name from suppliers where org_id = :org_id limit 5"
        result = validator.validate(query)
        assert result.is_valid

    def test_cui_columns_blocked_without_authorization(self, validator):
        """Test that CUI columns are blocked for unauthorized users."""
        query = "SELECT name, cage_code FROM suppliers WHERE org_id = :org_id LIMIT 10"
        result = validator.validate(query)
        assert not result.is_valid
        assert any("cui" in e.lower() or "cage_code" in e.lower() for e in result.errors)

    def test_cui_columns_allowed_with_authorization(self, cui_validator):
        """Test that CUI columns are accessible with authorization."""
        query = "SELECT name, cage_code FROM suppliers WHERE org_id = :org_id LIMIT 10"
        result = cui_validator.validate(query)
        assert result.is_valid

    def test_validation_result_dataclass(self):
        """Test ValidationResult dataclass structure."""
        result = ValidationResult(is_valid=True, sanitized_sql="SELECT 1", errors=[])
        assert result.is_valid is True
        assert result.sanitized_sql == "SELECT 1"
        assert result.errors == []
