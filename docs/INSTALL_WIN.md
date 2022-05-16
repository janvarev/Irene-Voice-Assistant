# Подготовка окружения Windows

Для установки на Windows 8 и выше нужно скачать и установить python с сайта  https://www.python.org/downloads/windows/

В случае если установка производится на Windows 7:
1. Установить обновление с актуальными сертификатами корневых удоставеряющих центров KB3004394
https://www.microsoft.com/en-us/download/details.aspx?id=45588
2. Установить обновление KB3063858 
32-bit: https://www.microsoft.com/en-us/download/details.aspx?id=47409
64-bit: https://www.microsoft.com/en-us/download/details.aspx?id=47442
3. Скачать последнюю версию pyton 3.8.9  02-Apr-2021, которая работает на Win7 
https://www.python.org/ftp/python/3.8.9/

После этого в CMD будет доступна команда pip.

Скачать репозиторий с GitHub и распаковать его, желательно поместить содержимое в папку с более коротким путём и,
которая не имеет пробелов и русских символов (в будущем проще будет с ней работать), например C:\Irene\

Запустить cmd и перейти в папку с Irene командой
```
cd C:\Irene\
```
если у вас располагается на другом диске то нужно сначала перейти на него:
d:
d:\Irene\
далее для установки требуемых пакетов запустить
``` 
pip install -r requirements.txt
```

(текст by lynxchat4)