import threading
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from projudi_ba.regra_captcha import record_loopback, transcrever_audio, extrair_numeros

PASTA_AUDIOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp", "audios")
os.makedirs(PASTA_AUDIOS, exist_ok=True)


def resolver_captcha_busca(page):
    """Resolve o captcha de áudio que aparece após clicar em Submit."""
    main = page.locator("frame[name=\"mainFrame\"]").content_frame
    inner = main.locator("iframe[name=\"userMainFrame\"]").content_frame
    captcha = inner.locator("iframe[name=\"https://ca.turing.captcha.qcloud.com\"]").content_frame

    # Muda para modo simples se necessário
    modo_simples = captcha.get_by_text("Modo simples")
    if modo_simples.is_visible():
        print("Mudando para modo simples...")
        modo_simples.click()
    page.wait_for_timeout(1500)

    # Grava e transcreve o áudio
    audio_result = {}

    def gravar():
        caminho = os.path.join(PASTA_AUDIOS, "captcha_busca.wav")
        audio_result["file"] = record_loopback(duration=15, filename=caminho)

    print("Iniciando gravação do captcha...")
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

    campo = captcha.get_by_role("textbox", name="Por favor insira os")
    campo.wait_for(timeout=5000)
    campo.click()
    page.wait_for_timeout(300)
    campo.type(numero, delay=120)
    page.wait_for_timeout(800)
    captcha.get_by_role("button", name="OK").click()
    print("Captcha resolvido!")
    page.wait_for_timeout(3000)


def voltar_para_busca(page):
    """Volta para a tela de Buscar Qualquer Processo."""
    main = page.locator("frame[name=\"mainFrame\"]").content_frame
    print("Voltando para busca...")
    main.locator("a").filter(has_text="Buscas").hover()
    page.wait_for_timeout(1000)
    main.locator("xpath=/html/body/div[14]/table/tbody/tr/td/table/tbody/tr[2]/td/a").click()
    page.wait_for_timeout(2000)


def executar(context, page, numero_processo):
    """
    Busca o processo no PROJUDI, resolve captcha e verifica resultado.
    Retorna True se encontrou resultado, False se não encontrou.
    """
    print(f"Buscando processo: {numero_processo}")

    main = page.locator("frame[name=\"mainFrame\"]").content_frame
    inner = main.locator("iframe[name=\"userMainFrame\"]").content_frame

    # Digita o número do processo
    campo = inner.get_by_role("textbox", name="Número Processo")
    campo.wait_for(timeout=10000)
    campo.click()
    campo.fill(numero_processo)
    print(f"Número digitado: {numero_processo}")
    page.wait_for_timeout(500)

    # Clica em Submit
    print("Clicando em Submeter...")
    inner.get_by_role("button", name="Submit").click()
    page.wait_for_timeout(3000)

    # Resolve captcha se aparecer
    main2 = page.locator("frame[name=\"mainFrame\"]").content_frame
    inner2 = main2.locator("iframe[name=\"userMainFrame\"]").content_frame
    captcha_frame = inner2.locator("iframe[name=\"https://ca.turing.captcha.qcloud.com\"]")
    if captcha_frame.is_visible():
        print("Captcha detectado, resolvendo...")
        resolver_captcha_busca(page)

    # Verifica se o botão Peticionar está visível (indica que encontrou o processo)
    page.wait_for_timeout(2000)
    main3 = page.locator("frame[name=\"mainFrame\"]").content_frame
    inner3 = main3.locator("iframe[name=\"userMainFrame\"]").content_frame

    btn_peticionar = inner3.locator("xpath=/html/body/div[2]/form[2]/table/tbody/tr[4]/td[7]/a")
    if btn_peticionar.is_visible():
        print(f"✅ Processo {numero_processo} encontrado! Botão Peticionar visível.")
        return True
    else:
        print(f"⚠️ Processo {numero_processo} sem resultado. Indo para o próximo...")
        voltar_para_busca(page)
        return False
