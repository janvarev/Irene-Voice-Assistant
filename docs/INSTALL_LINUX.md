# Настройка под Linux

## Некоторые проблемы при установке под Linux

Основные проблемы две:

- сделать, чтобы проигрывался wav-файл
- сделать, чтобы работал TTS

### Установка Python и подготовка окружения (Ubuntu/Debian)

Если Python не установлен или его версия ниже 3.10, выполните (для Ubuntu/Debian и производных):

```bash
sudo apt install cmake pkg-config python3-launchpadlib python3-pip libcairo2-dev
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install cmake pkg-config python3 python3-venv python3-dev python3-tk
# Если хотите установить конкретную версию Python: sudo apt install python3.10 python3.10-venv python3.10-dev python3.10-tk
```

Создайте и активируйте виртуальное окружение:

```bash
python3 -m venv .venv
# Если используете конкретную версию Python, создайте окружение так: python3.10 -m venv .venv
source .venv/bin/activate
```

Установка зависимостей:

```bash
pip install -r requirements_fixed.txt
```

##### Если возникает ошибка plugin_playwav_audioplayer error on load: No module named 'gi', выполните:

```bash
sudo apt install libgirepository-2.0-dev
pip install PyGObject
```

### Проигрывание WAV

По умолчанию в `options/core.json` указано:

```json
"playWavEngineId": "audioplayer",
```

Однако этот движок не всегда корректно работает на Linux.

Возможно, поможет установка:

```bash
sudo apt install portaudio19-dev
```

но она не всегда решает проблему.

Рекомендуется переключиться на один из других движков воспроизведения WAV.
Список доступен в [docs/PLUGINS.md](/docs/PLUGINS.md#PlayWav), в разделе с плагинами PlayWav.

Для Linux рекомендуется использовать один из следующих вариантов:

- `"playWavEngineId": "aplay"` — воспроизведение через утилиту `aplay`
- `"playWavEngineId": "sounddevice"` — через Python-библиотеку `sounddevice`

---

### Работа TTS (Text-to-Speech) движка

Также есть проблемы с запуском TTS движка. Варианта 2:

**1 вариант. Использовать pyttsx (по умолчанию)**

pyttsx идет по умолчанию.

Для работы требуется:

```bash
sudo apt install espeak-ng
```

Далее в плагине `plugins/plugin_tts_pyttsx.py` замените строку на:

```python
core.ttsEngine.setProperty("voice", "russian")
```

или найдите нужный ID языка и пропишите его в `options/plugin_tts_pyttsx.json`, поле `sysId`.

Звук будет воспроизводиться через `espeak-ng`, но качество русской озвучки невысокое.

---

**2 вариант. Установить TTS `rhvoice_rest` и запустить Docker-контейнер**

Простой вариант, не требующий ручной установки зависимостей.

1. Установите в options/core.json

```json
"ttsEngineId": "rhvoice_rest"
```

2. Используется Docker-сервер:  
   https://github.com/Aculeasis/rhvoice-rest  
   Перейдите по ссылке и запустите нужный контейнер.

Если нужна более качественная озвучка через `silero` (но потребуется больше ресурсов):

1. В `options/core.json`:

```json
"ttsEngineId": "silero_rest"
```

2. Используется Docker-сервер:  
   https://github.com/janvarev/silero_rest_service  
   Перейдите по ссылке и запустите нужный контейнер

---

**3 вариант. Установить TTS `rhvoice` локально**

1. Скопируйте `plugin_tts_rhvoice` из `plugins_active` в `plugins`:

```bash
cp -r plugins_active/plugin_tts_rhvoice plugins/
```

2. В `options/core.json` установите:

```json
"ttsEngineId": "rhvoice"
```

3. Посмотрите в [PLUGINS.md](/docs/PLUGINS.md), какие зависимости нужны для плагина `rhvoice`.

Для установки `rhvoice-wrapper-bin` на Linux могут понадобиться:

```bash
sudo apt install libspeechd-dev
pip3 install scons lxml
```

**Важно:** если вы используете `rhvoice`, установите в `core.json`:

```json
"playWavEngineId": "sounddevice"
```

Так как `audioplayer` не воспроизводит WAV в этом случае по неизвестным причинам.

---

Обсуждение проблем — в комментариях на Хабре:  
https://habr.com/ru/post/595855/#comment_24043171
