url_cap_social_1 = "https://sistemaswebb3-listados.b3.com.br/shareCapitalProxy/ShareCapitalCall/GetList/eyJuYW1lIjoiIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMH0="
url_cap_social_2 = "https://sistemaswebb3-listados.b3.com.br/shareCapitalProxy/ShareCapitalCall/GetList/eyJuYW1lIjoiIiwicGFnZU51bWJlciI6MiwicGFnZVNpemUiOjEyMH0="
url_cap_social_3 = "https://sistemaswebb3-listados.b3.com.br/shareCapitalProxy/ShareCapitalCall/GetList/eyJuYW1lIjoiIiwicGFnZU51bWJlciI6MywicGFnZVNpemUiOjEyMH0="
url_cap_social_4 = "https://sistemaswebb3-listados.b3.com.br/shareCapitalProxy/ShareCapitalCall/GetList/eyJuYW1lIjoiIiwicGFnZU51bWJlciI6NCwicGFnZVNpemUiOjEyMH0="
url_cap_social_5 = "https://sistemaswebb3-listados.b3.com.br/shareCapitalProxy/ShareCapitalCall/GetList/eyJuYW1lIjoiIiwicGFnZU51bWJlciI6NSwicGFnZVNpemUiOjEyMH0="
url_cap_social_6 = "https://sistemaswebb3-listados.b3.com.br/shareCapitalProxy/ShareCapitalCall/GetList/eyJuYW1lIjoiIiwicGFnZU51bWJlciI6NiwicGFnZVNpemUiOjEyMH0="
url_cap_social_7 = "https://sistemaswebb3-listados.b3.com.br/shareCapitalProxy/ShareCapitalCall/GetList/eyJuYW1lIjoiIiwicGFnZU51bWJlciI6NywicGFnZVNpemUiOjEyMH0="
url_cap_social_8 = "https://sistemaswebb3-listados.b3.com.br/shareCapitalProxy/ShareCapitalCall/GetList/eyJuYW1lIjoiIiwicGFnZU51bWJlciI6OCwicGFnZVNpemUiOjEyMH0="
url_cap_social_9 = "https://sistemaswebb3-listados.b3.com.br/shareCapitalProxy/ShareCapitalCall/GetList/eyJuYW1lIjoiIiwicGFnZU51bWJlciI6OSwicGFnZVNpemUiOjEyMH0="


# Defina até qual número vai a lista
url_cap_social_max = 9

# Gera a lista automaticamente
url_cap_social_list = [
    globals()[f"url_cap_social_{i}"] for i in range(1, url_cap_social_max + 1)
]
