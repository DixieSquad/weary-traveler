import os

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def fetch_data(url: str) -> list[str]:
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(options=options)

    driver.get(url)

    try:
        show_more_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='Show more']"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", show_more_button)
        show_more_button.click()
    except TimeoutException:
        pass

    html_content = driver.page_source

    driver.quit()

    soup = BeautifulSoup(html_content, "html.parser")

    tr_elements = soup.find_all("tr")
    column_names = []
    datalist = []

    for tr in tr_elements:
        td_elements = tr.find_all("td")
        if len(td_elements) < 2:
            th_elements = soup.find_all("th")
            for element in th_elements:
                column_names.append(element.text)
        else:
            items_dict = {}
            for i in range(0, len(td_elements)):
                if i == 0:
                    anchor_href = td_elements[i].find("a")
                    items_dict[column_names[i]] = anchor_href.find("span").text
                else:
                    items_dict[column_names[i]] = td_elements[i].text
            datalist.append(items_dict)
    data = pd.DataFrame(datalist)
    data["Level"] = data["Level"].astype(int)
    data["Value"] = data["Value"].astype(float)

    save_data(data)

    return data["Name"].tolist()


def save_data(data: pd.DataFrame) -> None:
    current_working_dir = os.getcwd()
    folder_path = os.path.join(current_working_dir, "data/ninja")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, "poe_ninja_data.csv")
    data.to_csv(file_path)
