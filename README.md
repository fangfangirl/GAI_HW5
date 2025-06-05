# EAI_final

## 資料蒐集（爬蟲說明）
在裡面主要蒐集的2024年的所有圖片為訓練資料，透過兩支 Python 程式分別進行文章蒐集與圖片下載，具體流程如下：

### 爬取文章資訊與圖片連結
- 檔案位置：scripts/ptt_crawler.py
- 使用套件：requests, BeautifulSoup, json, re, time
- 功能說明（如作業四的操作）：
  - 模擬登入 PTT 18 禁頁面以繞過驗證
  - 從 index3921.html 開始向下遞減爬取表特板文章（涵蓋 2024 全年）
  - 過濾掉 [公告]、無標題或無人氣的文章
  - 篩選出發文時間為 2024 年的文章，並抓取其標題與連結
  - 存成 ./output/articles_2024.jsonl（每列為一筆 JSON 文章資訊）
  - 再透過 image(start_date, end_date) 函數擷取指定日期內文章中的圖片連結，儲存至 ./output/image_2024_0101_1231.json
- 執行指令：
```python
python ptt_crawler.py crawl
python ptt_crawler.py image 0101 1231
```
### 批次下載圖片
- 檔案位置：scripts/image_downloader.py
- 使用套件：aiohttp, aiofiles, asyncio, PIL, tqdm
- 功能說明：
  - 使用非同步方式（asyncio）並行下載圖片，加速處理流程
  - 讀取前一步生成的圖片連結檔案（如：image_2024_0101_1231.json）
  - 嘗試最多 3 次連線，每張圖片會自動以原始格式命名儲存於 ./output/downloaded_images_2024/ 資料夾中
  - 若下載失敗，會記錄於 ./output/failed.txt
- 執行指令：
```python
python image_downloader.py
```
