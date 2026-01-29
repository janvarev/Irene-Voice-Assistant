import sounddevice as sd
import soundfile as sf


class LoopingSoundPlayer:
    def __init__(self, file_path, loop_count=None, volume=1.0):
        """
        Инициализация плеера

        Args:
            file_path: путь к WAV файлу
            loop_count: количество повторений (None = бесконечно, 1 = один раз, 2 = два раза и т.д.)
            volume: громкость от 0.0 (тишина) до 1.0 (максимум). Можно использовать значения > 1.0 для усиления
        """
        self.data, self.samplerate = sf.read(file_path)
        self.channels = self.data.shape[1] if len(self.data.shape) > 1 else 1
        self.position = 0
        self.is_playing = False
        self.stream = None
        self.loop_count = loop_count
        self.current_loop = 0
        self._volume = max(0.0, volume)  # Не допускаем отрицательных значений

    @property
    def volume(self):
        """Получить текущую громкость"""
        return self._volume

    @volume.setter
    def volume(self, value):
        """Установить громкость (можно менять во время воспроизведения)"""
        self._volume = max(0.0, value)

    def _callback(self, outdata, frames, time, status):
        if not self.is_playing:
            raise sd.CallbackStop()

        start = self.position
        end = start + frames

        if end <= len(self.data):
            outdata[:] = self.data[start:end] * self._volume
            self.position = end
        else:
            # Проверяем, нужно ли продолжать циклическое воспроизведение
            if self.loop_count is not None and self.current_loop >= self.loop_count - 1:
                # Проигрываем остаток и останавливаемся
                remaining = len(self.data) - start
                outdata[:remaining] = self.data[start:] * self._volume
                outdata[remaining:] = 0  # Заполняем тишиной
                self.is_playing = False
                raise sd.CallbackStop()
            else:
                # Циклическое воспроизведение
                remaining = len(self.data) - start
                outdata[:remaining] = self.data[start:] * self._volume
                outdata[remaining:] = self.data[:frames - remaining] * self._volume
                self.position = frames - remaining
                self.current_loop += 1

    def play(self):
        """Начинает воспроизведение"""
        self.is_playing = True
        self.position = 0
        self.current_loop = 0

        self.stream = sd.OutputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            callback=self._callback
        )

        with self.stream:
            while self.is_playing:
                sd.sleep(100)

    def stop(self):
        """Останавливает воспроизведение мгновенно"""
        self.is_playing = False
