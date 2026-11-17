from uuid import uuid4
from datetime import datetime
from bank_account_day1 import AccountClosedError, AccountFrozenError, InvalidOperationError, InsufficientFundsError
from bank_account_day2 import PremiumAccount
from bank_account_day3 import Bank, Client

class ExchangeRateUnavailableError(InvalidOperationError):
    pass

class Transaction:
    def __init__(self, sender_id, recipient_id, amount, currency="RUB", priority=0, scheduled_at=None, is_external=False):
        # sender_id и recipient_id — строки (str) с номерами счетов.
        self.sender_id = sender_id
        self.recipient_id = recipient_id

        # Сумма и валюта, которые указали при создании заявки.
        self.amount = amount
        self.currency = currency

        # uuid4() создаёт UUID, а .hex даёт его строковую запись (str).
        self.transaction_id = uuid4().hex

        # "transfer" — тип операции: перевод между счетами.
        self.transaction_type = "transfer"

        # "pending" — начальный статус: заявка ждёт обработки.
        self.status = "pending"

        # Комиссию рассчитает обработчик. Начальное значение — 0.
        self.fee = 0

        # None означает, что причины отказа пока нет.
        self.failure_reason = None

        # datetime.now() возвращает текущую дату и местное время компьютера.
        self.created_at = datetime.now()

        # None означает, что обработка ещё не завершилась.
        self.processed_at = None

        self.priority = priority
        self.scheduled_at = scheduled_at
        self.is_external = is_external

        # int — целое число. Новую заявку ещё ни разу не обрабатывали.
        self.attempts = 0

        # bool — логическое значение. У новой заявки ещё не было отказа.
        self.can_retry = False


class TransactionQueue:
    def __init__(self):
        # [] создаёт пустой список (list). У каждой очереди свой список.
        self.transactions = []

    def add(self, transaction):
        # transaction — объект Transaction, созданный ранее.
        # append() добавляет этот объект в конец списка.
        self.transactions.append(transaction)

    def get_next(self, now=None):
        # now — время, на которое проверяем готовность заявок.
        # None означает, что берём текущее время компьютера.

        if now is None:
            now = datetime.now()

        # Пока не нашли ни одной готовой заявки.
        next_transaction = None

        # self.transactions — список (list) объектов Transaction.
        for transaction in self.transactions:
            # Если время запуска задано и оно ещё не наступило,
            # continue пропускает эту заявку и переходит к следующей.
            if transaction.scheduled_at is not None and transaction.scheduled_at > now:
                continue

            # continue переходит к следующей заявке.
            if transaction.status != "pending":
                continue

            # Первая готовая заявка становится кандидатом.
            # Дальше заменяем её, только если найдём больший приоритет.
            if next_transaction is None or transaction.priority > next_transaction.priority:
                next_transaction = transaction

        # Вернём выбранную заявку или None, если готовых заявок нет.
        return next_transaction

    def cancel(self, transaction_id):
        # self.transactions — список (list) объектов Transaction.
        for transaction in self.transactions:
            # == сравнивает ID текущей заявки с ID, который нам передали.
            if transaction.transaction_id == transaction_id:
                # Отменить можно только заявку, которая ждёт обработки.
                if transaction.status != "pending":
                    raise ValueError("Отменить можно только ожидающую заявку")

                transaction.status = "cancelled"
                return  # Завершаем метод после успешной отмены.

        # Сюда доходим после цикла, если ни один ID не совпал.
        raise ValueError("Транзакция с таким ID не найдена")


