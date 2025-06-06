import os
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_emart_all_tab_sale_items():
    # Chrome 옵션 설정
    options = Options()
    # options.add_argument("--headless")  # 개발 중에는 headless 비활성화
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # 드라이버 시작
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://eapp.emart.com/webapp/product/flyer?trcknCode=main_leaflet")

    # 탭 버튼 로딩 대기
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".ern-leaflet-sub-menu button.exhibition-list-item"))
    )

    items = []
    visited_ids = set()

    tab_buttons = driver.find_elements(By.CSS_SELECTOR, ".ern-leaflet-sub-menu button.exhibition-list-item")

    for idx, tab in enumerate(tab_buttons):
        try:
            driver.execute_script("arguments[0].click();", tab)
            time.sleep(2)

            while True:
                product_elements = driver.find_elements(By.CSS_SELECTOR, "div.swiper-slide-active div.product-list")

                for product in product_elements:
                    try:
                        # 상품명 추출
                        title_el = product.find_elements(By.CSS_SELECTOR, "strong.title")
                        if not title_el:
                            continue
                        name = title_el[0].text.strip()

                        # 이미지 URL → itemId 추출
                        img_el = product.find_elements(By.CSS_SELECTOR, "div.product-img img")
                        product_link = ""
                        item_id = None
                        if img_el:
                            img_url = img_el[0].get_attribute("data-img") or img_el[0].get_attribute("src")
                            match = re.search(r'/(\d{10,})\.png', img_url)
                            if match:
                                item_id = match.group(1)
                                product_link = f"https://www.ssg.com/item/itemView.ssg?itemId={item_id}"

                        if not item_id or item_id in visited_ids:
                            continue
                        visited_ids.add(item_id)

                        # 가격 정보
                        price_el = product.find_elements(By.CSS_SELECTOR, "div.final-price span.value")
                        price = price_el[0].text if price_el else ""

                        origin_price_el = product.find_elements(By.CSS_SELECTOR, "div.origin-price span.value")
                        original_price = origin_price_el[0].text if origin_price_el else ""

                        discount_el = product.find_elements(By.CSS_SELECTOR, "div.discount")
                        discount = discount_el[0].text if discount_el else ""

                        # 결과 저장
                        items.append({
                            "카테고리": tab.text.strip(),
                            "상품명": name,
                            "상품링크": product_link,
                            "판매가": price,
                            "정상가": original_price,
                            "할인율": discount
                        })

                    except Exception as e:
                        print(f"[에러] 상품 처리 중 오류: {e}")
                        continue

                # 다음 슬라이드 버튼 클릭
                next_button = driver.find_elements(By.CSS_SELECTOR, "button.swiper-button-next")
                if not next_button or not next_button[0].is_enabled():
                    break

                driver.execute_script("arguments[0].click();", next_button[0])
                time.sleep(1.5)

        except Exception as e:
            print(f"[에러] 탭 {idx} ({tab.text}) 처리 중 오류: {e}")
            continue

    driver.quit()
    return pd.DataFrame(items)

# 실행 예시
if __name__ == "__main__":
    df = get_emart_all_tab_sale_items()
    df.to_csv("emart_items.csv", index=False, encoding="utf-8-sig")
    print(f"{len(df)}개 항목 저장 완료.")
