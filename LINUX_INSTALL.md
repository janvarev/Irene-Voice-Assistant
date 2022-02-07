# Настройка под Linux

### Некоторые проблемы при установке под Linux

Говорят, что требуется:
```apt install portaudio19-dev```

Также есть проблемы с запуском TTS движка. Варианта 2:

**1 вариант. Оставить pyttsx**

pyttsx идет по умолчанию.

Под него нужно ```apt install espeak-ng```

Далее в плагине plugins/plugin_tts_pyttsx.py поменять строку на
core.ttsEngine.setProperty("voice", "russian") либо найти нужный id языка
и установить его в options/plugin_tts_pyttsx.json sysId

Тогда звук будет идти через espeak-ng, и говорят, он не очень на русском.

**2 вариант. Поставить TTS rhvoice**

1. Скопируйте plugin_tts_rhvoice из plugins_active в plugins
2. Установите в options/core.json "ttsEngineId": "rhvoice"
3. Посмотрите в [PLUGINS.md](/PLUGINS.md), что нужно для плагина rhvoice.

На Linux-системе говорят, что для установки rhvoice-wrapper-bin
требуется
```
apt install libspeechd-dev
pip3 install scons lxml
```
 
Проблемы обсуждались в этой ветке комментариев: https://habr.com/ru/post/595855/#comment_24043171

