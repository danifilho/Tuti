# Importações necessárias
import g4f
import asyncio
import functools
import langid
import speech_recognition as sr
import sqlite3
from datetime import datetime
import tkinter as tk
import threading
from gtts import gTTS
import os

class VoiceCaptureApp:
    def __init__(self, root):
        self.root = root
        self.recognizer = sr.Recognizer()

        # Inicializa a captura de voz
        self.voice_capture_active = False

        # Variável para armazenar o texto reconhecido
        self.recognized_text = ""

        # Configuração da interface
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Voice Capture App")

        # Adiciona um rótulo
        self.label = tk.Label(self.root, text="Pressione e segure a barra de espaço para capturar voz.")
        self.label.pack(pady=10)

        # Associa eventos de teclado
        self.root.bind("<KeyPress-space>", self.start_voice_capture)
        self.root.bind("<KeyRelease-space>", self.stop_voice_capture)

    def start_voice_capture(self, event):
        if not self.voice_capture_active:
            self.voice_capture_active = True
            self.label.config(text="Capturando voz...")

            # Inicia a captura de voz em uma thread separada
            self.voice_capture_thread = threading.Thread(target=self.capture_voice_thread)
            self.voice_capture_thread.start()

def stop_voice_capture(self, event):
    if self.voice_capture_active:
        self.voice_capture_active = False
        self.label.config(text="Pressione e segure a barra de espaço para capturar voz.")

def capture_voice_thread(self):
    with sr.Microphone() as source:
        while self.voice_capture_active:
            try:
                audio = self.recognizer.listen(source, timeout=1)
                text = self.recognizer.recognize_google(audio, language="pt-BR")

                # Armazena o texto reconhecido na variável
                self.recognized_text = text

                # Faça algo com o texto reconhecido (opcional)
                print("Texto reconhecido:", text)

            except sr.UnknownValueError:
                pass  # Não foi possível entender o áudio
            except sr.RequestError as e:
                print(f"Erro na solicitação ao serviço de reconhecimento de voz: {e}")

# Inicialização do loop assíncrono
loop = asyncio.get_event_loop()

# Defina os provedores
_tuti_provider = g4f.Provider.GeminiProChat
_tuti_gpt4_provider = g4f.Provider.Bing

# Defina o provedor padrão
_provider = _tuti_provider

# Inicialize o banco de dados
def initialize_database():
    conn = sqlite3.connect('conversations.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_input TEXT,
            tuti_response TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Função para inserir uma interação na base de dados
def insert_interaction(user_input, tuti_response):
    conn = sqlite3.connect('conversations.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (user_input, tuti_response)
        VALUES (?, ?)
    ''', (user_input, tuti_response))
    conn.commit()
    conn.close()

# Função assíncrona para entrada
async def async_input(prompt: str) -> str:
    return await loop.run_in_executor(None, functools.partial(input, prompt))

# Função para reconhecimento de voz
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Diga algo...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=15)
    try:
        text = recognizer.recognize_google(audio, language="pt-BR")
        print("Texto reconhecido:", text)
        return text.lower()
    except sr.UnknownValueError:
        print("Não foi possível entender o áudio.")
        return None
    except sr.RequestError as e:
        print(f"Erro na solicitação ao serviço de reconhecimento de voz: {e}")
        return None

# Função para detectar o idioma do texto
def detect_language(text: str) -> str:
    lang, confidence = langid.classify(text)
    return lang

# Função assíncrona para executar o provedor
async def run_provider(provider: g4f.Provider.BaseProvider, user_input: str, max_tokens: int = 50):
    try:
        language = detect_language(user_input)
        
        # Verifique o idioma para execução
        if language == 'pt':
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.default,
                messages=[{"role": "user", "content": user_input}],
                provider=provider,
                max_tokens=max_tokens,
            )

            # Limita a resposta ao número máximo de tokens
            response = ' '.join(response.split()[:max_tokens])

            # Imprima a resposta
            print(f"{provider.__name__}: {response!r}")

        else:
            print(f"{provider.__name__}: Input não reconhecido como português do Brasil.")
    except Exception as e:
        print(f"{provider.__name__}:", e)


async def run_all_with_voice_input(user_input):
    global _provider, modo_texto
    
    # Inicialize o banco de dados
    initialize_database()
    
    # Log da interação no banco de dados
    insert_interaction(user_input, "")  # Inicia com uma resposta vazia

    # Execute o provedor atual
    await run_provider(_provider, user_input)

if __name__ == "__main__":
    modo_texto = False  # Inicializa o modo de texto como False
    user_input = ""  # Defina user_input inicialmente como uma string vazia

    while True:
        if modo_texto:
            user_input = input("Digite uma pergunta: ")
        else:
            # Reconhecimento de voz
            user_input = recognize_speech()

            if user_input is None:
                # Se o áudio não for entendido, continue para o próximo loop
                continue
        if user_input.lower() == 'exit':
            print("Saindo do programa. Até mais!")
            break

        # Execute o provedor atual com o texto reconhecido
        loop.run_until_complete(run_all_with_voice_input(user_input))
