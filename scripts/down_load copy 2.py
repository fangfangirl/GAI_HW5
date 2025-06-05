import os
import json
import asyncio
import aiohttp
import aiofiles
from PIL import Image
from io import BytesIO
from tqdm.asyncio import tqdm_asyncio

TARGET = 2024
save_dir = f"./downloaded_images_{TARGET}"
os.makedirs(save_dir, exist_ok=True)

MAX_CONCURRENT_DOWNLOADS = 20

with open(f"./output/image_{TARGET}_0101_1231.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    urls = data["image_urls"]

sem = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

# 用於記錄失敗的 URL
failed_urls = []


async def fetch_and_save(session, idx, url):
    async with sem:
        for attempt in range(3):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        image = Image.open(BytesIO(content))

                        # 使用原始格式與副檔名
                        image_format = image.format if image.format else "PNG"
                        extension = image_format.lower()
                        filename = f"img_{idx:05d}.{extension}"
                        filepath = os.path.join(save_dir, filename)

                        if os.path.exists(filepath):
                            return f"已存在: {filename}"

                        async with aiofiles.open(filepath, "wb") as f:
                            await f.write(content)

                        return f"完成: {filename}"
                    else:
                        await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(1)

        failed_urls.append(url)
        return f"失敗: {url}"


async def main():
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [fetch_and_save(session, idx, url)
                 for idx, url in enumerate(urls)]
        for f in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="下載中"):
            result = await f
            print(result)

    # 寫入失敗的 URL 到 failed.txt
    if failed_urls:
        async with aiofiles.open("failed.txt", "w", encoding="utf-8") as f:
            await f.write("\n".join(failed_urls))
        print(f"\n 有 {len(failed_urls)} 張圖片下載失敗，已儲存至 failed.txt")

if __name__ == "__main__":
    asyncio.run(main())
