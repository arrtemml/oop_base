from bank_account_day1 import BankAccount, InvalidOperationError, InsufficientFundsError
from math import isfinite

class SavingsAccount(BankAccount):
    def __init__(self, owner, balance, min_balance, monthly_rate):
        if isinstance(min_balance, bool) or not isinstance(min_balance, (int, float)):
            raise InvalidOperationError("Минимальный остаток должен быть числом")

        if isinstance(min_balance, float) and not isfinite(min_balance):
            raise InvalidOperationError("Минимальный остаток должен быть конечным")

        if min_balance < 0:
            raise InvalidOperationError("Минимальный остаток не может быть отрицательным")


        if isinstance(monthly_rate, bool) or not isinstance(monthly_rate, (int, float)):
            raise InvalidOperationError("Месячная ставка должен быть числом")

        if isinstance(monthly_rate, float) and not isfinite(monthly_rate):
            raise InvalidOperationError("Месячная ставка должен быть конечным")

        if monthly_rate < 0:
            raise InvalidOperationError("Месячная ставка не может быть отрицательным")

        super().__init__(owner, balance)

        if self._balance < min_balance:
            raise InvalidOperationError("Начальный баланс ниже минимального остатка")

        self.min_balance = min_balance

        self.monthly_rate = monthly_rate

    def withdraw(self, amount):
        self._check_status()
        self._check_amount(amount)

        if self._balance - amount < self.min_balance:
            raise InvalidOperationError("Остаток будет ниже минимального")

        super().withdraw(amount)

    def apply_monthly_interest(self):
        self._check_status()
        interest = self._balance * self.monthly_rate
        self._balance = self._balance + interest

    def get_account_info(self):
        info = super().get_account_info()
        info["min_balance"] = self.min_balance
        info["monthly_rate"] = self.monthly_rate
        return info

    def __str__(self):
        return (
            f"SavingsAccount | Клиент: {self.owner} | "
            f"Номер: …{self.account_id[-4:]} | Статус: {self.status} | "
            f"Баланс: {self._balance} {self.currency} | "
            f"Минимум: {self.min_balance} | Ставка: {self.monthly_rate:.2%} в месяц"
        )

class PremiumAccount(BankAccount):
    def __init__(self, owner, balance, withdrawal_limit, overdraft_limit, withdrawal_fee):
        self._check_amount(withdrawal_limit)

        if isinstance(overdraft_limit, bool) or not isinstance(overdraft_limit, (int, float)):
            raise InvalidOperationError("Лимит оведрафта должен быть числом")

        if isinstance(overdraft_limit, float) and not isfinite(overdraft_limit):
            raise InvalidOperationError("Лимит оведрафта  должен быть конечным")

        if overdraft_limit < 0:
            raise InvalidOperationError("Лимит оведрафта не может быть отрицательным")

        if isinstance(withdrawal_fee, bool) or not isinstance(withdrawal_fee, (int, float)):
            raise InvalidOperationError("Фиксированная комиссия должен быть числом")

        if isinstance(withdrawal_fee, float) and not isfinite(withdrawal_fee):
            raise InvalidOperationError("Фиксированная комиссия должен быть конечным")

        if withdrawal_fee < 0:
            raise InvalidOperationError("Фиксированная комиссия не может быть отрицательным")


        super().__init__(owner, balance)

        self.withdrawal_limit = withdrawal_limit
        self.overdraft_limit = overdraft_limit
        self.withdrawal_fee = withdrawal_fee

    def withdraw(self, amount):
        self._check_status()
        self._check_amount(amount)

        if amount > self.withdrawal_limit:
            raise InvalidOperationError("Сумма превышает лимит снятия")

        total = amount + self.withdrawal_fee
        new_balance = self._balance - total

        if new_balance < -self.overdraft_limit:
            raise InsufficientFundsError("Превышен лимит овердрафта")

        self._balance = new_balance

    def get_account_info(self):
        info = super().get_account_info()
        info["withdrawal_limit"] = self.withdrawal_limit
        info["overdraft_limit"] = self.overdraft_limit
        info["withdrawal_fee"] = self.withdrawal_fee
        return info

    def __str__(self):
        return (
            f"PremiumAccount | Клиент: {self.owner} | Тип счета: Premium | "
            f"Номер: …{self.account_id[-4:]} | Статус: {self.status} | "
            f"Баланс: {self._balance} {self.currency} | "
            f"Лимит снятия: {self.withdrawal_limit} | Возможность овердрафта: {self.overdraft_limit}  | Комиссия:  {self.withdrawal_fee} "
        )

