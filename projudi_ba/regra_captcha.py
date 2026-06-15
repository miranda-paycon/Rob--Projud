import re
import wave
import threading
import subprocess
import time
import os
import whisper
import numpy as np
import pyaudiowpatch as pyaudio
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

PASTA_AUDIOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp", "audios")
PASTA_IMAGENS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp", "imagens")
os.makedirs(PASTA_AUDIOS, exist_ok=True)
os.makedirs(PASTA_IMAGENS, exist_ok=True)

print("Carregando modelo Whisper...")
MODEL = whisper.load_model("medium")
print("Modelo pronto!")


def record_loopback(duration=10, filename="captcha_audio.wav"):
    with pyaudio.PyAudio() as p:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        if not default_speakers["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
        frames = []
        chunk = 512
        rate = int(default_speakers["defaultSampleRate"])
        channels = default_speakers["maxInputChannels"]
        with p.open(format=pyaudio.paInt16, channels=channels, rate=rate,
                    frames_per_buffer=chunk, input=True,
                    input_device_index=default_speakers["index"]) as stream:
            for _ in range(0, int(rate / chunk * duration)):
                frames.append(stream.read(chunk))
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(rate)
            wf.writeframes(b"".join(frames))
    return filename


def extrair_numeros(texto):
    return "".join(re.findall(r"\d+", texto))


def transcrever_audio(filepath):
    result = MODEL.transcribe(filepath, language="pt")
    return result["text"]


def executar():
    print("Fechando Edge...")
    subprocess.run("taskkill /IM msedge.exe /F", shell=True, capture_output=True)
    time.sleep(4)

    playwright = sync_playwright().start()

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=r"C:\Users\ANDREICERQUEIRADEMIR\AppData\Local\Microsoft\Edge\User Data",
        channel="msedge",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = context.pages[0] if context.pages else context.new_page()
    Stealth().apply_stealth_sync(page)
    page.goto("https://projudi.tjba.jus.br/projudi/")

    frame = page.locator("frame[name=\"mainFrame\"]").content_frame
    captcha = frame.locator("iframe[name=\"https://ca.turing.captcha.qcloud.com\"]").content_frame

    page.wait_for_timeout(2000)
    frame.get_by_role("link", name="entrar").click()

    page.wait_for_timeout(3000)
    modo_simples = captcha.get_by_text("Modo simples")
    if modo_simples.is_visible():
        modo_simples.click()
        print("Mudando para modo simples...")
    else:
        print("Captcha já está no modo de áudio, continuando...")
    page.wait_for_timeout(1500)

    audio_result = {}

    def gravar():
        caminho = os.path.join(PASTA_AUDIOS, "captcha_audio.wav")
        audio_result["file"] = record_loopback(duration=15, filename=caminho)

    print("Iniciando gravação...")
    t = threading.Thread(target=gravar)
    t.start()
    page.wait_for_timeout(800)
    captcha.get_by_role("button", name="Tocar").click()
    print("Áudio tocando, aguardando gravação...")
    t.join()
    print("Gravação concluída.")

    print("Transcrevendo...")
    texto = transcrever_audio(audio_result["file"])
    print(f"Texto transcrito: {texto}")
    numero = extrair_numeros(texto)
    print(f">>> Número extraído: {numero} <<<")

    campo = captcha.locator("input").first
    campo.wait_for(timeout=5000)
    campo.click()
    page.wait_for_timeout(300)
    campo.type(numero, delay=120)
    print(f"Número inserido: {numero}")
    page.wait_for_timeout(800)
    captcha.get_by_role("button", name="OK").click()

    print("Aguardando login completar...")
    page.wait_for_timeout(8000)
    print("LOGIN CONCLUÍDO!")

    # Seleciona a OAB
    main = page.locator("frame[name=\"mainFrame\"]").content_frame
    print("Selecionando OAB...")
    main.locator("body").click(position={"x": 260, "y": 410})
    page.wait_for_timeout(500)
    page.keyboard.press("Tab")
    page.wait_for_timeout(300)
    page.keyboard.press("Tab")
    page.wait_for_timeout(300)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)

    # Abre menu Buscas e clica em Buscar Qualquer Processo
    main3 = page.locator("frame[name=\"mainFrame\"]").content_frame
    print("Abrindo menu Buscas...")
    main3.locator("xpath=//*[@id=\"Stm0p0i8eTX\"]").hover()
    page.wait_for_timeout(2000)

    print("Clicando em Buscar Qualquer Processo...")
    main3.locator("xpath=/html/body/div[14]/table/tbody/tr/td/table/tbody/tr[2]/td/a").click()
    page.wait_for_timeout(2000)
    print("Tela de busca pronta!")

    return context, page, playwright
