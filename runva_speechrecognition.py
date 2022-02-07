# you need to install:
# pip install PyAudio
# pip install SpeechRecognition

# if you have problems with PyAudio install, check this:
# https://github.com/EnjiRouz/Voice-Assistant-App/blob/master/README.md

import traceback

import speech_recognition

from vacore import VACore

# most from @EnjiRouz code: https://habr.com/ru/post/529590/


def record_and_recognize_audio(*args: tuple):
    """
    Запись и распознавание аудио
    """
    with microphone:
        recognized_data = ""

        try:
            # print("Listening...")
            audio = recognizer.listen(microphone, 5, 5)

        except speech_recognition.WaitTimeoutError:
            print("Can you check if your microphone is on, please?")
            return

        # использование online-распознавания через Google
        try:
            # print("Started recognition...")
            recognized_data = recognizer.recognize_google(audio, language="ru").lower()

        except speech_recognition.UnknownValueError:
            pass

        # в случае проблем с доступом в Интернет происходит выброс ошибки
        except speech_recognition.RequestError:
            print("Check your Internet Connection, please")

        return recognized_data


# ------------------- vosk ------------------
if __name__ == "__main__":
    # инициализация инструментов распознавания и ввода речи
    recognizer = speech_recognition.Recognizer()
    microphone = speech_recognition.Microphone()

    with microphone:
        # регулирование уровня окружающего шума
        recognizer.adjust_for_ambient_noise(microphone, duration=2)

    # initing core
    core = VACore()
    # core.init_plugin("core")
    # core.init_plugins(["core"])
    core.init_with_plugins()

    while True:
        # старт записи речи с последующим выводом распознанной речи
        voice_input_str = record_and_recognize_audio()

        if voice_input_str != "":
            # print("Input: ",voice_input)
            if core.logPolicy == "all":
                print("Input: ", voice_input_str)

            try:
                voice_input = voice_input_str.split(" ")
                # callname = voice_input[0]
                for ind in range(len(voice_input)):
                    callname = voice_input[ind]
                    if callname in core.voiceAssNames:  # найдено имя ассистента
                        if core.logPolicy == "cmd":
                            print("Input (cmd): ", voice_input_str)

                        command_options = " ".join(
                            [
                                str(input_part)
                                for input_part in voice_input[
                                    (ind + 1) : len(voice_input)
                                ]
                            ]
                        )
                        core.execute_next(command_options, None)
                        break
            except Exception as err:
                print(traceback.format_exc())

        core._update_timers()
