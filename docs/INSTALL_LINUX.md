# Настройка под Linux

## Некоторые проблемы при установке под Linux

Основные проблемы две:
- сделать, чтобы проигрывался wav-файл
- сделать, чтобы работал TTS

### Проигрывание WAV

По дефолту в `options/core.json` установлено
`"playWavEngineId": "audioplayer",`

Эта библиотека не всегда удобно ставится под Linux.
Вроде можно
```apt install portaudio19-dev```
но не всегда работает.

Рекомендуется переключиться на один из других движков проигрывания WAV. 
Список - в [docs/PLUGINS.md](/docs/PLUGINS.md#PlayWav), в разделе с PlayWav плагинами.

Для Linux рекомендуется либо:
`"playWavEngineId": "aplay",` (играть через запуск aplay)
либо
`"playWavEngineId": "sounddevice",`

### Работа TTS (Text-to-Speech) движка

Также есть проблемы с запуском TTS движка. Варианта 2:

**1 вариант. Оставить pyttsx**

pyttsx идет по умолчанию.

Под него нужно ```apt install espeak-ng```

Далее в плагине plugins/plugin_tts_pyttsx.py поменять строку на
core.ttsEngine.setProperty("voice", "russian") либо найти нужный id языка
и установить его в options/plugin_tts_pyttsx.json sysId

Тогда звук будет идти через espeak-ng, и говорят, он не очень на русском.

**2 вариант. Поставить TTS rhvoice_rest и запустить Докер для rhvoice_rest**

Прстой вариант, чтобы не париться с зависимостями.
1. Установите в options/core.json `"ttsEngineId": "rhvoice_rest"`
2. Использует докер-сервер https://github.com/Aculeasis/rhvoice-rest для
   генерации голоса. Зайдите туда и запустите нужный вам докер.

Если вам нужна качественная генерация через silero (требует больше ресурсов)
1. Установите в options/core.json `"ttsEngineId": "silero_rest"`
2. Использует докер-сервер https://github.com/janvarev/silero_rest_service для
   генерации голоса. Зайдите туда и запустите нужный вам докер.

**3 вариант. Поставить TTS rhvoice**

1. Скопируйте plugin_tts_rhvoice из plugins_active в plugins
2. Установите в options/core.json "ttsEngineId": "rhvoice"
3. Посмотрите в [PLUGINS.md](/docs/PLUGINS.md), что нужно для плагина rhvoice.

На Linux-системе говорят, что для установки rhvoice-wrapper-bin
требуется
```
apt install libspeechd-dev
pip3 install scons lxml
```
 
Проблемы обсуждались в этой ветке комментариев: https://habr.com/ru/post/595855/#comment_24043171

**Важно:** если соберетесь использовать rhvoice, переключите настройку в core.json:
`"playWavEngineId": "sounddevice",`
потому что через audioplayer не проигрывает WAV по неизвестным причинам.



