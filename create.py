import asyncio
from telethon import TelegramClient
import qrcode
import os


async def create_session():
    print("Создание сессии Telegram")
    print("=" * 50)

    api_id_input = input("Введите API_ID (или нажмите Enter для использования стандартных ключей): ").strip()

    if not api_id_input:
        api_id = 2040
        api_hash = "b18441a1ff607e10a989891a5462e627"
        print("Используются стандартные API_ID и API_HASH Telegram.")
    else:
        if not api_id_input.isdigit():
            print("API_ID должен быть числом.")
            return
        api_id = int(api_id_input)

        api_hash = input("Введите API_HASH: ").strip()
        if not api_hash:
            print("API_HASH не может быть пустым.")
            return

    base_session_name = 'session'
    session_name = f"{base_session_name}1"
    counter = 2

    while os.path.exists(f"{session_name}.session"):
        session_name = f"{base_session_name}{counter}"
        counter += 1

    print(f"Будет создан файл сессии: {session_name}.session")

    client = TelegramClient(session_name, api_id, api_hash)
    await client.connect()

    print("=" * 50)
    print("Выберите способ авторизации:")
    print("1 - По QR-коду (откроется картинка)")
    print("2 - По номеру телефона (придет код в СМС/Telegram)")
    print("=" * 50)

    choice = input("Ваш выбор (1 или 2): ").strip()

    if choice == '1':
        print("\nИнициализация QR-входа...")
        try:
            qr_login = await client.qr_login()
        except Exception as e:
            print(f"Ошибка инициализации QR: {e}")
            await client.disconnect()
            return

        try:
            qr = qrcode.QRCode(border=1)
            qr.add_data(qr_login.url)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save("qr_login.png")
            img.show()
            print(" QR-код открыт на экране.")
        except Exception as e:
            print(f" Не удалось создать/открыть QR-код: {e}")
            print(f"Вручную откройте ссылку: {qr_login.url}\n")

        try:
            await qr_login.wait(120)
            print("QR-код успешно отсканирован!")

            if not await client.is_user_authorized():
                password = input("Введите пароль двухфакторной аутентификации (если есть): ")
                try:
                    await client.sign_in(password=password)
                    print("Пароль принят.")
                except Exception as pe:
                    print(f"Ошибка при вводе пароля: {pe}")
                    await client.disconnect()
                    return
        except asyncio.TimeoutError:
            print("Время ожидания истекло. Перезапустите скрипт.")
            await client.disconnect()
            return
        except Exception as e:
            if "password" in str(e).lower():
                password = input("Введите пароль двухфакторной аутентификации: ")
                try:
                    await client.sign_in(password=password)
                    print("Пароль принят.")
                except Exception as pe:
                    print(f"Неверный пароль или ошибка: {pe}")
                    await client.disconnect()
                    return
            else:
                print(f"Ошибка: {e}")
                await client.disconnect()
                return

    elif choice == '2':
        print("\nВход по номеру телефона.")
        phone = input("Введите номер телефона (в формате +1234567890): ").strip()

        if not phone:
            print("Номер телефона не может быть пустым.")
            await client.disconnect()
            return

        try:
            await client.send_code_request(phone)
            print("Код подтверждения отправлен в Telegram/СМС.")
        except Exception as e:
            print(f"Ошибка при отправке кода: {e}")
            await client.disconnect()
            return

        max_attempts = 3
        for attempt in range(max_attempts):
            code = input("Введите код из SMS/Telegram: ").strip()
            if not code:
                print("Код не может быть пустым.")
                continue

            try:
                await client.sign_in(phone, code)
                break
            except Exception as e:
                error_str = str(e).lower()
                if "password" in error_str:
                    print("Требуется пароль двухфакторной аутентификации.")
                    password = input("Введите пароль: ").strip()
                    try:
                        await client.sign_in(password=password)
                        print("Пароль принят.")
                        break
                    except Exception as pe:
                        print(f"Неверный пароль или ошибка: {pe}")
                        await client.disconnect()
                        return
                elif "phone code" in error_str or "code" in error_str:
                    print(f"Неверный код. Попытка {attempt + 1} из {max_attempts}.")
                    if attempt == max_attempts - 1:
                        print("Превышено количество попыток ввода кода.")
                        await client.disconnect()
                        return
                else:
                    print(f"Ошибка при входе: {e}")
                    await client.disconnect()
                    return
        else:
            print("Не удалось войти.")
            await client.disconnect()
            return

    else:
        print("Неверный выбор. Пожалуйста, запустите скрипт снова и введите '1' или '2'.")
        await client.disconnect()
        return

    if await client.is_user_authorized():
        print(f"\nУспех! Сессия создана и сохранена в файл '{session_name}.session'")

        if os.path.exists("qr_login.png"):
            os.remove("qr_login.png")

    else:
        print("Не удалось авторизоваться.")
    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(create_session())