from datetime import datetime, timedelta

import holidays

feriados_br = holidays.BR()
data = datetime.today() - timedelta(days=1)
while data.weekday() >= 5 or data in feriados_br:
    data -= timedelta(days=1)
data_formatada = data.strftime("%Y%m%d")

cookies_op1 = {
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
    "__cf_bm": "QW0NEe6IGhTwLlYYGW_W_MFmqXwmIjOYcoGL_L12H1E-1744317643-1.0.1.1-oYV5rxFMn1h3h1O3K_X3BZKIdue5b.wu2IcMlLQTOv3q4XxEdQd7FVoAQCk1npQl7sXj1YKWfFrjyTt6tpKvgmdTQRvwCQFZ3nfdtcnizEg",
    "cf_clearance": "5qWUcPVYp.ksv8PPuH9Tou3Zvl4hDeyG3edIgIuo_TI-1744317644-1.2.1.1-FFS9EeuYcMKqjOZmIUvkntLdazvRqWPyqvpEuUEzAc3ZHtX6cjn99269B6.O4aHLj.AQdnwp4cvJzCEHMQLJZqaORLMkoENuGYwefrOLYKPXzfRsBIaYJgxaIQ6GeJhSJoyhXMLlVZEDg0k61.QbTst0xdXWCL.X9Gwn2UMgw3_Dhyryol9ut78qne1U55HUdJ.ARHmcmCZBUDWP9_dawdIPuYzLAWOlqKMW8lvcnKGHNSRf8GXGazPbYIiqRimvsXk8GFE7_GphT59K8cWyyWNQD_haNPg7lo.AEiUCtjZYdbjFpm8hkSOTwYuA8OvzLavUll2cnBl2Aq2uCHaDe7HaYC52Ehv1wq4Azg8JuEE",
    "mp_ec0f5c39312fa476b16b86e4f6a1c9dd_mixpanel": "%7B%22distinct_id%22%3A%20%22%24device%3A1961b770863ee4-02d4ab934e763f8-26011c51-c0000-1961b770863ee4%22%2C%22%24device_id%22%3A%20%221961b770863ee4-02d4ab934e763f8-26011c51-c0000-1961b770863ee4%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D",
    "OptanonConsent": "isGpcEnabled=1&datestamp=Thu+Apr+10+2025+17%3A44%3A27+GMT-0300+(Hor%C3%A1rio+Padr%C3%A3o+de+Bras%C3%ADlia)&version=6.21.0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0003%3A1%2CC0001%3A1%2CC0004%3A1%2CC0002%3A1&geolocation=%3B&AwaitingReconsent=false",
    "JSESSIONID": "FE79C84B612F1BA93CF14BC27B094FE6.lumcor00201b",
    "lumUserSessionId": "fNPUYU_480jKBVaNd59KgcOxCqENHyfZ",
    "lumUserName": "Guest",
    "lumIsLoggedUser": "false",
    "TS0171d45d": "011d592ce12ce4717fde6984cf2cef9ec4330fe54030888f361d31ea4355926d5163c1203b8d339e6927536b017614fb736b4fea35",
    "dtPC": "27$117885762_816h1vHMBJUCFFPPWFUPFKPQHVSDBTCUURKUKR-0e0",
    "dtSa": "-",
    "rxvt": "1744319685771|1744317594172",
    "_ga_SS7FXRTPP3": "GS1.1.1744317644.6.1.1744317886.38.0.0",
}

referer_url = f"https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-a-vista/opcoes/series-autorizadas/series-autorizadas.htm?dtPreg={data_formatada}"

headers_op1 = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "if-modified-since": "Thu, 10 Apr 2025 18:36:19 GMT",
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

    referer_url = f"https://www.b3.com.br/json/{data_formatada}/Series/Empresa/SI_C_OPCSEREMP.json"

    response = requests.get(
        referer_url,
        cookies=cookies_op1,
        headers=headers_op1,
    )
