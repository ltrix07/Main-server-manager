# Main server manager

## Описание
Данный менеджер используется для развертывания на сервере для работы с [Checker-Plus](https://github.com/ltrix07/Checker-Plus)
и служит связным звеном между чекером, поставщиком прокси и телаграм ботом для отправки сообщений.

## Принцип работы
1. [Checker-Plus](https://github.com/ltrix07/Checker-Plus) перед началом работы делает запрос к серверу, для того чтобы 
получить от него прокси.
2. Менеджер (сервер) связывается через API с поставщиком прокси и собирает у него валидные прокси.
3. Если менеджер успешно получил прокси, он отдает их чекеру.
4. Чекер продолжает работу.
5. Чекер время от времени может присылать на сервер ряд сообщений. Это могут быть: отчеты, ошибки, уведомления и т.д.

## Установка и запуск
1. `git clone https://github.com/ltrix07/Main-server-manager.git`
2. `cd Main-server-manager`
3. `python -m venv venv`
4. `source venv/bin/activate` (Unix system); `venv/Scripts/activate` (Windows)
5. `pip install -r requirements.txt`
6. Создать папки `chat` и `creds`. в папках создать файлы `chats_info.json` и `creds.json` соответственно.
7. В файл `chats_info.json` поместить id чатов, которые будут использоваться для получения тех или иных сообщений.   
Пример:  
```json
{  
  "chat_id_for_flipping_reports": -11111111,  
  "chat_id_for_errors_backend": -22222222222,  
  "chat_id_for_errors_attention": -333333333333,  
  "chat_id_for_reports": -44444444  
}
```
Если нужно отправлять все типы сообщений в один чат, то везде нужно указать один и тот же id.
8. В файл `creds.json` нужно поместить: токен бота; API токен поставщика прокси; API ссылку, которая используется для работы.  
Пример:  
```json
{
  "bot_token": "<token>",
  "api_proxy_token": "<token>",
  "api_proxy_url": "<link>"
}
```
9. `python server/main.py`