import os
import logging
import time
import json
import re
import requests
import numpy as np
import scipy.sparse as sparse

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

firefox_options = Options()
firefox_options.add_argument("--headless")
driver = webdriver.Firefox(service=Service("./geckodriver"), options=firefox_options)


def get_colab(dblp_id, session):

    c = session.get(f"https://dblp.org/pid/{dblp_id}.xml").content
    colab = [x for x in re.findall(r'pid="(.*?)\"', str(c)) if x != dblp_id]
    colab = {k: colab.count(k) for k in set(colab)}

    return dict(sorted(colab.items(), key=lambda item: item[1], reverse=True))


if __name__ == "__main__":

    start_url = "https://csrankings.org/#/index?all&world"
    logging.info("Accesing %s ..." % start_url)
    driver.get(start_url)

    try:
        logging.info("Waiting for JS to load...")
        elem = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "ranking"))
        )
        scroll = elem.find_element(By.XPATH, "..")
        driver.execute_script("arguments[0].scrollBy(0, arguments[1]);", scroll, 270)
        driver.implicitly_wait(10)

    finally:
        logging.info("Scrapping content")
        content = driver.page_source.encode("utf-8")
        soup = BeautifulSoup(content, "html.parser")
        body = soup.find("table", {"id": "ranking"})
        rows = body.find_all("tr")

    countries = dict()
    with requests.Session() as s:
        logging.info("Extracting countries...")
        logging.info("Extracting universities...")
        for i, row in enumerate(rows):
            faculty = dict()

            if re.findall(r"<div\ id\=\"(.*?)\-faculty\"", str(row)):
                title = rows[i - 2].find_all("span")[1].text
                country = re.findall(
                    r"flags\/(.*?).png", rows[i - 2].find("img").attrs["src"]
                )[0]
                content = row.find_all("td")[0]

                if country not in countries:
                    countries[country] = {}

                if title:
                    for p in content.find_all("tr")[1::2]:
                        try:
                            name = p.find("a").text
                            href = [
                                x.find("a", href=re.compile("dblp"))
                                for x in p.find_all("td")
                            ]
                            href = next(x.attrs["href"] for x in href if x)
                            href = re.findall(r"pid\/(.*?).html", s.get(href).url)[0]
                            faculty[name] = {"dblp": href, "colab": get_colab(href, s)}

                        except:
                            continue
                    countries[country][title] = faculty
                else:
                    continue

    logging.info("Dumping file...")
    os.makedirs('./data/', exist_ok=True)
    with open("./data/dump.js", "w") as w:
        json.dump(countries, w)
    driver.quit()

    authors, coauthors, path = [], [], []

    for country in countries:
        for uni in countries[country]:
            for author in countries[country][uni]:
                authors.append(countries[country][uni][author]["dblp"])
                coauthors.append(countries[country][uni][author]["colab"])
                path.append([country, uni, author])

    coauthors_flat = [list(x.keys()) for x in coauthors]
    coauthors_flat = [item for sublist in coauthors_flat for item in sublist]

    coauthor_matrix = []
    for i, author_i in enumerate(authors):
        cm = []
        coauthors_i = countries[path[i][0]][path[i][1]][path[i][2]]["colab"]
        for j, author_j in enumerate(authors):
            cm.append(coauthors_i[author_j] if author_j in coauthors_i else 0)
        coauthor_matrix.append(cm)
    coauthor_matrix = sparse.csr_matrix(np.array(coauthor_matrix))
    sparse.save_npz("./coauthor.npz", coauthor_matrix)

    with open("./data/path.np", "wb") as w:
        np.save(w, np.array(path))
