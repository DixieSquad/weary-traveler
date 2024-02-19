from bs4 import BeautifulSoup
from selenium import webdriver
import time
import pandas as pd

url = 'https://poe.ninja/economy/skill-gems' 

def fetch_data(url):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(options=options)

    driver.get(url)

    time.sleep(5)

    html_content = driver.page_source

    driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')

    tr_elements = soup.find_all('tr')
    column_names=[]
    datalist = []

    for tr in tr_elements:
        td_elements = tr.find_all('td')
        if len(td_elements) < 2:
            th_elements = soup.find_all('th')
            for element in th_elements:
                column_names.append(element.text)
        else:
            items_dict = {}
            for i in range(0, len(td_elements)):
                if i == 0:
                    anchor_href = td_elements[i].find('a')
                    items_dict[column_names[i]] = anchor_href.find('span').text
                else:
                    items_dict[column_names[i]] = td_elements[i].text
            datalist.append(items_dict)
    data = pd.DataFrame(datalist)
    data['Level'] = data['Level'].astype(int)
    data['Value'] = data['Value'].astype(float)

    return data
