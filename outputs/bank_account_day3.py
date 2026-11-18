from bank_account_day1 import BankAccount
from bank_account_day2 import InvestmentAccount, PremiumAccount, SavingsAccount
from datetime import datetime

class Client:
    def __init__(self, full_name, client_id, age, contacts, pin, status="active"):
        if age < 18:
            raise ValueError("Клиенту должно быть не меньше 18 лет")
        self.full_name = full_name
        self.client_id = client_id
        self.age = age
        self.contacts = contacts
        self.status = status
        self.account_ids = []
        self._pin = pin  # Строка (str) с учебным PIN клиента.
        self.failed_attempts = 0

class Bank:
    def __init__(self, clock=datetime.now):
        # Сохраняем функцию и вызываем её при каждой проверке.
        self._clock = clock
        self.clients = {}
        self.accounts = {}
        self.suspicious_events = []

    def get_total_balance(self):
        # total — переменная с общей суммой. Начинаем с целого числа (int) 0.
        total = 0

        # self.accounts — словарь (dict): номер счёта → объект счёта.
        # values() даёт значения словаря, то есть сами объекты счетов.
        for account in self.accounts.values():
            # != означает «не равно». Закрытые счета пропускаем.
            if account.status != "closed":
                # += прибавляет баланс текущего счёта к общей сумме.
                total += account.get_balance()

        # return стоит после цикла, чтобы вернуть сумму по всем счетам.
        return total

    def get_clients_ranking(self):
        # [] создаёт пустой список (list) для строк рейтинга.
        ranking = []

        # self.clients — словарь (dict). values() даёт объекты Client.
        for client in self.clients.values():
            # Для каждого клиента начинаем считать заново с нуля.
            total = 0

            # search_accounts() возвращает список (list) счетов клиента.
            for account in self.search_accounts(client.client_id):
                if account.status != "closed":
                    total += account.get_balance()

            # {} создаёт словарь (dict) с данными одного клиента.
            # append() добавляет этот словарь в конец списка.
            ranking.append({
                "client_id": client.client_id,
                "full_name": client.full_name,
                "total_balance": total,
            })

        ranking.sort(key=lambda row: row["total_balance"], reverse=True)

        return ranking

        return ranking

    def _check_operation_time(self):
        now = self._clock()

        # now.hour — целое число (int) от 0 до 23.
        if now.hour < 5:
            raise ValueError("Операции недоступны с 00:00 до 05:00")



    def add_client(self, client):
        if client.client_id in self.clients:
            raise ValueError("Клиент с таким ID уже есть")

        self.clients[client.client_id] = client

    def open_account(self, client_id, balance, *, account_type="regular", **account_options):

        self._check_operation_time()


        # Открываем счета только клиентам, которые уже добавлены в банк.
        if client_id not in self.clients:
            raise ValueError("Клиент с таким ID не найден")

        # Находим клиента по ID и создаём счёт на его имя.
        client = self.clients[client_id]
        account_types = {
            "regular": BankAccount,
            "savings": SavingsAccount,
            "premium": PremiumAccount,
            "investment": InvestmentAccount,
        }
        if account_type not in account_types:
            raise ValueError("Неизвестный тип счёта")

        account_class = account_types[account_type]
        account = account_class(client.full_name, balance, **account_options)
        account._operation_time_check = self._check_operation_time

        # Банк сохраняет сам счёт, а клиент получает его номер в свой список.
        self.accounts[account.account_id] = account
        client.account_ids.append(account.account_id)

        # Отдаём созданный счёт, чтобы вызывающий код мог сразу им пользоваться.
        return account

    def freeze_account(self, account_id):

        self._check_operation_time()
        # Проверяем, что банк знает счёт с таким номером.
        if account_id not in self.accounts:
            raise ValueError("Счёт с таким номером не найден")

        # Достаём из словаря сам объект счёта.
        account = self.accounts[account_id]

        # Заморозка разрешена только для активного счёта.
        if account.status != "active":
            raise ValueError("Заморозить можно только активный счёт")

        account.status = "frozen"


    def unfreeze_account(self, account_id):
        self._check_operation_time()
        # Проверяем, что банк знает счёт с таким номером.
        if account_id not in self.accounts:
            raise ValueError("Счёт с таким номером не найден")

        # Достаём из словаря сам объект счёта.
        account = self.accounts[account_id]

        # Разморозка разрешена только для замороженного счёта.
        if account.status != "frozen":
            raise ValueError("Разморозить можно только замороженный счёт")

        account.status = "active"


    def close_account(self, account_id):
        self._check_operation_time()
        # Проверяем, что банк знает счёт с таким номером.
        if account_id not in self.accounts:
            raise ValueError("Счёт с таким номером не найден")

        # Достаём из словаря сам объект счёта.
        account = self.accounts[account_id]

        # Закрыть можно только открытый счёт.
        if account.status == "closed":
            raise ValueError("Закрыть можно только открытый счёт")


        # Закрыть можно только счёт при нулевом балансе.
        if account.get_balance() != 0:
            raise ValueError("Закрыть можно только счёт при нулевом балансе")


        account.status = "closed"



    def search_accounts(self, client_id):
        # self.clients — словарь (dict): ID клиента → объект Client.
        # not in проверяет, что такого ключа в словаре нет.
        if client_id not in self.clients:
            raise ValueError("Клиент с таким ID не найден")

        # Квадратные скобки после имени словаря достают значение по ключу.
        # Например, self.clients["C001"] вернёт объект Анны.
        client = self.clients[client_id]

        # [] создаёт пустой список (list).
        # В этом списке будут сами объекты счетов.
        found_accounts = []

        # client.account_ids — список (list) номеров счетов клиента.
        # for по очереди записывает каждый номер в переменную account_id.
        for account_id in client.account_ids:
            # self.accounts — словарь (dict): номер счёта → объект счёта.
            # [account_id] достаёт объект по номеру, который сейчас в переменной.
            account = self.accounts[account_id]

            # append() — метод списка. Он добавляет объект в конец списка.
            found_accounts.append(account)

        # return стоит после цикла и возвращает весь список.
        # Если у клиента нет счетов, цикл пропускается и вернётся [].
        return found_accounts

    def authenticate_client(self, client_id, pin):
        # self.clients — словарь (dict). Оператор in проверяет его ключи.
        if client_id not in self.clients:
            return False

        # Квадратные скобки достают объект Client по ключу client_id.
        client = self.clients[client_id]

        # == сравнивает строки. Заблокированному клиенту сразу отказываем.
        if client.status == "blocked":
            return False

        # При верном PIN обнуляем счётчик и разрешаем вход.
        if pin == client._pin:
            client.failed_attempts = 0
            return True

        # += 1 увеличивает счётчик клиента на единицу.
        client.failed_attempts += 1

        # >= означает «больше или равно». На третьей ошибке блокируем клиента.
        if client.failed_attempts >= 3:
            client.status = "blocked"
            # {} создаёт словарь (dict) с данными одного события.
            # append() добавляет этот словарь в конец списка.
            self.suspicious_events.append({
                "client_id": client_id,
                "reason": "Три неверные попытки входа подряд",
            })



        # Текущая попытка была неверной, поэтому отказываем во входе.
        return False


