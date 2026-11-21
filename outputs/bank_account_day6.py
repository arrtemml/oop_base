from datetime import datetime

from bank_account_day3 import Bank, Client

from bank_account_day4 import Transaction, TransactionQueue, TransactionProcessor
from bank_account_day5 import AuditLog, RiskAnalyzer


if __name__ == "__main__":
    # Заданное время позволяет повторять демонстрацию с одинаковыми условиями.
    demo_time = datetime(2026, 11, 21, 12, 0)
    bank = Bank(clock=lambda: demo_time)

    # [] — список (list). Каждый его элемент — отдельный объект Client.
    clients = [
        Client("Анна Иванова", "C001", 25, {}, pin="0123"),
        Client("Иван Петров", "C002", 30, {}, pin="1234"),
        Client("Ольга Смирнова", "C003", 35, {}, pin="2345"),
        Client("Павел Соколов", "C004", 40, {}, pin="3456"),
        Client("Мария Волкова", "C005", 28, {}, pin="4567"),
    ]

    # for по очереди присваивает client каждый объект из списка.
    for client in clients:
        bank.add_client(client)

    # len() считает количество записей в словаре клиентов банка.
    print("Клиентов в банке:", len(bank.clients))  # 5

    # {} — словарь (dict). Ключ — удобное имя, значение — объект счёта.
    accounts = {}

    accounts["anna_regular"] = bank.open_account("C001", 200_000)
    accounts["anna_savings"] = bank.open_account(
        "C001", 50_000, account_type="savings",
        min_balance=10_000, monthly_rate=0.02,
    )

    accounts["ivan_regular"] = bank.open_account("C002", 30_000)
    accounts["ivan_investment"] = bank.open_account(
        "C002", 20_000, account_type="investment",
    )

    accounts["olga_regular"] = bank.open_account("C003", 40_000)
    accounts["olga_premium"] = bank.open_account(
        "C003", 10_000, account_type="premium",
        withdrawal_limit=50_000, overdraft_limit=5_000, withdrawal_fee=20,
    )

    accounts["pavel_regular"] = bank.open_account("C004", 25_000)
    accounts["pavel_savings"] = bank.open_account(
        "C004", 15_000, account_type="savings",
        min_balance=5_000, monthly_rate=0.01,
    )

    accounts["maria_regular"] = bank.open_account("C005", 35_000)
    accounts["maria_premium"] = bank.open_account(
        "C005", 5_000, account_type="premium",
        withdrawal_limit=30_000, overdraft_limit=3_000, withdrawal_fee=10,
    )

    print("Счетов в банке:", len(bank.accounts))  # 10

    # Список заявок и выбор следующей заявки.
    queue = TransactionQueue()

    # Журнал событий в памяти и файле.
    audit = AuditLog("audit_day6.log")

    # История клиентов и оценка риска переводов.
    analyzer = RiskAnalyzer()

    # Передаём обработчику уже созданные объекты.
    processor = TransactionProcessor(
        bank,
        risk_analyzer=analyzer,
        audit_log=audit,
    )

    # [] создаёт список (list) направлений переводов.
    # Каждый элемент — кортеж (tuple) с именами двух счетов.
    routes = [
        ("anna_regular", "ivan_regular"),
        ("ivan_regular", "olga_regular"),
        ("olga_regular", "pavel_regular"),
        ("pavel_regular", "maria_regular"),
        ("maria_regular", "anna_regular"),
    ]

    # Кортеж (tuple) из шести сумм.
    # Малые суммы — обычные переводы, 0 и -50 — ошибочные,
    # крупные суммы помогут проверить риск и нехватку денег.
    amounts = (100, 200, 0, -50, 100_000, 1_000_000)

    # Внешний цикл выбирает одну сумму.
    for amount in amounts:
        # Внутренний цикл создаёт пять переводов с этой суммой.
        for sender_name, recipient_name in routes:
            # По ключам достаём объекты счетов из словаря accounts.
            sender = accounts[sender_name]
            recipient = accounts[recipient_name]

            transaction = Transaction(
                sender.account_id,
                recipient.account_id,
                amount,
            )
            queue.add(transaction)

            # Записываем добавление каждой заявки в журнал.
            audit.record(
                "info",
                "Транзакция добавлена в очередь",
                details={
                    "transaction_id": transaction.transaction_id,
                    "sender_id": transaction.sender_id,
                    "recipient_id": transaction.recipient_id,
                    "amount": transaction.amount,
                },
            )

    # 6 сумм × 5 направлений = 30 заявок.
    print("Заявок в очереди:", len(queue.transactions))  # 30

    while True:
        # Получаем следующую готовую заявку.
        transaction = queue.get_next(now=demo_time)

        # None означает, что готовых заявок больше нет.
        if transaction is None:
            break

        # Обработчик выполнит перевод или запишет причину отказа.
        processor.process(transaction)

        if transaction.status == "completed":
            # Фиксируем успешное исполнение.
            audit.record(
                "info",
                "Транзакция выполнена",
                details={
                    "transaction_id": transaction.transaction_id,
                    "sender_id": transaction.sender_id,
                    "recipient_id": transaction.recipient_id,
                    "amount": transaction.amount,
                },
            )

        # Ошибки обработчик уже записывает в аудит.
        # Здесь показываем результат каждой заявки на экране.
        print(
            transaction.amount,
            transaction.status,
            transaction.failure_reason,
        )

        # ID клиента, чьи счета хотим посмотреть.
        selected_client_id = "C001"

        # [] после имени словаря достаёт объект клиента по его ID.
        selected_client = bank.clients[selected_client_id]
        print("Счета клиента:", selected_client.full_name)

        # search_accounts() возвращает список (list) объектов счетов клиента.
        for account in bank.search_accounts(selected_client_id):
            # print() вызывает __str__() соответствующего типа счёта.
            print(account)

        # selected_client — объект Анны, выбранный выше.
        # account_ids — список (list) номеров её счетов.
        client_account_ids = selected_client.account_ids

        print("История переводов:", selected_client.full_name)

        # Перебираем объекты Transaction, сохранённые в очереди.
        for transaction in queue.transactions:
            # Проверяем, принадлежит ли Анне счёт отправителя или получателя.
            if (
                    transaction.sender_id in client_account_ids
                    or transaction.recipient_id in client_account_ids
            ):
                print(
                    transaction.transaction_id,
                    transaction.amount,
                    transaction.currency,
                    transaction.status,
                    transaction.failure_reason,
                )

        print("Подозрительные операции")

        # Получаем список (list) событий со средним или высоким риском.
        suspicious = audit.get_suspicious_operations()

        # event — словарь (dict) одного события аудита.
        for event in suspicious:
            # По ключу "details" достаём вложенный словарь.
            details = event["details"]

            print(
                details["transaction_id"],
                details["client_id"],
                details["risk_level"],
                details["reasons"],
            )

        print("Количество подозрительных операций:", len(suspicious))

        print("Топ-3 клиентов по балансу")

        # get_clients_ranking() возвращает список (list) словарей (dict),
        # уже отсортированный от большей суммы к меньшей.
        ranking = bank.get_clients_ranking()

        # [:3] берёт первые три элемента списка.
        for row in ranking[:3]:
            # row — словарь с данными одного клиента.
            print(row["full_name"], row["total_balance"])

        print("Общий баланс банка:", bank.get_total_balance())

        # {} создаёт словарь (dict).
        # Ключ — статус, значение — количество заявок с этим статусом.
        statistics = {}

        # Перебираем все объекты Transaction из списка очереди.
        for transaction in queue.transactions:
            status = transaction.status

            # Если такой статус встретился впервые, создаём счётчик.
            if status not in statistics:
                statistics[status] = 0

            # Увеличиваем счётчик текущего статуса на 1.
            statistics[status] += 1

        print("Статистика транзакций:", statistics)
        print("Всего транзакций:", len(queue.transactions))