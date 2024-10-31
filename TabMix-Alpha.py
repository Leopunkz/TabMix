import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QSlider, QLabel, QHBoxLayout, QCheckBox, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TabMix - Alpha_v1.0.0")
        self.setGeometry(100, 100, 1200, 800)

        # Layout principale
        self.main_layout = QVBoxLayout()

        # Aggiungi pulsante per aprire una nuova scheda con YouTube
        self.youtube_button = QPushButton("Apri YouTube")
        self.youtube_button.clicked.connect(self.add_youtube_tab)
        self.main_layout.addWidget(self.youtube_button)

        # Crea il TabWidget per gestire le schede del browser
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Layout mixer audio che contiene i fader delle schede e il master fisso a destra
        self.audio_mixer_container = QHBoxLayout()
        self.main_layout.addLayout(self.audio_mixer_container)

        # Layout che contiene solo i fader delle schede
        self.tab_faders_layout = QHBoxLayout()
        self.audio_mixer_container.addLayout(self.tab_faders_layout)

        # Aggiungi il master fader fisso alla destra del layout
        self.add_master_fader()

        # Imposta il layout della finestra principale
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def add_new_tab(self, url, label):
        # Crea una nuova scheda del browser
        browser = QWebEngineView()
        browser.setUrl(QUrl(url))

        # Aggiungi la scheda al TabWidget
        self.tabs.addTab(browser, label)

        # Inietta lo script per controllare l'audio nella pagina
        browser.page().runJavaScript('''
            var videos = document.getElementsByTagName('video');
            for(var i = 0; i < videos.length; i++) {
                videos[i].volume = 0.5;  // Imposta il volume al 50% per cominciare
            }
        ''')

        # Crea un fader audio per la nuova scheda
        fader = self.create_fader(label, self.tabs.count() - 1)
        self.tab_faders_layout.addWidget(fader)

    def add_youtube_tab(self):
        # Aggiunge una nuova scheda con l'URL di YouTube e un fader
        self.add_new_tab("https://www.youtube.com", f"YouTube {self.tabs.count()}")

    def add_master_fader(self):
        # Aggiungi il master fader nella posizione finale del layout
        master_fader = self.create_fader("Master", "master")
        self.audio_mixer_container.addWidget(master_fader)

    def create_fader(self, label_text, tab_index):
        # Crea uno slider verticale per il volume
        slider = QSlider(Qt.Vertical)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(50)  # Volume iniziale a 50%
        slider.valueChanged.connect(lambda value, index=tab_index: self.set_volume(index, value))

        # Checkbox per il mute
        mute_checkbox = QCheckBox("Mute")
        mute_checkbox.stateChanged.connect(lambda state, index=tab_index: self.set_mute(index, state, slider))

        # Crea i pulsanti di Play e Pause con dimensioni ridotte
        play_button = QPushButton("▶")
        pause_button = QPushButton("⏸")

        # Imposta dimensioni fisse per i pulsanti
        play_button.setFixedSize(30, 25)
        pause_button.setFixedSize(30, 25)

        # Collega i pulsanti ai metodi di controllo della scheda
        if tab_index == "master":
            play_button.clicked.connect(self.play_all_videos)
            pause_button.clicked.connect(self.pause_all_videos)
        else:
            play_button.clicked.connect(lambda _, index=tab_index: self.play_video(index))
            pause_button.clicked.connect(lambda _, index=tab_index: self.pause_video(index))

        # Crea un'etichetta per il nome del fader
        label = QLabel(label_text)

        # Layout verticale per il fader e il mute checkbox
        fader_layout = QVBoxLayout()
        fader_layout.addWidget(slider)
        fader_layout.addWidget(mute_checkbox)
        fader_layout.addWidget(label)

        # Layout verticale per i pulsanti di controllo
        controls_layout = QVBoxLayout()
        controls_layout.addWidget(play_button)
        controls_layout.addWidget(pause_button)

        # Layout orizzontale che contiene sia il fader che i controlli di riproduzione
        h_layout = QHBoxLayout()
        h_layout.addLayout(fader_layout)
        h_layout.addLayout(controls_layout)

        # Crea un widget per il fader completo
        fader_widget = QWidget()
        fader_widget.setLayout(h_layout)

        return fader_widget

    def set_volume(self, tab_index, volume):
        # Normalizza il volume tra 0.0 e 1.0
        normalized_volume = volume / 100.0
        if tab_index == "master":
            # Applica il volume a tutte le schede
            for i in range(self.tabs.count()):
                browser = self.tabs.widget(i)
                browser.page().runJavaScript(f'''
                    var videos = document.getElementsByTagName('video');
                    for(var i = 0; i < videos.length; i++) {{
                        videos[i].volume = {normalized_volume};
                    }}
                ''')
        else:
            # Applica il volume solo alla scheda specificata
            browser = self.tabs.widget(tab_index)
            browser.page().runJavaScript(f'''
                var videos = document.getElementsByTagName('video');
                for(var i = 0; i < videos.length; i++) {{
                    videos[i].volume = {normalized_volume};
                }}
            ''')

    def set_mute(self, tab_index, state, slider):
        if tab_index == "master":
            mute_volume = 0 if state == Qt.Checked else slider.value() / 100.0
            for i in range(self.tabs.count()):
                browser = self.tabs.widget(i)
                browser.page().runJavaScript(f'''
                    var videos = document.getElementsByTagName('video');
                    for(var i = 0; i < videos.length; i++) {{
                        videos[i].volume = {mute_volume};
                    }}
                ''')
        else:
            browser = self.tabs.widget(tab_index)
            if state == Qt.Checked:
                browser.page().runJavaScript('''
                    var videos = document.getElementsByTagName('video');
                    for(var i = 0; i < videos.length; i++) {
                        videos[i].volume = 0;
                    }
                ''')
            else:
                normalized_volume = slider.value() / 100.0
                browser.page().runJavaScript(f'''
                    var videos = document.getElementsByTagName('video');
                    for(var i = 0; i < videos.length; i++) {{
                        videos[i].volume = {normalized_volume};
                    }}
                ''')

    def play_video(self, tab_index):
        browser = self.tabs.widget(tab_index)
        browser.page().runJavaScript('''
            var videos = document.getElementsByTagName('video');
            for(var i = 0; i < videos.length; i++) {
                videos[i].play();
            }
        ''')

    def pause_video(self, tab_index):
        browser = self.tabs.widget(tab_index)
        browser.page().runJavaScript('''
            var videos = document.getElementsByTagName('video');
            for(var i = 0; i < videos.length; i++) {
                videos[i].pause();
            }
        ''')

    def play_all_videos(self):
        for i in range(self.tabs.count()):
            self.play_video(i)

    def pause_all_videos(self):
        for i in range(self.tabs.count()):
            self.pause_video(i)


# Avvia l'applicazione
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrowserWindow()
    window.show()
    sys.exit(app.exec_())
