# -*- coding: utf-8 -*-
"""
Валидатор email-адресов с использованием регулярных выражений.
Итоговая работа по курсу "Python-разработчик с использованием инструментов ИИ".
Кейс 9.

Запуск:  python email_validator.py
"""

import json
import os
import re
import sys
from datetime import datetime

HISTORY_FILE = "history.json"

# ---------------------------------------------------------------------------
# Эталонное регулярное выражение
# ---------------------------------------------------------------------------
# Структура адреса: локальная_часть @ домен . зона
EMAIL_PATTERN = re.compile(
    r"^"                        # начало строки
    r"[A-Za-z0-9._%+-]+"        # локальная часть: буквы, цифры, . _ % + -
    r"@"                        # обязательный символ @ (ровно один)
    r"(?:[A-Za-z0-9-]+\.)+"     # доменные имена через точку: example. sub.
    r"[A-Za-z]{2,6}$"           # зона: только буквы, длина 2-6
)


def check_email(address):
    """
    Проверяет один email-адрес.

    Возвращает кортеж (is_valid: bool, reason: str | None).
    Порядок проверок — от наиболее частых ошибок к более тонким.
    """
    if not address:
        return False, "адрес пустой"
    if " " in address:
        return False, "адрес содержит пробел"
    if address.count("@") == 0:
        return False, "отсутствует символ @"
    if address.count("@") > 1:
        return False, "более одного символа @"

    local, domain = address.split("@", 1)

    if not local:
        return False, "нет локальной части (перед @)"
    if not domain:
        return False, "нет доменной части (после @)"
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False, "точки в начале/конце локальной части или две подряд"
    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        return False, "точки в начале/конце домена или две подряд"
    if "." not in domain:
        return False, "в домене нет точки (нет зоны)"

    zone = domain.rsplit(".", 1)[1]
    if not (2 <= len(zone) <= 6) or not zone.isalpha():
        return False, "некорректная доменная зона (2-6 букв)"

    if EMAIL_PATTERN.match(address):
        return True, None
    return False, "не соответствует эталонному формату username@domain.zone"


def append_history(address, is_valid, reason):
    """Добавляет запись о проверке в history.json. Ошибки не прерывают работу."""
    record = {
        "time": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "email": address,
        "result": "корректен" if is_valid else "некорректен",
        "reason": reason or "-",
    }
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []  # файла нет или он повреждён — начинаем заново
    history.append(record)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"  Внимание: не удалось сохранить историю: {e}")


def show_history():
    """Выводит последние 20 проверок из history.json."""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        print("\n  История пуста — ещё не было ни одной проверки.")
        return
    except json.JSONDecodeError:
        print("\n  Файл истории повреждён. Начинаю запись заново.")
        return
    if not history:
        print("\n  История пуста — ещё не было ни одной проверки.")
        return
    print(f"\n  Последние проверки (всего записей: {len(history)}):")
    for rec in history[-20:]:
        print(f"  [{rec['time']}] {rec['email']} -> {rec['result']} "
              f"(причина: {rec['reason']})")


def read_text_file_any_encoding(path):
    """
    Читает текстовый файл, перебирая кодировки: utf-8, cp1251, utf-16, latin-1.
    Возвращает список непустых строк.
    """
    for enc in ("utf-8", "cp1251", "utf-16", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return [line.strip() for line in f if line.strip()]
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("b", b"", 0, 1,
                             "не удалось определить кодировку файла")


def batch_check(path):
    """Пакетная проверка адресов из файла с сохранением результатов."""
    try:
        lines = read_text_file_any_encoding(path)
    except FileNotFoundError:
        print(f"\n  Ошибка: файл '{path}' не найден.")
        return
    except PermissionError:
        print(f"\n  Ошибка: нет прав доступа к файлу '{path}'.")
        return
    except UnicodeDecodeError:
        print("\n  Ошибка: не удалось определить кодировку файла.")
        return
    except OSError as e:
        print(f"\n  Ошибка при чтении файла: {e}")
        return

    if not lines:
        print("\n  Файл пуст — проверять нечего.")
        return

    out_name = "results.txt"
    results = []
    for addr in lines:
        ok, reason = check_email(addr)
        verdict = "корректен" if ok else "некорректен"
        results.append(f"{addr} -> {verdict}" + (f" (причина: {reason})" if reason else ""))
        append_history(addr, ok, reason)

    try:
        with open(out_name, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        print(f"\n  Проверено адресов: {len(results)}. Результаты сохранены в '{out_name}'.")
    except OSError as e:
        print(f"\n  Адреса проверены, но записать '{out_name}' не удалось: {e}")
    for r in results:
        print("  " + r)


def custom_check(pattern_text, address):
    """Проверка адреса по пользовательскому регулярному выражению."""
    try:
        pattern = re.compile(pattern_text)
    except re.error as e:
        print(f"\n  Ошибка в регулярном выражении: {e}")
        return None
    if pattern.match(address):
        print(f"\n  '{address}' СООТВЕТСТВУЕТ шаблону.")
        return True
    print(f"\n  '{address}' НЕ соответствует шаблону.")
    return False


def main():
    """Главный цикл программы: меню из четырёх пунктов."""
    while True:
        print("\n" + "=" * 60)
        print("ВАЛИДАТОР EMAIL-АДРЕСОВ")
        print("=" * 60)
        print("1 - Проверить один адрес")
        print("2 - Пакетная проверка из файла")
        print("3 - Проверка по своему регулярному выражению")
        print("4 - История проверок")
        print("0 - Выход")
        choice = input("Выберите пункт меню: ").strip()

        if choice == "1":
            addr = input("Введите email: ").strip()
            ok, reason = check_email(addr)
            if ok:
                print(f"\n  '{addr}' — КОРРЕКТЕН")
            else:
                print(f"\n  '{addr}' — НЕКОРРЕКТЕН. Причина: {reason}")
            append_history(addr, ok, reason)

        elif choice == "2":
            path = input("Путь к файлу с адресами (по одному на строку): ").strip()
            if not path:
                print("\n  Путь не введён — возвращаюсь в меню.")
                continue
            if not os.path.isfile(path):
                print(f"\n  Ошибка: файла '{path}' не существует. Проверьте путь.")
                continue
            batch_check(path)

        elif choice == "3":
            print("Введите регулярное выражение (без кавычек и префикса r).")
            print("Пример: ^\\w+@mycompany\\.ru$  — только адреса вида имя@mycompany.ru")
            pattern_text = input("Шаблон: ").strip()
            if not pattern_text:
                print("\n  Шаблон не введён.")
                continue
            addr = input("Введите email для проверки: ").strip()
            ok = custom_check(pattern_text, addr)
            if ok is not None:
                append_history(addr, ok, "по пользовательскому шаблону"
                               if ok else "не соответствует пользовательскому шаблону")

        elif choice == "4":
            show_history()

        elif choice == "0":
            print("\nВыход. Всего доброго!")
            break

        else:
            print("\n  Нет такого пункта меню. Введите 1, 2, 3, 4 или 0.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем (Ctrl+C). До встречи!")
        sys.exit(0)
