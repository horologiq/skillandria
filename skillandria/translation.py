from PyQt6.QtCore import QThread, pyqtSignal
from googletrans import Translator

class TranslationThread(QThread):
    translation_done = pyqtSignal(str)

    def __init__(self, subtitle_text, translation_language):
        super().__init__()
        self.subtitle_text = subtitle_text
        self.translation_language = translation_language
        self._stop_event = False

    def run(self):
        translator = Translator()
        try:
            if self.subtitle_text.strip() != '':
                translation = translator.translate(self.subtitle_text, dest=self.translation_language).text
                self.translation_done.emit(translation)
            else:
                self.translation_done.emit('')
        except Exception as e:
            print(f"Translation error: {e}")
            self.translation_done.emit('')

    def stop(self):
        self._stop_event = True
