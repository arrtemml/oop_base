from uuid import uuid4
from abc import ABC, abstractmethod
from math import isfinite

class InsufficientFundsError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class AccountFrozenError(Exception):
    pass

class AccountClosedError(Exception):
    pass

class AbstractAccount(ABC):
    _used_ids = set()
    def __init__(self, owner, balance, status="active", account_id=None):
        if not isinstance(owner, str):
            raise InvalidOperationError("Имя владельца должно быть строкой")

        if not owner.strip():
            raise InvalidOperationError("Имя владельца не должно быть пустым")

        if isinstance(balance, bool) or not isinstance(balance, (int, float)):
            raise InvalidOperationError("Начальный баланс должен быть числом")

        if isinstance(balance, float) and not isfinite(balance):
            raise InvalidOperationError("Начальный баланс должен быть конечным числом")

        if balance < 0:
            raise ValueError("Начальный баланс не может быть отрицательным")

        if status not in ("active", "frozen", "closed"):
            raise InvalidOperationError("Неизвестный статус счёта")

        if account_id is None:
            account_id = uuid4().hex[:12]
            while account_id in AbstractAccount._used_ids:
                account_id = uuid4().hex[:12]
        else:
            if not isinstance(account_id, str):
                raise InvalidOperationError("Номер счёта должен быть строкой")

            if not account_id.strip():
                raise InvalidOperationError("Номер счёта не должен быть пустым")

            if account_id in AbstractAccount._used_ids:
                raise InvalidOperationError("Номер счёта уже используется")

        self.account_id = account_id
        AbstractAccount._used_ids.add(account_id)
        self.owner = owner
        self._balance = balance
        self.status = status
    @abstractmethod
    def deposit(self, amount):
        pass

    @abstractmethod
    def withdraw(self, amount):
        pass

    @abstractmethod
    def get_account_info(self):
        pass

class BankAccount(AbstractAccount):
    def __init__(self, owner, balance, status="active", currency="RUB", account_id=None):
        if currency not in ("RUB", "USD", "EUR", "KZT", "CNY"):
            raise InvalidOperationError("Неподдерживаемая валюта")

        super().__init__(
            owner=owner,
            balance=balance,
            status=status,
            account_id=account_id,
        )

        self.currency = currency

    def _check_status(self):
        if self.status == "frozen":
            raise AccountFrozenError("Счёт заморожен")
        if self.status == "closed":
            raise AccountClosedError ("Счет закрыт")

    def _check_amount(self, amount):
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise InvalidOperationError("Сумма должна быть числом")

        if isinstance(amount, float) and not isfinite(amount):
            raise InvalidOperationError("Сумма должна быть конечным числом")

        if amount <= 0:
            raise InvalidOperationError("Сумма должна быть больше нуля")

    def deposit(self, amount):
        self._check_status()
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise InvalidOperationError("Сумма должна быть числом")
        if isinstance(amount, float) and not isfinite(amount):
            raise InvalidOperationError("Сумма должна быть конечным числом")
        if amount <= 0:
            raise InvalidOperationError("Сумма должна быть больше нуля")

        self._balance = self._balance + amount

    def withdraw(self, amount):
        self._check_status()
        self._check_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError("Недостаточно денег")

        self._balance = self._balance - amount

    def get_balance(self):
        return self._balance

    def get_account_info(self):
        return {
            "owner": self.owner,
            "balance": self._balance,
            "status": self.status,
            "currency": self.currency,
            "account_id": self.account_id,
        }
    def __str__(self):
        return (
            f"BankAccount | Клиент: {self.owner} | "
            f"Номер: …{self.account_id[-4:]} | Статус: {self.status} | "
            f"Баланс: {self._balance} {self.currency}"
        )

if __name__ == "__main__":
    account = BankAccount("Анна", 1000)
    frozen_account = BankAccount("Иван", 500, status="frozen")

    account.deposit(500)
    account.withdraw(200)
    print(account)


    try:
        frozen_account.deposit(100)
    except AccountFrozenError as error:
        print("Пополнение отклонено:", error)

    try:
        frozen_account.withdraw(100)
    except AccountFrozenError as error:
        print("Снятие отклонено:", error)

    print(frozen_account)