class InvestmentAccount(BankAccount):

    def __init__(self, owner, balance):
        super().__init__(owner, balance)
        self.portfolio = {
            "stocks": 0,
            "bonds": 0,
            "etf": 0,
        }

    def invest(self, asset_type, amount):
        if not isinstance(asset_type, str) or asset_type not in self.portfolio:
            raise InvalidOperationError("Недопустимый тип актива")
        super().withdraw(amount)
        self.portfolio[asset_type] += amount

    def project_yearly_growth(self, growth_rates):
        # self — конкретный счёт, growth_rates — переданный словарь ставок.

        total_growth = 0  # Начинаем с нуля. Сюда складываем прирост всех активов.

        for asset_type, invested_amount in self.portfolio.items():
            # Берём очередную пару из портфеля. На первом шаге это ("stocks", 600).
            # Python сам присваивает asset_type = "stocks" и invested_amount = 600.

            rate = growth_rates[asset_type]
            # По ключу "stocks" находим ставку 0.10, то есть 10%.

            total_growth += invested_amount * rate
            # Считаем 600 * 0.10 = 60 и прибавляем 60 к total_growth.

        return total_growth  # После всех шагов отдаём итог тому, кто вызвал метод.


    def withdraw(self, amount):
        """Снимает деньги с доступного баланса, сохраняя портфель."""
        super().withdraw(amount)


    def get_account_info(self):
        info = super().get_account_info()
        info["portfolio"] = self.portfolio.copy()
        return info

    def __str__(self):
        stocks = self.portfolio["stocks"]  # Берём сумму в акциях, например 600
        bonds = self.portfolio["bonds"]  # Берём сумму в облигациях, например 200
        etf = self.portfolio["etf"]  # Берём сумму в ETF, например 0

        return (
            f"Клиент: {self.owner} | Тип счета: InvestmentAccount | "
            f"Номер: …{self.account_id[-4:]} | Статус: {self.status} | "
            f"Баланс: {self._balance} {self.currency} | "
            f"Портфель: stocks {stocks} | bonds {bonds} | etf {etf}  "
        )


if __name__ == "__main__":
    savings_anna = SavingsAccount("Анна", 1000, min_balance=300, monthly_rate=0.02)
    savings_anna.withdraw(700)
    savings_anna.apply_monthly_interest()
    print(savings_anna)

    savings_ivan = SavingsAccount("Иван", 1000, min_balance=300, monthly_rate=0.03)
    try:
        savings_ivan.withdraw(701)
    except InvalidOperationError as error:
        print("Снятие отклонено:", error)
    print(savings_ivan)

    premium_olga = PremiumAccount(
        "Ольга", 1000, withdrawal_limit=10_000, overdraft_limit=500, withdrawal_fee=20
    )
    premium_olga.withdraw(1200)
    print(premium_olga)

    premium_pavel = PremiumAccount(
        "Павел", 1000, withdrawal_limit=10_000, overdraft_limit=500, withdrawal_fee=20
    )
    try:
        premium_pavel.withdraw(1481)
    except InsufficientFundsError as error:
        print("Снятие отклонено:", error)
    print(premium_pavel)

    rates = {"stocks": 0.10, "bonds": 0.04, "etf": 0.07}

    investment_anna = InvestmentAccount("Анна", 1000)
    investment_anna.invest("stocks", 600)
    investment_anna.invest("bonds", 200)
    investment_anna.withdraw(200)
    print(investment_anna)
    print(f"Годовой прирост Анны: {investment_anna.project_yearly_growth(rates):.2f} RUB")

    investment_ivan = InvestmentAccount("Иван", 500)
    investment_ivan.invest("etf", 300)
    try:
        investment_ivan.invest("stocks", 201)
    except InsufficientFundsError as error:
        print("Вложение отклонено:", error)
    print(investment_ivan)
    print(f"Годовой прирост Ивана: {investment_ivan.project_yearly_growth(rates):.2f} RUB")

    



