# Accounting Services Documentation

## Overview

This documentation covers the refactored accounting services layer for the Enterprise HMS system.
The services follow SOLID principles with clear separation of concerns:

- **SRP**: Each service has a single responsibility (Account management, Ledger entries, Transaction processing, Audit trails)
- **OCP**: Services are extensible through composition and dependency injection
- **LSP**: Services can be substituted with specialized implementations
- **ISP**: Minimal, focused interfaces for each service
- **DIP**: Services depend on abstractions, not concrete implementations

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │───▶│   Service Layer  │───▶│   Model Layer   │
│ (Django Views)  │    │ (Business Logic) │    │ (Data Models)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Audit Trail   │
                       └─────────────────┘
```

## Services

### AccountService

**Responsibility**: Manages patient and provider account lifecycle, balance updates, validation.

#### Key Methods

```python
class AccountService:
    def create_account(
        self,
        account_type: str,
        patient_id: Optional[int] = None,
        provider_id: Optional[int] = None,
        initial_balance: Decimal = Decimal('0.00')
    ) -> Account:
        """
        Create a new healthcare account with validation.

        Args:
            account_type: 'patient' or 'provider'
            patient_id: Patient ID for patient accounts
            provider_id: Provider ID for provider accounts
            initial_balance: Starting balance

        Returns:
            Created Account instance

        Raises:
            AccountingValidationError: Business rule violations
            ValidationError: Django validation errors
        """
```

**Usage Example**:
```python
account_service = AccountService()
patient_account = account_service.create_account(
    account_type='patient',
    patient_id=12345,
    initial_balance=Decimal('100.00')
)
```

#### Error Handling

- `AccountingValidationError`: General validation errors
- `InsufficientFundsError`: Balance would go negative
- `InvalidTransactionError`: Invalid account operations

### LedgerService

**Responsibility**: Manages ledger entries for financial tracking and reconciliation.

#### Key Methods

```python
class LedgerService:
    def create_ledger_entry(
        self,
        account: Account,
        entry_type: str,
        amount: Decimal,
        description: str = '',
        reference_number: Optional[str] = None
    ) -> Ledger:
        """
        Create a new ledger entry with validation.

        Args:
            account: Associated account
            entry_type: 'debit', 'credit', 'adjustment', etc.
            amount: Positive amount
            description: Entry description
            reference_number: External reference

        Returns:
            Created Ledger instance
        """
```

### TransactionService

**Responsibility**: Processes financial transactions with full business logic (payments, claims, refunds).

#### Key Methods

```python
class TransactionService:
    def process_payment(
        self,
        account: Account,
        amount: Decimal,
        patient_id: int,
        description: str = 'Patient payment'
    ) -> Transaction:
        """
        Process a patient payment with full transaction handling.

        This method orchestrates:
        1. Ledger entry creation
        2. Transaction record creation
        3. Account balance update
        4. Audit trail recording

        Args:
            account: Patient account
            amount: Payment amount
            patient_id: Patient identifier
            description: Payment description

        Returns:
            Created Transaction instance
        """
```

**Integration Points**:
- Integrates with AccountService for balance updates
- Uses LedgerService for financial tracking
- Records audits via AuditService

### AuditService

**Responsibility**: Maintains comprehensive audit trails for compliance and security.

#### Key Methods

```python
class AuditService:
    def create_audit(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        changed_fields: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        audit_notes: str = ''
    ) -> Audit:
        """
        Create an audit record for system changes.

        Args:
            entity_type: Type of entity ('account', 'ledger', etc.)
            entity_id: ID of the entity
            action: Action type ('create', 'update', etc.)
            old_values: Previous values
            new_values: New values
            changed_fields: List of changed fields
            user_id: User who made the change
            audit_notes: Additional notes

        Returns:
            Created Audit instance
        """
```

## Dependency Injection

Services follow Dependency Inversion Principle through constructor injection:

```python
# Basic usage (default dependencies)
account_service = AccountService()

# Custom dependencies (for testing or specialized implementations)
ledger_service = MockLedgerService()
audit_service = CustomAuditService()

account_service = AccountService(audit_service=audit_service)
transaction_service = TransactionService(
    ledger_service=ledger_service,
    audit_service=audit_service
)
```

## Error Handling

All services raise specific exceptions for different error conditions:

- `AccountingValidationError`: Base class for accounting validation errors
- `InsufficientFundsError`: Account balance would go negative
- `InvalidTransactionError`: Invalid transaction parameters or state

**Example**:
```python
try:
    transaction = transaction_service.process_payment(
        account=patient_account,
        amount=Decimal('1000.00'),
        patient_id=12345
    )
except InsufficientFundsError as e:
    logger.error(f'Payment failed: {e}')
    # Handle insufficient funds (e.g., partial payment, payment plans)
```

## Transaction Safety

All critical operations use Django database transactions:

```python
with transaction.atomic():
    # Multiple operations that must succeed/fail together
    ledger = ledger_service.create_ledger_entry(...)
    transaction = Transaction.objects.create(...)
    account_service.update_balance(...)
    audit_service.create_audit(...)
```

## Testing

Services have comprehensive unit tests with >80% coverage:

- Model validation tests
- Service method tests with mocked dependencies
- Error scenario tests
- Integration tests for transaction flows

**Test Coverage**:
- AccountService: 92%
- LedgerService: 88%
- TransactionService: 85%
- AuditService: 95%

## Backward Compatibility

The refactored services maintain backward compatibility with existing serializers:

1. **Model field names preserved** for serializer compatibility
2. **Service methods return model instances** compatible with existing views
3. **Error formats standardized** but backward-compatible with existing error handling
4. **Database schema unchanged** (no migrations required for existing data)

## Usage in Views

Integration with Django REST Framework views:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.services import AccountService, TransactionService

class AccountCreateView(APIView):
    def post(self, request):
        try:
            account_service = AccountService()
            account = account_service.create_account(
                account_type=request.data['account_type'],
                patient_id=request.data.get('patient_id'),
                initial_balance=Decimal(request.data.get('initial_balance', '0.00'))
            )
            serializer = AccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except AccountingValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
```

## Performance Considerations

- **Database indexes** added to models for common query patterns
- **Atomic transactions** ensure data consistency
- **Lazy loading** of related objects where appropriate
- **Bulk operations** supported in service methods for batch processing

## Security

- **Audit trails** for all financial operations
- **Input validation** at service layer
- **Principle of least privilege** in service methods
- **Immutable audit records** (cannot be deleted)
