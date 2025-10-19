from docs.imports import *


def human_sleep(a=1.0, b=3.0):
    time.sleep(random.uniform(a, b))


def human_scroll(driver, steps=5):
    body = driver.find_element(By.TAG_NAME, "body")
    for _ in range(steps):
        ActionChains(driver).move_to_element(body).scroll_by_amount(0, 400).perform()
        human_sleep(0.5, 1.2)


def dados_ajustes_divs():
    # Configuração do navegador
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    # Etapa 1: Acessar Google primeiro
    print("🔄 Acessando Google...")
    driver.get("https://www.google.com/")
    human_sleep(2, 4)
    # Etapa 2: Acessar B3 em seguida
    print("🔄 Acessando site da B3...")
    driver.get(
        "https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-a-vista/opcoes/ajuste-de-proventos/"
    )
    human_sleep(2, 4)
    # Simula o scroll para baixo na página principal
    human_scroll(driver, steps=5)
    try:
        # Espera até o botão de aceitação de cookies estar visível e clicável
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        # Clica no botão
        accept_button.click()
        print("✅ Aceitou os cookies.")
    except Exception as e:
        print("❌ Botão de cookies não apareceu ou não foi clicado:", e)
    # 3) Esperar até que o iframe esteja presente
    iframe = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "bvmf_iframe"))
    )
    # 4) Mudar para o iframe
    driver.switch_to.frame(iframe)
    print("✅ Mudou para o iframe.")
    # 5) Interagir com o dropdown (select) para escolher a opção "120"
    select = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "selectPage"))
    )
    # Selecionar a opção "120"
    options = select.find_elements(By.TAG_NAME, "option")
    for option in options:
        if option.get_attribute("value") == "120":
            option.click()
            print("✅ Selecionada a opção 120.")
            break
    # 6) Esperar a tabela carregar
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "table-responsive-sm"))
    )
    time.sleep(5)
    # 7) Obter o HTML da página (do iframe já ativo)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    # 8) Localizar a tabela pelo class
    table = soup.find("table", class_="table-responsive-sm")
    if table:
        rows = []
        for row in table.find("tbody").find_all("tr"):
            cols = [col.get_text(strip=True) for col in row.find_all("td")]
            rows.append(cols)
        # 9) Criar o DataFrame com colunas nomeadas
        df = pd.DataFrame(
            rows,
            columns=[
                "Tipo Ação",
                "Opção",
                "Data Ex",
                "Data Vencimento",
                "Preco Exerc. Original",
                "Preco Exerc. Ajustado",
                "Historico",
            ],
        )
        print("✅ Página 1 acessada.")
    else:
        print("❌ Tabela não encontrada no HTML.")
    time.sleep(2)
    todos_os_dados = []
    pagina = 2
    while True:
        try:
            # Aguarda a presença do botão com o número da página
            page_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[span[text()='{pagina}']]"))
            )
            page_button.click()
            print(f"✅ Página {pagina} acessada.")
            # Aguarda o carregamento da nova tabela
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table-responsive-sm"))
            )
            time.sleep(2)
            # Pega o HTML da página e extrai os dados com BeautifulSoup
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", class_="table-responsive-sm")
            if table:
                for row in table.find("tbody").find_all("tr"):
                    cols = [col.get_text(strip=True) for col in row.find_all("td")]
                    todos_os_dados.append(cols)
                    time.sleep(0.1)
            else:
                print(f"❌ Tabela não encontrada na página {pagina}.")
            pagina += 1  # Próxima página
        except Exception as e:
            print(f"⚠️ Fim da navegação ou erro na página {pagina}:", e)
            break

    # Cria o DataFrame com os dados consolidados
    df_final = pd.DataFrame(
        todos_os_dados,
        columns=[
            "Tipo Ação",
            "Opção",
            "Data Ex",
            "Data Vencimento",
            "Preco Exerc. Original",
            "Preco Exerc. Ajustado",
            "Historico",
        ],
    )
    time.sleep(0.5)
    df = pd.concat([df, df_final], ignore_index=True)
    df = df.drop_duplicates(keep="first")
    driver.quit()
    print("✅ Coleta finalizada de opções ajustadas pelos dividendos ✅")
    print("Arrumando Dataframe...")
    df.drop(columns=["Historico"], inplace=True)
    df["Data Ex"] = pd.to_datetime(df["Data Ex"], format="%d/%m/%Y", errors="coerce")
    df["Data Vencimento"] = pd.to_datetime(
        df["Data Vencimento"], format="%d/%m/%Y", errors="coerce"
    )
    df["Código"] = df["Tipo Ação"].astype(str).str[:4]
    df["Tipo Ação"] = df["Tipo Ação"].astype(str).str.strip().str[4:]
    df = df[df["Tipo Ação"].str.contains("ON|PN|UNT", na=False)]
    df["Tipo Ação"] = df["Tipo Ação"].str.extract(r"(ON|PN|UNT)", expand=False)
    df["Preco Exerc. Original"] = pd.to_numeric(
        df["Preco Exerc. Original"].str.replace(",", ".").str.strip(), errors="coerce"
    )
    df["Preco Exerc. Ajustado"] = pd.to_numeric(
        df["Preco Exerc. Ajustado"].str.replace(",", ".").str.strip(), errors="coerce"
    )
    df["Opção"] = df["Opção"].astype(str).str.strip()
    mask_e = df["Opção"].str.endswith(" E")
    df.loc[mask_e, "Opção"] = df.loc[mask_e, "Opção"].str[:-2].str.strip()
    df = df[df["Data Vencimento"] >= data]
    print("Dataframe Organizado.")
    return df


if __name__ == "__main__":
    import random
    import time

    import pandas as pd
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    df = dados_ajustes_divs()
