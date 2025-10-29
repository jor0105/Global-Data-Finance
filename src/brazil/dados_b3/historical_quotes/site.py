principal = r"https://bvmf.bmfbovespa.com.br/en-us/historical-quotes/FormConsultaValidaI.asp?arq="


def get_urls(first_year, last_year):
    list_urls = []
    for year in range(first_year, last_year + 1):
        url = principal + str(year) + ".ZIP"
        list_urls.append(url)

    return list_urls


if __name__ == "__main__":
    list_urls = get_urls(2000, 2025)
