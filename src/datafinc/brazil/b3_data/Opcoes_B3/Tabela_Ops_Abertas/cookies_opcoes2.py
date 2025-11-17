from datetime import datetime, timedelta

import holidays

feriados_br = holidays.BR()
data = datetime.today() - timedelta(days=1)
while data.weekday() >= 5 or data in feriados_br:
    data -= timedelta(days=1)
data_formatada2 = data.strftime("%d/%m/%Y")
data_formatada = data.strftime("%Y%m%d")

cookies_op2 = {
    "lumClientId": "8AA8D0CD94F633D2019590F2694D092C",
    "OptanonAlertBoxClosed": "2025-04-09T16:51:52.576Z",
    "dtCookie": "v_4_srv_27_sn_3912E1FDA0386FE9D520ECD2E3F45089_perc_100000_ol_0_mul_1_app-3Afd69ce40c52bd20e_1_rcs-3Acss_0",
    "TS0134a800": "011d592ce10dc6fd1e3013d6ef760fa957aaaa6a030a8bbd1b5f0d3a38dee3d0184cdd0a2cc7081e3ef1ba875230bec602de7ebadc",
    "rxVisitor": "174430788758671E9T78R63V7LIIR2E73BFKIB5VEOR0J",
    "lumUserLocale": "pt_BR",
    "BIGipServerpool_www.b3.com.br_443": "1209295882.47873.0000",
    "_ga_FTT9L7SR7B": "GS1.1.1744309116.1.1.1744309243.13.0.0",
    "_gid": "GA1.3.570450952.1744309293",
    "_ga": "GA1.1.547676165.1744217509",
    "_ga_CNJN5WQC5G": "GS1.1.1744309293.1.1.1744309328.25.0.0",
    "cf_clearance": "5qWUcPVYp.ksv8PPuH9Tou3Zvl4hDeyG3edIgIuo_TI-1744317644-1.2.1.1-FFS9EeuYcMKqjOZmIUvkntLdazvRqWPyqvpEuUEzAc3ZHtX6cjn99269B6.O4aHLj.AQdnwp4cvJzCEHMQLJZqaORLMkoENuGYwefrOLYKPXzfRsBIaYJgxaIQ6GeJhSJoyhXMLlVZEDg0k61.QbTst0xdXWCL.X9Gwn2UMgw3_Dhyryol9ut78qne1U55HUdJ.ARHmcmCZBUDWP9_dawdIPuYzLAWOlqKMW8lvcnKGHNSRf8GXGazPbYIiqRimvsXk8GFE7_GphT59K8cWyyWNQD_haNPg7lo.AEiUCtjZYdbjFpm8hkSOTwYuA8OvzLavUll2cnBl2Aq2uCHaDe7HaYC52Ehv1wq4Azg8JuEE",
    "JSESSIONID": "FE79C84B612F1BA93CF14BC27B094FE6.lumcor00201b",
    "lumUserSessionId": "fNPUYU_480jKBVaNd59KgcOxCqENHyfZ",
    "lumUserName": "Guest",
    "lumIsLoggedUser": "false",
    "dtSa": "-",
    "OptanonConsent": "isGpcEnabled=1&datestamp=Thu+Apr+10+2025+17%3A44%3A47+GMT-0300+(Hor%C3%A1rio+Padr%C3%A3o+de+Bras%C3%ADlia)&version=6.21.0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0003%3A1%2CC0001%3A1%2CC0004%3A1%2CC0002%3A1&geolocation=%3B&AwaitingReconsent=false",
    "mp_ec0f5c39312fa476b16b86e4f6a1c9dd_mixpanel": "%7B%22distinct_id%22%3A%20%22%24device%3A1961b770863ee4-02d4ab934e763f8-26011c51-c0000-1961b770863ee4%22%2C%22%24device_id%22%3A%20%221961b770863ee4-02d4ab934e763f8-26011c51-c0000-1961b770863ee4%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D",
    "__cf_bm": "hKBWHHliFDt7fzkzddOM691U1jzRyELVcAHgDbP5e9Q-1744318939-1.0.1.1-DU8unzOhLiXe34dWMMYYGOMORz0NkCSqSDCi4H0BSZjSfgczv2OxVcn5nB.6jQQe62_LlzeAmNCk4uCSDulgU0C2NYKEA0KAt7of7K1eQ0U",
    "_ga_SS7FXRTPP3": "GS1.1.1744317644.6.1.1744318940.60.0.0",
    "TS0171d45d": "011d592ce1a2f13da6f755f4188117ea6f147a1319f9283df929f7dc9cadc54d6e3df83e059fbed1ecd79a3b12de6484156a956ede",
    "dtPC": "27$118940995_984h1vHMBJUCFFPPWFUPFKPQHVSDBTCUURKUKR-0e0",
    "rxvt": "1744320741000|1744317594172",
}

referer_url = f"https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-a-vista/opcoes/posicoes-em-aberto/posicoes-em-aberto.htm?dataConsulta={data_formatada2}&f=0&dataConsulta={data_formatada2}&f=0"

headers_op2 = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "if-modified-since": "Thu, 10 Apr 2025 07:00:04 GMT",
    "priority": "u=1, i",
    "referer": referer_url,
    "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}

if __name__ == "__main__":
    import requests

    referer_url = f"https://www.b3.com.br/json/{data_formatada}/Posicoes/Empresa/SI_C_OPCPOSABEMP.json"

    response = requests.get(
        referer_url,
        cookies=cookies_op2,
        headers=headers_op2,
    )
