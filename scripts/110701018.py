import sys
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
from collections import defaultdict
import datetime

PTT_URL = 'https://www.ptt.cc'
BASE_URL = 'https://www.ptt.cc/bbs/Beauty/'
START_INDEX = 3921 # 爬下2024年所有的照片
# START_INDEX = 3652
# START_INDEX = 4003


def over18_session():
    sess = requests.Session()
    payload = {
        'from': '/bbs/Beauty/index.html',
        'yes': 'yes'
    }
    sess.post(f'{BASE_URL}/ask/over18', data=payload)
    return sess


def crawl():
    sess = over18_session()
    index = START_INDEX
    TARGET_1 = 2024
    while index > 0:
        url = f'{BASE_URL}index{index}.html'
        # print(url)
        res = sess.get(url)
        content = res.text

        if res.status_code != 200:
            print(f'無法取得 {url}，結束爬蟲')
            break

        soup = BeautifulSoup(content, "html.parser")
        # 抓取每一篇文章的 <a> 標籤
        entries = soup.select('.r-ent')
        for list_tag in reversed(entries):
            list_a = list_tag.select_one(".title a")
            list_number = list_tag.select_one(".nrec span")
            # list_date = list_tag.select_one(".meta .date")

            if list_a:
                href = list_a['href']
                title = list_a.text
            else:  # 忽略空標題或無網址
                continue

            if '[公告]' in title or 'Fw:[公告]' in title:
                continue  # 忽略公告相關標題

            if list_number:
                number = list_number.text
            else:
                number = 0  # 推和噓互相抵消

            full_link = f'{PTT_URL}{href}'
            date_timeString = int(full_link.split('/')[-1].split('.')[1])
            # print(date_timeString)
            time_struct = time.localtime(date_timeString)
            year = time_struct.tm_year
            month_day = f"{time_struct.tm_mon:02}{time_struct.tm_mday:02}"

            print(f"{index},{title},{full_link},{number},{year},{month_day}")

            if year == TARGET_1:

                article_data = {
                    "date": month_day,
                    "title": title,
                    "url": full_link
                }
                with open(f"./output/articles_{TARGET_1}.jsonl", "a", encoding="utf-8") as outfile:
                    json.dump(article_data, outfile, ensure_ascii=False)
                    outfile.write("\n")

            # 遇到第一次的12月
            if year == TARGET_1 - 1:
                print("結束")
                index = 0

        time.sleep(0.5)
        index -= 1
        # break


def image(start_date, end_date):

    count = 0
    image_urls = []
    TARGET = 2024

    with open(f"./output/articles_{TARGET}.jsonl", "r", encoding="utf-8") as f:
        articles_dataset = [json.loads(line) for line in f]

    for data in articles_dataset:
        date = data["date"]

        if date >= start_date and date <= end_date:
            print(data)
            count += 1
            sess = over18_session()
            url = data["url"]

            res = sess.get(url)
            content = res.text
            soup = BeautifulSoup(content, "html.parser")
            main_content = soup.find(id="main-content")
            full_text = main_content.get_text()

            if "※ 發信站:" not in full_text:
                print("沒有發信站")
                continue

            main_part = full_text.split("※ 發信站")[0]

            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                if re.match(r'^https?://.*\.(jpg|jpeg|png|gif)$', href, re.IGNORECASE):
                    image_urls.append(href)

    output = {
        "image_urls": image_urls
    }

    with open(f"./output/image_{TARGET}_{start_date}_{end_date}.json", "w", encoding="utf-8") as keyword_outfile:
        json.dump(output, keyword_outfile,
                  ensure_ascii=False)
        keyword_outfile.write("\n")


def main():
    start_time = time.time()
    if len(sys.argv) == 2 and sys.argv[1] == 'crawl':
        print("開始即時爬蟲（每篇即時輸出）...")
        try:
            crawl()
        except KeyboardInterrupt:
            print("\n已手動中斷。")
    elif len(sys.argv) == 4 and sys.argv[1] == "image":
        start_date = sys.argv[2]
        end_date = sys.argv[3]
        image(start_date, end_date)
    else:
        print("用法錯誤")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"總共花費時間：{elapsed_time:.2f} 秒")


if __name__ == '__main__':
    main()