class TransactionProcessor:
    def __init__(self, bank):
        # bank — объект Bank из Дня 3. Сохраняем ссылку на него.
        self.bank = bank

        # {} создаёт словарь (dict). Ключ — пара валют, значение — курс.
        # ("RUB", "USD") — кортеж (tuple): из какой валюты и в какую.
        self.exchange_rates = {
            ("RUB", "USD"): 0.01,
            ("USD", "RUB"): 100,
        }



    def _find_account(self, account_id):
        # self.bank.accounts — словарь (dict): номер → объект счёта.
        # Оператор in проверяет ключи словаря, то есть номера.
        if account_id not in self.bank.accounts:
            raise ValueError("Счёт с таким номером не найден")

        # Квадратные скобки достают объект счёта по ключу account_id.
        return self.bank.accounts[account_id]

    def process(self, transaction):

        if transaction.status != "pending":
            return

        # += 1 прибавляет единицу к счётчику этой заявки.
        transaction.attempts += 1

        try:
            # По двум номерам (str) получаем два объекта счёта.
            sender = self._find_account(transaction.sender_id)
            recipient = self._find_account(transaction.recipient_id)
            # Проверяем статус у каждого из двух объектов счёта.
            sender._check_status()
            recipient._check_status()
            # Проверяем сумму из заявки. При ошибке Python перейдёт в except.
            sender._check_amount(transaction.amount)

            # isinstance() проверяет, относится ли объект sender к PremiumAccount.
            # and требует выполнения обоих условий: баланс ниже нуля
            # и отправитель не относится к премиальному типу счёта.
            if sender.get_balance() < 0 and not isinstance(sender, PremiumAccount):
                raise InvalidOperationError(
                    "Перевод при отрицательном балансе доступен только премиум-счёту"
                )

            # Сумма заявки должна быть указана в валюте счёта отправителя.
            if sender.currency != transaction.currency:
                raise InvalidOperationError(
                    "Валюта перевода должна совпадать с валютой счёта отправителя"
                )

            # Считаем, сколько получатель получит в валюте своего счёта.
            # Если курса нет, ошибка возникнет до списания денег.
            amount_to_deposit = self._convert(
                transaction.amount, transaction.currency, recipient.currency
            )

            # is_external — логическое значение (bool).
            # Для внешнего перевода комиссия 20, для внутреннего 0.
            if transaction.is_external:
                fee = 20
            else:
                fee = 0

            # Сумма списания включает перевод и комиссию.
            total_to_withdraw = transaction.amount + fee

            # Запоминаем баланс на случай, если зачисление отклонится.
            sender_balance_before = sender.get_balance()
            sender.withdraw(total_to_withdraw)

            try:
                recipient.deposit(amount_to_deposit)
            except InvalidOperationError:
                # Возвращаем точный исходный баланс, включая возможную комиссию снятия.
                sender._balance = sender_balance_before
                raise  # Передаём ту же ошибку во внешний except.

        except (ValueError, AccountFrozenError, AccountClosedError, InvalidOperationError, InsufficientFundsError) as error:
            # error — объект пойманного исключения.
            # str(error) превращает его сообщение в строку.
            transaction.status = "failed"
            transaction.failure_reason = str(error)
            transaction.processed_at = datetime.now()
            # isinstance() вернёт True, если пойманная ошибка означает отсутствие курса.
            transaction.can_retry = isinstance(error, ExchangeRateUnavailableError)
            return






        # Пока только показываем, кого нашли. Списание добавим позже.
        print(sender.owner, "→", recipient.owner)

        transaction.status = "completed"
        transaction.fee = fee
        transaction.processed_at = datetime.now()

    def retry(self, transaction):
        # != означает «не равно». Повторяем только заявки со статусом failed.
        if transaction.status != "failed":
            return

        # not меняет True на False и наоборот.
        # Если can_retry равно False, завершаем метод.
        if not transaction.can_retry:
            return

        # attempts — число уже выполненных попыток.
        if transaction.attempts >= 2:
            return

        # process() принимает только заявки со статусом pending.
        # Готовим ту же заявку к новой попытке.
        transaction.status = "pending"
        transaction.failure_reason = None
        transaction.processed_at = None
        transaction.can_retry = False

        # process() сам увеличит attempts и запишет новый результат.
        self.process(transaction)

    def _convert(self, amount, from_currency, to_currency):
        # Если валюты совпадают, возвращаем исходную сумму.
        if from_currency == to_currency:
            return amount

        # Круглые скобки создают кортеж (tuple) из двух валют.
        # Например, ("RUB", "USD") — ключ в словаре курсов.
        pair = (from_currency, to_currency)

        # not in проверяет, отсутствует ли этот ключ в словаре (dict).
        if pair not in self.exchange_rates:
            raise ExchangeRateUnavailableError("Курс для этой пары валют не найден")

        # Квадратные скобки достают курс по ключу pair.
        rate = self.exchange_rates[pair]

        # * умножает сумму на курс. return возвращает результат.
        return amount * rate

if __name__ == "__main__":
    # Фиксируем время, чтобы открытие счетов прошло вне ночного запрета.
    demo_time = datetime(2026, 11, 17, 12, 0)
    bank = Bank()
    bank.add_client(Client("Анна", "A", 25, {}, pin="0123"))
    bank.add_client(Client("Иван", "B", 25, {}, pin="1234"))
    sender = bank.open_account("A", 1000, now=demo_time)
    recipient = bank.open_account("B", 500, now=demo_time)

    queue = TransactionQueue()
    processor = TransactionProcessor(bank)

    # Добавляем обычную, срочную и заведомо ошибочную заявку.
    queue.add(Transaction(sender.account_id, recipient.account_id, 200))
    queue.add(Transaction(sender.account_id, recipient.account_id, 100, priority=5))
    queue.add(Transaction(sender.account_id, recipient.account_id, -50))
    frozen = bank.open_account("B", 0, now=demo_time)
    bank.freeze_account(frozen.account_id, now=demo_time)

    # 4. Внешний перевод: Анна платит 50 + 20 комиссии.
    queue.add(Transaction(sender.account_id, recipient.account_id, 50, is_external=True))

    # 5–7. Три причины отказа: не хватает денег, счёт не найден, счёт заморожен.
    queue.add(Transaction(sender.account_id, recipient.account_id, 5000))
    queue.add(Transaction(sender.account_id, "unknown", 10))
    queue.add(Transaction(sender.account_id, frozen.account_id, 10))

    # 8. Сохраняем объект заявки в переменной, чтобы отменить её по ID.
    cancelled = Transaction(sender.account_id, recipient.account_id, 30)
    queue.add(cancelled)
    queue.cancel(cancelled.transaction_id)

    # 9. Заявка назначена на 13:00. Цикл пока проверяет очередь на 12:00.
    later = datetime(2026, 11, 17, 13, 0)
    delayed = Transaction(sender.account_id, recipient.account_id, 40, scheduled_at=later)
    queue.add(delayed)

    # 10. Меняем счета местами: теперь Иван отправляет Анне 25.
    queue.add(Transaction(recipient.account_id, sender.account_id, 25))

    while True:
        # get_next() возвращает готовую заявку или None.
        transaction = queue.get_next(now=demo_time)
        if transaction is None:
            break  # Выходим из цикла, когда готовых заявок больше нет.

        processor.process(transaction)
        print(transaction.amount, transaction.status, transaction.failure_reason)

    print(sender.get_balance(), recipient.get_balance())

    # later — объект datetime, в котором задано 13:00.
    # Спрашиваем очередь, какая заявка готова к этому времени.
    next_transaction = queue.get_next(now=later)

    # None означает, что очередь не нашла готовую заявку.
    if next_transaction is not None:
        processor.process(next_transaction)
        print(next_transaction.amount, next_transaction.status)

    print(sender.get_balance(), recipient.get_balance())