if __name__ == "__main__":
    # datetime(год, месяц, день, час, минута) задаёт время для примера.
    demo_time = datetime(2026, 11, 15, 12, 0)
    anna = Client("Анна Иванова", "C001", 25, {"email": "anna@example.com"}, "0123")
    print(anna.full_name)    # Анна Иванова
    print(anna.account_ids)  # []

    bank = Bank(clock=lambda: demo_time)
    print(bank.clients)  # {}

    bank.add_client(anna)
    print(bank.authenticate_client("C001", "0123"))  # True
    print(bank.authenticate_client("C001", "9999"))  # False
    print(bank.authenticate_client("C999", "0123"))  # False
    print(bank.clients["C001"].full_name)  # Анна Иванова

    account = bank.open_account("C001", 1000)
    print(account.status)
    print(account)           # Счёт Анны с балансом 1000
    print(anna.account_ids)  # Список с номером этого счёта

    bank.freeze_account(account.account_id)
    print(account.status)  # frozen

    bank.unfreeze_account(account.account_id)
    print(account.status)  # active

    account.withdraw(1000)

    bank.close_account(account.account_id)
    print(account.status)

    # Открываем Анне второй счёт с начальным балансом 500.
    bank.open_account("C001", 500)

    # Метод возвращает список (list) из двух объектов счетов.
    accounts = bank.search_accounts("C001")

    # for берёт по одному объекту счёта из списка accounts.
    for found_account in accounts:
        # print() использует __str__() счёта, чтобы показать его данные.
        print(found_account)

    # Создаём второго клиента и открываем ему счёт.
    ivan = Client("Иван Петров", "C002", 30, {"phone": "555-0102"}, pin="5678")
    bank.add_client(ivan)
    bank.open_account("C002", 300)

    # У Анны уже была одна ошибка выше. Верный PIN сбрасывает счётчик.
    bank.authenticate_client("C001", "0123")

    # range(1, 4) даёт числа 1, 2, 3. Правая граница 4 не включается.
    for attempt in range(1, 4):
        # result — значение типа bool. False означает, что во входе отказано.
        result = bank.authenticate_client("C001", "9999")
        print(f"Попытка {attempt}: вход = {result}, статус Анны = {anna.status}")

    # Проверяем вход с верным PIN для каждого клиента.
    print("Вход Анны с верным PIN:", bank.authenticate_client("C001", "0123"))
    print("Вход Ивана с верным PIN:", bank.authenticate_client("C002", "5678"))

    # suspicious_events — список (list) словарей (dict) с событиями.
    print("Подозрительные события:", bank.suspicious_events)
