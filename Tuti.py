# Importações necessárias
import g4f
import asyncio
import functools
import langid
import speech_recognition as sr
import sqlite3
from datetime import datetime
import pyttsx3

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

def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
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

            # Imprima a resposta sem tentar decodificar
            print(f"{provider.__name__}: {response!r}")

        else:
            print(f"{provider.__name__}: Input não reconhecido como português do Brasil.")
    except Exception as e:
        print(f"{provider.__name__}:", e)

# Função assíncrona para executar todas as interações
async def run_all(user_input: str):
    global _provider, modo_texto
    
    # Inicialize o banco de dados
    initialize_database()
    
    # Log da interação no banco de dados
    insert_interaction(user_input, "")  # Inicia com uma resposta vazia

    # Verifique o comando para alterar o provedor ou modo de texto
    if user_input.lower() == 'modo gpt4':
        _provider = _tuti_gpt4_provider
        print("Entrando no modo GPT-4")
        return
    elif user_input.lower() == 'modo de fábrica':
        _provider = _tuti_provider
        print("Voltando ao estágio original")
        return
    elif user_input.lower() == 'modo voz':
        modo_texto = False
        return

    # Execute o provedor atual
    try:
        language = detect_language(user_input)

        # Verifique o idioma para execução
        if language == 'pt':
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.default,
                messages=[{"role": "user", "content": user_input}],
                provider=_provider,
                max_tokens=50,
            )

            # Imprima a resposta sem tentar decodificar
            print(f"{_provider.__name__}: {response!r}")

            # Use pyttsx3 to speak the response
            speak_text(response)

        else:
            print(f"{_provider.__name__}: Input não reconhecido como português do Brasil.")
    except Exception as e:
        print(f"{_provider.__name__}:", e)

# Bloco principal de execução
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

        loop.run_until_complete(run_all(user_input))


        #PRECISO CONSERTAR A PARTE DE QUE SE ELA NAO ESCUTA VOLTA PARA O MODO TEXTO
        #TALVEZ COLOCAR TUTI COMO GATILHO PARA INTERACOES (MAS DESATIVAR A NECESSIDADE POR UM TEMPO)
        #PENSAR MELHOR NA ARQUITETURA E SE SERÃO NECESSÁRIOS MAIS ARQUIVOS (QUAIS?)
        #O PROBLEMA RELACIONADO COM A INTERFACE GRAFICA E A INICIALIZACAO
        #SOMENTE O GEMINI TEM LIMITE DE CARACTERES
