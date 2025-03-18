import pyaudio
import wave
import time
import os
import webbrowser
import struct
import pvporcupine  # Для Wake Word Detection
import pyttsx3
from vosk import Model, KaldiRecognizer

# Инициализация TTS движка
engine = pyttsx3.init()

# Получаем путь к папке проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Путь к модели Vosk
vosk_model_path = os.path.join(BASE_DIR, "vosk-model-small-ru-0.22")

# Загрузка модели Vosk
model = Model(vosk_model_path)

# Инициализация KaldiRecognizer с настройкой параметров
recognizer = KaldiRecognizer(model, 16000)
recognizer.SetMaxAlternatives(10)  # Альтернативные результаты
recognizer.SetWords(True)  # Включение вывода слов
recognizer.SetPartialWords(True)  # Включение частичных результатов

# Инициализация Porcupine для Wake Word Detection
ACCESS_KEY = "du3g4rwGYgjHhvg2Od+egSrjrizFfrNcMtfyC0SeZYD6JG2xgUlECA=="
# Путь к триггер слову
custom_keyword_path = os.path.join(BASE_DIR, "triggerword", "Cortex_en_windows_v3_0_0.ppn")

porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=[custom_keyword_path],
    sensitivities=[0.7]
)

# Параметры аудиопотока
CHUNK = 512
RATE = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1

# Флаг активации после триггера
is_listening_for_command = False


def transcribe_audio(audio_data):
    """Распознавание речи с помощью Vosk."""
    print("Передаем данные в Vosk...")
    
    if recognizer.AcceptWaveform(audio_data):
        result = recognizer.Result()
        result_data = eval(result)  # Преобразование строки в словарь
        alternatives = result_data.get('alternatives', [])

        if alternatives:
            final_text = alternatives[0].get('text', '').strip()
            print(f"Распознано: {final_text}")
            return final_text
    else:
        partial_result = recognizer.PartialResult()
        partial_data = eval(partial_result)
        partial_text = partial_data.get('partial', '').strip()
        if partial_text:
            print(f"Частичный результат: {partial_text}")
    return None


def execute_command(command):
    """Выполнение команды после распознавания."""
    command = command.lower()

    if "открой браузер" in command:
        print("Выполняю команду: открываю браузер...")
        webbrowser.open('http://google.com')
        engine.say("Браузер открыт")
        engine.runAndWait()

    elif "открой блокнот" in command:
        print("Выполняю команду: открываю блокнот...")
        os.system("notepad.exe")
        engine.say("Блокнот открыт")
        engine.runAndWait()

    elif "который час" in command:
        current_time = time.strftime("%H:%M", time.localtime())
        engine.say(f"Сейчас {current_time}")
        engine.runAndWait()

    elif "спасибо" in command:
        engine.say("Всегда рада помочь")
        engine.runAndWait()

    else:
        engine.say("Извините, я не понимаю эту команду")
        engine.runAndWait()


def continuous_listen():
    """Непрерывное прослушивание с детекцией Wake Word и распознаванием команд."""
    global is_listening_for_command
    p = pyaudio.PyAudio()

    # Открытие аудиопотока
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Голосовой помощник запущен! Ожидаю команду 'Cortex'...")

    while True:
        # Чтение данных из микрофона
        data = stream.read(CHUNK)
        pcm_data = struct.unpack_from("h" * CHUNK, data)  # Декодируем аудиоданные

        # Проверка на Wake Word с помощью Porcupine
        keyword_index = porcupine.process(pcm_data)

        if keyword_index >= 0 and not is_listening_for_command:
            print("Триггерное слово 'Cortex' обнаружено!")
            is_listening_for_command = True

        elif is_listening_for_command:
            print("Жду команду...")
            # Мгновенно переходим к прослушиванию команды (время уменьшено до 3 сек)
            audio_data = b''.join([stream.read(CHUNK) for _ in range(int(RATE / CHUNK * 3))])

            # Распознавание команды через Vosk
            command_text = transcribe_audio(audio_data)
            if command_text:
                execute_command(command_text)

            is_listening_for_command = False
            print("Ожидание команды 'Cortex'...")


def main():
    """Главная функция запуска голосового ассистента."""
    try:
        continuous_listen()
    finally:
        porcupine.delete()  # Очистка ресурсов Porcupine при завершении
        print("Ассистент выключен.")


if __name__ == "__main__":
    main()
