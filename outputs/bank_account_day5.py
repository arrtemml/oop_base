from datetime import datetime, timedelta
from bank_account_day3 import Bank, Client
from bank_account_day4 import Transaction, TransactionProcessor

class AuditLog:
    def __init__(self, file_path):
        # Список (list) событий в памяти.
        self.events = []

        # Строка (str) с путём к файлу для событий.
        self.file_path = file_path

    def record(self, level, message, details=None):

        # Кортеж (tuple) содержит три разрешённых строковых значения.
        # not in проверяет, что level отсутствует среди них.
        if level not in ("info", "warning", "error"):
            raise ValueError("Неизвестный уровень важности")

        # {} создаёт словарь (dict) одного события.
        event = {
            "timestamp": datetime.now(),
            "level": level,
            "message": message,
            "details": details,
        }

        # append() добавляет весь словарь в конец списка.
        self.events.append(event)

        # open() открывает файл по сохранённому пути.
        # "a" — append: дописываем в конец, сохраняя предыдущие записи.
        # encoding="utf-8" позволяет записывать русский текст.
        with open(self.file_path, "a", encoding="utf-8") as file:
            # f-строка собирает поля события в одну текстовую строку.
            # \\n в строке — символ перехода на новую строку.
            # Включаем дополнительные данные в текстовую строку события.
            line = f"{event['timestamp']} | {level} | {message} | {event['details']}\n"

            # write() записывает строку в открытый файл.
            file.write(line)


    def filter_by_level(self, level):
        # [] создаёт пустой список (list) для подходящих событий.
        found_events = []

        # self.events — список (list) словарей (dict).
        # event по очереди получает один словарь события.
        for event in self.events:
            # ["level"] достаёт уровень из словаря по ключу.
            if event["level"] == level:
                # append() добавляет подходящий словарь в список.
                found_events.append(event)

        # Возвращаем результат после проверки всех событий.
        return found_events

    def get_suspicious_operations(self):
        # [] создаёт пустой список (list) для подходящих событий.
        suspicious = []

        # event — один словарь (dict) события из списка events.
        for event in self.events:
            # get() достаёт значение по ключу "details".
            details = event.get("details")

            # У обычного события details может быть None.
            if details is None:
                continue

            # В details храним словарь (dict).
            # Если ключа "risk_level" нет, get() вернёт None.
            if details.get("risk_level") in ("medium", "high"):
                suspicious.append(event)

        return suspicious

    def get_client_risk_events(self, client_id):
        # [] — пустой список (list) событий выбранного клиента.
        found_events = []

        # event — словарь (dict) одного события.
        for event in self.events:
            details = event.get("details")

            # Пропускаем события без дополнительных данных.
            if details is None:
                continue

            # Проверяем и ID клиента, и наличие оценки риска.
            if details.get("client_id") == client_id and details.get("risk_level") is not None:
                found_events.append(event)

        return found_events

    def get_client_risk_profile(self, client_id):
        # {} создаёт словарь (dict).
        # Ключ — уровень риска, значение — количество событий этого уровня.
        counts = {"low": 0, "medium": 0, "high": 0}

        # Получаем список (list) оценок риска только выбранного клиента.
        events = self.get_client_risk_events(client_id)

        # event — словарь (dict) одного события из этого списка.
        for event in events:
            # ["details"] достаёт вложенный словарь.
            # ["risk_level"] достаёт из него строку, например "medium".
            level = event["details"]["risk_level"]

            # Если level == "medium", увеличиваем counts["medium"] на 1.
            counts[level] += 1

        # Возвращаем словарь с ID клиента и подсчитанными уровнями.
        return {"client_id": client_id, "counts": counts}

    def get_error_statistics(self):
        # {} создаёт пустой словарь (dict).
        # Ключ — текст ошибки, значение — количество таких событий.
        counts = {}

        # Используем готовый метод: получаем список событий уровня error.
        errors = self.filter_by_level("error")

        for event in errors:
            # Достаём текст сообщения из словаря события.
            message = event["message"]

            # Если такой ошибки ещё нет в словаре, начинаем её счётчик с 0.
            if message not in counts:
                counts[message] = 0

            # Прибавляем одно событие с этим сообщением.
            counts[message] += 1

        return counts

