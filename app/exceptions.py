"""
Custom Exceptions for the Banking API.

Provides specific, meaningful exceptions for different error scenarios.
Each exception maps to appropriate HTTP status codes.
"""


class BankingException(Exception):
    """Base exception for all banking operations."""

    def __init__(self, message: str, status_code: int = 400):
        """
        Initialize banking exception.

        Args:
            message: Error message
            status_code: HTTP status code (default: 400)
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AccountNotFoundError(BankingException):
    """Raised when account is not found."""

    def __init__(self, account_number: str):
        message = f"Account '{account_number}' not found"
        super().__init__(message, status_code=404)


class CustomerNotFoundError(BankingException):
    """Raised when customer is not found."""

    def __init__(self, customer_id: int):
        message = f"Customer with ID {customer_id} not found"
        super().__init__(message, status_code=404)


class InsufficientBalanceError(BankingException):
    """Raised when account has insufficient balance for withdrawal."""

    def __init__(self, current_balance: float, requested_amount: float):
        message = (
            f"Insufficient balance. "
            f"Current: {current_balance}, Requested: {requested_amount}"
        )
        super().__init__(message, status_code=400)


class InvalidAmountError(BankingException):
    """Raised when transaction amount is invalid."""

    def __init__(self, amount: float):
        message = f"Invalid amount: {amount}. Amount must be greater than 0"
        super().__init__(message, status_code=400)


class InactiveAccountError(BankingException):
    """Raised when account is not in ACTIVE state for operations."""

    def __init__(self, account_number: str, status: str):
        message = (
            f"Account '{account_number}' is not active. "
            f"Current status: {status}"
        )
        super().__init__(message, status_code=400)


class ClosedAccountError(BankingException):
    """Raised when trying to operate on a closed account."""

    def __init__(self, account_number: str):
        message = f"Account '{account_number}' is closed and cannot be used"
        super().__init__(message, status_code=400)


class BlockedAccountError(BankingException):
    """Raised when account is blocked."""

    def __init__(self, account_number: str):
        message = f"Account '{account_number}' is blocked"
        super().__init__(message, status_code=403)


class FrozenAccountError(BankingException):
    """Raised when account is frozen."""

    def __init__(self, account_number: str):
        message = f"Account '{account_number}' is frozen"
        super().__init__(message, status_code=403)


class InvalidTransactionError(BankingException):
    """Raised when transaction parameters are invalid."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class TransferNotAllowedError(BankingException):
    """Raised when transfer between accounts is not allowed."""

    def __init__(self, reason: str):
        message = f"Transfer not allowed: {reason}"
        super().__init__(message, status_code=400)


class SameAccountTransferError(BankingException):
    """Raised when trying to transfer to the same account."""

    def __init__(self):
        message = "Cannot transfer to the same account"
        super().__init__(message, status_code=400)


class DuplicateTransactionError(BankingException):
    """Raised when transaction reference is duplicate."""

    def __init__(self, reference_number: str):
        message = f"Transaction with reference '{reference_number}' already exists"
        super().__init__(message, status_code=409)


class TransactionFailedError(BankingException):
    """Raised when transaction processing fails."""

    def __init__(self, reason: str):
        message = f"Transaction failed: {reason}"
        super().__init__(message, status_code=400)
