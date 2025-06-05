# EAI_final

## 資料蒐集（爬蟲說明）
在裡面主要蒐集的2024年的所有圖片為訓練資料，透過兩支 Python 程式分別進行文章蒐集與圖片下載，具體流程如下：
> 此步驟流程皆在本地端電腦執行

### 本地端環境設置
使用資料中附的 requirement.txt
```python
pip install -r requirements.txt
```
在開始進行資料爬蟲之前請先在放置爬蟲py檔案的資料夾下新增一個 output 以免資料無法儲存。

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

## 資料前處理（Face Cropping & 過濾模糊照）
使用 face-crop-plus 進行臉部裁切與圖片品質過濾，並於 Kaggle Notebook 上執行，環境配有 NVIDIA P100 GPU。

> 此步驟流程皆在 kaggle 執行

> 前處理所使用的原始圖片皆來自自行上傳至 Kaggle Dataset 的 downloaded_images_2024，具體執行步驟使用的程式碼來自資料夾 face_crop_and_filter.ipynb。

> 如果是使用 .ipynb 請直接依照裡面的框框執行即可（需要安裝的套件已在 kaggle 以及裡面的格子中）

> 因 downloaded_images_2024 有違反 kaggle 的資料集設定無法轉為公用因此不附連結

### 使用套件安裝
```bash
pip install face-crop-plus
```
### 處理步驟（下面的資料夾名稱是根據在 kaggle 上執行放置）
1. 初步臉部裁切（256x256）：將原始圖片中偵測到的臉部裁切為 256x256 的圖片，並保留於暫存資料夾`/kaggle/working/cropped_image_temp_256_256`中。
2. 過濾模糊照片：定義模糊圖片為 Laplacian 變異數小於 100，過濾後的高品質圖片將複製到新的資料夾`/kaggle/working/cropped_image_temp_NO_BLURRY`中。
3. 最終臉部裁切（64x64）：針對非模糊圖片再次裁切臉部，尺寸縮小為 64x64，並輸出為訓練用資料集`/kaggle/working/cropped_image_64_64_NO_BLURRY_Final`。
4. 補充：壓縮處理後圖片：以便更好的放置到 kaggle 上的 dataset 當中
```bash
   zip -rq /kaggle/working/cropped_image_64_64_NO_BLURRY_Final.zip /kaggle/working/cropped_image_64_64_NO_BLURRY_Final
```
5. 放到 kaggle 上的 dataset，我這邊是將它放在 cropped_image_64_64_NO_BLURRY_Final 當中。

## 模型訓練
為了訓練生成模型，以 Diffusers 套件提供的 UNet 結構搭配 DDPM 方法進行。

> 此步驟流程皆在 kaggle 執行

> 使用訓練資料是前處理所產生的最終檔案 cropped_image_64_64_NO_BLURRY_Final，同樣也會上傳 kaggle 成為 dataset 名為 "cropped_image_64_64_NO_BLURRY_Final"，具體執行步驟使用的程式碼來自資料夾 train_diffusion_model.ipynb。

> 如果是使用 .ipynb 請直接依照裡面的框框執行即可（需要安裝的套件已在 kaggle 以及裡面的格子中）

> kaggle 資料集連結：[cropped_image_64_64_NO_BLURRY_Final]https://kaggle.com/datasets/050bd49377c744f6948b7d7fd906db7f7abf54eb3161bc2b2230c512b571ac49

### 使用套件安裝
```bash
pip install -U diffusers[training]
```
### 訓練過程的敘述
1. 使用 1000 steps 去增加噪音
2. 曾經嘗試果使用cosine以及linear的方式，最後選擇linear的方式，因其表現最佳。
3. 訓練的參數
```
    image_size = 64  # the generated image resolution
    train_batch_size = 16 # 越小訓練結果越佳
    eval_batch_size = 16  # how many images to sample during evaluation
    num_epochs = 73 # 因 kaggle 時間的上限 12hr 這個是他的上限可以訓練的 epoch
    gradient_accumulation_steps = 1
    learning_rate = 1e-4
    lr_warmup_steps = 500
    save_image_epochs = 10 # 每 10 epoch 會透過 DDPM pipeline 隨機生成圖片並儲存，供後續比較訓練過程中的生成品質
    save_model_epochs = 10 # 每訓練十個會儲存一次模型，同時每一個 Epoch 都會判別他是否為最好的模型（以 epoch loss 最低為最好）
    mixed_precision = "fp16"
    output_dir = "ddpm-PTTbeauty-64-v11-linear-80"
```
4. 結果最後會生成在 ddpm-PTTbeauty-64-v11-linear-80 中，同樣會進行下載並重新成為一個 kaggle 上的 dataset

## 圖片生成以及計算最終結果

> 此步驟流程皆在 kaggle 執行

> 使用的模型是 ddpm-PTTbeauty-64-v11-linear-80 這個 kaggle dataset 裡面中的 best_model也就是最好的資料

> 如果是使用 .ipynb 請直接依照裡面的框框執行即可（需要安裝的套件已在 kaggle 以及裡面的格子中）

### 使用套件安裝
```bash
pip install -q diffusers transformers accelerate torchvision safetensors
```
### 處理步驟（以下資料夾名稱與路徑為 Kaggle 上使用時的實際配置）
1. 設定模型與輸出資料夾：指定上一個步驟的 dataset 已訓練好的 DDPM 模型路徑（/kaggle/input/ddpm-PTTbeauty-64-v11-linear-80/best_model）及輸出生成圖像的資料夾。
2. 載入 DDPM Pipeline
   - 使用 DDPMPipeline 載入訓練好的模型，並配置生成參數
   - 生成張數：10,000 張
   - 批次大小：32
   - 每張圖大小：64x64
   - 推論步數：300（之前嘗試過100,1000，最後取時間含結果最佳）
3. 生成與儲存圖像：使用 pipeline() 方法逐批生成圖像，儲存為 PNG 格式，並將記憶體手動釋放以節省空間。
4. 壓縮並執行 FID 分數計算（助教提供的 FID 資料有一起上傳進行分數計算）
5. 下載最後生成的結果