class RiskAnalyzer:
    def __init__(self, large_amount_threshold=100_000):
        # Порог — число, с которым будем сравнивать сумму в рублях.
        self.large_amount_threshold = large_amount_threshold

        # {} создаёт пустой словарь (dict).
        # Ключ — ID клиента, значение — множество номеров его получателей.
        self.known_recipients = {}

        # {} создаёт пустой словарь (dict).
        # Ключ — ID клиента, значение — список (list) времени его операций.
        self.operation_times = {}

    def is_large_amount(self, amount_in_rub):
        # >= сравнивает сумму с порогом.
        # Результат — логическое значение (bool): True или False.
        return amount_in_rub >= self.large_amount_threshold

    def is_night(self, timestamp):
        # timestamp — объект datetime с датой и временем операции.
        # hour — целое число (int) от 0 до 23.
        return timestamp.hour < 5

    def is_new_recipient(self, client_id, recipient_id):
        # get() достаёт значение по ключу.
        # Если ключа нет, возвращает второй аргумент — пустое множество set().
        recipients = self.known_recipients.get(client_id, set())

        # not in проверяет, отсутствует ли номер в множестве.
        return recipient_id not in recipients

    def remember_recipient(self, client_id, recipient_id):
        # known_recipients — словарь (dict).
        # Если у клиента ещё нет записи, создаём для него множество (set).
        if client_id not in self.known_recipients:
            self.known_recipients[client_id] = set()

        # [client_id] достаёт множество получателей этого клиента.
        # add() добавляет номер. Повторный номер не создаёт дубликат.
        self.known_recipients[client_id].add(recipient_id)

    def remember_operation(self, client_id, timestamp):
        # operation_times — словарь (dict).
        # Если записи клиента ещё нет, создаём пустой список (list).
        if client_id not in self.operation_times:
            self.operation_times[client_id] = []

        # [client_id] достаёт список времени операций этого клиента.
        # append() добавляет объект datetime в конец списка.
        self.operation_times[client_id].append(timestamp)

    def is_frequent(self, client_id, timestamp):
        # timedelta — промежуток времени. Отступаем на минуту назад.
        window_start = timestamp - timedelta(minutes=1)

        # get() достаёт список (list) прошлых операций клиента.
        # Если клиента ещё нет в словаре, получаем пустой список [].
        times = self.operation_times.get(client_id, [])

        # Счётчик операций, попавших в последнюю минуту.
        count = 0

        for operation_time in times:
            # Учитываем время от начала окна до текущего момента включительно.
            if window_start <= operation_time <= timestamp:
                count += 1

        # Текущую операцию ещё не записали в историю, поэтому прибавляем 1.
        return count + 1 >= 5


    def analyze(self, client_id, recipient_id, amount_in_rub, timestamp):
        # [] — список (list) строк с причинами риска.
        reasons = []

        if self.is_large_amount(amount_in_rub):
            reasons.append("Крупная сумма")

        if self.is_frequent(client_id, timestamp):
            reasons.append("Частые операции")

        if self.is_new_recipient(client_id, recipient_id):
            reasons.append("Новый получатель")

        if self.is_night(timestamp):
            reasons.append("Ночная операция")

        # len() возвращает количество причин в списке.
        if len(reasons) >= 2:
            level = "high"
        elif len(reasons) == 1:
            level = "medium"
        else:
            level = "low"

        # Возвращаем словарь (dict) с оценкой и объяснением.
        return {"level": level, "reasons": reasons}


if __name__ == "__main__":
    # Задаём дневное время, чтобы банк разрешил финансовые операции.
    demo_time = datetime(2026, 11, 20, 12, 0)
    bank = Bank(clock=lambda: demo_time)

    # Создаём клиентов и регистрируем их в банке.
    bank.add_client(Client("Анна", "A", 25, {}, pin="0123"))
    bank.add_client(Client("Иван", "B", 25, {}, pin="1234"))

    # Создаём объекты счетов.
    sender = bank.open_account("A", 200_000)
    recipient = bank.open_account("B", 500)

    # Создаём журнал и анализатор.
    audit = AuditLog("audit_day5.log")
    analyzer = RiskAnalyzer()

    # Передаём обработчику ссылки на все необходимые объекты.
    processor = TransactionProcessor(
        bank,
        risk_analyzer=analyzer,
        audit_log=audit,
    )

    # range(2) выполняет тело цикла два раза.
    for _ in range(2):
        # Каждый раз создаём новую заявку с отдельным ID.
        transaction = Transaction(
            sender.account_id,
            recipient.account_id,
            200,
        )

        # Обработчик анализирует риск, записывает оценку и выполняет перевод.
        processor.process(transaction)
        print("Перевод:", transaction.status)

    # filter_by_level() возвращает список (list) подходящих событий.
    for event in audit.filter_by_level("warning"):
        # Достаём словарь (dict) с оценкой и печатаем его.
        print("Предупреждение:", event["details"])

    print("Баланс Анны:", sender.get_balance())  # 199600
    print("Баланс Ивана:", recipient.get_balance())  # 900



    # Открываем Ивану ещё один счёт. Для Анны этот номер пока новый.
    new_recipient = bank.open_account("B", 0)

    # Создаём заявку с двумя признаками риска.
    dangerous = Transaction(
        sender.account_id,
        new_recipient.account_id,
        100_000,
    )

    # Обработчик должен записать высокий риск и отклонить перевод.
    processor.process(dangerous)
    print("Опасный перевод:", dangerous.status, dangerous.failure_reason)

    # Выводим три отчёта, которые уже реализовали в AuditLog.
    print("Подозрительные операции:", audit.get_suspicious_operations())
    print("Риск-профиль Анны:", audit.get_client_risk_profile("A"))
    print("Статистика ошибок:", audit.get_error_statistics())

    # Проверяем, что заблокированный перевод не изменил балансы.
    print("Баланс Анны:", sender.get_balance())          # 199600
    print("Новый получатель:", new_recipient.get_balance())  # 0

