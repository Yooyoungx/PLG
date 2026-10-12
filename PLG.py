#!/usr/bin/env python3
# encoding=utf-8
import traceback
import argparse
import base64
import json
import logging
import os
import pathlib
import aiohttp
import platform
import random

import re
from io import BytesIO
from PIL import Image

import shutil
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse
import warnings
import webbrowser
from datetime import datetime
from typing import Optional
import asyncio
import time
import requests

import nodriver as uc
from nodriver import cdp
from nodriver.core.config import Config
from urllib3.exceptions import InsecureRequestWarning


import nodriver.cdp.page as cdp_page
import nodriver.cdp.input_ as cdp_input

import util
from NonBrowser import NonBrowser

try:
    import ddddocr
except Exception as exc:
    print(exc)
    pass
CONST_APP_VERSION = "1"

CONST_MAXBOT_ANSWER_ONLINE_FILE = "MAXBOT_ONLINE_ANSWER.txt"
CONST_MAXBOT_CONFIG_FILE = "settings.json"
CONST_MAXBOT_EXTENSION_STATUS_JSON = "status.json"
CONST_MAXBOT_EXTENSION_NAME = "Maxbotplus_1.0.0"
CONST_MAXBOT_INT28_FILE = "MAXBOT_INT28_IDLE.txt"
CONST_MAXBOT_LAST_URL_FILE = "MAXBOT_LAST_URL.txt"
CONST_MAXBOT_QUESTION_FILE = "MAXBOT_QUESTION.txt"
CONST_MAXBLOCK_EXTENSION_NAME = "Maxblockplus_1.0.0"
CONST_MAXBLOCK_EXTENSION_FILTER = [
    "*.doubleclick.net/*",
    "*.ssp.hinet.net/*",
    "*a.amnet.tw/*",
    "*anymind360.com/*",
    "*adx.c.appier.net/*",
    "*cdn.cookielaw.org/*",
    "*clarity.ms/*",
    "*cloudfront.com/*",
    "*cms.analytics.yahoo.com/*",
    "*e2elog.fetnet.net/*",
    "*fundingchoicesmessages.google.com/*",
    "*ghtinc.com/*",
    "*google-analytics.com/*",
    "*googletagmanager.com/*",
    "*googletagservices.com/*",
    "*img.uniicreative.com/*",
    "*lndata.com/*",
    "*match.adsrvr.org/*",
    "*onead.onevision.com.tw/*",
    "*play.google.com/log?*",
    "*popin.cc/*",
    "*rollbar.com/*",
    "*sb.scorecardresearch.com/*",
    "*tagtoo.co/*",
    "*ticketmaster.sg/js/adblock*",
    "*ticketmaster.sg/js/adblock.js*",
    "*tixcraft.com/js/analytics.js*",
    "*tixcraft.com/js/common.js*",
    "*tixcraft.com/js/custom.js*",
    "*treasuredata.com/*",
    "*www.youtube.com/youtubei/v1/player/heartbeat*",
]

CONST_CITYLINE_SIGN_IN_URL = "https://www.cityline.com/Login.html?targetUrl=https%3A%2F%2Fwww.cityline.com%2FEvents.html"
CONST_FAMI_SIGN_IN_URL = "https://www.famiticket.com.tw/Home/User/SignIn"
CONST_HKTICKETING_SIGN_IN_URL = "https://premier.hkticketing.com/Secure/ShowLogin.aspx"
CONST_KHAM_SIGN_IN_URL = "https://kham.com.tw/application/UTK13/UTK1306_.aspx"
CONST_KKTIX_SIGN_IN_URL = "https://kktix.com/users/sign_in?back_to=%s"
CONST_TICKET_SIGN_IN_URL = "https://ticket.com.tw/application/utk13/utk1306_.aspx"
CONST_URBTIX_SIGN_IN_URL = "https://www.urbtix.hk/member-login"

CONST_FROM_TOP_TO_BOTTOM = "from top to bottom"
CONST_FROM_BOTTOM_TO_TOP = "from bottom to top"
CONST_CENTER = "center"
CONST_RANDOM = "random"
CONST_SELECT_ORDER_DEFAULT = CONST_FROM_TOP_TO_BOTTOM

CONT_STRING_1_SEATS_REMAINING = ['@1 seat(s) remaining', '剩餘 1@', '@1 席残り']

CONST_OCR_CAPTCH_IMAGE_SOURCE_NON_BROWSER = "NonBrowser"
CONST_OCR_CAPTCH_IMAGE_SOURCE_CANVAS = "canvas"

CONST_WEBDRIVER_TYPE_NODRIVER = "nodriver"
CONST_CHROME_FAMILY = ["chrome", "edge", "brave"]

warnings.simplefilter('ignore', InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig()
logger = logging.getLogger('logger')

# ==========================================
# [設定區] 檔案路徑與常數
# ==========================================
CONST_MAXBOT_CONFIG_FILE = "settings.json"
warnings.simplefilter('ignore', InsecureRequestWarning)

# ==========================================
# [核心功能 1] 讀取設定檔
# ==========================================


def get_config_dict(args):
    app_root = util.get_app_root()

    # 1. 預設使用原本的常數 (例如 settings.json)
    target_filename = CONST_MAXBOT_CONFIG_FILE

    # 2. 如果 GUI 有傳入指定的設定檔名 (例如 settings-A.json)，就把它替換掉
    if hasattr(args, 'input') and args.input and len(args.input) > 0:
        target_filename = args.input

    # 3. 組合出完整的「絕對路徑」，確保 .exe 執行時絕對找得到！
    config_filepath = os.path.join(app_root, target_filename)

    config_dict = None
    if os.path.isfile(config_filepath):
        with open(config_filepath, 'r', encoding='utf-8') as json_data:
            config_dict = json.load(json_data)

            # 將 UI 參數覆蓋 (這段維持你原本的邏輯不變)
            arg_map = {
                "headless": ["advanced", "headless"],
                "homepage": ["homepage"],
                "ticket_number": ["ticket_number"],
                "browser": ["browser"],
                "proxy_server": ["advanced", "proxy_server_port"],
                "window_size": ["advanced", "window_size"]
            }
            for arg_name, json_path in arg_map.items():
                if hasattr(args, arg_name):
                    val = getattr(args, arg_name)
                    if val and str(val).strip():
                        d = config_dict
                        for key in json_path[:-1]:
                            d = d[key]
                        d[json_path[-1]] = val

            config_dict["token"] = util.get_token()

            # ==========================================
            # 🔥 神級修復：把目前的設定檔路徑，當作一個變數塞進字典裡！
            # 這樣 FubonBot 裡面的 config.get("config_filepath") 才抓得到東西
            # ==========================================
            config_dict["config_filepath"] = config_filepath

    else:
        # 加上一個防呆機制：如果找不到設定檔，印出錯誤訊息方便除錯
        print(f"找不到設定檔: {config_filepath}")

    return config_dict


class FubonBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""
        #  註冊彈窗監聽器 (只要有彈窗就會呼叫 self._handle_dialog)
        # self.tab.add_handler(
        #    cdp.page.JavascriptDialogOpening, self._handle_dialog)
        # 狀態變數
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_seat_selected = False
        # [新增] Telegram 通知相關狀態
        self.is_telegram_sent = False
        self.bot_start_time = time.time()  # 記錄機器人啟動的當下時間

        # [新增] 初始化 ddddocr 引擎，關閉廣告訊息保持 Log 乾淨
        print(">>> [系統] 正在載入 ddddocr 辨識模型...")
        self.ocr = ddddocr.DdddOcr(show_ad=False)

        # 音效狀態
        self.played_sound_ticket = False
        self.ticket_sound_tag = {"last_key": None}

        # 暫停控制檔案 (與 Settings_old 連動的關鍵)
        self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # 讀取設定檔
        self.date_auto_select = config.get("date_auto_select", {
            "enable": True, "mode": "from top to bottom", "date_keyword": ""
        })
        self.area_auto_select = config.get("area_auto_select", {
            "enable": True, "mode": "from top to bottom", "area_keyword": ""
        })

        # 讀取進階暫停/接續設定
        advanced = config.get("advanced", {})
        self.keyword_pause = advanced.get("keyword_pause", "")
        self.keyword_resume = advanced.get("keyword_resume", "")
        # 確保延遲時間是數字，預設為 0
        try:
            self.keyword_pause_sec = float(
                advanced.get("keyword_pause_sec", 0))
        except:
            self.keyword_pause_sec = 0
        try:
            self.keyword_resume_sec = float(
                advanced.get("keyword_resume_sec", 0))
        except:
            self.keyword_resume_sec = 0

    async def run(self):
        print(f"機器人啟動！(目標張數: {self.ticket_number})")

        d_mode = self.date_auto_select.get("mode", "預設")
        a_mode = self.area_auto_select.get("mode", "預設")
        print(f"模式設定 -> 日期: {d_mode} | 區域: {a_mode}")

        # 顯示關鍵字監控狀態
        if self.keyword_pause:
            print(f"監控暫停關鍵字: {self.keyword_pause}")
        if self.keyword_resume:
            print(f"監控接續關鍵字: {self.keyword_resume}")

        print("等待網頁載入中...")

        try:
            if self.config.get('homepage'):
                await self.tab.get(self.config['homepage'])
        except Exception as e:
            print(f"開啟網頁錯誤: {e}")

        while True:
            try:
                # ---------------------------------------------------
                # 0. 設定檔熱重載 (Hot Reload)
                # ---------------------------------------------------
                await self.reload_config_if_changed()

                # ---------------------------------------------------
                # 1. 執行關鍵字檢查 (自動暫停/繼續)
                # ---------------------------------------------------
                await self.check_flow_keywords()

                # ---------------------------------------------------
                # 2. 檢查是否處於暫停狀態
                # ---------------------------------------------------
                if os.path.exists(self.PAUSE_FILE):
                    # print(f">>> 機器人暫停中 (檢測到 {self.PAUSE_FILE})...")
                    await asyncio.sleep(0.5)
                    continue  # 直接跳過後面所有搶票邏輯

                # ---------------------------------------------------
                # 3. 正常的搶票流程
                # ---------------------------------------------------
                current_url = await self.tab.evaluate("window.location.href")

                # 檢測頁面切換
                if current_url and current_url != self.last_url:
                    print(f"偵測到頁面切換: {current_url}")

                    # [狀態重置] 離開日期或詳情頁時，重置日期選擇狀態
                    if "GameInfo" not in current_url and "ActivityInfo/Details" not in current_url:
                        self.is_date_selected = False

                    # [區域頁面重入檢測] 如果卡在區域選擇頁，嘗試刷新
                    if '/UTK02/UTK' in current_url.upper() and 'PRODUCT_ID=' in current_url.upper():
                        if self.is_area_selected:
                            print(">>> [重入檢測] 再次回到區域選擇頁面，重置狀態並刷新...")
                            self.is_area_selected = False
                            try:
                                await self.tab.reload()
                                await asyncio.sleep(0.5)
                            except:
                                pass

                    # 更新最後網址
                    self.last_url = current_url

                # 分派具體動作 (如選日期、選位)
                if current_url:
                    await self.dispatch_action(current_url)

            except Exception as e:
                # print(f"Main loop exception: {e}")
                pass

            await asyncio.sleep(0.5)

    async def check_flow_keywords(self):
        """
        [新增功能] 檢查頁面關鍵字以自動暫停或繼續
        邏輯完全參考 IBON_AAA
        """
        # 如果沒有設定關鍵字，就直接離開，節省資源
        if not self.keyword_pause and not self.keyword_resume:
            return

        try:
            # 獲取頁面文字 (包含 body 內的所有可見文字)
            body_text = await self.tab.evaluate("document.body.innerText")
            if not body_text:
                return

            # A. 檢查是否需要「自動繼續」 (當機器人處於暫停狀態時特別有用)
            if self.keyword_resume and os.path.exists(self.PAUSE_FILE):
                if self.keyword_resume in body_text:
                    print(f">>> 發現接續關鍵字: '{self.keyword_resume}'")
                    if self.keyword_resume_sec > 0:
                        print(f"    等待 {self.keyword_resume_sec} 秒後接續...")
                        await asyncio.sleep(self.keyword_resume_sec)

                    try:
                        os.remove(self.PAUSE_FILE)  # 刪除暫停檔 -> 恢復運作
                        print(">>> 已刪除暫停檔，機器人恢復運作！")
                    except Exception as e:
                        print(f"刪除暫停檔失敗: {e}")

            # B. 檢查是否需要「自動暫停」 (當機器人正在運作時)
            if self.keyword_pause and not os.path.exists(self.PAUSE_FILE):
                if self.keyword_pause in body_text:
                    print(f">>> 發現暫停關鍵字: '{self.keyword_pause}'")
                    if self.keyword_pause_sec > 0:
                        print(f"    等待 {self.keyword_pause_sec} 秒後暫停...")
                        await asyncio.sleep(self.keyword_pause_sec)

                    try:
                        with open(self.PAUSE_FILE, "w") as f:
                            f.write("paused by keyword")  # 建立暫停檔 -> 停止運作
                        print(">>> 已建立暫停檔，機器人進入暫停模式！")
                    except Exception as e:
                        print(f"建立暫停檔失敗: {e}")

        except Exception:
            pass

    async def dispatch_action(self, url):
        """任務分發中心 (專為 UTK 售票系統與富邦勇士修改)"""
        upper_url = url.upper()

        # ==========================================
        # [新增] 狀態重置區：當回到首頁時，完全重置所有鎖定狀態
        # ==========================================
        if 'UTK0101_' in upper_url:
            self.is_date_selected = False
            self.is_area_selected = False
            self.is_seat_selected = False
            self.is_telegram_sent = False
            return

        # ==========================================
        # 0. 購票成功 (UTK0206_ 結帳/購物車頁面)
        # ==========================================
        elif 'UTK0206_' in upper_url:
            if getattr(self, 'is_seat_selected', False):
                print(">>> [系統] 🎉 恭喜！成功進入購物車/結帳頁面！自動化流程已完成！")
                self.is_seat_selected = False  # 防呆重置

            # 觸發 Telegram 通知
            if not getattr(self, 'is_telegram_sent', False):
                try:
                    import time
                    from datetime import datetime

                    # 計算總耗時
                    current_elapsed = time.time() - getattr(self, 'bot_start_time', time.time())

                    msg_content = (
                        f"🎉 <b>富邦勇士 搶票成功！</b>\n"
                        f"--------------------------------\n"
                        f"🔗 <a href='{url}'>點此前往結帳</a>\n"
                        f"🎫 目標張數: {self.ticket_number} 張\n"
                        f"⏱️ 總耗時: {current_elapsed:.3f} 秒\n"
                        f"📅 時間: {datetime.now().strftime('%H:%M:%S')}\n"
                        f"⚠️ <b>請盡速在 10 分鐘內完成付款！</b>"
                    )

                    await self.send_telegram_message(msg_content)
                    self.is_telegram_sent = True

                except Exception as e:
                    print(f"⚠️ Telegram 通知準備失敗: {e}")

            return  # 已經在結帳頁面了，停止往下執行

        # ==========================================
        # 1. 第一階段：日期/場次選擇 (UTK0201_)
        # ==========================================
        elif 'UTK0201_' in upper_url:
            # 【關鍵修復】只要進入日期頁面，強制重置後續所有的狀態鎖！
            # 確保不管是第一輪還是第 N 輪，區域和座位都能正常觸發
            self.is_area_selected = False
            self.is_seat_selected = False
            self.is_telegram_sent = False

            if not self.is_date_selected:
                await self.select_date()

        # ==========================================
        # 2. 第二階段：區域選擇 (UTK0204_ 且沒有座位表時)
        # ==========================================
        elif 'UTK0204_' in upper_url and not self.is_area_selected:
            # 進入區域前，重置座位選擇標記
            self.is_seat_selected = False
            if self.area_auto_select.get("enable", True):
                await self.select_area_legacy()

        # ==========================================
        # 3. 第三階段：座位選擇 -> OCR -> 下一步 -> 錯誤重試
        # ==========================================
        elif 'UTK0205_' in upper_url or ('UTK0204_' in upper_url and getattr(self, 'is_area_selected', False)):

            # 【環節 A：錯誤重試】檢查是否有因為驗證碼錯誤跳出的 jQuery 彈窗
            is_error_dialog_closed = await self.check_and_close_jquery_dialog()

            if is_error_dialog_closed:
                print(">>> [系統] 發現驗證碼錯誤彈窗！準備重新辨識...")
                import asyncio
                await asyncio.sleep(0.5)  # 等待新圖片載入

                # 重新跑 OCR，如果成功填入，再次點擊下一步
                if await self.process_captcha():
                    await self.click_next()

            else:
                # 【環節 B：正常流程】如果還沒選過位子，才執行選位
                if not getattr(self, 'is_seat_selected', False):

                    # 1. 執行座位選擇
                    seat_success = await self.select_ticket_quantity_legacy()

                    if seat_success:
                        import asyncio
                        # 2. 選位成功後，稍微等待驗證碼圖片渲染
                        await asyncio.sleep(0.5)

                        # 3. 呼叫 ddddocr 執行自動辨識並填入
                        ocr_success = await self.process_captcha()

                        # 4. 如果 OCR 辨識成功，立刻點擊加入購物車
                        if ocr_success:
                            await self.click_next()

    async def select_date(self):
        """[第一階段] 場次/日期選擇 (簡化極速版：直接點擊第一個可用按鈕)"""
        if not self.date_auto_select.get("enable", True):
            return

        # 建構極簡版 JavaScript 腳本，尋找並點擊第一個可用的購買按鈕
        js_script = """
        (function() {
            try {
                // 直接尋找畫面上的 #buy_btn (或是任何可點擊的 button)
                const btn = document.querySelector('#buy_btn') || document.querySelector('button');
                if (btn && !btn.disabled) {
                    btn.click();
                    return 1; // 成功點擊，回傳 1 給 Python
                }
                return 2; // 找不到或不可點，回傳 2 觸發重整
            } catch (e) {
                return -1; // 發生錯誤
            }
        })();
        """

        try:
            # 執行 JS 並取得結果
            result = await self.tab.evaluate(js_script)

            if result == 1:
                print(">>> [場次/日期] 👉 成功抓到購買按鈕，執行點擊！")
                self.is_date_selected = True

            elif result == 2:
                # 沒票或還沒開賣時的處理邏輯 (自動隨機延遲後重整)
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))

                if base_wait > 0:
                    print(">>> [場次/日期] 尚未開賣或找不到按鈕，準備刷新...")
                    try:
                        # 使用隨機時間函數防封鎖 (確保不會 0 秒狂刷)
                        random_wait = self.get_random_reload_time(base_wait)
                        await self.tab.reload()
                        print(
                            f"    -> 刷新後隨機等待: {random_wait:.2f} 秒 (基準: {base_wait}s)")
                        await asyncio.sleep(random_wait)
                    except:
                        pass

            elif result == -1:
                print(">>> [DEBUG] 日期選擇 JS 執行發生內部錯誤")

        except Exception as e:
            pass

    async def select_area_legacy(self):
        """[第二階段] 區域選擇 (整合前端 JS 暴力選取，保留外部設定檔動態讀取)"""
        if not self.area_auto_select.get("enable", True):
            return

        # ==========================================
        # 1. 讀取並解析外部設定檔
        # ==========================================
        auto_select_mode = self.area_auto_select.get(
            "mode", "from top to bottom")
        raw_keyword = self.area_auto_select.get("area_keyword", "").strip()

        keyword_list = []
        if len(raw_keyword) > 0:
            try:
                if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                    keyword_list = json.loads(raw_keyword)
                else:
                    keyword_list = json.loads("[" + raw_keyword + "]")
            except:
                keyword_list = [raw_keyword]
        else:
            keyword_list = [""]

        # 將 Python 的變數轉成 JavaScript 可以讀取的格式
        js_keywords = json.dumps(keyword_list, ensure_ascii=False)
        js_mode = f"'{auto_select_mode}'"

        # ==========================================
        # 2. 構建超快速 JavaScript 區域掃描腳本
        # ==========================================
        js_script = f"""
        (function() {{
            try {{
                // 接收來自 Python 的設定參數
                const keywords = {js_keywords};
                const mode = {js_mode};

                let allRows = Array.from(document.querySelectorAll('tr.saleTr'));
                let candidates = [];

                if (allRows.length > 0) {{
                    for (let row of allRows) {{
                        const rowContent = row.innerText.toUpperCase();

                        // [防呆過濾] 檢查剩餘張數，若沒票就直接跳過
                        const seatElement = row.querySelector('#SEAT');
                        const seatCount = seatElement ? parseInt(seatElement.innerText) : 0;
                        if (seatCount <= 0) continue;

                        // [關鍵字比對] 支援空白分隔的多重條件，例如 "VIP A排"
                        let isMatch = false;
                        if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                            isMatch = true; // 沒設關鍵字，全部皆可
                        }} else {{
                            for (let k of keywords) {{
                                let target_kws = k.trim().split(" ").filter(w => w.length > 0);
                                let currentGroupMatch = true;
                                for (let w of target_kws) {{
                                    if (!rowContent.includes(w.toUpperCase())) {{
                                        currentGroupMatch = false;
                                        break;
                                    }}
                                }}
                                if (currentGroupMatch) {{
                                    isMatch = true;
                                    break;
                                }}
                            }}
                        }}

                        // 如果關鍵字符合且有票，加入候選名單
                        if (isMatch) {{
                            candidates.push(row);
                        }}
                    }}
                }}

                // 找不到符合且有票的區域，回傳 2 讓 Python 去重整網頁
                if (candidates.length === 0) return 2;

                // 根據外部設定檔的模式進行排序
                if (mode === "from bottom to top") {{
                    candidates.reverse();
                }} else if (mode === "random") {{
                    for (let i = candidates.length - 1; i > 0; i--) {{
                        const j = Math.floor(Math.random() * (i + 1));
                        [candidates[i], candidates[j]] = [
                            candidates[j], candidates[i]];
                    }}
                }}

                // 執行點擊 (點擊排序後的第一個符合區域)
                candidates[0].click();
                return 1; // 成功點擊

            }} catch(e) {{
                return -1; // 發生例外錯誤
            }}
        }})();
        """

        # ==========================================
        # 3. 執行腳本與狀態處理
        # ==========================================
        try:
            result = await self.tab.evaluate(js_script)

            if result == 1:
                print(f">>> [區域] 👉 成功匹配並點擊區域！")
                await asyncio.sleep(0.2)  # 給網頁一點反應時間
                self.is_area_selected = True

            elif result == 2:
                # 找不到票區或全部售完，觸發 Python 自動刷新
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))

                # 給予極短保底時間，避免 0 秒狂刷被伺服器封鎖
                if base_wait <= 0:
                    base_wait = 0.2

                print(">>> [區域] 找不到符合關鍵字或有空位的票區，準備刷新...")
                try:
                    random_wait = self.get_random_reload_time(base_wait)
                    await self.tab.reload()
                    print(
                        f"    -> 刷新後隨機等待: {random_wait:.2f} 秒 (基準設定: {base_wait}s)")
                    await asyncio.sleep(random_wait)
                except:
                    pass

            elif result == -1:
                print(">>> [DEBUG] 區域選擇 JS 執行發生內部錯誤")

        except Exception as e:
            pass

    def get_random_reload_time(self, base_time):
        """
        區域選擇專用
        計算隨機浮動的重整時間
        base_time: 設定的基準秒數 (例如 0.5)
        return: 浮動後的秒數 (例如 0.5 + 0.3 = 0.8)
        """
        try:
            base = float(base_time)
        except:
            base = 0.5  # 預設值

        # 隨機決定是 + 還是 -
        sign = 1 if random.random() < 0.5 else -1

        # 產生 0.1 ~ 0.6 的隨機浮動值
        jitter = random.uniform(0.1, 0.6)

        # 計算最終時間
        final_time = base + (sign * jitter)

        # 防呆：確保時間至少有 0.1 秒，不會變成負數
        return max(0.1, final_time)

    async def select_ticket_quantity_legacy(self):
        """ [核心功能] 座位選擇 (純圖形座位表模式：暴力選位 + 自動聚焦驗證碼) """

        ticket_num = self.ticket_number
        if ticket_num <= 0:
            return

        # 專注於圖形座位表 (#TBL) 的極簡極速腳本
        js_select = f"""
        (function() {{
            try {{
                const targetTicketCount = {ticket_num};
                const seatTable = document.querySelector('#TBL');

                if (!seatTable) return 0; // 座位表還沒載入，回傳 0 繼續等

                // 1. 點擊票別按鈕 (無腦抓綠色一般票按鈕)
                const typeButton = document.querySelector('div.flex.seatype button.f1.green') || document.querySelector('button.f1.green');
                if (typeButton) typeButton.click();

                // 2. 尋找座位 (優先找連號)
                let targetSeats = [];
                const rows = document.querySelectorAll('#TBL tbody tr');

                for (let row of rows) {{
                    const cells = row.querySelectorAll('td');
                    let consecutiveSeats = [];

                    for (let cell of cells) {{
                        const styleStr = cell.getAttribute('style') || "";
                        const isAvailable = styleStr.includes('cursor: pointer') && styleStr.includes('seat-empty');

                        if (isAvailable) {{
                            consecutiveSeats.push(cell);
                            if (consecutiveSeats.length === targetTicketCount) {{
                                targetSeats = consecutiveSeats;
                                break;
                            }}
                        }} else if (styleStr.includes('seat-people') || !cell.hasAttribute('title')) {{
                            consecutiveSeats = []; // 遇到障礙物，連號重算
                        }}
                    }}
                    if (targetSeats.length > 0) break;
                }}

                // 3. 防呆機制：沒連號就硬抓剩下的空位
                if (targetSeats.length === 0) {{
                    const allAvailableSeats = Array.from(document.querySelectorAll('#TBL td')).filter(cell => {{
                        const s = cell.getAttribute('style') || "";
                        return s.includes('cursor: pointer') && s.includes('seat-empty');
                    }});
                    if (allAvailableSeats.length >= targetTicketCount) {{
                        targetSeats = allAvailableSeats.slice(
                            0, targetTicketCount);
                    }}
                }}

                // 4. 執行點擊與驗證碼聚焦
                if (targetSeats.length === targetTicketCount) {{
                    targetSeats.forEach(seat => seat.click());

                    // 選好座位後，幫你把游標焦點鎖定在驗證碼輸入框
                    const captchaInput = document.querySelector('#CHECK_CNF_CODE');
                    if (captchaInput) captchaInput.focus();

                    return 1; // 選位成功
                }} else {{
                    return 2; // 空位不足
                }}
            }} catch (e) {{
                return -1;
            }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_select)

            if result == 1:
                print(f">>> [座位] 🎉 成功鎖定 {ticket_num} 個座位！準備進行 OCR 辨識...")
                self.is_seat_selected = True  # 上鎖，不讓迴圈重複選位
                return True

            elif result == 2:
                print(f">>> [座位] ❌ 殘念...剩餘空位不足 {ticket_num} 張！準備重新整理頁面...")

                # 觸發自動重整，等待別人清票或系統放票
                try:
                    base_wait = float(self.config.get("advanced", {}).get(
                        "auto_reload_page_interval", 0.5))
                    if base_wait <= 0:
                        base_wait = 0.2

                    # 取一個隨機延遲時間，避免機器人特徵太明顯被封鎖
                    random_wait = self.get_random_reload_time(base_wait)

                    await self.tab.reload()  # 執行 F5 重新整理

                    print(
                        f"    -> 刷新後隨機等待: {random_wait:.2f} 秒 (基準設定: {base_wait}s)")
                    await asyncio.sleep(random_wait)
                except Exception as e:
                    pass

                return False  # 回傳 False，讓 dispatch_action 下次迴圈再進來找位子

            elif result == 0:
                # 畫面還沒載入完成，不做任何事，等待下一次迴圈
                return False

            elif result == -1:
                print("[DEBUG] 選位 JS 執行發生內部錯誤")
                return False

        except Exception as e:
            pass

        return False

    async def click_next(self):
        """[核心功能] 點擊下一步 (加入購物車) (含音效)"""

        # 1. 播放音效邏輯 (保持原樣)
        def play_coin_sound_independently():
            if self.config["advanced"].get("play_sound", {}).get("ticket", False):
                try:
                    import os
                    import util
                    app_root = util.get_app_root()
                    sound_path = os.path.join(app_root, "coin01.mp3")
                    if os.path.exists(sound_path):
                        print(f"[SOUND] 播放音效: {sound_path}")
                        util.play_mp3_async(sound_path)
                except Exception:
                    pass

        # 2. 核心點擊邏輯 (極簡極速版)
        js_click_cart = """
        (function() {
            try {
                // 直接透過 ID 尋找「加入購物車」按鈕
                const btn = document.querySelector('#addcart');
                if (btn && !btn.disabled) {
                    btn.click();
                    return 1; // 成功點擊
                }
                return 0; // 找不到或按鈕無效
            } catch (e) {
                return -1; // 發生錯誤
            }
        })();
        """

        try:
            result = await self.tab.evaluate(js_click_cart)

            if result == 1:
                # 判斷是否需要播放音效 (避免重複播放)
                try:
                    cur_url = await self.tab.evaluate("location.href")
                except:
                    cur_url = ""
                page_key = f"{cur_url}#addcart"

                if self.ticket_sound_tag.get("last_key") != page_key:
                    play_coin_sound_independently()
                    self.played_sound_ticket = True
                    self.ticket_sound_tag["last_key"] = page_key

                print(">>> [下一步]  成功點擊「加入購物車」按鈕！")
                return True

            elif result == 0:
                # 這裡不特別印出錯誤，因為主迴圈可能會頻繁呼叫它直到按鈕出現
                pass

        except Exception as e:
            pass

        return False

    async def process_captcha(self):
        """處理圖形驗證碼：抓取 #chk_pic -> ddddocr 辨識 -> 填入 #CHK"""

        print(">>> [OCR] 開始處理圖形驗證碼...")

        # 1. 利用 JS 將網頁上的圖片轉成 Base64
        js_get_image = """
        (function() {
            var img = document.querySelector('#chk_pic');
            if (!img) return null;

            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """

        try:
            # 最多嘗試辨識 3 次
            for attempt in range(3):
                base64_data = await self.tab.evaluate(js_get_image)

                if not base64_data:
                    print(">>> [OCR] 找不到驗證碼圖片 (#chk_pic)")
                    return False

                # 2. 解碼 Base64 並交給 ddddocr 辨識
                img_bytes = base64.b64decode(base64_data)
                ocr_answer = self.ocr.classification(img_bytes)

                # 清理辨識結果 (去掉空白)
                ocr_answer = ocr_answer.strip() if ocr_answer else ""
                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                # 3. 判斷是否為 4 碼
                if len(ocr_answer) == 4:
                    # 4. 透過 JS 將答案填入輸入框 #CHK
                    js_fill_input = f"""
                    (function() {{
                        var input = document.querySelector('#CHK');
                        if (input) {{
                            input.value = '{ocr_answer}';
                            // 觸發網頁事件，讓前端框架知道有打字了
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }})();
                    """
                    await self.tab.evaluate(js_fill_input)
                    print(f">>> [OCR]  已自動填入驗證碼: {ocr_answer}")
                    return True

                else:
                    print(">>> [OCR]  辨識長度不等於 4 碼，準備刷新圖片重試...")
                    # 透過 JS 刷新圖片，改變 src 後面的 timestamp
                    js_refresh_img = """
                    var img = document.querySelector('#chk_pic');
                    if(img) img.src = '/Home/pic?TYPE=UTK0205&ts=' + new Date().getTime();
                    """
                    await self.tab.evaluate(js_refresh_img)
                    await asyncio.sleep(0.2)  # 等待新圖片載入

            print(">>> [OCR]  嘗試 3 次辨識皆失敗，請手動輸入！")
            return False

        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False

    async def check_and_close_jquery_dialog(self):
        """[寬宏售票] 處理 jQuery UI 的錯誤彈窗，並擷取彈窗內的文字內容 (強化 Ok 按鈕選取版)"""
        js_check_dialog = """
        (function() {
            try {
                // 🔥 強化選取器：同時搜尋 dialog 底部按鈕容器與所有 ui-button 類別的按鈕
                let btns = document.querySelectorAll('div.ui-dialog-buttonpane button, button.ui-button, div.ui-dialog button');
                
                for (let btn of btns) {
                    // 確認按鈕存在，且目前在畫面上是顯示狀態 (非隱藏)
                    if (btn && btn.offsetParent !== null) {
                        // 將按鈕文字轉大寫去空白，涵蓋 OK, Ok, ok, 確定, 確認, 關閉
                        let btnText = (btn.innerText || "").trim().toUpperCase();
                        
                        if (btnText.includes('OK') || btnText.includes('確定') || btnText.includes('確認') || btnText.includes('關閉')) {
                            
                            // 往上尋找整個彈窗的父容器
                            let dialogBox = btn.closest('.ui-dialog');
                            let msgText = "未知的提示內容";
                            
                            if (dialogBox) {
                                // 優先尋找 jQuery UI 存放文字內容的區塊
                                let contentNode = dialogBox.querySelector('.ui-dialog-content');
                                if (contentNode && contentNode.innerText.trim() !== "") {
                                    msgText = contentNode.innerText.trim();
                                } else {
                                    // 備用方案：如果找不到 contentNode，直接抓取整個 dialog 的文字並移除按鈕文字
                                    msgText = dialogBox.innerText.replace(btn.innerText, '').trim();
                                }
                            }
                            
                            // 🔥 點下 OK 按鈕把彈窗點掉
                            btn.click(); 
                            return msgText; // 將抓到的「節目尚未啟售！」等文字回傳給 Python
                        }
                    }
                }
                return false;
            } catch (e) {
                return false;
            }
        })();
        """
        try:
            result = await self.tab.evaluate(js_check_dialog)
            if result:
                return result
        except:
            pass

        return False

    async def reload_config_if_changed(self):
        """[核心新增] 檢查設定檔 (settings.json) 是否變更，若有則熱重載"""
        try:
            # 請確認您的設定檔檔名是否為 settings.json
            config_path = "settings.json"

            # 檢查檔案是否存在
            if not os.path.exists(config_path):
                return

            # 獲取檔案最後修改時間
            mtime = os.path.getmtime(config_path)

            # 初始化 last_config_mtime (如果還沒有這個變數)
            if not hasattr(self, "last_config_mtime"):
                self.last_config_mtime = mtime
                return  # 第一次執行不需重載

            # 如果檔案修改時間比上次紀錄的新，代表被改過了
            if mtime > self.last_config_mtime:
                self.last_config_mtime = mtime

                print(f">>> [系統] 偵測到設定檔變更，正在熱重載...")

                import json
                with open(config_path, "r", encoding="utf-8") as f:
                    new_config = json.load(f)

                # 1. 更新區域關鍵字
                if "area_auto_select" in new_config:
                    self.area_auto_select = new_config["area_auto_select"]
                    k = self.area_auto_select.get('area_keyword', '')
                    m = self.area_auto_select.get('mode', '預設')
                    print(f"    -> 區域更新: 關鍵字[{k}] | 模式[{m}]")

                # 2. 更新日期關鍵字
                if "date_auto_select" in new_config:
                    self.date_auto_select = new_config["date_auto_select"]
                    k = self.date_auto_select.get('date_keyword', '')
                    print(f"-> 日期更新: 關鍵字[{k}]")

                # 3. 更新進階設定 (刷新秒數等)
                if "advanced" in new_config:
                    self.config["advanced"] = new_config["advanced"]
                    print(f"-> 進階設定已更新")

        except Exception as e:
            print(f">>> [熱重載失敗] {e}")

    async def send_telegram_message(self, message):
        """
        發送 Telegram 通知 (專屬類別版)
        """
        # 1. [基礎防呆] 檢查設定檔是否存在 (直接讀取 self.config)
        if not self.config or "advanced" not in self.config:
            return

        # 2. [開關檢查] 檢查是否啟用
        if not self.config["advanced"].get("telegram_enable", False):
            return

        # 3. [讀取資料]
        bot_token = self.config["advanced"].get("telegram_bot_token", "")
        chat_id = self.config["advanced"].get("telegram_chat_id", "")

        # 4. [資料檢查]
        if not bot_token or not chat_id:
            print("⚠️ Telegram 設定不完整，跳過通知")
            return

        # 5. [發送請求]
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }

            # 設定 timeout=6 秒，避免網路卡頓影響搶票
            response = requests.post(url, data=payload, timeout=6)

            if response.status_code == 200:
                print("✅ Telegram 搶票成功通知發送成功！")
            else:
                print(
                    f"❌ Telegram 發送失敗 (代碼 {response.status_code}): {response.text}")

        except Exception as e:
            print(f"❌ Telegram 連線錯誤: {e}")


# ==========================================
# [PLG富邦搶票]
# ==========================================


class EraBot:

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        # 🔥 統一標準：從主程式接收檔案路徑，沒傳的話保底用 settings.json
        self.settings_path = config.get("config_filepath", "settings.json")

        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態變數
        self.is_login_done = False
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_seat_selected = False
        self.is_telegram_sent = False

        # ==========================================
        # [新增] 綁定 GUI 的暫停控制檔案
        # ==========================================
        self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # 初始化 ddddocr 引擎
        print(">>> [年代售票] 正在載入 ddddocr 辨識模型...")
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    async def dispatch_action(self, url):
        """年代售票 任務分發中心"""
        upper_url = url.upper()

        # ==========================================
        # 0. 首頁狀態重置 (UTK0101_)
        # ==========================================
        if 'UTK0101_' in upper_url:
            self.is_date_selected = False
            self.is_area_selected = False
            self.is_seat_selected = False
            self.is_telegram_sent = False
            self.is_ticket_secured = False

        # ==========================================
        # 1. 自動登入階段 (UTK1306_)
        # ==========================================
        elif 'UTK1306_' in upper_url:
            if not getattr(self, 'is_login_done', False):
                await self.auto_login()

        # ==========================================
        # 2. 選擇區域 (UTK0201_000 或 UTK0204_)
        # ==========================================
        elif 'UTK0201_000' in upper_url or 'UTK0204_' in upper_url:
            self.is_seat_selected = False
            if not getattr(self, 'is_area_selected', False):
                await self.select_area()

        # ==========================================
        # 3. 選擇日期/場次 (UTK0201_00)
        # ==========================================
        elif 'UTK0201_00' in upper_url:
            self.is_area_selected = False
            self.is_seat_selected = False
            if not getattr(self, 'is_date_selected', False):
                await self.select_date()

        # ==========================================
        # 4. 第三階段：座位選擇 / 張數輸入 -> OCR -> 加入購物車
        # ==========================================
        elif 'UTK0202_' in upper_url or 'UTK0205_' in upper_url or ('UTK0204_' in upper_url and getattr(self, 'is_area_selected', False)):

            # 如果已經搶到票，直接跳過不處理，避免動作過快干擾轉跳
            if getattr(self, 'is_ticket_secured', False):
                return

            # 【環節 A：錯誤彈窗與成功彈窗處理】
            error_msg = await self.check_and_close_jquery_dialog()

            if error_msg:
                # 🔥 修正：確實將 success_markers 應用於 any() 比對
                success_markers = ["加入購物車完成", "完成結帳", "分鐘內完成結帳"]
                is_success = any(
                    marker in error_msg for marker in success_markers)

                if is_success:
                    print(f">>> [系統] 🎉 偵測到成功訊息：【{error_msg}】")
                    print(">>> [系統] ✅ 已成功加入購物車！為避免刷票蓋掉這張票，機器人將自動暫停。")
                    print(">>> [系統] 👉 請在時限內自行完成結帳，結帳完成後如需繼續搶票，請手動移除暫停檔案。")
                    self.is_ticket_secured = True
                    try:
                        with open(self.PAUSE_FILE, "w", encoding="utf-8") as f:
                            f.write(
                                "auto-paused: ticket secured, waiting for manual checkout")
                    except Exception as e:
                        print(f">>> [系統] ⚠️ 寫入暫停檔案失敗，請自行停止程式避免誤刷票！錯誤: {e}")
                    return  # 成功搶到，直接中斷，絕對不 reload

                # 不是成功訊息 -> 走原本的錯誤重試邏輯 (如驗證碼錯誤、座位被搶走)
                print(f">>> [系統] 系統彈窗攔截: 【{error_msg}】 (已自動點擊 Ok)")
                print(">>> [系統] 準備重新整理頁面，獲取最新空位狀態...")

                import asyncio
                self.is_seat_selected = False
                await self.tab.reload()
                await asyncio.sleep(0.5)

            else:
                # 【環節 B：正常流程】如果沒有彈窗，且還沒選過位子，才執行選位/選張數
                if not getattr(self, 'is_seat_selected', False):
                    seat_success = await self.select_tickets()
                    if seat_success:
                        import asyncio
                        await asyncio.sleep(0.5)
                        ocr_success = await self.process_captcha()
                        if ocr_success:
                            await self.click_next()

    async def run(self):
        print(f">>> [年代售票] 機器人啟動！(目標張數: {self.ticket_number})")
        print("等待網頁載入中...")

        import os
        import asyncio

        while True:
            try:
                # ==========================================
                # 【防護】GUI 暫停機制攔截
                # ==========================================
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                # 取得當前網址
                current_url = await self.tab.evaluate("window.location.href")

                # 檢測頁面切換
                if current_url and current_url != self.last_url:
                    print(f"偵測到頁面切換: {current_url}")
                    upper_url = current_url.upper()

                    # ==========================================
                    # 🔥 修正：精準切割區域與日期，避免鎖被誤洗！
                    # ==========================================
                    # 1. 區域選擇頁面 (UTK0201_000)
                    if 'UTK0201_000' in upper_url:
                        # 進入區域頁了，千萬不要重置日期鎖！
                        pass

                    # 2. 真實的日期選擇頁面 (UTK0201_00)
                    elif 'UTK0201_00' in upper_url:
                        if getattr(self, 'is_date_selected', False):
                            print(">>> [系統] 偵測到真實退回日期選擇頁，已重置日期鎖，準備重新掃描場次！")
                            self.is_date_selected = False
                        await self.reload_settings()

                    # 3. 另外一種區域選擇頁 (UTK0204_)
                    elif 'UTK0204_' in upper_url and getattr(self, 'is_area_selected', False):
                        print(">>> [系統] 偵測到退回區域選擇頁，已重置區域鎖，準備重新刷票！")
                        self.is_area_selected = False

                    # 4. 退回到「票數/座位選擇頁」
                    elif ('UTK0202_' in upper_url or 'UTK0205_' in upper_url) and getattr(self, 'is_seat_selected', False):
                        print(">>> [系統] 偵測到退回座位/票數頁面，已重置座位鎖，準備重新選位！")
                        self.is_seat_selected = False

                    self.last_url = current_url

                # 分發動作
                if current_url:
                    await self.dispatch_action(current_url)

            except Exception as e:
                pass

            await asyncio.sleep(0.05)

    async def reload_settings(self):
        """[年代售票] 從設定檔讀取最新搶票設定 (支援多重設定檔動態切換 + 磁碟 I/O 提速)"""
        import json
        import os

        # 🔥 核心修正：使用初始化時存好的動態路徑
        settings_path = getattr(self, 'settings_path', 'settings.json')

        try:
            # 檢查檔案是否存在
            if not os.path.exists(settings_path):
                return

            # 🔥 終極提速核心：檢查檔案修改時間，沒變過就不讀取硬碟，直接秒退！
            current_mtime = os.path.getmtime(settings_path)
            if getattr(self, 'last_settings_mtime', 0) == current_mtime:
                return
            self.last_settings_mtime = current_mtime

            # 讀取 JSON 檔案
            with open(settings_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)

            # 更新年代售票需要的設定區塊
            if "area_auto_select" in new_config:
                self.config["area_auto_select"] = new_config["area_auto_select"]
                # 年代特有：同步更新屬性，確保 select_area 抓得到
                self.area_auto_select = new_config["area_auto_select"]
            if "date_auto_select" in new_config:
                self.config["date_auto_select"] = new_config["date_auto_select"]
            if "advanced" in new_config:
                self.config["advanced"] = new_config["advanced"]
            if "keyword_exclude" in new_config:
                self.config["keyword_exclude"] = new_config["keyword_exclude"]
            if "ticket_number" in new_config:
                self.config["ticket_number"] = new_config["ticket_number"]
                self.ticket_number = int(new_config.get("ticket_number", 1))

            # 抓出純檔名，讓 Log 看起來乾淨俐落
            filename = os.path.basename(settings_path)
            print(f">>> [系統] 進入日期選擇頁面！已成功套用最新設定 ({filename})")

        except json.JSONDecodeError:
            filename = os.path.basename(settings_path)
            print(f">>> [系統錯誤] {filename} 格式有誤！請檢查是否多加了逗號或少了雙引號。")
        except Exception as e:
            pass

    async def auto_login(self):
        """[核心] 年代售票：自動填入帳號密碼 -> OCR 驗證碼 -> 穩健點擊登入"""

        # 1. 從設定檔讀取帳號密碼
        account = self.config.get("advanced", {}).get("ticket_account", "")
        password = self.config.get("advanced", {}).get(
            "ticket_password_plaintext", "").strip()

        if not password:
            try:
                import util
                password = util.decrypt_me(self.config.get(
                    "advanced", {}).get("ticket_password", ""))
            except:
                pass

        if not account or not password:
            print(">>> [年代售票] ⚠️ 未設定帳號密碼，跳過自動登入！")
            self.is_login_done = True
            return

        # 2. 構建 JS 腳本：瞬間填入帳號與密碼
        js_fill_credentials = f"""
        (function() {{
            try {{
                let accInput = document.querySelector('input[cname="帳號"]');
                let pwdInput = document.querySelector('input[cname="密碼"]');

                if (accInput && pwdInput && accInput.value === '') {{
                    accInput.value = '{account}';
                    pwdInput.value = '{password}';

                    accInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    return true;
                }}
                return accInput.value !== '';
            }} catch(e) {{
                return false;
            }}
        }})();
        """

        try:
            is_filled = await self.tab.evaluate(js_fill_credentials)

            if is_filled:
                print(">>> [年代售票] 帳號密碼已填入！準備處理驗證碼...")

                # 3. 呼叫 OCR 辨識並填入驗證碼
                ocr_success = await self.process_captcha()

                # 4. 確認驗證碼填寫成功後，再按確認登入
                if ocr_success:
                    print(">>> [年代售票] 驗證碼填寫完畢，等待 0.5 秒確保網頁接收...")
                    import asyncio
                    await asyncio.sleep(0.5)  # 不拚速度，確保萬無一失

                    js_click_login = """
                    (function() {
                        // 支援年代售票可能的登入按鈕寫法 (包含 a 標籤或 input)
                        let loginBtn = document.querySelector('a.btn-login') ||
                                       document.querySelector('input[value="登入"]') ||
                                       document.querySelector('button[value="登入"]');
                        if (loginBtn) {
                            loginBtn.click();
                            return true;
                        }
                        return false;
                    })();
                    """
                    btn_clicked = await self.tab.evaluate(js_click_login)
                    if btn_clicked:
                        print(">>> [年代售票] 👉 已點擊登入按鈕！")
                        self.is_login_done = True
                    else:
                        print(">>> [年代售票] ⚠️ 找不到登入按鈕，請確認網頁結構！")

        except Exception as e:
            print(f">>> [年代售票] 登入過程發生錯誤: {e}")

    async def process_captcha(self):
        """共用核心：處理圖形驗證碼"""
        print(">>> [OCR] 開始處理圖形驗證碼...")

        js_get_image = """
        (function() {
            var img = document.querySelector('#chk_pic');
            if (!img) return null;

            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """

        try:
            for attempt in range(3):
                base64_data = await self.tab.evaluate(js_get_image)
                if not base64_data:
                    print(">>> [OCR] 找不到驗證碼圖片 (#chk_pic)")
                    return False

                import base64
                img_bytes = base64.b64decode(base64_data)
                ocr_answer = self.ocr.classification(img_bytes)
                ocr_answer = ocr_answer.strip() if ocr_answer else ""

                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                if len(ocr_answer) == 4:
                    js_fill_input = f"""
                    (function() {{
                        // 【關鍵修改】：加入 ASP.NET 的專屬 ID，並保留其他備用選項
                        var input = document.querySelector('#ctl00_ContentPlaceHolder1_CHK') ||
                                    document.querySelector('#CHK') ||
                                    document.querySelector('input[cname="認證碼"]');
                        if (input) {{
                            input.value = '{ocr_answer}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }})();
                    """
                    is_filled = await self.tab.evaluate(js_fill_input)
                    if is_filled:
                        print(f">>> [OCR] ✅ 已自動填入驗證碼: {ocr_answer}")
                        return True
                    else:
                        print(">>> [OCR] ⚠️ 找不到驗證碼輸入框！")
                        return False
                else:
                    # 辨識失敗，點擊換圖
                    print(">>> [OCR] ⚠️ 辨識長度不對，刷新圖片重試...")
                    js_refresh_img = "let img = document.querySelector('#chk_pic'); if(img) img.click();"
                    await self.tab.evaluate(js_refresh_img)
                    import asyncio
                    await asyncio.sleep(0.5)

            return False
        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False

    async def select_date(self):
        """[年代售票] 場次/日期選擇 (修正：永遠持續刷新直到可購票 + 狙擊逾時保險)"""
        print(">>> [系統] 進入年代售票日期選擇階段...")
        try:
            date_auto_select = self.config.get("date_auto_select", {})
            if not date_auto_select.get("enable", True):
                print(">>> [年代售票-日期] 設定檔未啟用，跳過。")
                return

            raw_keyword = date_auto_select.get("date_keyword", "").strip()
            import json
            keyword_list = []
            if len(raw_keyword) > 0:
                try:
                    if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                        keyword_list = json.loads(raw_keyword)
                    else:
                        keyword_list = json.loads("[" + raw_keyword + "]")
                except:
                    keyword_list = [raw_keyword]
            else:
                keyword_list = [""]

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_mode = f"'{date_auto_select.get('mode', 'from top to bottom')}'"

            js_script = f"""
            (function() {{
                try {{
                    const keywords = {js_keywords};
                    const mode = {js_mode};

                    let rows = Array.from(document.querySelectorAll("table tbody tr"));
                    let candidates_ready = [];
                    let candidates_countdown = [];

                    if (rows && rows.length > 0) {{
                        for (let row of rows) {{
                            let btn = row.querySelector("button.btn-event") || row.querySelector("button");
                            if (!btn) continue;

                            // 🔥 修正：文字先去除所有空白 (含 &nbsp; 造成的內部空格)，比對才準確
                            let btnTextRaw = (btn.innerText || "").toUpperCase();
                            let btnTextClean = btnTextRaw.replace(/\\s+/g, '');

                            // 1. 絕對死亡名單 (真的不能買的) - 同時支援「售完」與「完售」兩種順序
                            let isDead = btnTextClean.includes('售完') ||
                                         btnTextClean.includes('完售') ||
                                         btnTextClean.includes('SOLDOUT') ||
                                         btnTextClean.includes('暫停');
                            if (isDead) continue;

                            // 2. 硬體鎖定 (disabled) 但文字不是死亡名單 -> 視為「倒數/尚未開賣」候選
                            let isDisabled = btn.disabled || btn.classList.contains('disabled');

                            // 3. 倒數名單關鍵字 (含硬體鎖定的情況也算倒數)
                            let isCountdown = isDisabled ||
                                              btnTextClean.includes('倒數') ||
                                              btnTextClean.includes('分') ||
                                              btnTextClean.includes('秒') ||
                                              btnTextClean.includes('尚未');

                            // 4. 組合場次文字 (日期/時間關鍵字比對用)
                            let rowText = row.innerText.toUpperCase();
                            let timeEl = row.querySelector("time");
                            if (timeEl && timeEl.getAttribute("datetime")) {{
                                let dt = timeEl.getAttribute("datetime").toUpperCase();
                                let p = dt.split("-");
                                if (p.length === 3) {{
                                    let y = p[0]; let m_str = p[1]; let d_str = p[2];
                                    let m_int = parseInt(m_str, 10).toString();
                                    let d_int = parseInt(d_str, 10).toString();
                                    rowText += ` ${{dt}} ${{y}}/${{m_str}}/${{d_str}} ${{y}}/${{m_int}}/${{d_int}} ${{m_str}}/${{d_str}} ${{m_int}}/${{d_int}} ${{m_str}}${{d_str}} ${{m_int}}月${{d_int}}日 ${{m_str}}月${{d_str}}日`;
                                }} else {{
                                    rowText += " " + dt;
                                }}
                            }}

                            // 5. 關鍵字過濾
                            let isMatch = false;
                            if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                                isMatch = true;
                            }} else {{
                                for (let k of keywords) {{
                                    let target_kws = k.trim().split(" ").filter(w => w.length > 0);
                                    let currentGroupMatch = true;
                                    for (let w of target_kws) {{
                                        if (!rowText.includes(w.toUpperCase())) {{
                                            currentGroupMatch = false;
                                            break;
                                        }}
                                    }}
                                    if (currentGroupMatch) {{
                                        isMatch = true;
                                        break;
                                    }}
                                }}
                            }}

                            if (!isMatch) continue;

                            // 6. 分流：真的可以買了？還是還沒解鎖（含硬體 disabled）？
                            if (isDisabled || isCountdown) {{
                                candidates_countdown.push(btn);
                            }} else {{
                                candidates_ready.push(btn);
                            }}
                        }}
                    }}

                    // 🔥 狀況 A：有已經解鎖的按鈕 -> 點擊並回傳 1
                    if (candidates_ready.length > 0) {{
                        if (mode === "from bottom to top") {{
                            candidates_ready.reverse();
                        }} else if (mode === "random") {{
                            for (let i = candidates_ready.length - 1; i > 0; i--) {{
                                const j = Math.floor(Math.random() * (i + 1));
                                [candidates_ready[i], candidates_ready[j]] = [
                                    candidates_ready[j], candidates_ready[i]];
                            }}
                        }}
                        candidates_ready[0].click();
                        return 1;
                    }}

                    // 🔥 狀況 B：符合關鍵字但還鎖著（含 disabled/倒數）-> 回傳 3，讓 Python 決定要 poll 還是強制 reload
                    if (candidates_countdown.length > 0) {{
                        return 3;
                    }}

                    // 🔥 狀況 C：完全找不到符合的場次 -> 回傳 2 (重新整理)
                    return 2;

                }} catch (e) {{
                    return -1;
                }}
            }})();
            """

            result = await self.tab.evaluate(js_script)

            base_wait = float(self.config.get("advanced", {}).get(
                "auto_reload_page_interval", 0.5))
            # 保底：即使設定檔填 0 或負數，也至少保留一個很小的安全間隔，避免無限緊迴圈或被伺服器封鎖
            safe_wait = max(0.05, base_wait)

            if result == 1:
                print(">>> [年代售票-日期] 🎉 成功匹配日期並執行點擊！等待網頁跳轉...")
                self.is_date_selected = True
                self.date_sniper_start_time = 0
                import asyncio
                await asyncio.sleep(0.5)

            elif result == 2:
                # 🔥 修正：移除「base_wait > 0 才 reload」的判斷，永遠刷新
                print(">>> [年代售票-日期] 找不到符合關鍵字或完全售完，準備刷新...")
                self.date_sniper_start_time = 0
                import asyncio
                await self.tab.reload()
                await asyncio.sleep(safe_wait)

            elif result == 3:
                # 找到符合關鍵字但還沒解鎖的場次 (含 disabled 硬鎖) -> 進入狙擊監控模式
                import time
                import asyncio
                if not hasattr(self, 'date_sniper_start_time') or not self.date_sniper_start_time:
                    self.date_sniper_start_time = time.time()
                    print(">>> [年代售票-日期] ⏳ 鎖定倒數場次！開始監控解鎖狀態...")

                if not hasattr(self, 'date_sniper_log'):
                    self.date_sniper_log = 0
                self.date_sniper_log += 1
                if self.date_sniper_log % 20 == 0:
                    print(">>> [年代售票-日期] ⏳ 持續監控解鎖狀態中...")

                # 🔥 逾時保險：因為這個網站是伺服器端渲染，disabled 狀態不會自己在前端消失，
                #    純輪詢可能永遠等不到變化，所以固定每隔 sniper_timeout 秒強制 reload 一次
                sniper_timeout = float(self.config.get("advanced", {}).get(
                    "date_sniper_timeout", 3.0))
                elapsed = time.time() - self.date_sniper_start_time
                if elapsed >= sniper_timeout:
                    print(
                        f">>> [年代售票-日期] 🔄 監控已達 {sniper_timeout} 秒仍未解鎖，強制重新整理一次...")
                    self.date_sniper_start_time = 0
                    await self.tab.reload()
                    await asyncio.sleep(safe_wait)
                else:
                    await asyncio.sleep(0.05)

            elif result == -1:
                print(">>> [DEBUG] 日期選擇 JS 執行發生內部錯誤")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_date 發生 Python 例外: {e}")

    async def select_area(self):
        """[年代售票] 區域選擇 (精準鎖定 <li> <a> 結構 + 排除關鍵字 + 去逗號防呆)"""

        print(">>> [系統] 進入年代售票區域選擇階段...")

        try:
            # 1. 讀取設定檔的區域自動選擇設定
            area_auto_select = getattr(
                self, 'area_auto_select', self.config.get("area_auto_select", {}))
            if not area_auto_select.get("enable", True):
                print(">>> [年代售票-區域] 設定檔未啟用區域自動選擇，跳過。")
                return

            auto_select_mode = area_auto_select.get(
                "mode", "from top to bottom")

            # ==========================================
            # 🔥 修正：同時讀取「包含」與「排除」關鍵字
            # ==========================================
            raw_keyword = area_auto_select.get("area_keyword", "").strip()
            raw_keyword_exclude = self.config.get("keyword_exclude", "")
            if not raw_keyword_exclude:
                raw_keyword_exclude = area_auto_select.get(
                    "area_keyword_exclude", "")
            raw_keyword_exclude = str(raw_keyword_exclude).strip()

            import json

            def parse_keywords(kw_str):
                kw_str = kw_str.strip()
                if not kw_str:
                    return [""]
                try:
                    if kw_str.startswith("[") and kw_str.endswith("]"):
                        return json.loads(kw_str)
                    if '"' in kw_str or "'" in kw_str:
                        return json.loads("[" + kw_str + "]")
                except:
                    pass
                return [x.strip().strip('\'"') for x in kw_str.replace('，', ',').split(',') if x.strip()]

            keyword_list = parse_keywords(raw_keyword)
            exclude_list = parse_keywords(raw_keyword_exclude)

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_excludes = json.dumps(exclude_list, ensure_ascii=False)
            js_mode = f"'{auto_select_mode}'"

            # 2. 構建 年代售票專用 的超快速 JavaScript 腳本
            js_script = f"""
            (function() {{
                try {{
                    const keywords = {js_keywords};
                    const excludes = {js_excludes};
                    const mode = {js_mode};

                    // 【關鍵防護升級】：精準鎖定真正的票區按鈕
                    let availableLinks = Array.from(document.querySelectorAll('li > a')).filter(a => {{
                        return a.querySelector('font') !== null && a.querySelector('img') === null;
                    }});

                    let candidates = [];

                    if (availableLinks.length > 0) {{
                        for (let link of availableLinks) {{
                            //  修正：把文字裡的逗號去掉，轉大寫，確保比對精準
                            const rowContent = link.innerText.replace(/,/g, '').toUpperCase();

                            // [雙重防呆] 確保真的沒有包含售完字眼
                            if (rowContent.includes('SOLD OUT') || rowContent.includes('售完')) continue;

                            // ==========================================
                            // 🔥 修正：新增排除關鍵字判斷
                            // ==========================================
                            let isExcluded = false;
                            if (excludes.length > 0 && excludes[0] !== "") {{
                                for (let exc of excludes) {{
                                    let cleanExc = exc.trim().replace(/,/g, '').toUpperCase();
                                    if (cleanExc.length > 0 && rowContent.includes(cleanExc)) {{
                                        isExcluded = true; break;
                                    }}
                                }}
                            }}
                            if (isExcluded) continue; // 發現排除字眼(如：輪椅)，直接跳過這個區域！

                            // 關鍵字比對邏輯
                            let isMatch = false;
                            if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                                isMatch = true; // 沒設關鍵字，全部皆可
                            }} else {{
                                for (let k of keywords) {{
                                    // 🔥 修正：目標關鍵字也去逗號
                                    let target_kws = k.trim().replace(/,/g, '').split(/\\s+/).filter(w => w.length > 0);
                                    let currentGroupMatch = true;
                                    for (let w of target_kws) {{
                                        if (!rowContent.includes(w.toUpperCase())) {{
                                            currentGroupMatch = false;
                                            break;
                                        }}
                                    }}
                                    if (currentGroupMatch) {{
                                        isMatch = true;
                                        break;
                                    }}
                                }}
                            }}

                            // 如果關鍵字符合，將這個 <a> 標籤加入候選名單
                            if (isMatch) {{
                                candidates.push(link);
                            }}
                        }}
                    }}

                    // 找不到符合且有票的區域，回傳 2 讓 Python 去重整網頁
                    if (candidates.length === 0) return 2;

                    // 根據設定檔的模式進行排序
                    if (mode === "from bottom to top") {{
                        candidates.reverse();
                    }} else if (mode === "random") {{
                        for (let i = candidates.length - 1; i > 0; i--) {{
                            const j = Math.floor(Math.random() * (i + 1));
                            [candidates[i], candidates[j]] = [
                                candidates[j], candidates[i]];
                        }}
                    }}

                    // 執行點擊 (點擊排序後的第一個區域)
                    candidates[0].click();
                    return 1;

                }} catch(e) {{
                    return -1; // 發生例外錯誤
                }}
            }})();
            """

            # 3. 執行 JS 與狀態處理
            result = await self.tab.evaluate(js_script)

            if result == 1:
                print(f">>> [年代售票-區域] 👉 成功匹配關鍵字並點擊區域！")
                import asyncio
                await asyncio.sleep(0.2)  # 給網頁一點跳轉的緩衝時間
                self.is_area_selected = True

            elif result == 2:
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                if base_wait <= 0:
                    base_wait = 0.2

                print(">>> [年代售票-區域] 找不到符合關鍵字或有空位的票區，準備刷新...")
                import asyncio
                await self.tab.reload()
                print(f"    -> 刷新後固定等待: {base_wait} 秒")
                await asyncio.sleep(base_wait)

            elif result == -1:
                print(">>> [DEBUG] 區域選擇 JS 執行發生內部錯誤")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_area 發生 Python 例外: {e}")

    async def select_tickets(self):
        """[年代售票] 智能票數與座位選擇 (雙模式自動切換)"""
        ticket_num = self.ticket_number
        if ticket_num <= 0:
            return False

        js_select = f"""
        (function() {{
            try {{
                const targetTickets = {ticket_num};
                const seatTable = document.querySelector('#TBL');

                // ==========================================
                // 模式 2：座位圖模式 (有 #TBL)
                // ==========================================
                if (seatTable) {{
                    // A. 選擇票種 (避開身障)
                    let typeBtns = document.querySelectorAll('div.ticketType button');
                    let selectedBtn = null;
                    for (let btn of typeBtns) {{
                        let btnText = btn.innerText || "";
                        if (btnText.includes('身障') || btnText.includes('身心障礙')) continue;
                        selectedBtn = btn;
                        break;
                    }}
                    if (selectedBtn) selectedBtn.click();

                    // B. 尋找空座位 (優先找連號)
                    let rows = document.querySelectorAll('#TBL tbody tr');
                    let targetSeats = [];
                    for (let row of rows) {{
                        let cells = row.querySelectorAll('td');
                        let consec = [];
                        for (let cell of cells) {{
                            let bg = cell.style.backgroundImage || "";
                            // 判斷是否為空位
                            if (bg.includes('icon_chair_empty') && cell.style.cursor === 'pointer') {{
                                consec.push(cell);
                                if (consec.length === targetTickets) {{
                                    targetSeats = consec;
                                    break;
                                }}
                            // 如果遇到已售出或走道，連號重算
                            }} else if (bg.includes('icon_chair_sale') || !cell.hasAttribute('title')) {{
                                consec = [];
                            }}
                        }}
                        if (targetSeats.length > 0) break;
                    }}

                    // 防呆：沒連號就硬抓剩下的空位
                    if (targetSeats.length === 0) {{
                        let allEmpty = Array.from(document.querySelectorAll('#TBL td')).filter(c => {{
                            let b = c.style.backgroundImage || "";
                            return b.includes('icon_chair_empty') && c.style.cursor === 'pointer';
                        }});
                        if (allEmpty.length >= targetTickets) {{
                            targetSeats = allEmpty.slice(0, targetTickets);
                        }}
                    }}

                    // C. 點擊座位並聚焦驗證碼
                    if (targetSeats.length === targetTickets) {{
                        targetSeats.forEach(s => s.click());
                        let captchaInput = document.querySelector('#ctl00_ContentPlaceHolder1_CHK');
                        if(captchaInput) captchaInput.focus();
                        return 1; // 成功
                    }} else {{
                        return 2; // 空位不足
                    }}
                }}
                // ==========================================
                // 模式 1：一般張數輸入模式 (沒有 #TBL)
                // ==========================================
                else {{
                    let rows = document.querySelectorAll('table tbody tr');
                    let targetInput = null;

                    for (let row of rows) {{
                        let labelCell = row.querySelector('td[data-th="內容"]');
                        if (labelCell) {{
                            let labelText = labelCell.innerText || "";
                            if (labelText.includes('身障') || labelText.includes('身心障礙')) continue;
                        }}

                        let input = row.querySelector('input.qty');
                        if (input && !input.disabled) {{
                            targetInput = input;
                            break;
                        }}
                    }}

                    if (targetInput) {{
                        targetInput.value = targetTickets;
                        // 觸發網頁的驗證腳本
                        targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        targetInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        // 嘗試呼叫內建的 checkNum 函式 (年代售票的防呆機制)
                        if (typeof checkNum === "function") {{
                            checkNum(targetInput.id, targetTickets);
                        }}

                        let captchaInput = document.querySelector('#ctl00_ContentPlaceHolder1_CHK');
                        if(captchaInput) captchaInput.focus();
                        return 1; // 成功
                    }}
                    return 2; // 找不到可輸入的格子
                }}
            }} catch(e) {{
                return -1;
            }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_select)
            if result == 1:
                print(f">>> [座位/票數] 🎉 成功鎖定 {ticket_num} 張票！準備進行 OCR 辨識...")
                self.is_seat_selected = True
                return True
            elif result == 2:
                print(f">>> [座位/票數] ❌ 殘念...剩餘空位不足 {ticket_num} 張！準備重新整理頁面...")
                try:
                    base_wait = float(self.config.get("advanced", {}).get(
                        "auto_reload_page_interval", 0.5))
                    if base_wait <= 0:
                        base_wait = 0.2
                    import asyncio
                    await self.tab.reload()
                    await asyncio.sleep(base_wait)
                except:
                    pass
                return False
        except Exception as e:
            pass
        return False

    async def click_next(self):
        """[年代售票] 點擊加入購物車 (雙模式相容)"""
        js_submit = """
        (function() {
            try {
                // 優先找一般模式的加入購物車按鈕
                let btn1 = document.querySelector('#ctl00_ContentPlaceHolder1_AddShopingCart');
                // 再找座位圖模式的加入購物車按鈕
                let btn2 = document.querySelector('button.sumitButton');

                let btn = btn1 || btn2;
                if (btn && !btn.disabled) {
                    btn.click();
                    return true;
                }
                return false;
            } catch (e) {
                return false;
            }
        })();
        """
        try:
            result = await self.tab.evaluate(js_submit)
            if result:
                print(">>> [下一步] 🛒 已成功點擊「加入購物車」按鈕！")
                return True
        except:
            pass
        return False

    async def check_and_close_jquery_dialog(self):
        """處理 jQuery UI 的錯誤彈窗，並擷取彈窗內的文字內容"""
        js_check_dialog = """
        (function() {
            try {
                let btn = document.querySelector('div.ui-dialog-buttonpane button');

                // 確認按鈕存在、文字包含 Ok，且目前是顯示狀態
                if (btn && btn.innerText.includes('Ok') && btn.offsetParent !== null) {

                    // 往上尋找整個彈窗的父容器
                    let dialogBox = btn.closest('.ui-dialog');
                    let msgText = "未知的提示內容";

                    if (dialogBox) {
                        // 尋找 jQuery UI 存放文字內容的區塊
                        let contentNode = dialogBox.querySelector('.ui-dialog-content');
                        if (contentNode) {
                            msgText = contentNode.innerText.trim();
                        }
                    }

                    btn.click(); // 點擊關閉
                    return msgText; // 將抓到的文字回傳給 Python
                }
                return false;
            } catch (e) {
                return false;
            }
        })();
        """
        try:
            result = await self.tab.evaluate(js_check_dialog)
            # 如果回傳的是字串 (也就是有抓到彈窗)，Python 的 if 判斷會是 True
            if result:
                return result
        except:
            pass

        return False


# ==========================================
# [年代售票]
# ==========================================

class KhamBot:

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        # 🔥 統一標準：從 config 拿取路徑，如果沒有就用預設值 settings.json
        self.settings_path = config.get("config_filepath", "settings.json")

        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態變數
        self.is_login_done = False
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_seat_selected = False
        self.is_telegram_sent = False

        # ==========================================
        # 綁定 GUI 的暫停控制檔案
        # ==========================================
        import os
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # 初始化 ddddocr 引擎
        print(">>> [寬宏售票] 正在載入 ddddocr 辨識模型...")
        try:
            import ddddocr
            self.ocr = ddddocr.DdddOcr(show_ad=False)
        except Exception as e:
            print(f">>> [系統] ddddocr 載入失敗: {e}")
            self.ocr = None

        # ==========================================
        # 新增：原生 Dialog 狀態
        # ==========================================
        self.last_native_alert = ""
        self.native_dialog_handler_installed = False

    async def run(self):
        print(f">>> [寬宏售票] 機器人啟動！(目標張數: {self.ticket_number})")
        print("等待網頁載入中...")

        # ==========================================
        # 🔥 在主迴圈開始前，套用網路加速器與原生彈窗攔截
        await self.optimize_network_speed()
        await self.setup_native_dialog_handler()
        # ==========================================

        import os
        import asyncio
        while True:
            try:
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue
                current_url = await self.tab.evaluate("window.location.href")
                if current_url and current_url != self.last_url:
                    print(f"偵測到頁面切換: {current_url}")
                    upper_url = current_url.upper()

                    # ==========================================
                    # 🔥 修正：精準的 URL 路由與狀態重置
                    # ==========================================
                    is_date_page = any(x in upper_url for x in [
                                       'UTK0201_00.ASPX', 'UTK0201_041'])
                    is_area_page = any(x in upper_url for x in [
                                       'UTK0204_', 'UTK0201_000'])
                    is_ticket_page = any(x in upper_url for x in [
                                         'UTK0202_', 'UTK0205_', 'UTK0201_001'])

                    if is_area_page:
                        if getattr(self, 'is_area_selected', False):
                            print(">>> [系統] 🔄 偵測到退回區域選擇頁，重新啟動刷票！")
                            self.is_area_selected = False
                            self.is_seat_selected = False
                            self.is_printing_area = False

                    elif is_ticket_page:
                        # 頁面真的切換進張數頁時，解除舊的座位鎖
                        if getattr(self, 'is_seat_selected', False):
                            self.is_seat_selected = False

                    elif is_date_page:
                        if getattr(self, 'is_date_selected', False):
                            print(">>> [系統] 偵測到退回日期選擇頁，重新掃描場次！")
                            self.is_date_selected = False

                    # 偵測登出狀態
                    elif 'UTK1306_' in upper_url:
                        if getattr(self, 'is_login_done', False):
                            print(">>> [系統] ⚠️ 偵測到跳回登入頁面，重置狀態，準備重新登入！")
                        self.is_login_done = False
                        self.is_date_selected = False
                        self.is_area_selected = False
                        self.is_seat_selected = False
                        self.is_printing_login = False
                        self.is_printing_no_acc = False

                    self.last_url = current_url

                if current_url:
                    await self.dispatch_action(current_url)
            except Exception as e:
                pass
            await asyncio.sleep(0.05)

    async def dispatch_action(self, url):
        """寬宏售票 任務分發中心 (升級版：精準支援 UTK0201_ 家族各種跳轉)"""
        upper_url = url.upper()

        # ==========================================
        # 🔥 新增：在處理任何動作前，先物理消滅灰屏與轉圈圈！
        # ==========================================
        await self.block_loading_overlay()
        # ==========================================
        # 0. 首頁狀態重置與登入跳轉
        # ==========================================
        if 'UTK0101_' in upper_url:
            self.is_date_selected = False
            self.is_area_selected = False
            self.is_seat_selected = False
            self.is_telegram_sent = False

            if not getattr(self, 'is_login_done', False):
                print(">>> [寬宏售票] 偵測到在首頁且尚未登入，準備強制導航前往登入頁面...")
                login_url = "https://kham.com.tw/application/utk13/utk1306_.aspx"
                jump_js = f"window.location.href = '{login_url}';"
                try:
                    await self.tab.evaluate(jump_js)
                except:
                    pass
                import asyncio
                await asyncio.sleep(1)
                return

        # ==========================================
        # 1. 自動登入階段
        # ==========================================
        elif 'UTK1306_' in upper_url:
            if not getattr(self, 'is_login_done', False):
                if hasattr(self, 'auto_login'):
                    await self.auto_login()

        # ==========================================
        # 1.5 活動詳情頁 (我要購票按鈕)
        # 排除 000(區域頁), 001(票數頁), 041/00.ASPX(日期頁)
        # ==========================================
        elif 'UTK0201_040' in upper_url or ('UTK0201_' in upper_url and not any(x in upper_url for x in ['UTK0201_00', 'UTK0201_041', 'UTK0201_000', 'UTK0201_001'])):
            self.is_date_selected = False
            self.is_area_selected = False
            self.is_seat_selected = False
            if hasattr(self, 'click_go_buy'):
                await self.click_go_buy()

        # ==========================================
        # 2. 選擇日期/場次
        # ==========================================
        elif any(x in upper_url for x in ['UTK0201_00.ASPX', 'UTK0201_041']):
            self.is_area_selected = False
            self.is_seat_selected = False
            if not getattr(self, 'is_date_selected', False):
                if hasattr(self, 'select_date'):
                    await self.select_date()

        # ==========================================
        # 3. 🔥 選擇區域 (支援舊版 UTK0204_ 與新版 UTK0201_000)
        # ==========================================
        elif any(x in upper_url for x in ['UTK0204_.ASPX', 'UTK0201_000']):

            # 🌟 新增：在點擊區域前/後，隨時檢查是否有 jQuery 彈窗擋路
            error_msg = await self.check_and_close_jquery_dialog()

            if error_msg:
                # 如果抓到彈窗 (例如: "節目尚未啟售！" 或 "無足夠空位")
                print(f">>> [系統] 💥 區域頁面遭系統攔截: 【{error_msg}】 (已自動點掉)")
                self.is_area_selected = False

                # 既然沒點成功，立刻觸發極速重整，不浪費時間
                base_wait = getattr(self, 'refresh_sec', 0.2)
                try:
                    await self.fast_reload(base_wait)
                except:
                    pass
                import asyncio
                await asyncio.sleep(base_wait)
                return  # 提早結束這回合，等待新頁面載入

            # 如果沒有彈窗，才進行正常的選區邏輯
            self.is_seat_selected = False
            if not getattr(self, 'is_area_selected', False):
                if hasattr(self, 'select_area'):
                    await self.select_area()

        # ==========================================
        # 4. 票數選擇 / 座位選擇
        # ==========================================
        elif any(x in upper_url for x in ['UTK0202_', 'UTK0205_', 'UTK0201_001']):
            if not getattr(self, 'is_area_selected', False):
                print(">>> [系統] 🎯 偵測到已進入票數/座位頁面，立刻啟動搶票程式！")
                self.is_area_selected = True

            # 🔥 情境 3：處理進入瞬間的原生或 jQuery 彈窗
            native_msg = self.consume_native_alert()
            jquery_msg = await self.check_and_close_jquery_dialog()
            error_msg = native_msg or jquery_msg

            if error_msg:
                if "加入購物車" in error_msg or "完成" in error_msg:
                    print(f">>> [系統] 🎉 恭喜！系統提示：【{error_msg}】")
                    self.is_seat_selected = True
                else:
                    print(f">>> [系統] 💥 系統彈窗攔截: 【{error_msg}】")
                    self.is_seat_selected = False

                    # CDP 關掉 alert 後，重新確認現在到底在哪一頁
                    try:
                        live_url = await self.tab.evaluate("window.location.href")
                        live_upper = live_url.upper()
                    except:
                        return

                    # 已經被退回區域頁 → 不要 reload，直接交給下一輪 select_area
                    if any(x in live_upper for x in ['UTK0204_', 'UTK0201_000']):
                        print(">>> [系統] 🔄 彈窗關閉後已退回區域頁，繼續刷區域！")
                        self.is_area_selected = False
                        self.is_seat_selected = False
                        self.is_printing_area = False
                        return

                    # 還留在張數/座位頁 → 才重整這一頁
                    if any(x in live_upper for x in ['UTK0202_', 'UTK0205_', 'UTK0201_001']):
                        base_wait = getattr(self, 'refresh_sec', 0.2)
                        if base_wait <= 0:
                            base_wait = 0.2
                        print(f">>> [系統] ⏳ 仍停留張數頁，{base_wait} 秒後重新整理...")
                        try:
                            await self.fast_reload(base_wait)
                        except:
                            pass
                        return

                    return  # 其他未知頁面提早結束

            # 正常選位與打碼流程
            if not getattr(self, 'is_seat_selected', False):
                print(">>> [DEBUG] 準備執行 select_tickets 選位模組...")
                seat_success = await self.select_tickets()
                print(f">>> [DEBUG] select_tickets 執行完畢，結果: {seat_success}")

                if seat_success:
                    self.is_seat_selected = True  # 先鎖住，避免同頁面重複執行
                    import asyncio
                    await asyncio.sleep(0.3)

                    # 執行 OCR
                    ocr_success = await self.process_captcha()
                    if not ocr_success:
                        self.is_seat_selected = False  # OCR失敗解鎖
                        return

                    # 點擊送出
                    clicked = await self.click_next()
                    if not clicked:
                        self.is_seat_selected = False  # 點擊失敗解鎖
                        return

                    # 🔥 情境 2：點擊送出後的狀態判定
                    await asyncio.sleep(0.15)
                    post_native_msg = self.consume_native_alert()
                    try:
                        now_url = await self.tab.evaluate("window.location.href")
                    except:
                        return
                    now_upper = now_url.upper()

                    # 情況 A：系統把我們退回區域頁
                    if any(x in now_upper for x in ['UTK0204_', 'UTK0201_000']):
                        print(">>> [系統] 🔄 送出後已退回區域頁，交回選區程式繼續刷票")
                        self.is_area_selected = False
                        self.is_seat_selected = False
                        self.is_printing_area = False
                        return

                    # 情況 B：還卡在張數頁面
                    if any(x in now_upper for x in ['UTK0202_', 'UTK0205_', 'UTK0201_001']):
                        if post_native_msg:
                            print(f">>> [系統] 💥 送出後收到原生提示：【{post_native_msg}】")
                            self.is_seat_selected = False  # 解開鎖以利下一輪

                            # 若為售完，執行刷新
                            if "售完" in post_native_msg or "無足夠空位" in post_native_msg:
                                base_wait = getattr(self, 'refresh_sec', 0.2)
                                if base_wait <= 0:
                                    base_wait = 0.2
                                print(f">>> [系統] {base_wait} 秒後重新整理張數頁...")
                                await self.fast_reload(base_wait)
                            else:
                                # 其他錯誤 (如: 驗證碼錯誤) 不刷新頁面，直接讓下一輪重新填寫/辨識
                                print(">>> [系統] ⚠️ 非售完提示，已解除座位鎖並重新判定流程")
                        return

    async def reload_settings(self, silent=False):
        """[寬宏售票] 從設定檔讀取最新搶票設定 (支援多重設定檔動態切換 + 磁碟 I/O 提速)"""
        import json
        import os

        # 🔥 核心修正：直接使用初始化時從 plg.py 接過來的正確路徑
        settings_path = getattr(self, 'settings_path', 'settings.json')

        try:
            if not os.path.exists(settings_path):
                return

            # 🔥 終極提速核心：檢查檔案修改時間，沒變過就不讀取硬碟，直接秒退！
            current_mtime = os.path.getmtime(settings_path)
            if getattr(self, 'last_settings_mtime', 0) == current_mtime:
                return
            self.last_settings_mtime = current_mtime

            with open(settings_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)

            # 同步更新各個區塊的設定
            if "area_auto_select" in new_config:
                self.config["area_auto_select"] = new_config["area_auto_select"]
            if "date_auto_select" in new_config:
                self.config["date_auto_select"] = new_config["date_auto_select"]
            if "advanced" in new_config:
                self.config["advanced"] = new_config["advanced"]
            if "keyword_exclude" in new_config:
                self.config["keyword_exclude"] = new_config["keyword_exclude"]
            if "ticket_number" in new_config:
                self.config["ticket_number"] = new_config["ticket_number"]
                self.ticket_number = int(new_config.get("ticket_number", 1))

            # 強制優先讀取 GUI 上的「重新整理間隔」
            if "advanced" in new_config and "auto_reload_page_interval" in new_config["advanced"]:
                self.refresh_sec = float(
                    new_config["advanced"]["auto_reload_page_interval"])
            elif "refresh_sec" in new_config:
                self.refresh_sec = float(new_config["refresh_sec"])

            if not silent:
                current_refresh = getattr(self, 'refresh_sec', 0.2)
                # 抓出純檔名，讓 Log 看起來乾淨俐落
                filename = os.path.basename(settings_path)
                print(
                    f">>> [系統] 寬宏售票已套用最新設定 [{filename}] (目標: {self.ticket_number} 張 | 失敗重整: {current_refresh} 秒)")

        except Exception as e:
            # print(f">>> [DEBUG] 寬宏 reload_settings 出錯: {e}")
            pass

    async def setup_native_dialog_handler(self):
        """全域處理瀏覽器原生 alert / confirm / prompt"""
        if getattr(self, "native_dialog_handler_installed", False):
            return

        import nodriver as uc

        async def on_dialog(event):
            try:
                msg = getattr(event, "message", "") or ""
                self.last_native_alert = msg

                print(f">>> [原生彈窗] ⚠️ {msg}")

                # 真正從瀏覽器層把 alert 按掉
                await self.tab.send(
                    uc.cdp.page.handle_java_script_dialog(accept=True)
                )

            except Exception as e:
                print(f">>> [原生彈窗] 處理失敗: {e}")

        self._native_dialog_callback = on_dialog

        self.tab.add_handler(
            uc.cdp.page.JavascriptDialogOpening,
            self._native_dialog_callback
        )

        await self.tab.send(uc.cdp.page.enable())
        self.native_dialog_handler_installed = True

    def consume_native_alert(self):
        """取出並清空最近一次的原生彈窗訊息"""
        msg = getattr(self, "last_native_alert", "")
        self.last_native_alert = ""
        return msg

    async def optimize_network_speed(self):
        """
        [方案 A - 已停用]
        由於目前使用的 nodriver 版本會有底層衝突 (可能導致瀏覽器閃退)，
        因此在此環境下放棄攔截 CSS，全面交由方案 B (fast_reload) 的 window.stop() 來斬斷連線。
        """
        self.is_network_optimized = True
        return

    async def fast_reload(self, wait_sec=0.2):
        """
        🔥 [方案 B] 極速重整機制：
        取代原生的 window.location.reload()。先強制截斷當前卡住的請求，再進行無快取替換。
        """
        js_fast_reload = """
        (function() {
            try {
                window.stop(); // 🔪 殺掉所有正在 pending 的網路請求 (防卡頓)
                window.location.replace(window.location.href); // 🚀 替換當前頁面，不產生歷史紀錄
            } catch(e) {}
        })();
        """
        try:
            await self.tab.evaluate(js_fast_reload)
        except:
            pass

        # 統一在這裡處理延遲，讓你的主程式碼更乾淨
        import asyncio
        await asyncio.sleep(wait_sec)

    async def block_loading_overlay(self):
        """[寬宏售票] 破甲機制：強制隱藏轉圈圈與灰屏遮罩，防止點擊被攔截"""
        js_inject_css = """
        (function() {
            try {
                // 如果已經注入過，就不要重複注入
                if (document.getElementById('anti-kham-loading')) return;
                
                let style = document.createElement('style');
                style.id = 'anti-kham-loading';
                
                // 🔥 終極破甲：加入寬宏專屬的 #__SCREEN 與 #__LOADINGBAR
                style.innerHTML = `
                    #__SCREEN, #__LOADINGBAR,
                    .blockUI, .blockOverlay, .blockMsg, 
                    #loading, #WaitBox, #mask, .loading-mask, 
                    #ajax-loader, .spinner, #loading-spinner,
                    div[style*="z-index: 1000"][style*="opacity"] {
                        display: none !important;
                        visibility: hidden !important;
                        opacity: 0 !important;
                        width: 0 !important;
                        height: 0 !important;
                        pointer-events: none !important;
                    }
                `;
                document.head.appendChild(style);
            } catch (e) {}
        })();
        """
        try:
            await self.tab.evaluate(js_inject_css)
        except:
            pass

    async def auto_login(self):
        """[核心] 寬宏售票：會說話的自動填表與 OCR 登入"""

        # 防呆提示：不要每 0.05 秒一直印
        if not getattr(self, 'is_printing_login', False):
            print(">>> [寬宏售票-登入] 進入登入頁面，準備填寫帳密與驗證碼...")
            self.is_printing_login = True

        # ==========================================
        # 🔥 核心修正：讀取寬宏專屬的帳號密碼！
        # ==========================================
        account = self.config.get("advanced", {}).get("kham_account", "")
        password = self.config.get("advanced", {}).get(
            "kham_password_plaintext", "").strip()

        if not password:
            try:
                import util
                password = util.decrypt_me(self.config.get(
                    "advanced", {}).get("kham_password", ""))
            except:
                pass

        if not account or not password:
            if not getattr(self, 'is_printing_no_acc', False):
                print(">>> [寬宏售票-登入] ⚠️ 未設定寬宏帳號密碼，請手動登入！")
                self.is_printing_no_acc = True
            return

        # 狀態機 JS 腳本：精準回報網頁現況
        js_fill_credentials = f"""
        (function() {{
            try {{
                let accInput = document.querySelector('#ACCOUNT');
                let pwdInput = document.querySelector('#PASSWORD');

                // 如果元素還沒生出來，回報 WAITING
                if (!accInput || !pwdInput) return "WAITING_DOM";

                // 如果是空的，執行填寫並回報 JUST_FILLED
                if (accInput.value === '') {{
                    accInput.value = '{account}';
                    pwdInput.value = '{password}';
                    accInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return "JUST_FILLED";
                }}

                // 如果已經填過了，回報 ALREADY_FILLED
                return "ALREADY_FILLED";
            }} catch(e) {{
                return "ERROR";
            }}
        }})();
        """

        try:
            status = await self.tab.evaluate(js_fill_credentials)

            # 只要帳密格子裡有字了 (剛填好 或 已經填好)，就發動 OCR 攻擊！
            if status == "JUST_FILLED" or status == "ALREADY_FILLED":
                if status == "JUST_FILLED":
                    print(">>> [寬宏售票-登入] 帳號密碼自動填寫完成！準備破解圖形驗證碼...")

                # 呼叫 OCR
                ocr_success = await self.process_captcha()

                # 如果 OCR 成功，點擊送出
                if ocr_success:
                    print(">>> [寬宏售票-登入] 驗證碼填入完畢，等待 0.5 秒確保網頁消化...")
                    import asyncio
                    await asyncio.sleep(0.5)

                    js_click_login = """
                    (function() {
                        let loginBtn = document.querySelector('button[onclick*="doLogin1"]');
                        if (loginBtn && !loginBtn.disabled) {
                            loginBtn.click();
                            return true;
                        }
                        return false;
                    })();
                    """
                    btn_clicked = await self.tab.evaluate(js_click_login)
                    if btn_clicked:
                        print(">>> [寬宏售票-登入] 👉 已自動點擊「送出」按鈕！")
                        self.is_login_done = True
                        self.is_printing_login = False  # 解開 Log 鎖，以防登入失敗退回還能重新印
                    else:
                        print(">>> [寬宏售票-登入] ⚠️ 找不到送出按鈕！")

        except Exception as e:
            print(f">>> [寬宏售票-登入] 過程發生錯誤: {e}")

    async def process_captcha(self):
        """[寬宏售票] 共用核心：處理圖形驗證碼"""
        print(">>> [OCR] 開始處理圖形驗證碼...")

        # 抓取寬宏驗證碼圖片 (#chk_pic)
        js_get_image = """
        (function() {
            var img = document.querySelector('#chk_pic');
            if (!img) return null;

            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """

        try:
            # 最多嘗試辨識 3 次
            for attempt in range(3):
                base64_data = await self.tab.evaluate(js_get_image)
                if not base64_data:
                    print(">>> [OCR] 找不到驗證碼圖片 (#chk_pic)")
                    return False

                import base64
                img_bytes = base64.b64decode(base64_data)

                # 確保 ddddocr 已經成功載入
                if self.ocr:
                    ocr_answer = self.ocr.classification(img_bytes)
                    ocr_answer = ocr_answer.strip() if ocr_answer else ""
                else:
                    print(">>> [OCR] ddddocr 尚未初始化，無法辨識！")
                    return False

                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                # 寬宏的驗證碼通常是 4 碼
                if len(ocr_answer) == 4:
                    js_fill_input = f"""
                    (function() {{
                        // 填入寬宏驗證碼輸入框 (#CHK)
                        var input = document.querySelector('#CHK');
                        if (input) {{
                            input.value = '{ocr_answer}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }})();
                    """
                    is_filled = await self.tab.evaluate(js_fill_input)
                    if is_filled:
                        print(f">>> [OCR]  已自動填入驗證碼: {ocr_answer}")
                        return True
                    else:
                        print(">>> [OCR]  找不到驗證碼輸入框！")
                        return False
                else:
                    # 辨識失敗，點擊圖片換一張新的
                    print(">>> [OCR]  辨識長度不對，刷新圖片重試...")
                    js_refresh_img = "let img = document.querySelector('#chk_pic'); if(img) img.click();"
                    await self.tab.evaluate(js_refresh_img)
                    import asyncio
                    await asyncio.sleep(0.5)  # 給網頁時間載入新圖片

            return False

        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False

    async def select_date(self):
        """[寬宏售票] 場次/日期選擇 (泛用表格結構相容版 + 優先購買解鎖)"""
        await self.reload_settings(silent=True)

        if not getattr(self, 'is_printing_date', False):
            print(">>> [寬宏售票-日期] 進入日期選擇頁面，等待場次表載入...")
            self.is_printing_date = True

        try:
            date_auto_select = self.config.get("date_auto_select", {})
            if not date_auto_select.get("enable", True):
                print(">>> [寬宏售票-日期] 設定檔未啟用，跳過。")
                return

            raw_keyword = date_auto_select.get("date_keyword", "").strip()
            import json
            keyword_list = []
            if len(raw_keyword) > 0:
                try:
                    if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                        keyword_list = json.loads(raw_keyword)
                    else:
                        keyword_list = json.loads("[" + raw_keyword + "]")
                except:
                    keyword_list = [raw_keyword]
            else:
                keyword_list = [""]

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_mode = f"'{date_auto_select.get('mode', 'from top to bottom')}'"

            js_script = f"""
            (function() {{
                try {{
                    const keywords = {js_keywords};
                    const mode = {js_mode};

                    // 🔥 修正：不再強求 table 具備特定 class，直接抓取所有表格列
                    let rows = Array.from(document.querySelectorAll("table tbody tr"));

                    if (rows.length === 0) return "WAITING_DOM";
                    if (rows.length === 1 && rows[0].innerText.includes('載入')) return "WAITING_DOM";

                    let candidates = [];

                    for (let row of rows) {{
                        // 防呆：如果是標題列 (th) 就直接跳過
                        if (row.querySelector('th')) continue;

                        let btn = row.querySelector("button");
                        if (!btn || btn.disabled) continue;

                        let btnText = btn.innerText || "";
                        if (btnText.includes('售完') || btnText.includes('額滿')) continue;
                        // 確保這個按鈕是我們想要的訂購按鈕
                        if (!btnText.includes('訂購') && !btnText.includes('購票')) continue;

                        let rowText = row.innerText.toUpperCase();
                        // 日期格式化：增加配對容錯率
                        let dateMatch = rowText.match(/(\\d{{4}})\\s*\\/\\s*(\\d{{2}})\\s*\\/\\s*(\\d{{2}})/);
                        if (dateMatch) {{
                            let y = dateMatch[1];
                            let m_str = dateMatch[2];
                            let d_str = dateMatch[3];
                            let m_int = parseInt(m_str, 10).toString();
                            let d_int = parseInt(d_str, 10).toString();
                            rowText += ` ${{y}}/${{m_str}}/${{d_str}} ${{y}}/${{m_int}}/${{d_int}} ${{m_str}}/${{d_str}} ${{m_int}}/${{d_int}} ${{m_str}}${{d_str}} ${{m_int}}月${{d_int}}日 ${{m_str}}月${{d_str}}日`;
                        }}

                        let isMatch = false;
                        if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                            isMatch = true;
                        }} else {{
                            for (let k of keywords) {{
                                let target_kws = k.trim().split(" ").filter(w => w.length > 0);
                                let currentGroupMatch = true;
                                for (let w of target_kws) {{
                                    if (!rowText.includes(w.toUpperCase())) {{
                                        currentGroupMatch = false;
                                        break;
                                    }}
                                }}
                                if (currentGroupMatch) {{
                                    isMatch = true;
                                    break;
                                }}
                            }}
                        }}

                        if (isMatch) {{
                            candidates.push(btn);
                        }}
                    }}

                    if (candidates.length === 0) return "RELOAD";

                    if (mode === "from bottom to top") {{
                        candidates.reverse();
                    }} else if (mode === "random") {{
                        for (let i = candidates.length - 1; i > 0; i--) {{
                            const j = Math.floor(Math.random() * (i + 1));
                            [candidates[i], candidates[j]] = [
                                candidates[j], candidates[i]];
                        }}
                    }}

                    candidates[0].click();
                    return "SUCCESS";

                }} catch (e) {{
                    return "ERROR|" + e.toString();
                }}
            }})();
            """

            result = await self.tab.evaluate(js_script)
            import asyncio

            if result == "SUCCESS":
                print(">>> [寬宏售票-日期] 🎉 成功匹配日期並執行點擊！")

                # ==========================================
                # 🔥 新增：偵測並處理「優先購買 / 會員驗證碼」彈窗
                # ==========================================
                await asyncio.sleep(0.2)  # 給予彈窗顯示的短暫緩衝時間

                # 安全取得 user_guess_string
                raw_guess_code = self.config.get("advanced", {}).get(
                    "user_guess_string", self.config.get("user_guess_string", ""))

                # 💡 自動切割處理：如果設定為 "123","456" 則只取第一個 123，並自動脫掉頭尾引號與空白
                if isinstance(raw_guess_code, list) and raw_guess_code:
                    first_guess = str(raw_guess_code[0])
                else:
                    first_guess = str(raw_guess_code).split(',')[0]
                guess_code = first_guess.strip(' \'"')

                js_vip_login = f"""
                (function() {{
                    try {{
                        let input1 = document.querySelector('#ID1');
                        let btn = document.querySelector('button[onclick*="DoVIPLogin"]');
                        
                        // 檢查輸入框是否存在，且不是隱藏狀態
                        if (input1 && input1.offsetParent !== null) {{
                            input1.value = '{guess_code}';
                            input1.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input1.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            
                            if (btn) {{
                                btn.click();
                                return "VIP_SUBMITTED";
                            }}
                            return "BTN_NOT_FOUND";
                        }}
                        return "NO_POPOUT";
                    }} catch(e) {{
                        return "ERROR|" + e.toString();
                    }}
                }})();
                """
                vip_res = await self.tab.evaluate(js_vip_login)
                if vip_res == "VIP_SUBMITTED":
                    print(
                        f">>> [寬宏售票-日期] 🔐 偵測到優先購買驗證，已自動填入代碼並送出: 【{guess_code}】")
                    await asyncio.sleep(0.5)  # 給予伺服器驗證與跳轉的飛行時間
                elif vip_res == "BTN_NOT_FOUND":
                    print(">>> [寬宏售票-日期] ⚠️ 偵測到驗證輸入框，但找不到送出按鈕！")
                # ==========================================

                self.is_date_selected = True

            elif result == "WAITING_DOM":
                if not hasattr(self, 'date_wait_count'):
                    self.date_wait_count = 0
                self.date_wait_count += 1
                if self.date_wait_count % 10 == 0:
                    print(">>> [寬宏售票-日期] ⏳ 等待寬宏伺服器回傳場次資料... (網頁轉圈圈中)")
                await asyncio.sleep(0.05)

            elif result == "RELOAD":
                base_wait = getattr(self, 'refresh_sec', 0.2)
                if base_wait <= 0:
                    base_wait = 0.2

                print(f">>> [寬宏售票-日期] ⏳ 找不到符合關鍵字的場次或已售完，{base_wait} 秒後自動重整...")
                try:
                    # 🔥 幫你修正了這裡的 actual_wait Bug
                    await self.fast_reload(base_wait)
                except:
                    pass
                await asyncio.sleep(base_wait)

            elif isinstance(result, str) and result.startswith("ERROR|"):
                print(f">>> [DEBUG] 日期選擇 JS 執行發生內部錯誤: {result}")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_date 發生 Python 例外: {e}")

    async def select_area(self):
        """[寬宏售票] 區域選擇 (新版表格相容 + 防擋彈窗 + 隨機秒數重整)"""

        await self.reload_settings(silent=True)

        if not getattr(self, 'is_printing_area', False):
            print(">>> [系統] 進入寬宏售票區域選擇階段...")
            self.is_printing_area = True

        import asyncio
        await asyncio.sleep(0.15)

        try:
            area_auto_select = getattr(
                self, 'area_auto_select', self.config.get("area_auto_select", {}))
            if not area_auto_select.get("enable", True):
                print(">>> [寬宏售票-區域] 設定檔未啟用區域自動選擇，跳過。")
                return

            auto_select_mode = area_auto_select.get(
                "mode", "from top to bottom")
            raw_keyword = area_auto_select.get("area_keyword", "").strip()
            raw_keyword_exclude = self.config.get("keyword_exclude", "")
            if not raw_keyword_exclude:
                raw_keyword_exclude = area_auto_select.get(
                    "area_keyword_exclude", "")
            raw_keyword_exclude = str(raw_keyword_exclude).strip()

            import json

            def parse_keywords(kw_str):
                kw_str = kw_str.strip()
                if not kw_str:
                    return [""]
                try:
                    if kw_str.startswith("[") and kw_str.endswith("]"):
                        return json.loads(kw_str)
                    if '"' in kw_str or "'" in kw_str:
                        return json.loads("[" + kw_str + "]")
                except:
                    pass
                return [x.strip().strip('\'"') for x in kw_str.replace('，', ',').split(',') if x.strip()]

            keyword_list = parse_keywords(raw_keyword)
            exclude_list = parse_keywords(raw_keyword_exclude)

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_excludes = json.dumps(exclude_list, ensure_ascii=False)
            js_mode = f"'{auto_select_mode}'"

            # 構建 寬宏售票專用 的 JavaScript 腳本
            js_script = f"""
            (function() {{
                try {{
                    // 偷偷攔截系統原生的 alert，防止點擊時被無意義的警告彈窗卡住
                    if (!window.khamHookedArea) {{
                        window.khamAlertMsgArea = "";
                        window.originalAlertArea = window.alert;
                        window.alert = function(msg) {{
                            window.khamAlertMsgArea = msg;
                        }};
                        window.khamHookedArea = true;
                    }}

                    const keywords = {js_keywords};
                    const excludes = {js_excludes};
                    const mode = {js_mode};

                    // 尋找所有狀態列 (寬宏新版的區域都是 tr.status_tr)
                    let rows = Array.from(document.querySelectorAll('tr.status_tr'));
                    let candidates = [];

                    if (rows.length > 0) {{
                        for (let row of rows) {{
                            // 1. 檢查空位狀態
                            let emptyTd = row.querySelector('td[data-title="空位："]');
                            if (!emptyTd) continue;
                            let emptyText = (emptyTd.innerText || "").trim().toUpperCase();

                            // 如果空位寫著 0, 售完, 額滿，直接跳過這區
                            if (emptyText === '0' || emptyText.includes('售完') || emptyText.includes('額滿')) continue;

                            // 2. 獲取該區的文字內容並清理格式
                            let rowContent = (row.innerText || "").replace(/,/g, '').toUpperCase();

                            // 預設排除身障席位 (除非關鍵字有明講)
                            let isHandicap = rowContent.includes('輪椅') || rowContent.includes('身障') || rowContent.includes('陪同');

                            // 3. 處理排除關鍵字
                            let isExcluded = false;
                            if (excludes.length > 0 && excludes[0] !== "") {{
                                for (let exc of excludes) {{
                                    let cleanExc = exc.trim().replace(/,/g, '').toUpperCase();
                                    if (cleanExc.length > 0 && rowContent.includes(cleanExc)) {{
                                        isExcluded = true;
                                        break;
                                    }}
                                }}
                            }}
                            if (isExcluded) continue;

                            // 4. 處理包含關鍵字配對
                            let isMatch = false;
                            if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                                // 沒有設關鍵字：有票就當作候選！但自動排除身障席
                                if (!isHandicap) isMatch = true;
                            }} else {{
                                for (let k of keywords) {{
                                    let target_kws = k.trim().replace(/,/g, '').split(/\\s+/).filter(w => w.length > 0);
                                    let currentGroupMatch = true;
                                    for (let w of target_kws) {{
                                        // 價格容錯：例如使用者輸入 5600，但網頁是 5680，我們可以只比對前面數字
                                        // 這裡直接比對字串是否包含
                                        if (!rowContent.includes(w.toUpperCase())) {{
                                            currentGroupMatch = false;
                                            break;
                                        }}
                                    }}
                                    if (currentGroupMatch) {{
                                        isMatch = true;
                                        break;
                                    }}
                                }}
                            }}

                            if (isMatch) {{
                                candidates.push(row);
                            }}
                        }}
                    }}

                    // 如果沒有任何候選區域有票，回報重整
                    if (candidates.length === 0) return "RELOAD";

                    // 5. 根據排序模式決定點擊哪一個
                    if (mode === "from bottom to top") {{
                        candidates.reverse();
                    }} else if (mode === "random") {{
                        for (let i = candidates.length - 1; i > 0; i--) {{
                            const j = Math.floor(Math.random() * (i + 1));
                            [candidates[i], candidates[j]] = [
                                candidates[j], candidates[i]];
                        }}
                    }}

                    let targetRow = candidates[0];

                    // 點擊事件觸發
                    if (typeof jQuery !== 'undefined') {{
                        jQuery(targetRow).trigger('click');
                    }} else {{
                        targetRow.click();
                    }}

                    // 檢查點擊瞬間有沒有被系統彈窗擋下來 (例如秒殺被搶空)
                    if (window.khamAlertMsgArea !== "") {{
                        let msg = window.khamAlertMsgArea;
                        window.khamAlertMsgArea = "";
                        return "ALERT|" + msg;
                    }}

                    return "SUCCESS";

                }} catch(e) {{
                    return "ERROR|" + e.toString();
                }}
            }})();
            """

            result = await self.tab.evaluate(js_script)

            # 取得基礎重整秒數，防呆備用
            base_wait = getattr(self, "refresh_sec", 0.2)
            if base_wait <= 0:
                base_wait = 0.2

            if result == "SUCCESS":
                # ==========================================
                # 🔥 新增：點擊後不要盲目等待，給予 0.15 秒讓 jQuery 錯誤彈窗浮現
                # ==========================================
                await asyncio.sleep(0.15)
                error_msg = await self.check_and_close_jquery_dialog()

                if error_msg:
                    # 抓到點太慢跳出的提示 (例如: "無足夠空位" / "此區域已售完")
                    print(
                        f">>> [寬宏售票-區域] 💥 點擊慢了一步！系統攔截: 【{error_msg}】 (已自動點掉 Ok)"
                    )
                    self.is_area_selected = False
                    self.is_printing_area = False
                    print(">>> [寬宏售票-區域] 🚀 立即極速重整，搶進其他區域...")
                    await self.fast_reload(base_wait)
                    return

                # 如果毫無彈窗，才是真正成功的點擊！
                print(">>> [寬宏售票-區域] 🎉 成功匹配關鍵字並點擊空位區域！")
                await asyncio.sleep(0.3)
                self.is_area_selected = True

            elif isinstance(result, str) and result.startswith("ALERT|"):
                alert_msg = result.split("|")[1]
                print(f">>> [系統] ⚠️ 點擊區域時被原生系統攔截！訊息：【{alert_msg}】")
                print(">>> [系統] 準備重新整理尋找其他機會...")
                self.is_printing_area = False
                await self.fast_reload(base_wait)

            elif result == "RELOAD":
                advanced_conf = self.config.get("advanced", {})
                is_random = advanced_conf.get("auto_reload_random_mode", False)
                actual_wait = base_wait

                if is_random:
                    import random

                    try:
                        rand_range = float(
                            advanced_conf.get("auto_reload_random_range", 1.0)
                        )
                    except:
                        rand_range = 1.0
                    actual_wait = round(
                        base_wait + random.uniform(0, rand_range), 2)

                print(
                    f">>> [寬宏售票-區域] ⏳ 找不到符合關鍵字或皆已售完，準備刷新... (等待 {actual_wait} 秒)"
                )
                await self.fast_reload(actual_wait)

            elif isinstance(result, str) and result.startswith("ERROR|"):
                print(f">>> [DEBUG] 區域選擇 JS 執行發生內部錯誤: {result}")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_area 發生 Python 例外: {e}")

    async def select_tickets(self):
        """[寬宏售票] 智能票數與座位選擇 (支援一般/座位圖雙模式 + 隨機秒數重整)"""
        ticket_num = self.ticket_number
        if ticket_num <= 0:
            return False

        js_select = f"""
        (function() {{
            try {{
                const targetTickets = {ticket_num};
                const seatTable = document.querySelector('#TBL');

                // ==========================================
                // 模式 2：座位圖模式 (有 #TBL)
                // ==========================================
                if (seatTable || window.location.href.toUpperCase().includes('UTK0205_')) {{

                    // A. 選擇票種 (尋找綠色按鈕，避開身障與陪同票)
                    let typeBtns = document.querySelectorAll('button.green');
                    let selectedBtn = null;
                    for (let btn of typeBtns) {{
                        let btnText = btn.innerText || "";
                        if (btnText.includes('身障') || btnText.includes('陪同') || btnText.includes('身心障礙')) continue;
                        selectedBtn = btn;
                        break;
                    }}
                    if (selectedBtn) selectedBtn.click();

                    // B. 尋找空座位 (優先找同行連號)
                    let rows = document.querySelectorAll('#TBL tbody tr');
                    let targetSeats = [];
                    for (let row of rows) {{
                        let cells = row.querySelectorAll('td');
                        let consec = [];
                        for (let cell of cells) {{
                            // 寬宏的空位 class 包含 empty
                            if (cell.classList.contains('empty')) {{
                                consec.push(cell);
                                if (consec.length === targetTickets) {{
                                    targetSeats = consec;
                                    break;
                                }}
                            }} else if (cell.classList.contains('people') || cell.innerHTML.includes('&nbsp;')) {{
                                // 遇到已售出或是走道，連號重新計算
                                consec = [];
                            }}
                        }}
                        if (targetSeats.length > 0) break;
                    }}

                    // 防呆：如果找不到連號，就硬抓剩下的所有散位
                    if (targetSeats.length === 0) {{
                        let allEmpty = Array.from(document.querySelectorAll('td.empty'));
                        if (allEmpty.length >= targetTickets) {{
                            targetSeats = allEmpty.slice(0, targetTickets);
                        }}
                    }}

                    // C. 點擊座位並聚焦驗證碼
                    if (targetSeats.length === targetTickets) {{
                        targetSeats.forEach(s => s.click());
                        let captchaInput = document.querySelector('#CHK');
                        if (captchaInput) captchaInput.focus();
                        return 1; // 成功
                    }} else {{
                        return 2; // 空位不足
                    }}
                }}

                // ==========================================
                // 模式 1：一般張數輸入模式 (沒有 #TBL)
                // ==========================================
                else {{
                    let rows = document.querySelectorAll('table tbody tr');
                    let targetInput = null;

                    for (let row of rows) {{
                        let labelCell = row.querySelector('td[data-th="內容："]');
                        if (labelCell) {{
                            let labelText = labelCell.innerText || "";
                            // 排除身障與陪同票
                            if (labelText.includes('身障') || labelText.includes('陪同') || labelText.includes('身心障礙')) continue;
                        }}

                        let input = row.querySelector('input.numbox[type="number"]');
                        if (input && !input.disabled) {{
                            targetInput = input;
                            break;
                        }}
                    }}

                    if (targetInput) {{
                        // 【關鍵】：先清空原本的 0，再填寫目標張數
                        targetInput.value = '';
                        targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        targetInput.value = targetTickets;

                        // 觸發寬宏的驗證腳本
                        targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        targetInput.dispatchEvent(new Event('change', {{ bubbles: true }}));

                        if (typeof checkNum === "function") {{
                            checkNum(targetInput);
                        }}

                        let captchaInput = document.querySelector('#CHK');
                        if (captchaInput) captchaInput.focus();
                        return 1; // 成功
                    }}
                    return 2; // 找不到可輸入的格子或已售完
                }}
            }} catch(e) {{
                return -1;
            }}
        }})();
        """

        try:
            print(">>> [DEBUG] 正在對網頁注入 js_select 腳本...")
            result = await self.tab.evaluate(js_select)
            print(f">>> [DEBUG] js_select 執行完畢，回傳值: {result}")
            if result == 1:
                print(f">>> [座位/票數] 🎉 成功鎖定 {ticket_num} 張票！準備進行 OCR 辨識...")
                self.is_seat_selected = True
                return True

            elif result == 2:
                # ==========================================
                # 失敗重整邏輯 (結合隨機秒數)
                # ==========================================
                advanced_conf = self.config.get("advanced", {})
                base_wait = getattr(self, 'refresh_sec', 0.2)
                if base_wait <= 0:
                    base_wait = 0.2

                is_random = advanced_conf.get("auto_reload_random_mode", False)
                actual_wait = base_wait

                if is_random:
                    import random
                    try:
                        rand_range = float(advanced_conf.get(
                            "auto_reload_random_range", 1.0))
                    except:
                        rand_range = 1.0
                    actual_wait = round(
                        base_wait + random.uniform(0, rand_range), 2)

                print(
                    f">>> [座位/票數] ❌ 殘念...剩餘空位不足 {ticket_num} 張！準備刷新... (等待 {actual_wait} 秒)")

                await self.fast_reload(actual_wait)

            elif result == -1:
                print(">>> [DEBUG] 選位 JS 執行發生內部錯誤")
                return False

        except Exception as e:
            print(f">>> [嚴重錯誤] select_tickets 發生例外: {e}")
        return False

    async def click_next(self):
        """[寬宏售票] 點擊加入購物車"""
        js_submit = """
        (function() {
            try {
                // 尋找帶有 addShoppingCart 函數的紅色按鈕
                let btn = document.querySelector('button[onclick*="addShoppingCart"]');

                if (btn && !btn.disabled) {
                    btn.click();
                    return true;
                }
                return false;
            } catch (e) {
                return false;
            }
        })();
        """
        try:
            result = await self.tab.evaluate(js_submit)
            if result:
                print(">>> [下一步] 🛒 已成功點擊「加入購物車」按鈕！")
                return True
        except:
            pass
        return False

    async def check_and_close_jquery_dialog(self):
        """[寬宏售票] 處理 jQuery UI 的錯誤彈窗，並擷取彈窗內的文字內容"""
        js_check_dialog = """
        (function() {
            try {
                // 尋找 jQuery UI 的底部按鈕
                let btn = document.querySelector('div.ui-dialog-buttonpane button');

                // 確認按鈕存在，且目前在畫面上是顯示狀態
                if (btn && btn.offsetParent !== null) {

                    // 將按鈕文字轉大寫去空白，擴大守備範圍
                    let btnText = (btn.innerText || "").trim().toUpperCase();

                    if (btnText.includes('OK') || btnText.includes('確定') || btnText.includes('確認') || btnText.includes('關閉')) {

                        // 往上尋找整個彈窗的父容器
                        let dialogBox = btn.closest('.ui-dialog');
                        let msgText = "未知的提示內容";

                        if (dialogBox) {
                            // 尋找 jQuery UI 存放文字內容的區塊
                            let contentNode = dialogBox.querySelector('.ui-dialog-content');
                            if (contentNode) {
                                msgText = contentNode.innerText.trim();
                            }
                        }

                        btn.click(); // 點擊關閉
                        return msgText; // 將抓到的文字回傳給 Python
                    }
                }
                return false;
            } catch (e) {
                return false;
            }
        })();
        """
        try:
            result = await self.tab.evaluate(js_check_dialog)
            # 如果回傳的是字串 (也就是有抓到彈窗)，Python 的 if 判斷會是 True
            if result:
                return result
        except:
            pass

        return False

    async def click_go_buy(self):
        """[寬宏售票] 第 1.5 階段：開賣前監控與狂點「我要購票」 (修復實名制無限迴圈版)"""
        await self.reload_settings(silent=True)
        base_wait = getattr(self, "refresh_sec", 0.2)
        if base_wait <= 0:
            base_wait = 0.2

        import asyncio

        # ==========================================
        # 🔥 1. 點擊前檢查：先檢查畫面上是否已經有預設彈窗 (例如：實名制宣告)
        # ==========================================
        error_msg = await self.check_and_close_jquery_dialog()
        if error_msg:
            # 關鍵修正：點掉公告後【絕對不要重整】，給它 0.2 秒淡出動畫的時間，然後繼續往下點擊購票！
            print(
                f">>> [寬宏售票] 💡 偵測到活動公告彈窗: 【{error_msg}】 (已自動點擊 Ok 關閉，繼續嘗試購票)")
            await asyncio.sleep(0.2)

        js_click = """
        (function() {
            try {
                // 攔截系統原生警告 (window.alert)，避免 alert 卡死瀏覽器
                if (!window.khamHookedPre) {
                    window.khamAlertMsgPre = "";
                    window.originalAlertPre = window.alert;
                    window.alert = function(msg) {
                        window.khamAlertMsgPre = msg;
                    };
                    window.khamHookedPre = true;
                }

                // 特徵掃描尋找購票按鈕
                let targetBtn = null;
                let btns = document.querySelectorAll('button, a.btn, input[type="button"]');
                for (let b of btns) {
                    let txt = (b.innerText || b.value || "").replace(/\\s/g, "");
                    let onc = b.getAttribute("onclick") || "";
                    if (txt.includes("我要購票") || txt.includes("立即購票") || onc.includes("doSend")) {
                        targetBtn = b;
                        break;
                    }
                }

                if (targetBtn) {
                    targetBtn.click();

                    // 檢查點擊後有沒有被原生 window.alert 阻擋
                    if (window.khamAlertMsgPre !== "") {
                        let msg = window.khamAlertMsgPre;
                        window.khamAlertMsgPre = "";
                        return "ALERT|" + msg;
                    }
                    return "CLICKED";
                }
                return "NOT_FOUND";
            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        try:
            result = await self.tab.evaluate(js_click)

            if result == "CLICKED":
                if not getattr(self, "is_printing_gobuy", False):
                    print(">>> [寬宏售票] 🚀 找到「我要購票」按鈕，發動點擊！等待跳轉...")
                    self.is_printing_gobuy = True

                # ==========================================
                # 🔥 2. 點擊後檢查：給予 0.1 秒讓 jQuery 彈窗動畫浮現 (處理「尚未啟售」)
                # ==========================================
                await asyncio.sleep(0.1)
                post_click_msg = await self.check_and_close_jquery_dialog()
                if post_click_msg:
                    print(
                        f">>> [寬宏售票] 💥 點擊後跳出彈窗: 【{post_click_msg}】 (已自動點擊 Ok 關閉)"
                    )
                    # 點擊按鈕後才跳出的彈窗 (尚未啟售等)，這時候才需要極速重整！
                    await self.fast_reload(base_wait)
                    return

                await asyncio.sleep(base_wait)

            elif isinstance(result, str) and result.startswith("ALERT|"):
                alert_msg = result.split("|")[1]
                if not getattr(self, "is_printing_gobuy_alert", False):
                    print(
                        f">>> [寬宏售票] ⏳ 系統提示：【{alert_msg}】，持續按設定的秒數重整搶進中..."
                    )
                    self.is_printing_gobuy_alert = True
                await self.fast_reload(base_wait)

            elif result == "NOT_FOUND":
                if not getattr(self, "is_printing_gobuy_wait", False):
                    print(
                        ">>> [寬宏售票] ⏳ 尚未看到「我要購票」按鈕，持續重整監控中..."
                    )
                    self.is_printing_gobuy_wait = True
                await self.fast_reload(base_wait)

        except Exception as e:
            pass


# ==========================================
# [寬宏售票]
# ==========================================


class KhamBot_API:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.settings_path = config.get("config_filepath", "settings.json")
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""
        self.is_done = False

        # ==========================================
        # KhamBot 診斷模式（只記錄，不改變原本搶票流程）
        # ==========================================
        self.diag_enabled = True
        self.diag_eval_count = 0
        self.diag_reload_count = 0
        self.diag_error_count = 0
        self.diag_consecutive_errors = 0
        self.diag_last_url = ""
        self.diag_started_at = time.monotonic()
        try:
            self.diag_log_path = os.path.join(
                util.get_app_root(), "kham_diagnostic.log")
        except Exception:
            self.diag_log_path = os.path.abspath("kham_diagnostic.log")
        self._diag_log("SESSION_START",
                       f"pid={os.getpid()} | log={self.diag_log_path}")

        # 狀態控制鎖
        self.is_login_done = False
        self.is_date_selected = False
        self.is_api_locking = False
        self.is_printing_login = False
        self.is_printing_no_acc = False

        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        print(">>> [寬宏 API 模式] 正在載入 ddddocr 模型...")
        try:
            import ddddocr
            self.ocr = ddddocr.DdddOcr(show_ad=False)
        except Exception as e:
            print(f">>> [系統] ddddocr 載入失敗: {e}")
            self.ocr = None

    def _diag_log(self, event, message=""):
        """寫入 KhamBot 專用診斷檔；避免記錄帳號、密碼與 JS 原文。"""
        if not getattr(self, "diag_enabled", False):
            return
        try:
            elapsed = time.monotonic() - getattr(self, "diag_started_at", time.monotonic())
            line = (f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] "
                    f"[+{elapsed:8.3f}s] [{event}] {message}\n")
            with open(self.diag_log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    @staticmethod
    def _diag_script_id(script):
        """只記錄 JS 長度與 hash，避免診斷檔意外包含登入資訊。"""
        try:
            import hashlib
            raw = str(script).encode("utf-8", errors="replace")
            return f"len={len(raw)} sha256={hashlib.sha256(raw).hexdigest()[:16]}"
        except Exception:
            return "script_id=unavailable"

    async def _diag_evaluate(self, script, *args, **kwargs):
        """evaluate 包裝器：記錄次數、耗時與例外，保留原本回傳值。"""
        caller = "unknown"
        try:
            import inspect
            caller = inspect.currentframe().f_back.f_code.co_name
        except Exception:
            pass

        self.diag_eval_count += 1
        seq = self.diag_eval_count
        script_id = self._diag_script_id(script)
        t0 = time.monotonic()
        self._diag_log("EVAL_START", f"#{seq} caller={caller} {script_id}")
        try:
            result = await self.tab.evaluate(script, *args, **kwargs)
            elapsed = time.monotonic() - t0
            self.diag_consecutive_errors = 0
            self._diag_log("EVAL_OK",
                           f"#{seq} caller={caller} elapsed={elapsed:.3f}s result_type={type(result).__name__}")
            if elapsed >= 1.0:
                self._diag_log(
                    "EVAL_SLOW", f"#{seq} caller={caller} elapsed={elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.monotonic() - t0
            self.diag_error_count += 1
            self.diag_consecutive_errors += 1
            self._diag_log(
                "EVAL_ERROR",
                f"#{seq} caller={caller} elapsed={elapsed:.3f}s "
                f"errors={self.diag_error_count} consecutive={self.diag_consecutive_errors} "
                f"exc={type(e).__name__}: {e}")
            raise

    def _diag_is_connection_error(self, exc):
        """判斷是否很像 Browser/CDP 連線已斷。"""
        text = f"{type(exc).__name__}: {exc}".lower()
        markers = (
            "websocket", "connection closed", "connection reset",
            "broken pipe", "target closed", "target crashed",
            "browser closed", "browser disconnected", "disconnected",
            "session closed", "no connection", "cdp",
        )
        return any(m in text for m in markers)

    async def run(self):
        print(f">>> [寬宏 API 變種搶票] 機器人啟動！(目標張數: {self.ticket_number})")
        while not self.is_done:
            try:
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                current_url = await self._diag_evaluate("window.location.href")
                self.diag_last_url = current_url or ""
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                upper_url = current_url.upper()
                await self.block_loading_overlay()

                # 0. 結帳頁面防護：原地休眠守護，不退出腳本，避免外層一直重建
                if 'UTK0206_' in upper_url:
                    if not getattr(self, 'is_printing_checkout', False):
                        print(
                            ">>> [結帳頁面] ✅ 已成功抵達結帳頁，請於時間內完成付款！(返回區域頁可自動解鎖重新刷票)")
                        self.is_printing_checkout = True
                    await asyncio.sleep(1)
                    continue
                else:
                    # 離開結帳頁面 (如手動按上一頁) 時，解除結帳印字鎖定
                    self.is_printing_checkout = False

                # 1. 首頁狀態重置與未登入自動跳轉
                if 'UTK0101_' in upper_url:
                    self.is_date_selected = False
                    self.is_api_locking = False
                    if not getattr(self, 'is_login_done', False):
                        print(">>> [寬宏售票] 偵測到在首頁且尚未登入，強制前往登入頁面...")
                        login_url = "https://kham.com.tw/application/utk13/utk1306_.aspx"
                        await self._diag_evaluate(f"window.location.href = '{login_url}';")
                        await asyncio.sleep(1)
                        continue

                # 2. 自動登入階段 (UTK1306_)
                elif 'UTK1306_' in upper_url:
                    if not getattr(self, 'is_login_done', False):
                        await self.auto_login()

                # 3. 活動詳情頁：監控開賣與點擊我要購票
                elif 'UTK0201_040' in upper_url or ('UTK0201_' in upper_url and not any(x in upper_url for x in ['UTK0201_00', 'UTK0201_041', 'UTK0201_000', 'UTK0201_001', 'UTK0205_', 'UTK0206_'])):
                    self.is_date_selected = False
                    self.is_api_locking = False
                    await self.click_go_buy()

                # 4. 場次/日期選擇頁
                elif any(x in upper_url for x in ['UTK0201_00.ASPX', 'UTK0201_041']):
                    self.is_api_locking = False
                    if not self.is_date_selected:
                        await self.select_date()

                # 5. 區域選擇頁面：直接在背景發動 API 鎖票
                elif any(x in upper_url for x in ['UTK0204_.ASPX', 'UTK0201_000']):
                    if not self.is_api_locking:
                        self.is_api_locking = True
                        print(">>> [API 模式] 🎯 進入區域頁面，發動 API 關鍵字鎖票與鎖位...")
                        success = await self.fast_api_lock_from_area_page()
                        if success:
                            print(">>> [API 模式] 🎉🎉 鎖票成功！直跳結帳頁面...")

                            await self._diag_evaluate("window.location.href = 'https://kham.com.tw/application/utk02/UTK0206_.aspx';")
                            # 不 break，交給下一次迴圈進入結帳頁面防護
                            continue
                        else:
                            self.is_api_locking = False

                # 6. 備用：若意外進入座位/票數頁，直接在記憶體修改/填表，搶輸自動極速重整
                elif any(x in upper_url for x in ['UTK0205_', 'UTK0202_', 'UTK0201_001']):
                    success = await self.fast_api_lock_fallback()
                    if success:
                        print(">>> [API 模式] 🎉🎉 鎖票成功！直跳結帳頁面...")
                        await self._diag_evaluate("window.location.href = 'https://kham.com.tw/application/utk02/UTK0206_.aspx';")
                        # 不 break，交給下一次迴圈進入結帳頁面防護
                        continue

            except Exception as e:
                self.diag_error_count += 1
                self.diag_consecutive_errors += 1
                self._diag_log(
                    "RUN_ERROR",
                    f"url={self.diag_last_url!r} errors={self.diag_error_count} "
                    f"consecutive={self.diag_consecutive_errors} "
                    f"exc={type(e).__name__}: {e}")

                # 診斷重點：若 CDP/Browser 明顯已斷線，或連續 3 次錯誤，
                # 停止無限 50ms 重試，讓外層拿到真正 traceback。
                if self._diag_is_connection_error(e) or self.diag_consecutive_errors >= 3:
                    self._diag_log("ABORT", "停止 KhamBot 重試，保留原始例外 traceback")
                    raise

            await asyncio.sleep(0.05)

    async def auto_login(self):
        """[核心] 寬宏售票：自動填表與 OCR 登入"""
        if not getattr(self, 'is_printing_login', False):
            print(">>> [寬宏售票-登入] 進入登入頁面，準備填寫帳密與驗證碼...")
            self.is_printing_login = True

        account = self.config.get("advanced", {}).get("kham_account", "")
        password = self.config.get("advanced", {}).get(
            "kham_password_plaintext", "").strip()

        if not password:
            try:
                import util
                password = util.decrypt_me(self.config.get(
                    "advanced", {}).get("kham_password", ""))
            except:
                pass

        if not account or not password:
            if not getattr(self, 'is_printing_no_acc', False):
                print(">>> [寬宏售票-登入] ⚠️ 未設定寬宏帳號密碼，請手動登入！")
                self.is_printing_no_acc = True
            return

        js_fill_credentials = f"""
        (function() {{
            try {{
                let accInput = document.querySelector('#ACCOUNT');
                let pwdInput = document.querySelector('#PASSWORD');
                if (!accInput || !pwdInput) return "WAITING_DOM";

                if (accInput.value === '') {{
                    accInput.value = '{account}';
                    pwdInput.value = '{password}';
                    accInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return "JUST_FILLED";
                }}
                return "ALREADY_FILLED";
            }} catch(e) {{
                return "ERROR";
            }}
        }})();
        """

        try:
            status = await self._diag_evaluate(js_fill_credentials)
            if status in ["JUST_FILLED", "ALREADY_FILLED"]:
                if status == "JUST_FILLED":
                    print(">>> [寬宏售票-登入] 帳號密碼自動填寫完成！準備破解圖形驗證碼...")

                ocr_success = await self.process_login_captcha()
                if ocr_success:
                    print(">>> [寬宏售票-登入] 驗證碼填入完畢，等待 0.5 秒確保網頁消化...")
                    await asyncio.sleep(0.5)

                    js_click_login = """
                    (function() {
                        let loginBtn = document.querySelector('button[onclick*="doLogin1"]');
                        if (loginBtn && !loginBtn.disabled) {
                            loginBtn.click();
                            return true;
                        }
                        return false;
                    })();
                    """
                    btn_clicked = await self._diag_evaluate(js_click_login)
                    if btn_clicked:
                        print(">>> [寬宏售票-登入] 👉 已自動點擊「送出」按鈕！")
                        self.is_login_done = True
                        self.is_printing_login = False
                    else:
                        print(">>> [寬宏售票-登入] ⚠️ 找不到送出按鈕！")
        except Exception as e:
            print(f">>> [寬宏售票-登入] 過程發生錯誤: {e}")

    async def process_login_captcha(self):
        """專用：登入頁圖形驗證碼辨識與自動填入"""
        print(">>> [OCR] 正在處理登入驗證碼...")
        js_get_image = """
        (function() {
            var img = document.querySelector('#chk_pic');
            if (!img) return null;
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """

        try:
            for attempt in range(3):
                base64_data = await self._diag_evaluate(js_get_image)
                if not base64_data:
                    print(">>> [OCR] 找不到驗證碼圖片 (#chk_pic)")
                    return False

                img_bytes = base64.b64decode(base64_data)
                if self.ocr:
                    ocr_answer = self.ocr.classification(img_bytes)
                    ocr_answer = ocr_answer.strip() if ocr_answer else ""
                else:
                    print(">>> [OCR] ddddocr 尚未初始化，無法辨識！")
                    return False

                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                if len(ocr_answer) == 4:
                    js_fill_input = f"""
                    (function() {{
                        var input = document.querySelector('#CHK');
                        if (input) {{
                            input.value = '{ocr_answer}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }})();
                    """
                    is_filled = await self._diag_evaluate(js_fill_input)
                    if is_filled:
                        print(f">>> [OCR] ✅ 已自動填入登入驗證碼: {ocr_answer}")
                        return True
                    else:
                        print(">>> [OCR] ⚠️ 找不到驗證碼輸入框！")
                        return False
                else:
                    print(">>> [OCR] ⚠️ 辨識長度不對，刷新圖片重試...")
                    await self._diag_evaluate("let img = document.querySelector('#chk_pic'); if(img) img.click();")
                    await asyncio.sleep(0.5)

            return False
        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False

    async def fast_api_lock_from_area_page(self):
        """【第一階段】UTK0204 快速找區：極致效能微調版 (已恢復等待秒數提示)"""
        await self.reload_settings(silent=True)
        import json
        import asyncio

        # 讀取 debug 模式設定 (若無設定預設為 False)
        is_debug = getattr(self, "debug_mode", False)

        # ==========================================
        # 輔助函數：局部更新，極致效能 DOM 簽章比對
        # ==========================================
        async def do_ajax_refresh(wait_sec):
            # 🔥 已恢復：每次都會正常印出等待秒數
            print(f">>> [區域頁面] ⏳ 等待 {wait_sec} 秒後執行「更新票數」...")
            await asyncio.sleep(wait_sec)

            js_refresh = """
            (async function() {
                try {
                    const path = location.pathname.toUpperCase();
                    if (!path.includes("UTK0204_.ASPX") && !path.includes("UTK0201_000.ASPX")) {
                        return JSON.stringify({ status: "WRONG_PAGE", pathname: path });
                    }

                    // 1. 共用的 Row Selector 函式 (包含 fallback)
                    function getAreaRows() {
                        let rows = Array.from(document.querySelectorAll('tr.status_tr'));
                        if (!rows.length) {
                            rows = Array.from(document.querySelectorAll('table tbody tr, .table tr')).filter(r => !r.querySelector('th'));
                        }
                        return rows;
                    }

                    // 2. 嚴謹且輕量的 DOM Signature (使用 textContent 避免 Layout 重算)
                    function buildSignature(rows) {
                        return rows.map(r => {
                            return [
                                r.id || '',
                                r.className || '',
                                r.getAttribute('rel') || '',
                                (r.textContent || '').replace(/\\s+/g, ' ').trim()
                            ].join('|');
                        }).join('||');
                    }

                    const rowsBefore = getAreaRows();
                    const before = buildSignature(rowsBefore);

                    // 3. 實體點擊 (拔除耗時的 Hook)
                    const btn = document.querySelector('.btn-update');
                    if (btn) {
                        btn.click();
                    } else if (typeof window.refreshArea === 'function') {
                        window.refreshArea();
                    } else {
                        return JSON.stringify({ status: "NO_BUTTON", pathname: path });
                    }

                    // 4. 極速等待 DOM 更新 (縮減至 0.2 秒: 4次 * 50ms)
                    for (let i = 0; i < 4; i++) {
                        await new Promise(r => setTimeout(r, 50));
                        const rowsNow = getAreaRows();
                        const after = buildSignature(rowsNow);
                        
                        if (after !== before) {
                            return JSON.stringify({
                                status: "UPDATED",
                                pathname: path,
                                beforeRows: rowsBefore.length,
                                afterRows: rowsNow.length
                            });
                        }
                    }

                    // 0.2 秒後若無變化則視為 NO_DOM_CHANGE 放行
                    return JSON.stringify({
                        status: "NO_DOM_CHANGE",
                        pathname: path,
                        beforeRows: rowsBefore.length,
                        afterRows: getAreaRows().length
                    });
                    
                } catch(e) {
                    return JSON.stringify({ status: "ERROR", msg: e.toString() });
                }
            })();
            """

            try:
                raw = await self._diag_evaluate(js_refresh, await_promise=True)
                try:
                    info = json.loads(raw)
                except Exception:
                    info = {"status": str(raw)}

                status = info.get("status")

                if is_debug:
                    print(
                        f">>> [REFRESH DEBUG] STATUS={status} | PAGE={info.get('pathname')} | ROWS={info.get('beforeRows')}->{info.get('afterRows')}")

                if status in ("UPDATED", "NO_DOM_CHANGE", "WRONG_PAGE"):
                    return

                print(f">>> [區域頁面] ⚠️ 更新異常 ({status})，改用整頁更新...")
                await self.fast_reload(0.2)

            except Exception as e:
                msg = str(e)
                if "navigated" in msg.lower() or "-32000" in msg:
                    return
                print(f">>> [區域頁面] ⚠️ 更新例外: {msg}")

        # ==========================================
        # 1. 系統防護與參數準備
        # ==========================================
        error_msg = await self.check_and_close_jquery_dialog()
        if error_msg:
            wait_time = self.get_actual_wait_time()
            print(
                f">>> [區域頁面] 💥 系統彈窗攔截: 【{error_msg}】 (已自動關閉，{wait_time} 秒後整頁重整...)")
            await self.fast_reload(wait_time)
            return False

        area_conf = self.config.get("area_auto_select", {})
        raw_keyword = area_conf.get("area_keyword", "").strip()
        raw_exclude = self.config.get(
            "keyword_exclude", area_conf.get("area_keyword_exclude", ""))
        mode = area_conf.get("mode", "from top to bottom")

        # ==========================================
        # 2. 搜尋並取得所有符合條件的目標區域
        # ==========================================
        js_find_area = f"""
        (function() {{
            try {{
                let rows = Array.from(document.querySelectorAll('tr.status_tr'));
                if (rows.length === 0) {{
                    rows = Array.from(document.querySelectorAll('table tbody tr, .table tr')).filter(r => !r.querySelector('th'));
                }}
                if (rows.length === 0) return JSON.stringify({{ status: "WAITING_DOM" }});
                
                let keywords = {json.dumps(self.parse_keywords(raw_keyword), ensure_ascii=False)};
                let excludes = {json.dumps(self.parse_keywords(str(raw_exclude)), ensure_ascii=False)};
                let candidates = [];
                
                for (let i = 0; i < rows.length; i++) {{
                    let row = rows[i];
                    let rowContent = (row.innerText || "").replace(/,/g, '').toUpperCase();
                    let rowClass = row.className || "";
                    
                    if (rowClass.includes('Soldout') || rowContent.includes('已售完') || rowContent.includes('額滿')) continue;
                    let isHandicap = rowContent.includes('輪椅') || rowContent.includes('身障') || rowContent.includes('陪同');
                    let isExcluded = false;
                    
                    if (excludes.length > 0 && excludes[0] !== "") {{
                        for (let exc of excludes) {{
                            if (exc && rowContent.includes(exc.toUpperCase())) {{ isExcluded = true; break; }}
                        }}
                    }}
                    if (isExcluded) continue;
                    
                    let isMatch = false;
                    if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                        if (!isHandicap) isMatch = true;
                    }} else {{
                        for (let k of keywords) {{
                            let words = k.trim().split(/\\s+/);
                            let groupMatch = words.every(w => rowContent.includes(w.toUpperCase()));
                            if (groupMatch) {{ isMatch = true; break; }}
                        }}
                    }}
                    
                    if (isMatch) {{
                        let areaId = row.getAttribute('id') || "";
                        let relVal = row.getAttribute('rel') || "";
                        let allMatches = [...relVal.matchAll(/a(\\d+)/gi)];
                        let extractedGroupIds = allMatches.length > 0 ? allMatches.map(m => m[1]) : ["25"];
                        
                        candidates.push({{
                            index: i,
                            areaId: areaId,
                            groupIds: extractedGroupIds,
                            text: rowContent.split('\\n')[0]
                        }});
                    }}
                }}
                
                if (candidates.length === 0) return JSON.stringify({{ status: "RELOAD" }});
                
                if ('{mode}' === 'from bottom to top') candidates.reverse();
                else if ('{mode}' === 'random') candidates.sort(() => Math.random() - 0.5);
                
                return JSON.stringify({{ status: "SUCCESS", candidates: candidates, total: candidates.length }});
            }} catch(e) {{
                return JSON.stringify({{ status: "ERROR", msg: e.toString() }});
            }}
        }})();
        """

        try:
            raw_res = await asyncio.wait_for(self._diag_evaluate(js_find_area), timeout=3.0)
            find_res = json.loads(raw_res) if isinstance(
                raw_res, str) else raw_res
        except Exception:
            return False

        if not find_res or find_res.get("status") == "WAITING_DOM":
            await asyncio.sleep(0.1)
            return False

        if find_res.get("status") == "ERROR":
            print(f">>> [區域頁面] ⚠️ DOM 解析發生錯誤: {find_res.get('msg')}，強制整頁重整...")
            await self.fast_reload(0.5)
            return False

        if find_res.get("status") == "RELOAD":
            wait_time = self.get_actual_wait_time()
            # 🔥 已恢復：總是印出這個狀態
            print(f">>> [區域頁面] ⏳ 關鍵字【{raw_keyword}】目前暫無空位。")
            await do_ajax_refresh(wait_time)
            return False

        candidates = find_res.get("candidates", [])
        if not candidates:
            return False

        # ==========================================
        # 3. 探測所有 Candidate 與其下的 GROUP_IDs (無快取 GET)
        # ==========================================
        target_tickets = self.ticket_number
        js_debug_flag = "true" if is_debug else "false"

        js_probe_all_candidates = f"""
        (async function() {{
            const fetchTimeout = (url, options = {{}}, timeout = 5000) => {{
                return Promise.race([
                    fetch(url, options),
                    new Promise((_, reject) => setTimeout(() => reject(new Error('TIMEOUT')), timeout))
                ]);
            }};
            
            try {{
                let urlParams = new URLSearchParams(window.location.search);
                let perfId = urlParams.get('PERFORMANCE_ID') || document.querySelector('#PERFORMANCE_ID')?.value || '';
                let candidates = {json.dumps(candidates)};
                let targetCount = {target_tickets};
                let isDebug = {js_debug_flag};
                
                for (let candidate of candidates) {{
                    let areaId = candidate.areaId;
                    let groupIds = candidate.groupIds;
                    let areaText = candidate.text;
                    
                    // 🔥 單張票且單一群組時的 Fast Path：免背景探測直達
                    if (targetCount === 1 && candidates.length === 1 && groupIds.length === 1) {{
                        let directUrl = `/application/UTK02/UTK0205_.aspx?PERFORMANCE_ID=${{perfId}}&GROUP_ID=${{groupIds[0]}}&PERFORMANCE_PRICE_AREA_ID=${{areaId}}`;
                        setTimeout(() => {{ window.location.href = directUrl; }}, 0);
                        return JSON.stringify({{ 
                            status: "NAVIGATING_TO_UTK0205", 
                            msg: `單張單一票區，直接跳轉: ${{areaText}}` 
                        }});
                    }}
                    
                    // 多群組/多張票：逐一無快取探測
                    for (let currentGroupId of groupIds) {{
                        let targetUrl = `/application/UTK02/UTK0205_.aspx?PERFORMANCE_ID=${{perfId}}&GROUP_ID=${{currentGroupId}}&PERFORMANCE_PRICE_AREA_ID=${{areaId}}`;
                        try {{
                            let fetchOptions = {{ cache: 'no-store', credentials: 'same-origin' }};
                            let seatRes = await fetchTimeout(targetUrl, fetchOptions, 3000);
                            let httpStatus = seatRes.status;
                            let seatHtml = await seatRes.text();
                            
                            let seatMatch = seatHtml.match(/seatStr\\s*=\\s*["']([^"']+)["']/);
                            let selectedCount = 0;
                            let hasSeatStr = !!seatMatch;
                            
                            if (seatMatch) {{
                                let sAry = seatMatch[1].split('\\t');
                                for (let s of sAry) {{
                                    let parts = s.split(':');
                                    if (parts.length < 3) continue;
                                    if (parts[1] === '0') {{
                                        let cellList = parts[2].split('.');
                                        for (let cell of cellList) {{
                                            let cInfo = cell.split(',');
                                            let seatName = cInfo[3] || "";
                                            if (seatName.includes('身障') || seatName.includes('輪椅') || seatName.includes('陪同')) continue;
                                            selectedCount++;
                                            if (selectedCount >= targetCount) break;
                                        }}
                                    }}
                                    if (selectedCount >= targetCount) break;
                                }}
                            }}
                            
                            if (isDebug) {{
                                console.log(`>>> [PROBE] AREA=${{areaId}} | GROUP=${{currentGroupId}} | HTTP=${{httpStatus}} | SEAT_STR=${{hasSeatStr}} | AVAILABLE=${{selectedCount}}`);
                            }}
                            
                            if (selectedCount >= targetCount) {{
                                setTimeout(() => {{ window.location.href = targetUrl; }}, 0);
                                return JSON.stringify({{ 
                                    status: "NAVIGATING_TO_UTK0205",
                                    msg: `🎯 找到足夠座位，發動跳轉至: ${{areaText}} (GROUP: ${{currentGroupId}})`
                                }});
                            }}
                        }} catch(sub_e) {{
                            if (isDebug) console.log(`>>> [PROBE ERROR] AREA=${{areaId}} | GROUP=${{currentGroupId}} | MSG=${{sub_e.toString()}}`);
                            continue;
                        }}
                    }}
                }}
                
                return JSON.stringify({{ status: "ALL_PROBED_EMPTY" }});
                
            }} catch(e) {{
                return JSON.stringify({{ status: "JS_EXCEPTION", msg: e.toString() }});
            }}
        }})();
        """

        try:
            raw_prep = await asyncio.wait_for(
                self._diag_evaluate(js_probe_all_candidates,
                                    await_promise=True, return_by_value=True),
                timeout=15.0
            )
            prep_data = json.loads(raw_prep) if isinstance(
                raw_prep, str) else raw_prep
        except Exception:
            return False

        if prep_data.get("status") == "ALL_PROBED_EMPTY":
            wait_time = self.get_actual_wait_time()
            # 🔥 已恢復：總是印出這個狀態
            print(f">>> [區域頁面] ❌ 所有符合關鍵字的票區皆被搶走或不足 {target_tickets} 張。")
            await do_ajax_refresh(wait_time)
            return False

        if prep_data.get("status") == "NAVIGATING_TO_UTK0205":
            success_msg = prep_data.get("msg", "發動真實跳轉至座位頁...")
            print(f">>> [區域頁面] ⚡ {success_msg}")
            return False

        return False

    async def fast_api_lock_fallback(self):
        """【安全直連版】利用原生 opera1() 與 addShoppingCart() 完美避開 500 錯誤與 0 張數 Bug"""
        await self.reload_settings(silent=True)

        # 1. 檢查頁面是否已被彈窗攔截
        dialog_res = await self.check_and_close_jquery_dialog()
        if dialog_res:
            d_type = dialog_res.get("type") if isinstance(
                dialog_res, dict) else ""
            d_msg = dialog_res.get("msg", "") if isinstance(
                dialog_res, dict) else str(dialog_res)

            if d_type == "WARNING" or "不同排" in d_msg:
                print(f">>> [座位/票數頁] 💡 提示：【{d_msg}】 (自動確認中...)")
                await asyncio.sleep(0.15)
                await self.click_next()
                return False
            else:
                wait_time = self.get_actual_wait_time()
                print(
                    f">>> [座位/票數頁] 💥 系統彈窗攔截: 【{d_msg}】 ({wait_time} 秒後重整刷新...)")
                await self.fast_reload(wait_time)
                return False

        # 2. 背景提取圖形驗證碼
        captcha_code = await self.get_captcha_text_from_dom()
        if not captcha_code:
            return False

        target_count = self.ticket_number

        # ==========================================
        # 🔍 API DEBUG: 追蹤 Profile 與 Session 是否共用 (票數頁 DOM 送出)
        # ==========================================
        try:
            import os
            import hashlib
            current_pid = os.getpid()
            account_id = self.config.get("advanced", {}).get(
                "kham_account", "Unknown")

            exe_path = getattr(self.driver.config, "browser_executable_path",
                               "Unknown") if self.driver and hasattr(self.driver, "config") else "Unknown"
            user_data_dir = getattr(self.driver.config, "user_data_dir", "Unknown") if self.driver and hasattr(
                self.driver, "config") else "Unknown"

            raw_cookie = await self._diag_evaluate("document.cookie") or ""
            session_fp = hashlib.sha256(raw_cookie.encode(
                "utf-8")).hexdigest()[:12] if raw_cookie else "None"

            print("\n========== API DEBUG (FALLBACK DOM) ==========")
            print(f"PID       : {current_pid}")
            print(f"EXE_PATH  : {exe_path}")
            print(f"PROFILE   : {user_data_dir}")
            print(f"ACCOUNT   : {account_id}")
            print(f"SESSION_FP: {session_fp}")
            print(f"TARGET_QTY: {target_count}")
            print("==============================================\n")
        except Exception as e:
            print(f">>> [DEBUG Error] {e}")
        # ==========================================

        # 3. 執行 JS，利用原生函式精準加票與送出
        js_submit = f"""
        (function() {{
            try {{
                // A. 填入驗證碼
                let chkInput = document.querySelector('#CHK');
                if (chkInput) {{
                    chkInput.value = '{captcha_code}';
                    chkInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}

                // B. 模式 1：座位圖劃位模式 (UTK0205_)
                if (typeof seats !== 'undefined' && Object.keys(seats).length > 0) {{
                    let checkNumBtn = document.querySelector('.checkNum') || document.querySelector('button.checkNum') || document.querySelector('button.green');
                    if (!checkNumBtn) return JSON.stringify({{ status: "WAITING" }});
                    let typeId = checkNumBtn.getAttribute('id') || checkNumBtn.getAttribute('name');
                    let typeName = checkNumBtn.getAttribute('val') || checkNumBtn.innerText;
                    
                    let count = 0;
                    for (let k in seats) {{
                        let s = seats[k];
                        if (s.S == 0 && s.A === "") {{
                            if (s.I && (s.I.includes('身障') || s.I.includes('輪椅') || s.I.includes('陪同'))) continue;
                            s.A = "S";
                            s.Y = typeId;
                            s.Z = typeName;
                            count++;
                            if (count >= {target_count}) break;
                        }}
                    }}
                    if (count < {target_count}) return JSON.stringify({{ status: "NOT_ENOUGH_SEATS" }});
                    
                    if (typeof addShoppingCart === 'function') {{
                        addShoppingCart();
                        return JSON.stringify({{ status: "SUBMITTED" }});
                    }}
                }}

                // C. 模式 2：一般張數輸入模式 (UTK0202_ / UTK0201_001)
                let rows = Array.from(document.querySelectorAll('table tbody tr, .table tr'));
                let targetInput = null;

                for (let row of rows) {{
                    let rowText = (row.innerText || "").toUpperCase();
                    if (rowText.includes('身障') || rowText.includes('輪椅') || rowText.includes('陪同') || rowText.includes('愛心')) continue;

                    let input = row.querySelector('input.numbox, input[type="number"], select.numbox');
                    if (input && !input.disabled) {{
                        targetInput = input;
                        break;
                    }}
                }}

                if (!targetInput) return JSON.stringify({{ status: "NOT_ENOUGH_SEATS" }});

                // 🔥 核心：直接使用原生 opera1 函式模擬按 + 號，100% 觸發底層正確計數！
                let key = targetInput.getAttribute('key');
                if (typeof opera1 === 'function' && key) {{
                    // 先確保數值歸零，然後連點目標次數的 + 號
                    targetInput.value = '0';
                    for (let i = 0; i < {target_count}; i++) {{
                        opera1(key, true);
                    }}
                }} else {{
                    // 萬一沒有 opera1 的保底做法
                    targetInput.value = '{target_count}';
                    if (window.jQuery) window.jQuery(targetInput).trigger('change');
                    if (typeof checkNum === 'function') checkNum(targetInput);
                }}

                // D. 呼叫網站原生送出，並把擾人的 alert 靜音攔截
                if (typeof addShoppingCart === 'function') {{
                    window.khamHookedAlert = "";
                    window.alert1 = function(msg, cb) {{ window.khamHookedAlert = msg; if(cb) cb(); }};
                    window.alert = function(msg) {{ window.khamHookedAlert = msg; }};
                    
                    addShoppingCart();
                    return JSON.stringify({{ status: "SUBMITTED" }});
                }}

                return JSON.stringify({{ status: "NOT_ENOUGH_SEATS" }});
                
            }} catch(e) {{
                return JSON.stringify({{ status: "ERROR", msg: e.toString() }});
            }}
        }})();
        """

        try:
            raw_res = await self._diag_evaluate(js_submit)
            res_data = json.loads(raw_res) if isinstance(
                raw_res, str) else raw_res
        except Exception:
            return False

        status = res_data.get("status") if isinstance(
            res_data, dict) else str(res_data)

        if status == "NOT_ENOUGH_SEATS":
            wait_time = self.get_actual_wait_time()
            print(
                f">>> [座位/票數頁] ❌ 剩餘空位不足 {target_count} 張！{wait_time} 秒後自動重整...")
            await self.fast_reload(wait_time)
            return False

        if status == "SUBMITTED":
            print(f">>> [座位/票數頁] ⚡ 已秒速加票並送出，等待伺服器回應...")
            await asyncio.sleep(0.4)  # 給 AJAX 請求 0.4 秒的飛行時間

            # 檢查送出後有沒有跳出錯誤彈窗 (無足夠空位、驗證碼錯誤等)
            post_err = await self.check_and_close_jquery_dialog()
            if post_err:
                d_type = post_err.get("type") if isinstance(
                    post_err, dict) else ""
                d_msg = post_err.get("msg", "") if isinstance(
                    post_err, dict) else str(post_err)

                if d_type == "SUCCESS" or "完成" in d_msg:
                    return True
                else:
                    wait_time = self.get_actual_wait_time()
                    print(
                        f">>> [座位/票數頁] 💥 遭到系統阻擋或搶輸: 【{d_msg}】，{wait_time} 秒後重試...")
                    await self.fast_reload(wait_time)
                    return False
            return True

        return False

    async def select_date(self):
        await self.reload_settings(silent=True)

        date_conf = self.config.get("date_auto_select", {})

        if not date_conf.get("enable", True):
            return

        # ============================================================
        # 1. 日期關鍵字
        # ============================================================
        raw_keyword = date_conf.get("date_keyword", "").strip()
        keyword_list = self.parse_keywords(raw_keyword)

        # ============================================================
        # 2. 排除關鍵字
        # ============================================================
        raw_exclude = self.config.get(
            "keyword_exclude",
            date_conf.get("date_keyword_exclude", "")
        )
        exclude_list = self.parse_keywords(str(raw_exclude))

        js_keywords = json.dumps(keyword_list, ensure_ascii=False)
        js_excludes = json.dumps(exclude_list, ensure_ascii=False)
        js_mode = f"'{date_conf.get('mode', 'from top to bottom')}'"

        js_script = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                const excludes = {js_excludes};
                const mode = {js_mode};

                let rows = Array.from(
                    document.querySelectorAll("table tbody tr")
                );

                if (rows.length === 0) {{
                    return "WAITING_DOM";
                }}

                if (
                    rows.length === 1 &&
                    rows[0].innerText.includes('載入')
                ) {{
                    return "WAITING_DOM";
                }}

                let candidates = [];

                for (let row of rows) {{
                    // ------------------------------------------------
                    // 基本過濾
                    // ------------------------------------------------
                    if (row.querySelector('th')) continue;

                    let btn = row.querySelector("button");

                    if (!btn || btn.disabled) continue;

                    let btnText = btn.innerText || "";

                    if (
                        btnText.includes('售完') ||
                        btnText.includes('額滿')
                    ) {{
                        continue;
                    }}

                    if (
                        !btnText.includes('訂購') &&
                        !btnText.includes('購票')
                    ) {{
                        continue;
                    }}

                    // ------------------------------------------------
                    // 取得整列文字
                    // ------------------------------------------------
                    let rowText = (row.innerText || "")
                        .replace(/,/g, '')
                        .toUpperCase();

                    // ------------------------------------------------
                    // 日期格式補強
                    // ------------------------------------------------
                    let dateMatch = rowText.match(
                        /(\\d{{4}})\\s*\\/\\s*(\\d{{2}})\\s*\\/\\s*(\\d{{2}})/
                    );

                    if (dateMatch) {{
                        let y = dateMatch[1];
                        let m = parseInt(dateMatch[2], 10);
                        let d = parseInt(dateMatch[3], 10);

                        rowText +=
                            ` ${{y}}/${{dateMatch[2]}}/${{dateMatch[3]}}` +
                            ` ${{m}}/${{d}}` +
                            ` ${{m}}月${{d}}日`;
                    }}

                    // ------------------------------------------------
                    // ⭐ 第一關：排除關鍵字
                    // ------------------------------------------------
                    let isExcluded = false;

                    if (
                        excludes.length > 0 &&
                        excludes[0] !== ""
                    ) {{
                        for (let exc of excludes) {{
                            if (!exc) continue;
                            if (
                                rowText.includes(
                                    exc.toUpperCase()
                                )
                            ) {{
                                isExcluded = true;
                                break;
                            }}
                        }}
                    }}

                    if (isExcluded) {{
                        continue;
                    }}

                    // ------------------------------------------------
                    // 第二關：日期關鍵字
                    // ------------------------------------------------
                    let isMatch = false;

                    if (
                        keywords.length === 0 ||
                        (
                            keywords.length === 1 &&
                            keywords[0] === ""
                        )
                    ) {{
                        isMatch = true;
                    }} else {{
                        for (let k of keywords) {{
                            let target_kws = k
                                .trim()
                                .split(/\\s+/)
                                .filter(w => w.length > 0);

                            let currentGroupMatch =
                                target_kws.every(
                                    w => rowText.includes(
                                        w.toUpperCase()
                                    )
                                );

                            if (currentGroupMatch) {{
                                isMatch = true;
                                break;
                            }}
                        }}
                    }}

                    // ------------------------------------------------
                    // 最終候選
                    // ------------------------------------------------
                    if (isMatch) {{
                        candidates.push(btn);
                    }}
                }}

                if (candidates.length === 0) {{
                    return "RELOAD";
                }}

                if (mode === "from bottom to top") {{
                    candidates.reverse();
                }} else if (mode === "random") {{
                    for (
                        let i = candidates.length - 1;
                        i > 0;
                        i--
                    ) {{
                        const j = Math.floor(
                            Math.random() * (i + 1)
                        );
                        [
                            candidates[i],
                            candidates[j]
                        ] = [
                            candidates[j],
                            candidates[i]
                        ];
                    }}
                }}

                candidates[0].click();
                return "SUCCESS";

            }} catch (e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await self._diag_evaluate(js_script)
        except Exception as e:
            print(f">>> [API 模式-日期] ⚠️ 日期判斷發生例外: {e}")
            return False

        if result == "SUCCESS":
            print(f">>> [API 模式-日期] 🎉 成功匹配目標日期並點擊！")

            # ==========================================
            # 🔥 新增：偵測並處理「優先購買 / 會員驗證碼」彈窗
            # ==========================================
            await asyncio.sleep(0.2)  # 給予彈窗顯示的短暫緩衝時間

            # 安全取得 user_guess_string
            raw_guess_code = self.config.get("advanced", {}).get(
                "user_guess_string", self.config.get("user_guess_string", ""))

            # 💡 幫你加上這行：自動脫掉字串頭尾的雙引號或單引號
            guess_code = str(raw_guess_code).strip('\'"')

            js_vip_login = f"""
            (function() {{
                try {{
                    let input1 = document.querySelector('#ID1');
                    let btn = document.querySelector('button[onclick*="DoVIPLogin"]');
                    
                    // 檢查輸入框是否存在，且不是隱藏狀態
                    if (input1 && input1.offsetParent !== null) {{
                        input1.value = '{guess_code}';
                        input1.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input1.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        if (btn) {{
                            btn.click();
                            return "VIP_SUBMITTED";
                        }}
                        return "BTN_NOT_FOUND";
                    }}
                    return "NO_POPOUT";
                }} catch(e) {{
                    return "ERROR|" + e.toString();
                }}
            }})();
            """
            vip_res = await self._diag_evaluate(js_vip_login)
            if vip_res == "VIP_SUBMITTED":
                print(
                    f">>> [API 模式-日期] 🔐 偵測到優先購買驗證，已自動填入代碼並送出: 【{guess_code}】")
                await asyncio.sleep(0.5)  # 給予伺服器驗證與跳轉的飛行時間
            elif vip_res == "BTN_NOT_FOUND":
                print(">>> [API 模式-日期] ⚠️ 偵測到驗證輸入框，但找不到送出按鈕！")
            # ==========================================

            self.is_date_selected = True

        elif result == "RELOAD":
            wait_time = self.get_actual_wait_time()
            print(f">>> [API 模式-日期] ⏳ 找不到符合日期條件或全部被排除，{wait_time} 秒後自動重整...")
            await self.fast_reload(wait_time)

        elif result == "WAITING_DOM":
            await asyncio.sleep(0.1)

        elif isinstance(result, str) and result.startswith("ERROR|"):
            print(f">>> [API 模式-日期] ⚠️ {result}")

    async def get_captcha_text_from_dom(self):

        js_get = """
        (function() {
            var img = document.querySelector('#chk_pic');
            if (!img || !img.complete || img.naturalWidth === 0) return null;
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """

        attempt = 0
        # 拔除 5 次限制，改為無限迴圈，直到辨識正確為止
        while True:
            attempt += 1
            base64_data = await self._diag_evaluate(js_get)

            if base64_data and self.ocr:
                img_bytes = base64.b64decode(base64_data)
                raw_ans = self.ocr.classification(img_bytes)

                # 清洗雜訊
                ans = re.sub(r'[^A-Z0-9]', '', raw_ans.strip().upper())

                print(f">>> [OCR] 第 {attempt} 次辨識結果: '{ans}'")

                # 正確：剛好 4 碼，直接回傳放行送出
                if len(ans) == 4:
                    return ans

                # 錯誤：不是 4 碼，直接點擊圖片刷新
                print(f">>> [OCR] ⚠️ 長度異常 (原始: '{raw_ans}')，直接點擊圖片刷新重新判斷...")
                await self._diag_evaluate("let img = document.querySelector('#chk_pic'); if(img) img.click();")
                await asyncio.sleep(0.5)  # 等待新圖片載入

            else:
                print(f">>> [OCR] 第 {attempt} 次取不到圖片，等待 0.2 秒...")
                await asyncio.sleep(0.02)

    async def check_and_close_jquery_dialog(self):
        js_check = """
        (function() {
            try {
                let btn = document.querySelector('div.ui-dialog-buttonpane button');
                if (btn && btn.offsetParent !== null) {
                    let dialogBox = btn.closest('.ui-dialog');
                    let msg = dialogBox?.querySelector('.ui-dialog-content')?.innerText.trim() || "";
                    btn.click();
                    return msg;
                }
                return false;
            } catch (e) { return false; }
        })();
        """
        return await self._diag_evaluate(js_check)

    async def fast_reload(self, wait_sec=0.2):
        self.diag_reload_count += 1
        reload_no = self.diag_reload_count
        self._diag_log("RELOAD_START",
                       f"#{reload_no} url={self.diag_last_url!r} wait={wait_sec}s")
        js_reload = "(function() { try { window.stop(); window.location.replace(window.location.href); } catch(e) {} })();"
        t0 = time.monotonic()
        try:
            await self._diag_evaluate(js_reload)
            elapsed = time.monotonic() - t0
            self._diag_log("RELOAD_EVAL_OK",
                           f"#{reload_no} elapsed={elapsed:.3f}s")
        except Exception as e:
            self._diag_log("RELOAD_ERROR",
                           f"#{reload_no} exc={type(e).__name__}: {e}")
            raise
        await asyncio.sleep(wait_sec)

    async def block_loading_overlay(self):
        """【嚴謹版】等待 head 生成後注入，絕不吞噬錯誤，配合診斷系統"""
        js_inject_css = """
        (async function() {
            // 1. 給予極短暫的輪詢，確保 document.head 真的誕生了
            let count = 0;
            while (!document.head && count < 50) {
                await new Promise(r => setTimeout(r, 10));
                count++;
            }
            
            // 如果真的等不到，回傳明確狀態讓 Python 知道
            if (!document.head) return "HEAD_NOT_FOUND";
            
            // 2. 如果已經注入過，就直接離開
            if (document.getElementById('anti-kham-loading')) {
                return "ALREADY_INJECTED";
            }
            
            // 3. 注入簡潔有效的 CSS
            let style = document.createElement('style');
            style.id = 'anti-kham-loading';
            style.innerHTML = `
                #__SCREEN, #__LOADINGBAR, .blockUI, .blockOverlay, #loading, #WaitBox {
                    display: none !important; 
                    opacity: 0 !important; 
                    pointer-events: none !important;
                }
            `;
            document.head.appendChild(style);
            
            return "INJECTED_SUCCESS";
        })();
        """

        try:
            # 使用 await_promise=True 確保 JS 內的 async 迴圈正確執行並回傳狀態
            result = await self._diag_evaluate(js_inject_css, await_promise=True)

            # 針對異常狀態寫入你的診斷 Log
            if result == "HEAD_NOT_FOUND":
                self._diag_log("BLOCK_OVERLAY_WARN",
                               "document.head 尚未生成，無法注入 CSS")

        except Exception as e:
            # 🔥 拔除 pass，將執行失敗的真正原因寫入你的診斷系統中
            self._diag_log("BLOCK_OVERLAY_ERROR",
                           f"exc={type(e).__name__}: {e}")

    def get_actual_wait_time(self):
        """計算重整等待秒數 (支援隨機浮動)"""
        advanced_conf = self.config.get("advanced", {})
        base_wait = getattr(self, 'refresh_sec', 0.2)
        if base_wait <= 0:
            base_wait = 0.2
        if advanced_conf.get("auto_reload_random_mode", False):
            import random
            try:
                rand_range = float(advanced_conf.get(
                    "auto_reload_random_range", 1.0))
            except:
                rand_range = 1.0
            return round(base_wait + random.uniform(0, rand_range), 2)
        return base_wait

    async def reload_settings(self, silent=False):
        settings_path = getattr(self, 'settings_path', 'settings.json')
        try:
            if not os.path.exists(settings_path):
                return
            mtime = os.path.getmtime(settings_path)
            if getattr(self, 'last_mtime', 0) == mtime:
                return
            self.last_mtime = mtime
            with open(settings_path, 'r', encoding='utf-8') as f:
                new_cfg = json.load(f)
            self.config.update(new_cfg)
            self.ticket_number = int(new_cfg.get("ticket_number", 1))
            self.refresh_sec = float(new_cfg.get("advanced", {}).get(
                "auto_reload_page_interval", 0.2))
        except:
            pass

    def parse_keywords(self, kw_str):
        kw_str = str(kw_str).strip()
        if not kw_str:
            return [""]
        try:
            if kw_str.startswith("[") and kw_str.endswith("]"):
                return json.loads(kw_str)
            if '"' in kw_str or "'" in kw_str:
                return json.loads("[" + kw_str + "]")
        except:
            pass
        return [x.strip().strip('\'"') for x in kw_str.replace('，', ',').split(',') if x.strip()]

# ==========================================
# [寬宏API模式售票]
# ==========================================


class TicketPlusBot:
    """遠大售票 (TicketPlus) 專用機器人 (完整修復整合版)"""

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.settings_path = config.get("config_filepath", "settings.json")
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""
        try:
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        self.is_login_done = False
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_ticket_assigned = False
        self.is_next_clicked = False
        self.is_telegram_sent = False

    def get_reload_interval(self):
        """[時間計算] 讀取 GUI 設定，計算固定或隨機刷新秒數"""
        advanced = self.config.get("advanced", {})
        base_interval = float(advanced.get("auto_reload_page_interval", 0.5))
        random_mode = bool(advanced.get("auto_reload_random_mode", False))
        random_range_str = str(
            advanced.get("auto_reload_random_range", "0.5")).strip()

        if not random_mode:
            return max(0.05, base_interval)

        try:
            if "," in random_range_str:
                parts = [float(x.strip())
                         for x in random_range_str.split(",") if x.strip()]
                if len(parts) >= 2:
                    min_sec, max_sec = min(
                        parts[0], parts[1]), max(parts[0], parts[1])
                    actual_wait = random.uniform(min_sec, max_sec)
                else:
                    actual_wait = base_interval
            else:
                delta = float(random_range_str)
                actual_wait = base_interval + random.uniform(-delta, delta)
        except Exception:
            actual_wait = base_interval

        return max(0.05, round(actual_wait, 3))

    async def reload_config_if_changed(self):
        """[動態更新] 檢查設定檔是否變更，若有則熱重載"""
        current_time = time.time()
        if current_time - getattr(self, 'last_config_check_time', 0) < 2.0:
            return
        self.last_config_check_time = current_time
        try:
            config_path = getattr(self, 'settings_path', 'settings.json')
            if not os.path.exists(config_path):
                return
            mtime = os.path.getmtime(config_path)
            if not hasattr(self, "last_config_mtime"):
                self.last_config_mtime = mtime
                return
            if mtime > self.last_config_mtime:
                self.last_config_mtime = mtime
                filename = os.path.basename(config_path)
                print(f">>> [系統] 偵測到 {filename} 變更，正在熱重載最新戰術...")
                with open(config_path, "r", encoding="utf-8") as f:
                    new_config = json.load(f)

                if "area_auto_select" in new_config:
                    self.config["area_auto_select"] = new_config["area_auto_select"]
                if "date_auto_select" in new_config:
                    self.config["date_auto_select"] = new_config["date_auto_select"]
                if "advanced" in new_config:
                    self.config["advanced"] = new_config["advanced"]
                if "keyword_exclude" in new_config:
                    self.config["keyword_exclude"] = new_config["keyword_exclude"]
                if "ticket_number" in new_config:
                    self.config["ticket_number"] = new_config["ticket_number"]
                    self.ticket_number = int(
                        new_config.get("ticket_number", 1))
                print(f"    -> [更新] 遠大售票 ({filename}) 設定套用完畢！")
        except Exception:
            pass

    async def run(self):
        """[核心主迴圈] 監聽網址變化、分發任務與狀態控制"""
        print(f">>> [遠大售票] 機器人啟動！(目標張數: {self.ticket_number})")
        print("等待網頁載入中...")
        while True:
            try:
                # 1. 暫停攔截
                if os.path.exists(self.PAUSE_FILE):
                    if not getattr(self, 'is_printing_pause', False):
                        self.is_printing_pause = True
                    await asyncio.sleep(0.5)
                    continue
                else:
                    if getattr(self, 'is_printing_pause', False):
                        self.is_printing_pause = False

                # 2. 獲取當前網址
                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                upper_curr = current_url.upper()

                # 3. 搶票核心頁面檢查熱重載
                if '/ACTIVITY/' in upper_curr or '/ORDER/' in upper_curr:
                    await self.reload_config_if_changed()

                # 4. 偵測頁面切換與解鎖防呆
                if current_url != self.last_url:
                    print(f"偵測到頁面切換: {current_url}")
                    if current_url == 'https://ticketplus.com.tw/':
                        self.is_date_selected = False
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                        self.is_next_clicked = False
                        self.is_telegram_sent = False
                    elif '/ACTIVITY/' in upper_curr and getattr(self, 'is_date_selected', False):
                        print(">>> [系統] 偵測到退回日期選擇頁，已重置日期鎖，準備重新掃描場次！")
                        self.is_date_selected = False
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                        self.is_next_clicked = False
                        self.is_telegram_sent = False
                    elif '/ORDER/' in upper_curr and getattr(self, 'is_area_selected', False):
                        print(">>> [系統] 偵測到退回區域選擇頁，已重置相關鎖定，準備重新刷票！")
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                        self.is_next_clicked = False
                        self.is_telegram_sent = False
                    self.last_url = current_url

                # 5. 全域彈窗擊殺器
                if '/ORDER/' in upper_curr:
                    current_time = time.time()
                    if current_time - getattr(self, 'last_popup_check_time', 0) > 0.2:
                        self.last_popup_check_time = current_time
                        js_kill_popup = """
                        (function() {
                            let popups = document.querySelectorAll('div[role="dialog"], .v-dialog');
                            for (let dialog of popups) {
                                if (dialog.offsetParent !== null) {
                                    let text = dialog.innerText || "";
                                    if (text.includes('失敗') || text.includes('售完') || text.includes('我知道了')) {
                                        let btn = dialog.querySelector('button.primary') ||
                                                  dialog.querySelector('button.primary-1') ||
                                                  dialog.querySelector('button.v-btn') ||
                                                  dialog.querySelector('button');
                                        if (btn) {
                                            btn.click();
                                            return true;
                                        }
                                    }
                                }
                            }
                            return false;
                        })();
                        """
                        killed = await self.tab.evaluate(js_kill_popup)
                        if killed:
                            print(
                                ">>> [系統] 💥 攔截到「購票失敗/售完」彈窗！已點擊關閉，解除所有鎖定重新撿漏...")
                            js_frontend_reset = """
                            (function() {
                                try {
                                    document.querySelectorAll('button').forEach(btn => {
                                        btn.disabled = false;
                                        btn.removeAttribute('disabled');
                                        btn.classList.remove('v-btn--disabled');
                                        btn.style.pointerEvents = 'auto';
                                    });
                                    document.querySelectorAll('.v-overlay, .v-progress-circular').forEach(el => {
                                        el.style.display = 'none';
                                        el.style.visibility = 'hidden';
                                        el.style.opacity = '0';
                                        el.style.pointerEvents = 'none';
                                    });
                                    document.querySelectorAll('input[type="text"]').forEach(input => {
                                        if (input.value !== '') {
                                            input.value = '';
                                            input.dispatchEvent(new Event('input', { bubbles: true }));
                                            input.dispatchEvent(new Event('change', { bubbles: true }));
                                        }
                                    });
                                } catch(e) {}
                            })();
                            """
                            await self.tab.evaluate(js_frontend_reset)
                            self.is_area_selected = False
                            self.is_ticket_assigned = False
                            self.is_next_clicked = False
                            await asyncio.sleep(0.3)

                # 6. 分發任務
                await self.dispatch_action(current_url)
            except Exception:
                pass
            await asyncio.sleep(0.05)

    async def dispatch_action(self, url):
        """遠大售票 任務分發中心"""
        lower_url = url.lower()
        if lower_url == 'https://ticketplus.com.tw' or lower_url == 'https://ticketplus.com.tw/':
            if not getattr(self, 'is_login_done', False):
                await self.auto_login()
        elif '/activity/' in lower_url:
            self.is_area_selected = False
            self.is_ticket_assigned = False
            if not getattr(self, 'is_date_selected', False):
                await self.select_date()
        elif '/order/' in lower_url:
            if not getattr(self, 'is_area_selected', False):
                await self.select_area()
            elif not getattr(self, 'is_ticket_assigned', False):
                await self.assign_ticket_number()
            elif not getattr(self, 'is_next_clicked', False):
                await self.click_next()
        elif '/confirm/' in lower_url or '/confirmseat/' in lower_url:
            self.is_area_selected = True
            self.is_ticket_assigned = True
            await self.process_confirmation()

    async def auto_login(self):
        """[遠大售票] 自動填寫帳密並登入"""
        account = self.config.get("advanced", {}).get("ticketplus_account", "")
        password = self.config.get("advanced", {}).get(
            "ticketplus_password_plaintext", "").strip()
        if not password:
            try:
                password = util.decrypt_me(self.config.get(
                    "advanced", {}).get("ticketplus_password", ""))
            except:
                pass
        if not account or not password:
            print(">>> [遠大售票] 未設定帳號密碼，跳過自動登入！")
            self.is_login_done = True
            return

        js_login_flow = f"""
        (function() {{
            try {{
                if (document.cookie.includes('%22account%22')) {{
                    return "LOGGED_IN";
                }}
                let pwdInput = document.querySelector('input[type="password"]');
                let accInput = document.querySelector('input[placeholder="手機號碼 *"]');
                if (!pwdInput || pwdInput.offsetParent === null) {{
                    let loginIcon = document.querySelector('i.mdi-account');
                    if (loginIcon) {{
                        let btn = loginIcon.closest('button');
                        if (btn) btn.click();
                    }} else {{
                        let rwdBtns = document.querySelectorAll('div.drawerItem');
                        if (rwdBtns.length > 3) rwdBtns[3].click();
                    }}
                    return "WAIT_MODAL";
                }}
                if (accInput && pwdInput) {{
                    if (accInput.value !== '{account}') {{
                        accInput.value = '{account}';
                        accInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                    if (pwdInput.value !== '{password}') {{
                        pwdInput.value = '{password}';
                        pwdInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                    let btns = Array.from(document.querySelectorAll('button'));
                    let submitBtn = btns.find(b => b.innerText.includes('登入') && !b.disabled);
                    if (submitBtn) {{
                        submitBtn.click();
                        return "SUBMITTED";
                    }}
                    return "READY_TO_SUBMIT";
                }}
                return "WORKING";
            }} catch(e) {{
                return "ERROR";
            }}
        }})();
        """
        try:
            result = await self.tab.evaluate(js_login_flow)
            if result == "LOGGED_IN":
                print(">>> [遠大售票] 偵測到已登入狀態！")
                self.is_login_done = True
            elif result == "WAIT_MODAL":
                await asyncio.sleep(0.5)
            elif result == "SUBMITTED":
                print(">>> [遠大售票] 帳密已填入並點擊登入！等待驗證...")
                await asyncio.sleep(1.0)
            elif result == "READY_TO_SUBMIT":
                pwd_element = await self.tab.select('input[type="password"]')
                if pwd_element:
                    await pwd_element.send_keys('\n')
                await asyncio.sleep(1.0)
        except Exception as e:
            print(f">>> [嚴重錯誤] auto_login 發生 Python 例外: {e}")

    async def select_date(self):
        """[遠大售票] 場次/日期選擇 (依隨機設定間隔刷新)"""
        try:
            date_auto_select = self.config.get("date_auto_select", {})
            if not date_auto_select.get("enable", True):
                return
            auto_select_mode = date_auto_select.get(
                "mode", "from top to bottom")
            raw_keyword = date_auto_select.get("date_keyword", "").strip()
            keyword_list = []
            if len(raw_keyword) > 0:
                try:
                    if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                        keyword_list = json.loads(raw_keyword)
                    else:
                        keyword_list = json.loads("[" + raw_keyword + "]")
                except:
                    keyword_list = [raw_keyword]
            else:
                keyword_list = [""]

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_mode = f"'{auto_select_mode}'"

            js_script = f"""
            (function() {{
                try {{
                    let popups = document.querySelectorAll('div[role="dialog"]');
                    popups.forEach(dialog => {{
                        if (dialog.offsetParent !== null) {{
                            let primaryBtn = dialog.querySelector('button.primary') || dialog.querySelector('button.primary-1') || dialog.querySelector('button');
                            if (primaryBtn) primaryBtn.click();
                        }}
                    }});
                    let loader = document.querySelector('.v-progress-circular');
                    if (loader && loader.offsetParent !== null) return "LOADING";

                    const keywords = {js_keywords};
                    const mode = {js_mode};
                    let rows = Array.from(document.querySelectorAll('div#buyTicket div.sesstion-item div.row'));
                    let candidates = [];
                    if (rows.length > 0) {{
                        for (let row of rows) {{
                            let rowText = row.innerText.toUpperCase();
                            let btn = row.querySelector('button');
                            if (!btn || btn.disabled) continue;
                            if (!btn.innerText.includes('立即購')) continue;
                            if (rowText.includes('銷售一空')) continue;

                            let isMatch = false;
                            if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                                isMatch = true;
                            }} else {{
                                for (let k of keywords) {{
                                    let target_kws = k.trim().split(" ").filter(w => w.length > 0);
                                    let currentGroupMatch = true;
                                    for (let w of target_kws) {{
                                        if (!rowText.includes(w.toUpperCase())) {{
                                            currentGroupMatch = false; break;
                                        }}
                                    }}
                                    if (currentGroupMatch) {{ isMatch = true; break; }}
                                }}
                            }}
                            if (isMatch) candidates.push(btn);
                        }}
                    }}
                    if (candidates.length === 0) return "NO_TICKETS";

                    if (mode === "from bottom to top") {{
                        candidates.reverse();
                    }} else if (mode === "random") {{
                        for (let i = candidates.length - 1; i > 0; i--) {{
                            const j = Math.floor(Math.random() * (i + 1));
                            [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
                        }}
                    }}

                    let target = candidates[0];
                    let uniqueId = 'maxbot_target_' + Date.now();
                    target.id = uniqueId;
                    target.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                    return uniqueId;
                }} catch(e) {{
                    return "ERROR";
                }}
            }})();
            """
            result = await self.tab.evaluate(js_script)
            if isinstance(result, str) and result.startswith("maxbot_target_"):
                print(f">>> [遠大售票-日期] 🎯 成功鎖定場次！發動點擊...")
                target_element = await self.tab.select(f'#{result}')
                if target_element:
                    await target_element.click()
                await asyncio.sleep(0.5)
                self.is_date_selected = True
            elif result == "LOADING":
                await asyncio.sleep(0.1)
            elif result == "NO_TICKETS":
                wait_time = self.get_reload_interval()
                print(
                    f">>> [遠大售票-日期] 找不到符合場次或尚未開賣，準備刷新 (等待: {wait_time} 秒)...")
                await self.tab.reload()
                await asyncio.sleep(wait_time)
        except Exception as e:
            print(f">>> [嚴重錯誤] select_date 發生 Python 例外: {e}")

    async def select_area(self):
        """[遠大售票] 區域選擇 (依隨機設定間隔點擊更新票數/重整)"""
        try:
            area_auto_select = getattr(
                self, 'area_auto_select', self.config.get("area_auto_select", {}))
            if not area_auto_select.get("enable", True):
                return
            auto_select_mode = area_auto_select.get(
                "mode", "from top to bottom")
            raw_keyword = area_auto_select.get("area_keyword", "").strip()
            raw_keyword_exclude = self.config.get("keyword_exclude", "")
            if not raw_keyword_exclude:
                raw_keyword_exclude = area_auto_select.get(
                    "area_keyword_exclude", "")
            raw_keyword_exclude = str(raw_keyword_exclude).strip()

            def parse_keywords(kw_str):
                kw_str = kw_str.strip()
                if not kw_str:
                    return [""]
                try:
                    if kw_str.startswith("[") and kw_str.endswith("]"):
                        return json.loads(kw_str)
                    if '"' in kw_str or "'" in kw_str:
                        return json.loads("[" + kw_str + "]")
                except:
                    pass
                return [x.strip().strip('\'"') for x in kw_str.replace('，', ',').split(',') if x.strip()]

            keyword_list = parse_keywords(raw_keyword)
            exclude_list = parse_keywords(raw_keyword_exclude)
            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_excludes = json.dumps(exclude_list, ensure_ascii=False)
            js_mode = f"'{auto_select_mode}'"

            js_script = f"""
                (function() {{
                    try {{
                        if (!document.getElementById('maxbot-no-animation')) {{
                            let style = document.createElement('style');
                            style.id = 'maxbot-no-animation';
                            style.innerHTML = `* {{ transition: none !important; animation: none !important; scroll-behavior: auto !important; }}`;
                            document.head.appendChild(style);
                        }}
                        let popups = document.querySelectorAll('div[role="dialog"]');
                        let isErrorPopup = false;
                        popups.forEach(dialog => {{
                            if (dialog.offsetParent !== null) {{
                                let text = dialog.innerText || "";
                                if (text.includes('失敗') || text.includes('售完') || text.includes('限制')) {{
                                    isErrorPopup = true;
                                }}
                                let btn = dialog.querySelector('button.primary') || dialog.querySelector('button.primary-1') || dialog.querySelector('button.v-btn');
                                if (btn) btn.click();
                            }}
                        }});
                        if (isErrorPopup) return "ERROR_POPUP";
                        let loader = document.querySelector('.v-progress-circular');
                        if (loader && loader.offsetParent !== null) return "LOADING";

                        const keywords = {js_keywords};
                        const excludes = {js_excludes};
                        const mode = {js_mode};
                        let rows = Array.from(document.querySelectorAll('.v-expansion-panel'));
                        if (rows.length === 0) {{
                            rows = Array.from(document.querySelectorAll('.price-group > div, div.rwd-margin'));
                        }}
                        let candidates = [];
                        for (let row of rows) {{
                            let header = row.querySelector('.v-expansion-panel-header');
                            let evaluateEl = header ? header : row;
                            let rawText = evaluateEl.textContent || evaluateEl.innerText || "";
                            let rowText = rawText.toUpperCase().replace(/,/g, '');
                            let rowHtml = evaluateEl.innerHTML.toLowerCase();
                            
                            if (rowText.includes('已售完') || rowText.includes('剩餘 0') || rowText.includes('剩餘：0') || rowHtml.includes('soldout')) {{
                                continue;
                            }}
                            let isExcluded = false;
                            if (excludes.length > 0 && excludes[0] !== "") {{
                                for (let exc of excludes) {{
                                    let cleanExc = exc.trim().toUpperCase().replace(/,/g, '');
                                    if (cleanExc.length > 0 && rowText.includes(cleanExc)) {{
                                        isExcluded = true; break;
                                    }}
                                }}
                            }}
                            if (isExcluded) continue;

                            let isMatch = false;
                            if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                                isMatch = true;
                            }} else {{
                                for (let k of keywords) {{
                                    let target_kws = k.trim().split(/\\s+/).filter(w => w.length > 0);
                                    let currentGroupMatch = true;
                                    for (let w of target_kws) {{
                                        let cleanW = w.toUpperCase().replace(/,/g, '');
                                        if (!rowText.includes(cleanW)) {{
                                            currentGroupMatch = false; break;
                                        }}
                                    }}
                                    if (currentGroupMatch) {{ isMatch = true; break; }}
                                }}
                            }}
                            if (isMatch) candidates.push(evaluateEl);
                        }}
                        
                        if (candidates.length === 0) return "NO_TICKETS";
                        if (mode === "from bottom to top") {{
                            candidates.reverse();
                        }} else if (mode === "random") {{
                            for (let i = candidates.length - 1; i > 0; i--) {{
                                const j = Math.floor(Math.random() * (i + 1));
                                [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
                            }}
                        }}
                        let targetElement = candidates[0];
                        let rawTargetText = targetElement.textContent || targetElement.innerText || "";
                        let targetName = rawTargetText.replace(/\\s+/g, ' ').trim();
                        if (targetElement.classList.contains('v-expansion-panel-header')) {{
                            if (targetElement.getAttribute('aria-expanded') === 'true') {{
                                return "ALREADY_EXPANDED|" + targetName;
                            }}
                        }}
                        targetElement.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                        targetElement.click(); 
                        return "CLICKED_BY_JS|" + targetName;
                    }} catch(e) {{
                        return "ERROR";
                    }}
                }})();
            """
            result = await self.tab.evaluate(js_script)
            if isinstance(result, str) and result.startswith("CLICKED_BY_JS|"):
                parts = result.split("|", 1)
                self.current_area_name = parts[1] if len(parts) > 1 else "未知區域"
                print(
                    f">>> [遠大售票-區域] 🎯 鎖定票區：【{self.current_area_name}】，展開面板...")
                await asyncio.sleep(0.05)
                self.is_area_selected = True
            elif isinstance(result, str) and result.startswith("ALREADY_EXPANDED"):
                parts = result.split("|", 1)
                self.current_area_name = parts[1] if len(parts) > 1 else "未知區域"
                self.is_area_selected = True
            elif result == "LOADING":
                await asyncio.sleep(0.1)
            elif result == "ERROR_POPUP":
                print(f">>> [系統] ⚠️ 發現錯誤彈窗！已關閉並準備重整...")
                self.is_area_selected = False
                self.is_ticket_assigned = False
                await self.tab.reload()
                await asyncio.sleep(0.5)
            elif result == "NO_TICKETS":
                wait_time = self.get_reload_interval()
                if not hasattr(self, 'refresh_log_count'):
                    self.refresh_log_count = 0
                self.refresh_log_count += 1
                if self.refresh_log_count % 3 == 0:
                    print(
                        f">>> [遠大售票-區域] ♻️ 無符合區域或已售完，依設定間隔 ({wait_time}s) 點擊「更新票數」...")

                js_refresh = """
                    (function() {
                        try {
                            let refreshBtn = null;
                            let spans = Array.from(document.querySelectorAll('span'));
                            for (let span of spans) {
                                if (span.textContent && span.textContent.includes('更新票數')) {
                                    refreshBtn = span.closest('button') || span.closest('.v-btn') || span;
                                    break;
                                }
                            }
                            if (!refreshBtn) {
                                let btns = Array.from(document.querySelectorAll('button, .v-btn'));
                                refreshBtn = btns.find(b => (b.innerText && b.innerText.includes('更新票數')) ||
                                                            (b.textContent && b.textContent.includes('更新票數')));
                            }
                            if (refreshBtn && !refreshBtn.disabled) {
                                refreshBtn.click();
                                return true;
                            }
                            return false;
                        } catch(e) { return false; }
                    })();
                """
                try:
                    is_btn_clicked = await self.tab.evaluate(js_refresh)
                    if not is_btn_clicked:
                        await self.tab.reload()
                except Exception:
                    try:
                        await self.tab.reload()
                    except:
                        pass
                await asyncio.sleep(wait_time)
        except Exception:
            pass

    async def assign_ticket_number(self):
        """[遠大售票] 分配票數 (依隨機設定間隔處理重新整理)"""
        js_script = f"""
        (function() {{
            try {{
                let allPlusIcons = document.querySelectorAll('i.mdi-plus');
                let validBtns = [];
                for (let icon of allPlusIcons) {{
                    let btn = icon.closest('button');
                    if (btn && btn.offsetParent !== null && !btn.disabled) {{
                        validBtns.push(btn);
                    }}
                }}
                if (validBtns.length > 0) {{
                    const priorityKeywords = ['福利', '加購', '套票'];
                    let targetBtn = validBtns[0];
                    for (let btn of validBtns) {{
                        let rowEl = btn.closest('.row') || btn.closest('.d-flex');
                        if (rowEl) {{
                            let rowText = rowEl.innerText.toUpperCase();
                            if (priorityKeywords.some(kw => rowText.includes(kw))) {{
                                targetBtn = btn;
                                break;
                            }}
                        }}
                    }}
                    let targetTickets = {self.ticket_number};
                    for (let i = 0; i < targetTickets; i++) {{
                        targetBtn.click();
                    }}
                    return "CLICKED_BY_JS";
                }}
                
                let activePanels = document.querySelectorAll('.v-expansion-panel--active');
                for (let i = 0; i < activePanels.length; i++) {{
                    let panel = activePanels[i];
                    let rawText = panel.innerText || panel.textContent || "";
                    let cleanText = rawText.replace(/\\s+/g, ''); 
                    
                    if (cleanText.includes('已售完') || 
                        cleanText.includes('售罄') || 
                        cleanText.includes('剩餘0') || 
                        cleanText.includes('開賣時間') || 
                        cleanText.includes('开卖时间')) {{
                        
                        let spans = Array.from(document.querySelectorAll('span'));
                        let refreshBtn = null;
                        for (let span of spans) {{
                            if (span.textContent && span.textContent.includes('更新票數')) {{
                                refreshBtn = span.closest('button') || span.closest('.v-btn') || span;
                                break;
                            }}
                        }}
                        if (!refreshBtn) {{
                            let btns = Array.from(document.querySelectorAll('button, .v-btn'));
                            refreshBtn = btns.find(b => (b.innerText && b.innerText.includes('更新票數')) || (b.textContent && b.textContent.includes('更新票數')));
                        }}
                        if (refreshBtn && !refreshBtn.disabled) {{
                            refreshBtn.click();
                        }}
                        return "FAST_FAIL_AND_REFRESHED";
                    }}
                }}
                return "WAITING_FOR_DOM";
            }} catch(e) {{
                return "ERROR";
            }}
        }})();
        """
        try:
            result = await self.tab.evaluate(js_script)
            wait_time = self.get_reload_interval()

            if result == "CLICKED_BY_JS":
                self.wait_dom_count = 0
                area_name = getattr(self, 'current_area_name', '該區域')
                print(
                    f">>> [遠大售票-票數] ⚡ 成功捕捉！JS 連點 {self.ticket_number} 張【 {area_name} 】！")
                self.is_ticket_assigned = True
                await self.click_next()
            elif result == "FAST_FAIL_AND_REFRESHED":
                self.wait_dom_count = 0
                self.is_area_selected = False
                await asyncio.sleep(wait_time)
            elif result == "WAITING_FOR_DOM" or result == "NOT_READY":
                if not hasattr(self, 'wait_dom_count'):
                    self.wait_dom_count = 0
                self.wait_dom_count += 1
                if self.wait_dom_count >= 3:
                    self.wait_dom_count = 0
                    self.is_area_selected = False
                    print(
                        f">>> [遠大售票-票數] ⚠️ 快速超時，強制發動「更新票數」 (間隔: {wait_time}s)...")
                    js_click_refresh = """
                    (function() {
                        let btns = Array.from(document.querySelectorAll('button, .v-btn, span'));
                        let refreshBtn = btns.find(b => (b.innerText && b.innerText.includes('更新票數')) || (b.textContent && b.textContent.includes('更新票數')));
                        if (refreshBtn) {
                            let actualBtn = refreshBtn.closest('button') || refreshBtn.closest('.v-btn') || refreshBtn;
                            if (!actualBtn.disabled) actualBtn.click();
                        }
                    })();
                    """
                    await self.tab.evaluate(js_click_refresh)
                    await asyncio.sleep(wait_time)
                else:
                    await asyncio.sleep(0.05)
        except Exception:
            pass

    async def click_next(self):
        """[遠大售票] 填寫問答題/專屬碼 並 點選下一步"""
        raw_answers = self.config.get("advanced", {}).get(
            "user_guess_string", "").strip()
        ans_list = []
        if raw_answers:
            try:
                if raw_answers.startswith("[") and raw_answers.endswith("]"):
                    ans_list = json.loads(raw_answers)
                elif '"' in raw_answers or "'" in raw_answers:
                    ans_list = json.loads("[" + raw_answers + "]")
                else:
                    ans_list = [x.strip()
                                for x in raw_answers.split(",") if x.strip()]
            except:
                pass
        target_answer = ans_list[0] if len(ans_list) > 0 else ""
        js_next = f"""
        (function() {{
            try {{
                let answerInput = document.querySelector('input[placeholder="答案選項"]') ||
                                  document.querySelector('input[placeholder*="專屬"]') ||
                                  document.querySelector('.exclusive-code input[type="text"]');
                if (answerInput && !answerInput.disabled && answerInput.value === '') {{
                    answerInput.value = '{target_answer}';
                    answerInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    answerInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                let nextBtn = document.querySelector('button.nextBtn');
                if (nextBtn && !nextBtn.disabled) {{
                    nextBtn.click();
                    return true;
                }}
                return false;
            }} catch(e) {{
                return false;
            }}
        }})();
        """
        try:
            result = await self.tab.evaluate(js_next)
            if result:
                print(
                    f">>> [遠大售票-下一步] 🚀 已填入答案【 {target_answer} 】並點擊「下一步」！準備進入結帳...")
                self.is_next_clicked = True
                await asyncio.sleep(0.05)
                return True
        except:
            pass
        return False

    async def process_confirmation(self):
        """[遠大售票] 結帳頁面處理：確認搶到票，自動打勾並發送通知"""
        js_confirm = """
        (function() {
            try {
                let timer = document.querySelector('.timer');
                if (!timer || !timer.innerText.includes('完成購票手續')) {
                    return false;
                }
                let checkbox = document.querySelector('input[type="checkbox"]');
                if (checkbox && !checkbox.checked) {
                    let wrapper = checkbox.closest('.v-input--selection-controls__input') || checkbox.closest('label') || checkbox;
                    wrapper.click();
                }
                return true;
            } catch(e) {
                return false;
            }
        })();
        """
        try:
            is_checkout_ready = await self.tab.evaluate(js_confirm)
            if is_checkout_ready and not getattr(self, 'is_telegram_sent', False):
                self.is_telegram_sent = True
                print("\n=======================================================")
                print(">>> [遠大售票-結帳] 💳 偵測到結帳倒數計時器！已自動勾選同意條款！")
                print(">>> [遠大售票-結帳] ⚠️ 請盡速手動確認後續付款流程！")
                print("=======================================================\n")
                area_name = getattr(self, 'current_area_name', '未知的神祕區域')
                ticket_num = self.ticket_number
                msg = f"🎉 <b>遠大售票 搶票成功！</b>\n\n系統已成功鎖定座位並進入結帳倒數！\n🎟️ <b>目標區域：</b>{area_name}\n🎫 <b>成功張數：</b>{ticket_num} 張\n\n⚠️ <b>請盡速回電腦前完成付款手續！</b>"
                await self.send_telegram_message(msg)
        except Exception:
            pass

    async def send_telegram_message(self, message):
        """[遠大售票] 發送 Telegram 通知"""
        if not self.config or "advanced" not in self.config:
            return
        if not self.config["advanced"].get("telegram_enable", False):
            return
        bot_token = self.config["advanced"].get("telegram_bot_token", "")
        chat_id = self.config["advanced"].get("telegram_chat_id", "")
        if not bot_token or not chat_id:
            print(">>> [系統] ⚠️ Telegram 設定不完整，跳過通知")
            return

        async def _async_send():
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=payload, timeout=6) as response:
                        if response.status == 200:
                            print(">>> [系統] 📱 Telegram 搶票成功通知發送成功！")
                        else:
                            error_text = await response.text()
                            print(f">>> [系統] ❌ Telegram 發送失敗: {error_text}")
            except Exception as e:
                print(f">>> [系統] ❌ Telegram 連線錯誤: {e}")

        asyncio.create_task(_async_send())

# ==========================================
# [遠大售票]
# ==========================================


class KKTIXBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        self.settings_path = config.get("config_filepath", "settings.json")

        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        import os
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # ==========================================
        # KKTIX 專屬狀態鎖
        # ==========================================
        self.is_printing_pause = False
        self.is_login_done = False
        self.is_event_next_clicked = False  # 活動首頁的「立即購票」按鈕鎖
        self.is_ticket_assigned = False     # 區域與張數分配鎖
        self.is_terms_agreed = False        # 同意條款打勾鎖
        self.is_captcha_solved = False      # 驗證碼/問答題鎖
        self.is_reg_next_clicked = False    # 購票頁面的「下一步」鎖
        self.is_telegram_sent = False
        self.has_seen_spinner = False
        self.is_printing_spinner = False

        print(">>> [KKTIX] 正在載入 ddddocr 辨識模型...")
        try:
            import ddddocr
            self.ocr = ddddocr.DdddOcr(show_ad=False)
        except Exception as e:
            print(f">>> [系統] ddddocr 載入失敗: {e}")
            self.ocr = None

    async def run(self):
        print(f">>> [KKTIX] 機器人啟動！(目標張數: {self.ticket_number})")
        print("等待網頁載入中...")

        import os
        import asyncio

        while True:
            try:
                # 1. 暫停攔截
                if os.path.exists(self.PAUSE_FILE):
                    if not getattr(self, 'is_printing_pause', False):
                        self.is_printing_pause = True
                    await asyncio.sleep(0.5)
                    continue
                else:
                    if getattr(self, 'is_printing_pause', False):
                        self.is_printing_pause = False

                # 2. 獲取網址
                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                upper_curr = current_url.upper()

                # 3. 檢測頁面切換與退回防呆解鎖
                if current_url != self.last_url:
                    print(f"偵測到頁面切換: {current_url}")

                    if '/EVENTS/' in upper_curr and '/REGISTRATIONS/' not in upper_curr:
                        print(">>> [系統] 退回或進入活動頁面，解鎖所有購票狀態！")
                        self.is_event_next_clicked = False
                        self.is_ticket_assigned = False
                        self.is_terms_agreed = False
                        self.is_captcha_solved = False
                        self.is_reg_next_clicked = False
                        self.is_telegram_sent = False
                        self.has_seen_spinner = False

                        await self.reload_settings()

                    elif '/REGISTRATIONS/' in upper_curr and upper_curr.endswith('/NEW'):
                        print(">>> [系統] 偵測到進入選票頁面，解鎖填表狀態！")
                        self.is_ticket_assigned = False
                        self.is_terms_agreed = False
                        self.is_captcha_solved = False
                        self.is_reg_next_clicked = False
                        self.is_telegram_sent = False
                        self.has_seen_spinner = False

                    self.last_url = current_url

                # ==========================================
                # 【樣態 2】攔截彈窗 (內部已包含解鎖與重整機制)
                # ==========================================
                has_popup = await self.check_and_close_popups()
                if has_popup:
                    base_wait = getattr(self, 'refresh_sec', 0.2)
                    if base_wait <= 0:
                        base_wait = 0.2
                    await asyncio.sleep(base_wait)
                    continue

                # 5. 分發任務
                await self.dispatch_action(current_url)

            except Exception as e:
                pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, url):
        """KKTIX 任務分發中心"""
        lower_url = url.lower()

        # ==========================================
        # 🔥 核心新增：訂單靜默鎖定與解除機制
        # ==========================================
        if getattr(self, 'is_order_locked', False):
            # 檢查網址是否已經退回到「活動首頁」或「選張數/問答頁面」
            if ('/events/' in lower_url and '/registrations/' not in lower_url) or \
               ('/registrations/' in lower_url and lower_url.endswith('/new')):
                print("\n>>> [系統] 偵測到返回活動/選票頁面，解除訂單靜默鎖，機器人重新啟動！\n")

                # 解鎖！
                self.is_order_locked = False

                # 順便把先前的選票狀態全部清空，讓機器人可以乾淨地進行下一輪搶票
                self.is_ticket_assigned = False
                self.is_terms_agreed = False
                self.is_captcha_solved = False
                self.is_reg_next_clicked = False
                self.is_event_next_clicked = False
                self.is_telegram_sent = False
            else:
                # 如果還在結帳頁面，直接 return，讓機器人繼續安靜待命
                return

        # ==========================================
        # 以下維持您原本的分發邏輯...
        # ==========================================
        if '/users/sign_in' in lower_url:
            if not getattr(self, 'is_login_done', False):
                await self.auto_login()

        elif '/events/' in lower_url and '/registrations/' not in lower_url:
            if not getattr(self, 'is_event_next_clicked', False):
                await self.click_event_next()

        elif '/registrations/' in lower_url:
            if lower_url.endswith('/new'):
                if not getattr(self, 'is_ticket_assigned', False) or not getattr(self, 'is_terms_agreed', False):
                    await self.assign_ticket_number()
                elif not getattr(self, 'is_captcha_solved', False):
                    await self.solve_kktix_question()
                elif not getattr(self, 'is_reg_next_clicked', False):
                    await self.click_reg_next()
                else:
                    await self.monitor_booking_spinner()
            else:
                await self.process_order_confirmation()

    async def auto_login(self):
        if not getattr(self, 'is_login_checking', False):
            print(">>> [KKTIX-登入] 進入自動登入模組，準備執行登入腳本...")
            self.is_login_checking = True

        account = self.config.get("advanced", {}).get("kktix_account", "")
        password = self.config.get("advanced", {}).get(
            "kktix_password_plaintext", "").strip()

        if not password:
            try:
                import util
                password = util.decrypt_me(self.config.get(
                    "advanced", {}).get("kktix_password", ""))
            except:
                pass

        if not account or not password:
            print(">>> [KKTIX-登入]  未設定帳號密碼，跳過自動登入！")
            self.is_login_done = True
            return

        js_check = """
        (function() {
            try {
                let currentUrl = window.location.href;
                if (currentUrl.includes('/users/sign_in')) {
                    let accInput = document.querySelector('#user_login');
                    if (accInput && accInput.offsetParent !== null) return "READY_FOR_CDP";
                    return "WAITING_DOM";
                }
                let signOutBtn = document.querySelector('a[href="/users/sign_out"]');
                if (signOutBtn && signOutBtn.offsetParent !== null) return "LOGGED_IN";

                if (currentUrl === 'https://kktix.com' || currentUrl === 'https://kktix.com/') {
                    let loginBtn = document.querySelector('a[href="/users/sign_in"]');
                    if (loginBtn && loginBtn.offsetParent !== null) { loginBtn.click(); return "WAIT_JUMP"; }
                }
                return "UNKNOWN_PAGE";
            } catch(e) { return "ERROR"; }
        })();
        """
        try:
            result = await self.tab.evaluate(js_check)
            if result == "LOGGED_IN":
                print(">>> [KKTIX-登入]  成功偵測到「可見的登出按鈕」，確認已登入！")
                self.is_login_done = True
            elif result == "READY_FOR_CDP":
                import asyncio
                acc_val = await self.tab.evaluate('document.querySelector("#user_login").value')
                if not acc_val and not getattr(self, 'is_credentials_filled', False):
                    print(f">>> [KKTIX-登入]  實體鍵盤輸入帳號密碼...")
                    acc_input = await self.tab.select('#user_login')
                    if acc_input:
                        await acc_input.send_keys(account)
                    await asyncio.sleep(0.3)
                    pwd_input = await self.tab.select('#user_password')
                    if pwd_input:
                        await pwd_input.send_keys(password)
                    await asyncio.sleep(0.3)
                    print("\n>>> [KKTIX-登入] 帳密已自動填妥！請您【手動】點擊登入按鈕與打勾驗證！\n")
                    self.is_credentials_filled = True
            elif result == "WAIT_JUMP":
                import asyncio
                await asyncio.sleep(0.5)
        except Exception as e:
            pass

    async def assign_ticket_number(self):
        if not getattr(self, 'is_printing_assign', False):
            self.is_printing_assign = True

        import json
        import asyncio

        area_auto_select = self.config.get("area_auto_select", {})
        raw_keyword = area_auto_select.get("area_keyword", "").strip()
        raw_keyword_exclude = self.config.get("keyword_exclude", "")
        if not raw_keyword_exclude:
            raw_keyword_exclude = area_auto_select.get(
                "area_keyword_exclude", "")
        raw_keyword_exclude = str(raw_keyword_exclude).strip()
        area_mode = area_auto_select.get("mode", "from top to bottom")

        def parse_keywords(kw_str):
            kw_str = kw_str.strip()
            if not kw_str:
                return [""]
            try:
                if kw_str.startswith("[") and kw_str.endswith("]"):
                    return json.loads(kw_str)
                if '"' in kw_str or "'" in kw_str:
                    return json.loads("[" + kw_str + "]")
            except:
                pass
            return [x.strip().strip('\'"') for x in kw_str.replace('，', ',').split(',') if x.strip()]

        js_keywords = json.dumps(parse_keywords(
            raw_keyword), ensure_ascii=False)
        js_excludes = json.dumps(parse_keywords(
            raw_keyword_exclude), ensure_ascii=False)
        js_mode = f"'{area_mode}'"

        js_scan = f"""
        (function() {{
            try {{
                let outOfStockAlert = document.querySelector('.alert-warning .alert');
                if (outOfStockAlert && outOfStockAlert.innerText.includes('沒有任何可以購買')) {{
                    return "OUT_OF_STOCK_PAGE";
                }}

                if (document.querySelector('.loading') || document.querySelector('.spinner')) return "LOADING";
                let rows = Array.from(document.querySelectorAll('.display-table-row, .ticket-unit'));
                if (rows.length === 0) {{
                    let names = document.querySelectorAll('.ticket-name');
                    if (names.length === 0) return "NOT_READY";
                    names.forEach(n => rows.push(n.closest('div')));
                }}

                const keywords = {js_keywords};
                const excludes = {js_excludes};
                const mode = {js_mode};

                let candidates = [];
                for (let row of rows) {{
                    if (!row) continue;
                    let rowText = row.innerText.replace(/,/g, '').toUpperCase();
                    let rowHtml = row.innerHTML;

                    if (rowText.includes('已售完') || rowText.includes('SOLD OUT') ||
                        rowText.includes('暫無票') || rowText.includes('未開賣') || rowText.includes('完売') ||
                        !rowHtml.includes('<input')) continue;

                    let isExcluded = false;
                    if (excludes.length > 0 && excludes[0] !== "") {{
                        for (let exc of excludes) {{
                            let cleanExc = exc.trim().replace(/,/g, '').toUpperCase();
                            if (cleanExc.length > 0 && rowText.includes(cleanExc)) {{ isExcluded = true; break; }}
                        }}
                    }}
                    if (isExcluded) continue;

                    let isMatch = false;
                    if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) isMatch = true;
                    else {{
                        for (let k of keywords) {{
                            let target_kws = k.trim().replace(/,/g, '').split(/\\s+/).filter(w => w.length > 0);
                            let currentGroupMatch = true;
                            for (let w of target_kws) {{
                                if (!rowText.includes(w.toUpperCase())) {{ currentGroupMatch = false; break; }}
                            }}
                            if (currentGroupMatch) {{ isMatch = true; break; }}
                        }}
                    }}

                    if (isMatch) {{
                        let input = row.querySelector('input[type="text"]');
                        if (input && !input.disabled) {{
                            let nameEl = row.querySelector('.ticket-name');
                            let areaName = nameEl ? nameEl.innerText.replace(/\\s+/g, ' ').trim() : "指定區域";
                            candidates.push(
                                {{ input: input, areaName: areaName }});
                        }}
                    }}
                }}

                if (candidates.length === 0) return "NO_TICKETS";

                if (mode === "from bottom to top") candidates.reverse();
                else if (mode === "random") {{
                    for (let i = candidates.length - 1; i > 0; i--) {{
                        const j = Math.floor(Math.random() * (i + 1));
                        [candidates[i], candidates[j]] = [
                            candidates[j], candidates[i]];
                    }}
                }}

                let target = candidates[0];
                let uniqueId = 'maxbot_kktix_input_' + Date.now();
                target.input.id = uniqueId;
                target.input.scrollIntoView(
                    {{ behavior: 'instant', block: 'center' }});
                return uniqueId + "|" + target.areaName;
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_scan)

            if isinstance(result, str) and result.startswith("maxbot_kktix_input_"):
                parts = result.split("|", 1)
                target_id = parts[0]
                area_name = parts[1] if len(parts) > 1 else "目標區域"
                self.current_area_name = area_name

                print(f">>> [KKTIX-選票]  鎖定票區：【{area_name}】，執行清空並打入張數...")

                input_element = await self.tab.select(f'#{target_id}')
                if input_element:
                    await input_element.click()
                    clear_js = f"""
                        let el = document.getElementById("{target_id}");
                        el.value = "";
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    """
                    await self.tab.evaluate(clear_js)
                    await asyncio.sleep(0.01)

                    await input_element.send_keys(str(self.ticket_number))
                    await asyncio.sleep(0.01)

                    print(f">>> [KKTIX-選票] 🎉 成功填入正確張數: {self.ticket_number} 張")
                    self.is_ticket_assigned = True

                # ==========================================
                # 服務條款處理 - 極速版
                # 有 → 自動勾選
                # 沒有 → 立即跳過
                # 不使用 select() 等待不存在的元素
                # ==========================================

                terms_result = await self.tab.evaluate("""
                (function() {
                    try {
                        let checkbox = document.querySelector('#person_agree_terms');

                        // 新版 KKTIX 沒有服務條款
                        if (!checkbox) {
                            return "NO_TERMS";
                        }

                        // 已經勾選
                        if (checkbox.checked) {
                            return "ALREADY_CHECKED";
                        }

                        // 暫時不能點
                        if (checkbox.disabled) {
                            return "DISABLED";
                        }

                        // 直接由 JS 點擊，避免 Python 再 select 一次
                        checkbox.click();

                        // 確認結果
                        if (checkbox.checked) {
                            return "CHECKED";
                        }

                        return "CLICK_FAILED";

                    } catch(e) {
                        return "ERROR|" + e.toString();
                    }
                })();
                """)

                if terms_result == "NO_TERMS":

                    print(
                        ">>> [KKTIX-條款] "
                        "此活動沒有服務條款勾選框，直接繼續"
                    )

                    self.is_terms_agreed = True

                elif terms_result == "ALREADY_CHECKED":

                    self.is_terms_agreed = True

                elif terms_result == "CHECKED":

                    print(
                        ">>> [KKTIX-條款] "
                        "已勾選「同意服務條款」"
                    )

                    self.is_terms_agreed = True

                elif terms_result == "DISABLED":

                    # 暫時不能操作，下一輪再處理
                    self.is_terms_agreed = False

                    await asyncio.sleep(0.01)

                elif terms_result == "CLICK_FAILED":

                    print(
                        ">>> [KKTIX-條款] "
                        "⚠️ 找到服務條款，但勾選失敗"
                    )

                    self.is_terms_agreed = False

                elif isinstance(terms_result, str) and terms_result.startswith("ERROR|"):

                    print(
                        f">>> [KKTIX-條款] "
                        f"⚠️ 條款檢查錯誤: {terms_result}"
                    )

                    self.is_terms_agreed = False

            # ==========================================
            # 🔥 找不到票時的「隨機重整秒數」與狀態列印邏輯
            # ==========================================
            elif result in ["NO_TICKETS", "OUT_OF_STOCK_PAGE"]:
                self.is_printing_assign = False  # 讓重整後可以重新印 Log

                advanced_conf = self.config.get("advanced", {})
                base_wait = getattr(self, 'refresh_sec', 0.2)
                if base_wait <= 0:
                    base_wait = 0.2

                # 判斷開關狀態
                is_random = advanced_conf.get("auto_reload_random_mode", False)
                random_status = "啟用" if is_random else "關閉"
                actual_wait = base_wait

                if is_random:
                    import random
                    try:
                        rand_range = float(advanced_conf.get(
                            "auto_reload_random_range", 1.0))
                    except:
                        rand_range = 1.0
                    actual_wait = round(
                        base_wait + random.uniform(0, rand_range), 2)

                # 根據不同情況印出包含開關狀態的 Log
                # if result == "OUT_OF_STOCK_PAGE":
                    # print(f">>> [系統] ⚠️ 畫面顯示橘色橫幅「目前沒有任何可以購買的票券」，就地重整！ (隨機秒數: {random_status} | 準備等待 {actual_wait} 秒)")
                # else:
                    # print(f">>> [KKTIX-選票] 找不到符合關鍵字或有空位的票區，準備刷新... (隨機秒數: {random_status} | 準備等待 {actual_wait} 秒)")

                # 發動 JS 重整防卡死
                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass
                await asyncio.sleep(actual_wait)

        except Exception as e:
            pass

    async def solve_kktix_question(self):
        """
        [KKTIX] 智能分類填寫
        支援：
        1. 新版會員碼 .member-code / ticketModel.member_codes
        2. 舊版會員碼 .code-input
        3. 自訂問答 conditions.custom_captcha / captcha_answer
        4. 其他未知文字輸入框
        5. AngularJS 欄位尚未啟用時自動等待重試
        """

        import json
        import asyncio

        # ============================================================
        # 1. 讀取設定檔中的答案
        # ============================================================
        raw_answers = self.config.get("advanced", {}).get(
            "user_guess_string", "").strip()
        ans_list = []

        if raw_answers:
            try:
                # 標準 JSON 格式： ["答案1", "答案2"]
                parsed = json.loads(raw_answers)
                if isinstance(parsed, list):
                    ans_list = [str(x).strip()
                                for x in parsed if str(x).strip()]
                else:
                    value = str(parsed).strip()
                    if value:
                        ans_list = [value]
            except Exception:
                # 相容舊格式： 答案1,答案2 或 "答案1","答案2" 或 '答案1','答案2'
                ans_list = [
                    x.strip().strip('"').strip("'")
                    for x in raw_answers.replace("，", ",").split(",")
                    if x.strip()
                ]

        # 防止 ans_list[-1] 發生 IndexError
        if not ans_list:
            ans_list = [""]

        # ============================================================
        # 2. JS 雷達
        # ============================================================
        js_find_inputs = """
        (function() {
            try {
                let output = {
                    memberCode: "",
                    captcha: "",
                    others: []
                };

                // ------------------------------------------------
                // 共用工具
                // ------------------------------------------------
                function isVisible(el) {
                    if (!el) return false;
                    return (el.offsetParent !== null || (el.getClientRects && el.getClientRects().length > 0));
                }

                function isEmpty(el) {
                    if (!el) return false;
                    return String(el.value || "").trim() === "";
                }

                function isUsable(el) {
                    if (!el) return false;
                    if (!isVisible(el)) return false;
                    if (el.disabled || el.readOnly) return false;
                    if (!isEmpty(el)) return false;
                    return true;
                }

                // ====================================================
                // A. 會員碼 / 卡友碼
                // ====================================================
                const memberSelector = [
                    'input.member-code[type="text"]',
                    'input[ng-model*="ticketModel.member_codes"]',
                    'input[ng-if*="member_code"][type="text"]',
                    '.code-input input[type="text"]',
                    '.code-input input:not([type="radio"]):not([type="checkbox"]):not([type="hidden"])'
                ].join(',');

                let memberCandidates = Array.from(document.querySelectorAll(memberSelector));
                memberCandidates = Array.from(new Set(memberCandidates));

                let codeInput = memberCandidates.find(el => isUsable(el)) || null;
                if (codeInput) {
                    if (!codeInput.id) {
                        codeInput.id = 'maxbot_code_' + Date.now() + '_' + Math.floor(Math.random() * 10000);
                    }
                    output.memberCode = codeInput.id;
                }

                // ====================================================
                // B. 自訂問答題
                // ====================================================
                const captchaSelector = [
                    'input[ng-model="conditions.custom_captcha"]',
                    'input[name="captcha_answer"]'
                ].join(',');

                let captchaCandidates = Array.from(document.querySelectorAll(captchaSelector));
                captchaCandidates = Array.from(new Set(captchaCandidates));

                let captchaInput = captchaCandidates.find(el => isUsable(el)) || null;
                if (captchaInput) {
                    if (!captchaInput.id) {
                        captchaInput.id = 'maxbot_captcha_' + Date.now() + '_' + Math.floor(Math.random() * 10000);
                    }
                    output.captcha = captchaInput.id;
                }

                // ====================================================
                // C. 其他未知 input[type="text"]
                // ====================================================
                let allTexts = Array.from(document.querySelectorAll('input[type="text"]')).filter(el => {
                    if (el.disabled || el.readOnly || !isVisible(el) || !isEmpty(el)) return false;
                    let ngModel = el.getAttribute('ng-model') || '';
                    if (ngModel.toLowerCase().includes('quantity')) return false;
                    if (memberCandidates.includes(el) || captchaCandidates.includes(el)) return false;
                    return true;
                });

                // ====================================================
                // D. 一般文字框設定 ID
                // ====================================================
                allTexts.forEach((el, idx) => {
                    if (!el.id) {
                        el.id = 'maxbot_other_' + Date.now() + '_' + idx + '_' + Math.floor(Math.random() * 10000);
                    }
                    output.others.push(el.id);
                });

                // ====================================================
                // E. AngularJS 尚未 Ready 判斷
                // ====================================================
                let memberWaiting = memberCandidates.some(el => {
                    if (!el || !isEmpty(el) || el.readOnly) return false;
                    return isVisible(el) && el.disabled;
                });

                let captchaWaiting = captchaCandidates.some(el => {
                    if (!el || !isEmpty(el) || el.readOnly) return false;
                    return isVisible(el) && el.disabled;
                });

                // ====================================================
                // F. 回傳
                // ====================================================
                if (!output.memberCode && !output.captcha && output.others.length === 0) {
                    if (memberWaiting || captchaWaiting) {
                        return "WAIT_INPUT";
                    }
                    return "NONE";
                }
                return "JSON|" + JSON.stringify(output);

            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        try:
            result = await self.tab.evaluate(js_find_inputs)

            # ========================================================
            # 3. 有找到需要填寫的 Input
            # ========================================================
            if isinstance(result, str) and result.startswith("JSON|"):
                # Angular 等待計數歸零
                self.kktix_question_wait_count = 0

                data_str = result.split("|", 1)[1]
                data = json.loads(data_str)

                total_fields = (
                    (1 if data.get("memberCode") else 0) +
                    (1 if data.get("captcha") else 0) +
                    len(data.get("others", []))
                )

                print(f">>> [KKTIX-問答] 偵測到 {total_fields} 個需要填寫的格子！")
                ans_index = 0

                # ====================================================
                # 4. 單一欄位填寫函數
                # ====================================================
                async def fill_field(q_id, field_name):
                    nonlocal ans_index
                    if not q_id:
                        return False

                    # 決定要用哪一個答案
                    ans = str(ans_list[ans_index] if ans_index < len(
                        ans_list) else ans_list[-1])

                    # 重新抓取 element
                    q_element = await self.tab.select(f'#{q_id}')
                    if not q_element:
                        print(f"    -> [{field_name}] ⚠️ DOM 已更新，暫時找不到欄位。")
                        return False

                    # 再次確認目前狀態，防止 Angular 在 JS 掃描後改變狀態
                    status_js = f"""
                        (function() {{
                            let el = document.getElementById("{q_id}");
                            if (!el) return "NOT_FOUND";
                            if (el.disabled) return "DISABLED";
                            if (el.readOnly) return "READONLY";
                            return "READY";
                        }})();
                    """
                    status = await self.tab.evaluate(status_js)

                    if status == "DISABLED":
                        print(
                            f"    -> [{field_name}] Angular 尚未解除 disabled，下一輪重試...")
                        return False
                    if status in ["NOT_FOUND", "READONLY"]:
                        return False

                    # 實際輸入
                    try:
                        await q_element.click()
                        await asyncio.sleep(0.02)
                        await q_element.send_keys(ans)
                    except Exception as e:
                        print(
                            f"    -> [{field_name}] ⚠️ send_keys 失敗，下一輪重試: {e}")
                        return False

                    # Angular / Browser Event
                    trigger_js = f"""
                        (function() {{
                            let el = document.getElementById("{q_id}");
                            if (!el) return false;
                            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            el.dispatchEvent(new Event('keyup', {{ bubbles: true }}));
                            el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                            return true;
                        }})();
                    """
                    await self.tab.evaluate(trigger_js)
                    await asyncio.sleep(0.01)

                    # 確認真的填進去了
                    verify_js = f"""
                        (function() {{
                            let el = document.getElementById("{q_id}");
                            return el ? el.value : null;
                        }})();
                    """
                    final_value = await self.tab.evaluate(verify_js)

                    if final_value is not None and str(final_value) != "":
                        print(f"    -> [{field_name}] 已精準填入：【{ans}】")
                        # 只有「真的填成功」才消耗下一個答案
                        ans_index += 1
                        return True

                    print(f"    -> [{field_name}] ⚠️ 輸入後 value 仍為空，下一輪重試。")
                    return False

                # ====================================================
                # 5. 按原本優先順序填寫
                # ====================================================
                all_success = True

                if data.get("memberCode"):
                    if not await fill_field(data["memberCode"], "會員/卡友認證碼"):
                        all_success = False

                if data.get("captcha"):
                    if not await fill_field(data["captcha"], "自訂問答題"):
                        all_success = False

                for other_id in data.get("others", []):
                    if not await fill_field(other_id, "一般文字框"):
                        all_success = False

                # ====================================================
                # 6. 必須真的全部處理完成才能鎖定
                # ====================================================
                if all_success:
                    self.is_captcha_solved = True
                    self.kktix_question_wait_count = 0
                    return True
                else:
                    self.is_captcha_solved = False
                    await asyncio.sleep(0.05)
                    return False

            # ========================================================
            # 7. Angular input 已出現，但目前 disabled
            # ========================================================
            elif result == "WAIT_INPUT":
                wait_count = getattr(self, "kktix_question_wait_count", 0)
                wait_count += 1
                self.kktix_question_wait_count = wait_count

                if wait_count == 1:
                    print(">>> [KKTIX-問答] 已偵測到問答/會員碼欄位，等待 Angular 啟用輸入框...")

                if wait_count <= 60:
                    await asyncio.sleep(0.05)
                    return False
                else:
                    print(">>> [KKTIX-問答] ⚠️ 欄位長時間保持 disabled，判定目前不需要填寫，繼續下一步。")
                    self.kktix_question_wait_count = 0
                    self.is_captcha_solved = True
                    return True

            # ========================================================
            # 8. 確定頁面完全沒有問答欄位
            # ========================================================
            elif result == "NONE":
                self.kktix_question_wait_count = 0
                self.is_captcha_solved = True
                return True

            # ========================================================
            # 9. JS 發生錯誤
            # ========================================================
            elif isinstance(result, str) and result.startswith("ERROR|"):
                print(f">>> [KKTIX-問答] JS 雷達發生錯誤: {result}")
                self.is_captcha_solved = False
                return False

        except Exception as e:
            print(f">>> [嚴重錯誤] solve_kktix_question 發生例外: {e}")
            self.is_captcha_solved = False

        return False

    async def click_reg_next(self):
        js_next = """
        (function() {
            try {
                let container = document.querySelector('.register-new-next-button-area') || document.querySelector('.form-actions');
                if (!container) return false;
                let buttons = Array.from(container.querySelectorAll('button.btn-primary'));
                if (buttons.length === 0) return false;

                let targetBtn = null;
                let computerBtn = buttons.find(b => b.innerText.includes('電腦配位') && !b.disabled);
                if (computerBtn) targetBtn = computerBtn;
                else targetBtn = buttons.find(b => !b.disabled);

                if (targetBtn) {
                    targetBtn.click();
                    return targetBtn.innerText.trim();
                }
                return false;
            } catch(e) { return false; }
        })();
        """
        try:
            clicked_text = await self.tab.evaluate(js_next)
            if clicked_text:
                print(f">>> [KKTIX-下一步]  已點擊「{clicked_text}」！準備進入訂單確認頁...")
                self.is_reg_next_clicked = True
        except:
            pass

    async def click_event_next(self):
        js_click_next = """
        (function() {
            try {
                let btn = document.querySelector('.tickets a.btn-point') || document.querySelector('.tickets a.btn-primary');
                if (btn) {
                    if (btn.innerText.includes('已售完') || btn.innerText.includes('Sold Out')) return "SOLD_OUT";
                    if (btn.innerText.includes('尚未開賣')) return "NOT_YET";
                    let uniqueId = 'kktix_next_' + Date.now();
                    btn.id = uniqueId;
                    return uniqueId;
                }
                return "NOT_FOUND";
            } catch(e) { return "ERROR"; }
        })();
        """
        try:
            result = await self.tab.evaluate(js_click_next)
            import asyncio
            if isinstance(result, str) and result.startswith("kktix_next_"):
                print(">>> [KKTIX-活動頁]  找到「立即購票」按鈕！發動點擊進入選票頁面...")
                target_element = await self.tab.select(f'#{result}')
                if target_element:
                    await target_element.click()
                self.is_event_next_clicked = True
                await asyncio.sleep(0.5)
            elif result == "SOLD_OUT":
                actual_wait = self.get_actual_wait_time()
                # print(f">>> [KKTIX-活動頁]  系統顯示「已售完」，等待 {actual_wait} 秒後刷新...")
                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass
                await asyncio.sleep(actual_wait)
            elif result == "NOT_YET":
                actual_wait = self.get_actual_wait_time()
                # print(f">>> [KKTIX-活動頁]  尚未開賣，等待 {actual_wait} 秒後刷新...")
                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass
                await asyncio.sleep(actual_wait)
        except:
            pass

    async def process_order_confirmation(self):
        """[KKTIX] 訂單確認頁處理：偵測倒數計時器並發送通知 (支援無縫連刷)"""
        js_close_popup = """
        (function() {
            try {
                let buttons = document.querySelectorAll('button, a.btn');
                for (let btn of buttons) {
                    let text = btn.innerText.trim();
                    if (['確定', '確認', '關閉', '我知道了'].includes(text)) {
                        if (btn.offsetParent !== null) { btn.click(); return text; }
                    }
                }
                return false;
            } catch(e) { return false; }
        })();
        """
        js_check_order = """
        (function() {
            try {
                let timer = document.querySelector('.countdown-block');
                if (timer && (timer.innerText.includes('訂單已保留') || timer.innerText.includes('請在'))) {
                    return timer.innerText.trim();
                }
                return false;
            } catch(e) { return false; }
        })();
        """
        try:
            clicked_btn_text = await self.tab.evaluate(js_close_popup)
            if clicked_btn_text:
                print(
                    f">>> [KKTIX-系統] 訂單完成頁面偵測到彈窗！已自動點擊「{clicked_btn_text}」按鈕關閉。")

            order_info = await self.tab.evaluate(js_check_order)

            # 如果偵測到訂單，且還沒發送過通知
            if order_info and not getattr(self, 'is_telegram_sent', False):
                self.is_telegram_sent = True

                print("\n=======================================================")
                print(f">>> [KKTIX-訂單]  成功搶到票了！系統偵測到保留位！")
                print(f">>> [KKTIX-訂單]  {order_info}")
                print(">>> [KKTIX-訂單]  機器人已於此頁面靜默待命。")
                print(">>> [KKTIX-訂單]  若要繼續搶票，請直接點擊瀏覽器的「上一頁」，機器人將瞬間重啟！")
                print("=======================================================\n")

                area_name = getattr(self, 'current_area_name', '已選區域')
                msg = f"🎉 <b>KKTIX 搶票成功！</b>\n\n🎟️ <b>區域：</b>{area_name}\n🎫 <b>張數：</b>{self.ticket_number} 張\n⏰ <b>狀態：</b>{order_info}\n\n⚠️ <b>請在時限內手動完成付款！</b>"

                # 發送 Telegram 通知
                await self.send_telegram_message(msg)

                # ==========================================
                # 核心新增：通知發送完畢後，正式掛上「靜默鎖」！
                # ==========================================
                self.is_order_locked = True

        except Exception as e:
            pass

    async def send_telegram_message(self, message):
        """發送 Telegram 通知 (還原完整 Log 與錯誤捕捉版)"""
        # 1. 檢查設定是否存在且啟用
        if not self.config or "advanced" not in self.config:
            return
        if not self.config["advanced"].get("telegram_enable", False):
            return

        bot_token = self.config["advanced"].get("telegram_bot_token", "")
        chat_id = self.config["advanced"].get("telegram_chat_id", "")

        if not bot_token or not chat_id:
            print(">>> [系統] Telegram 設定不完整，跳過通知")
            return

        # 2. 定義發送任務
        def _send():
            import requests
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, data=payload, timeout=6)
                if response.status_code == 200:
                    print(">>> [系統] 📱 Telegram 搶票成功通知發送成功！")
                else:
                    print(f">>> [系統] ⚠️ Telegram 發送失敗: {response.text}")
            except Exception as e:
                print(f">>> [系統] ❌ Telegram 連線錯誤: {e}")

        # 3. 將 requests 丟到背景執行，不卡死主執行緒
        import asyncio
        asyncio.create_task(asyncio.to_thread(_send))

    async def monitor_booking_spinner(self):
        """【樣態 1】監測「查詢空位中」的轉圈圈狀態"""
        js_check = """
        (function() {
            try {
                let spinners = document.querySelectorAll('.spinner-holder, span.ng-binding');
                for (let s of spinners) {
                    if (s.innerText.includes('查詢空位中') && s.offsetParent !== null) return "SPINNING";
                }
                let alerts = document.querySelectorAll('.alert-danger, .error-message');
                for (let a of alerts) {
                    let text = a.innerText || "";
                    if (text.includes('不足') || text.includes('售完') || text.includes('錯誤') || text.includes('失敗')) return "INLINE_ERROR";
                }
                return "STOPPED";
            } catch(e) { return "ERROR"; }
        })();
        """
        try:
            result = await self.tab.evaluate(js_check)
            import asyncio
            if result == "SPINNING":
                if not getattr(self, 'is_printing_spinner', False):
                    print(">>> [KKTIX] ⏳ 系統「查詢空位中」，請勿亂動，祈禱中...")
                    self.is_printing_spinner = True
                self.has_seen_spinner = True
                await asyncio.sleep(0.05)
            elif result == "INLINE_ERROR":
                print("\n>>> [系統] 💥 畫面上出現紅字錯誤提示！判定為搶票失敗。")
                await self.reset_and_reload()
            elif result == "STOPPED":
                if getattr(self, 'has_seen_spinner', False):
                    print("\n>>> [系統] 💥 「查詢空位中」已結束，但未進入訂單頁！判定為票已沒了。")
                    await self.reset_and_reload()
                else:
                    await asyncio.sleep(0.05)
        except:
            pass

    async def reset_and_reload(self):
        """[核心] 觸發失敗重整並解鎖所有狀態"""
        print(">>> [系統] 準備解鎖所有狀態並重新整理...\n")
        self.is_ticket_assigned = False
        self.is_terms_agreed = False
        self.is_captcha_solved = False
        self.is_reg_next_clicked = False
        self.is_printing_assign = False
        self.is_printing_spinner = False
        self.has_seen_spinner = False

        actual_wait = self.get_actual_wait_time()

        import asyncio
        # 發動 JS 重整防卡死
        try:
            await self.tab.evaluate("window.location.reload();")
        except:
            pass

        print(f"    -> 網頁已刷新，等待 {actual_wait} 秒後瞬間重啟搜尋...\n")
        await asyncio.sleep(actual_wait)

    async def check_and_close_popups(self):
        """【樣態 2】全域彈窗攔截 (極速一體化 + 內建暴力解鎖防卡死)"""
        js_unified_check = """
        (function() {
            let results = [];
            if (!window.interceptedPopups) {
                window.interceptedPopups = [];
                window.confirm = function(msg) { window.interceptedPopups.push("[Confirm] " + msg); return true; };
                window.alert = function(msg) { window.interceptedPopups.push("[Alert] " + msg); return true; };
            }
            if (window.interceptedPopups.length > 0) {
                results = window.interceptedPopups.slice();
                window.interceptedPopups = [];
            }
            try {
                let buttons = document.querySelectorAll('button, a.btn');
                for (let btn of buttons) {
                    let text = (btn.innerText || '').trim().toUpperCase();
                    if (['確定', '確認', '關閉', '我知道了', 'OK'].includes(text)) {
                        if (btn.offsetParent !== null) {
                            let container = btn.closest('.ngdialog, .modal, .popup-container');
                            let content = container ? container.innerText.replace(/\\n/g, ' ').trim() : "未知網頁彈窗";
                            btn.click();
                            results.push("[HTML] " + content);
                            break;
                        }
                    }
                }
            } catch(e) {}
            return results.length > 0 ? results : null;
        })();
        """
        try:
            caught_msgs = await self.tab.evaluate(js_unified_check)
            if caught_msgs and isinstance(caught_msgs, list):
                for msg in caught_msgs:
                    clean_msg = str(msg.get('value', msg)
                                    if isinstance(msg, dict) else msg)
                    print(f">>> [系統攔截] 🛡️ 成功攔截並點掉彈窗！內容：「{clean_msg}」")

                print(">>> [系統] 💥 觸發防卡死機制：瞬間解鎖所有狀態，交由系統重整...")
                self.is_ticket_assigned = False
                self.is_terms_agreed = False
                self.is_captcha_solved = False
                self.is_reg_next_clicked = False
                self.is_printing_assign = False
                self.is_printing_spinner = False
                self.has_seen_spinner = False

                # 發動 JS 重整防卡死
                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass

                return True
        except Exception as e:
            pass
        return False

    def get_actual_wait_time(self):
        """[核心模組] 獲取實際等待秒數（支援讀取設定檔的隨機秒數開關與範圍）"""
        advanced_conf = self.config.get("advanced", {})
        base_wait = getattr(self, 'refresh_sec', 0.2)
        if base_wait <= 0:
            base_wait = 0.2

        is_random = advanced_conf.get("auto_reload_random_mode", False)
        if not is_random:
            return base_wait

        import random
        try:
            rand_range = float(advanced_conf.get(
                "auto_reload_random_range", 1.0))
        except:
            rand_range = 1.0

        return round(base_wait + random.uniform(0, rand_range), 2)

    async def reload_settings(self):
        """[KKTIX] 動態讀取 GUI 指定的設定檔路徑"""
        import json
        import os

        settings_path = getattr(self, 'settings_path', 'settings.json')

        try:
            if not os.path.exists(settings_path):
                return

            with open(settings_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)

            # 更新字典內容
            if "area_auto_select" in new_config:
                self.config["area_auto_select"] = new_config["area_auto_select"]
            if "advanced" in new_config:
                self.config["advanced"] = new_config["advanced"]
            if "kktix" in new_config:
                self.config["kktix"] = new_config["kktix"]
            if "keyword_exclude" in new_config:
                self.config["keyword_exclude"] = new_config["keyword_exclude"]
            if "ticket_number" in new_config:
                self.config["ticket_number"] = new_config["ticket_number"]
                self.ticket_number = int(new_config.get("ticket_number", 1))

            # 更新重整時間
            if "refresh_sec" in new_config:
                self.refresh_sec = float(new_config["refresh_sec"])
            elif "advanced" in new_config and "auto_reload_page_interval" in new_config["advanced"]:
                self.refresh_sec = float(
                    new_config["advanced"]["auto_reload_page_interval"])

            current_refresh = getattr(self, 'refresh_sec', 0.2)

            # 🔥 優化：從路徑中抓出純檔名 (例如 settings-A.json)，讓 Log 看起來更清楚
            filename = os.path.basename(settings_path)
            print(
                f">>> [系統] 進入活動頁面！已套用最新設定 ({filename} | 目標: {self.ticket_number} 張 | 失敗重整: {current_refresh} 秒)")

        except Exception as e:
            # print(f">>> [DEBUG] KKTIX reload_settings 出錯: {e}")
            pass
# ==========================================
# [KKTIX售票]
# ==========================================


class MelonBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        import os
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # 狀態變數鎖
        self.is_date_time_selected = False
        self.is_popup_opened = False
        self.is_area_selected = False
        self.is_seat_selected = False
        self.is_telegram_sent = False

        # 🔥 新增：驗證碼通知鎖，避免連續狂發訊息
        self.is_captcha_notified = False

        # 用來存放彈出視窗的 tab 物件
        self.popup_tab = None
        self.popup_opened_time = 0  # 🔥 紀錄彈窗開啟的時間

    async def send_telegram_message(self, message):
        """發送 Telegram 通知 (還原完整 Log 與錯誤捕捉版)"""
        # 1. 檢查設定是否存在且啟用
        if not self.config or "advanced" not in self.config:
            return
        if not self.config["advanced"].get("telegram_enable", False):
            return

        bot_token = self.config["advanced"].get("telegram_bot_token", "")
        chat_id = self.config["advanced"].get("telegram_chat_id", "")

        if not bot_token or not chat_id:
            print(">>> [系統] Telegram 設定不完整，跳過通知")
            return

        # 2. 定義發送任務
        def _send():
            import requests
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, data=payload, timeout=6)
                if response.status_code == 200:
                    print(">>> [系統] 📱 Telegram 通知發送成功！")
                else:
                    print(f">>> [系統] ⚠️ Telegram 發送失敗: {response.text}")
            except Exception as e:
                print(f">>> [系統] ❌ Telegram 連線錯誤: {e}")

        # 3. 將 requests 丟到背景執行，不卡死主執行緒
        import asyncio
        asyncio.create_task(asyncio.to_thread(_send))

    async def run(self):
        print(f">>> [Melon Ticket] 機器人啟動！(目標張數: {self.ticket_number})")
        import os
        import time
        import asyncio

        while True:
            try:
                # 1. 暫停攔截
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                # 2. 處理彈出視窗 (Popup Window)
                tab_count = len(self.driver.tabs)
                if tab_count > 1 and not self.is_popup_opened:
                    print(">>> [系統] 偵測到彈出視窗！正在將視角切換至搶票小視窗...")
                    self.popup_tab = self.driver.tabs[-1]
                    self.is_popup_opened = True
                    self.popup_opened_time = time.time()  # 🔥 開始計時
                    await asyncio.sleep(1)

                # 🔥 修正 1：偵測彈窗關閉，徹底重置進度鎖定
                elif tab_count == 1 and self.is_popup_opened:
                    print(">>> [系統] ⚠️ 彈出視窗已關閉！已清除舊視窗紀錄並解鎖狀態...")
                    self.is_popup_opened = False
                    self.popup_tab = None

                    # 【關鍵解鎖 1】：重置視窗內部的進度！
                    self.is_area_selected = False
                    self.is_seat_selected = False
                    self.is_telegram_sent = False  # 重置 TG 鎖
                    self.is_captcha_notified = False  # 🔥 重置驗證碼通知鎖

                    # 【關鍵解鎖 2】：這行解開，只要視窗不見，就會自動重點 Get Tickets
                    self.is_date_time_selected = False

                # 🔥 新增功能：20分鐘 (1200秒) 強制關閉彈窗重刷機制
                if self.is_popup_opened and self.popup_tab:
                    if time.time() - self.popup_opened_time > 1800:
                        print(
                            ">>> [系統] ⏱️ 彈窗停留超過 30 分鐘！為了防止 Melon 伺服器斷線，正在強制重啟...")
                        try:
                            await self.popup_tab.close()
                        except:
                            pass
                        self.is_popup_opened = False
                        self.popup_tab = None
                        self.is_area_selected = False
                        self.is_seat_selected = False
                        self.is_date_time_selected = False
                        self.is_captcha_notified = False  # 🔥 重置驗證碼通知鎖
                        continue  # 直接進入下一個迴圈，觸發重開邏輯

                active_tab = self.popup_tab if self.is_popup_opened else self.tab

                # 3. 獲取網址
                current_url = await active_tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue
                # ==========================================

                # 🔥 修正 2：完美 F5 重新整理偵測術
                if '/PERFORMANCE/INDEX.HTM' in current_url.upper():
                    is_fresh = await active_tab.evaluate("typeof window.maxbot_reloaded === 'undefined'")
                    if is_fresh:
                        await active_tab.evaluate("window.maxbot_reloaded = true")
                        if getattr(self, 'is_date_time_selected', False):
                            print(">>> [系統] 🔄 偵測到網頁重新載入！已為您解開日期與 ENTER 鎖！")
                            self.is_date_time_selected = False
                            self.is_area_selected = False
                            self.is_seat_selected = False
                            self.is_captcha_notified = False  # 🔥 重置驗證碼通知鎖

                if current_url != getattr(self, 'last_url', ''):
                    print(f"偵測到頁面切換: {current_url}")
                    self.last_url = current_url

                # 4. 分發任務
                await self.dispatch_action(current_url, active_tab)

            except Exception as e:
                # 建議在開發/除錯期間把錯誤印出來，才不會發生「默默壞掉」找不到原因的狀況
                # print(f">>> [迴圈錯誤] {e}")
                pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, url, active_tab):
        """Melon Ticket 任務分發中心"""
        upper_url = url.upper()

        if '/PERFORMANCE/INDEX.HTM' in upper_url:
            if not getattr(self, 'is_date_time_selected', False):
                await self.select_date_and_time(active_tab)

        elif '/RESERVATION/POPUP' in upper_url:
            # 0. 全時雷達：每次都即時檢查驗證碼是否擋路
            captcha_status = await self.check_and_solve_captcha(active_tab)
            if captcha_status == "BLOCKING":
                return

            # 1. 選區塊
            if not getattr(self, 'is_area_selected', False):
                await self.select_area(active_tab)

            # 2. 刷座位
            elif not getattr(self, 'is_seat_selected', False):
                await self.select_seat(active_tab)

    async def check_and_solve_captcha(self, active_tab):
        """[Melon 第二階段前置] 實體可見度偵測與驗證碼破解"""
        import asyncio

        # 核心 JS 邏輯：檢查、攔截警告、填寫狀態、重新整理
        js_captcha = """
        (function() {
            try {
                let docMain = document;
                let frame = document.getElementById('oneStopFrame');
                let docFrame = frame ? frame.contentWindow.document : null;

                if (!window._alertHooked) {
                    window.alert = function(msg) { window._lastAlert = msg; };
                    window._alertHooked = true;
                }
                if (docFrame && !frame.contentWindow._alertHooked) {
                    frame.contentWindow.alert = function(msg) { frame.contentWindow._lastAlert = msg; };
                    frame.contentWindow._alertHooked = true;
                }

                let alertMsg = window._lastAlert || (docFrame && frame.contentWindow._lastAlert);
                let reloadBtn = docMain.getElementById('btnReload') || (docFrame && docFrame.getElementById('btnReload'));

                // 【需求 3】送出後錯誤警告：自動點擊 Re Flash
                if (alertMsg) {
                    window._lastAlert = null;
                    if (docFrame) frame.contentWindow._lastAlert = null;
                    window._captchaSubmitted = false;
                    if (reloadBtn) reloadBtn.click();
                    return "ALERT_CAUGHT|" + alertMsg;
                }

                let captchaImg = docMain.getElementById('captchaImg') || (docFrame && docFrame.getElementById('captchaImg'));
                let certBox = docMain.getElementById('certification') || (docFrame && docFrame.getElementById('certification'));

                let isVisible = false;
                if (certBox && certBox.offsetWidth > 0 && certBox.offsetHeight > 0) {
                    let style = window.getComputedStyle(certBox);
                    if (style.display !== 'none' && style.opacity !== '0' && style.visibility !== 'hidden') {
                        isVisible = true;
                    }
                }

                if (!isVisible) {
                    window._captchaSubmitted = false;
                    return "NO_CAPTCHA";
                }

                if (window._captchaSubmitted) {
                    if (Date.now() - window._submitTime > 2500) {
                        window._captchaSubmitted = false;
                        if (reloadBtn) reloadBtn.click();
                        return "STUCK_RELOAD";
                    }
                    return "SUBMITTING_WAIT";
                }

                if (!captchaImg || !captchaImg.src) return "BLOCKING";

                return "CAPTCHA_PENDING|" + captchaImg.src;

            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        try:
            result = await active_tab.evaluate(js_captcha)

            if isinstance(result, str):
                if result == "NO_CAPTCHA":
                    self.is_captcha_notified = False
                    self.ocr_fail_count = 0  # 🔥 成功通過時，將失敗計數器歸零

                    if not getattr(self, 'captcha_cleared_printed', False):
                        # print(">>> [Melon] ✅ 驗證碼視窗已確認消失，準備執行區域點擊...")
                        self.captcha_cleared_printed = True

                    return "PASS"

                elif result.startswith("ALERT_CAUGHT|"):
                    msg = result.split("|")[1]
                    print(
                        f">>> [Melon] 🛑 發現警告: 【{msg}】已自動點擊 [Re Flash] 重新取得驗證碼！")
                    self.last_captcha_src = ""
                    await asyncio.sleep(0.5)
                    return "BLOCKING"

                elif result == "SUBMITTING_WAIT":
                    return "BLOCKING"

                elif result == "STUCK_RELOAD":
                    print(">>> [Melon] ⚠️ 送出後無回應超過 2.5 秒，已自動點擊 [Re Flash] 刷新！")
                    self.last_captcha_src = ""
                    await asyncio.sleep(0.5)
                    return "BLOCKING"

                elif result.startswith("CAPTCHA_PENDING|"):
                    self.captcha_cleared_printed = False
                    base64_src = result.split("|")[1]

                    if getattr(self, 'last_captcha_src', '') == base64_src:
                        if not hasattr(self, 'captcha_wait_count'):
                            self.captcha_wait_count = 0
                        self.captcha_wait_count += 1
                        await asyncio.sleep(0.1)
                        return "BLOCKING"

                    self.last_captcha_src = base64_src
                    print(">>> [Melon] 🛡️ 擷取到驗證碼，啟動 ddddocr...")

                    try:
                        import base64
                        import re
                        from io import BytesIO
                        from PIL import Image

                        if not hasattr(self, 'custom_ocr'):
                            import ddddocr
                            self.custom_ocr = ddddocr.DdddOcr(show_ad=False)

                        img_data = base64_src.split(
                            ',')[1] if ',' in base64_src else base64_src
                        raw_img_bytes = base64.b64decode(img_data)

                        try:
                            img = Image.open(BytesIO(raw_img_bytes))
                            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                                bg = Image.new('RGB', img.size,
                                               (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGBA')
                                bg.paste(img, mask=img.split()[3])
                                img = bg
                            else:
                                img = img.convert('RGB')

                            buffered = BytesIO()
                            img.save(buffered, format="PNG")
                            ocr_img_bytes = buffered.getvalue()
                        except Exception as img_err:
                            ocr_img_bytes = raw_img_bytes

                        raw_text = self.custom_ocr.classification(
                            ocr_img_bytes)
                        replace_map = {
                            '0': 'O', '1': 'I', '2': 'Z', '3': 'B', '4': 'A',
                            '5': 'S', '6': 'G', '7': 'T', '8': 'B', '9': 'P'
                        }
                        corrected_text = ''.join(
                            [replace_map.get(char, char) for char in raw_text.upper()])
                        clean_text = re.sub(r'[^A-Z]', '', corrected_text)

                        print(
                            f">>> [Melon] 🤖 OCR 辨識結果: 【{clean_text}】 (原始: {raw_text})")

                        if len(clean_text) == 6:
                            self.ocr_fail_count = 0  # 🔥 成功辨識出 6 碼，重置計數器
                            fill_js = f"""
                            (function() {{
                                let docMain = document;
                                let frame = document.getElementById('oneStopFrame');
                                let docFrame = frame ? frame.contentWindow.document : null;

                                let input = docMain.getElementById('label-for-captcha') || (docFrame && docFrame.getElementById('label-for-captcha'));
                                let btnComplete = docMain.getElementById('btnComplete') || (docFrame && docFrame.getElementById('btnComplete'));

                                if (input && btnComplete) {{
                                    let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                                    if (nativeInputValueSetter) {{
                                        nativeInputValueSetter.call(
                                            input, '{clean_text}');
                                    }} else {{
                                        input.value = '{clean_text}';
                                    }}

                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));

                                    btnComplete.click();
                                    window._captchaSubmitted = true;
                                    window._submitTime = Date.now();
                                    return true;
                                }}
                                return false;
                            }})();
                            """
                            success = await active_tab.evaluate(fill_js)
                            if success:
                                print(
                                    f">>> [Melon] 🚀 已將【{clean_text}】輸入格子並點擊 [輸入完成]！等待伺服器驗證...")
                            else:
                                print(
                                    f">>> [Melon] ⚠️ 找不到 #label-for-captcha 或 #btnComplete 元素！")

                            return "BLOCKING"

                        # 🛑 【關鍵更新區塊】：字數不符時，啟動 4 次停損重整邏輯
                        else:
                            # 讀取當前失敗次數，並 +1
                            fail_count = getattr(self, 'ocr_fail_count', 0) + 1
                            self.ocr_fail_count = fail_count

                            if fail_count <= 4:
                                print(
                                    f">>> [Melon] ⚠️ 辨識字數有誤 (長度: {len(clean_text)}，第 {fail_count}/4 次)，自動點擊 [Re Flash] 換圖...")

                                # 發送 JS 直接點擊重整按鈕
                                reload_js = """
                                (function() {
                                    let docMain = document;
                                    let frame = document.getElementById('oneStopFrame');
                                    let docFrame = frame ? frame.contentWindow.document : null;
                                    let reloadBtn = docMain.getElementById('btnReload') || (docFrame && docFrame.getElementById('btnReload'));
                                    if (reloadBtn) reloadBtn.click();
                                })();
                                """
                                await active_tab.evaluate(reload_js)

                                # 清空圖片紀錄，讓下一圈迴圈去抓新出來的驗證碼
                                self.last_captcha_src = ""
                                await asyncio.sleep(0.5)
                            else:
                                print(
                                    f">>> [Melon] ❌ 連續 {fail_count} 次辨識失敗！已達停損點，等待人工接管...")
                                if hasattr(self, 'send_telegram_message') and not getattr(self, 'is_captcha_notified', False):
                                    await self.send_telegram_message("🚨 <b>[Melon Ticket] 🛑 驗證碼辨識連續失敗！</b>\n\n系統已達 4 次自動重試上限，請立即留意畫面，進行【手動接管輸入】！")
                                    self.is_captcha_notified = True

                            return "BLOCKING"

                    except Exception as ocr_err:
                        print(f">>> [Melon] ⚠️ OCR 執行錯誤: {ocr_err}")
                        return "BLOCKING"

        except Exception as e:
            print(f">>> [例外] 驗證碼檢查過程發生錯誤: {e}")

        return "PASS"

    async def select_date_and_time(self, active_tab):
        """[Melon 第一階段] 選擇日期、場次 (修復 Melon 預設選取陷阱與排序模式)"""

        reload_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))
        if reload_interval <= 0:
            reload_interval = 0.5

        raw_keyword = self.config.get("date_auto_select", {}).get(
            "date_keyword", "").strip()
        # 🔥 新增：讀取 GUI 上的日期排序模式
        date_mode = self.config.get("date_auto_select", {}).get(
            "mode", "top-down").lower()

        import json
        keyword_list = []
        if len(raw_keyword) > 0:
            try:
                if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                    keyword_list = json.loads(raw_keyword)
                else:
                    keyword_list = json.loads("[" + raw_keyword + "]")
            except:
                keyword_list = [raw_keyword]
        else:
            keyword_list = [""]

        js_keywords = json.dumps(keyword_list, ensure_ascii=False)

        js_script = f"""
        (function() {{
            try {{
                // 全域攔截 Alert 與 Confirm
                if (!window._alertHooked_datetime) {{
                    window.originalAlert = window.alert;
                    window.alert = function(msg) {{ window._lastAlert = msg; }};
                    window.originalConfirm = window.confirm;
                    window.confirm = function(msg) {{ window._lastAlert = msg; return true; }}; 
                    window._alertHooked_datetime = true;
                }}
                
                if (window._lastAlert) {{
                    let msg = window._lastAlert;
                    window._lastAlert = null;
                    return "ALERT_CAUGHT|" + msg;
                }}

                const keywords = {js_keywords};
                const mode = "{date_mode}";

                let ticketBtn = document.querySelector('button.reservationBtn');
                let onSaleBox = document.querySelector('#box_tkt_txt');

                // 1. 尚未開賣的倒數狀態
                if (!ticketBtn) {{
                    if (onSaleBox) {{
                        let boxText = onSaleBox.innerText || "";
                        if (boxText.includes('On-sale') || boxText.includes('预订开启') || boxText.includes('On-sale') || boxText.includes('予約開始')) {{
                            return "REFRESH_PAGE";
                        }}
                    }}
                    if (!onSaleBox) return "WAITING_DOM";
                }}

                let loader = document.querySelector('#loading') || document.querySelector('.v-progress-circular');
                if (loader && window.getComputedStyle(loader).display !== 'none') return "WAITING_DOM";

                // 2. 🔥 選擇日期 (無視預設的 .on，嚴格篩選)
                let days = Array.from(document.querySelectorAll('#list_date li'));
                if (days.length === 0) return "WAITING_DOM";

                let validDates = [];
                if (keywords.length === 0 || keywords[0] === "") {{
                    validDates = days;
                }} else {{
                    for (let d of days) {{
                        let text = (d.innerText || "").toUpperCase().replace(/,/g, '');
                        let dataDay = d.getAttribute('data-perfday');
                        if (dataDay && dataDay.length === 8) {{
                            let y = dataDay.substring(0, 4);
                            let m_str = dataDay.substring(4, 6);
                            let d_str = dataDay.substring(6, 8);
                            let m_int = parseInt(m_str, 10).toString();
                            let d_int = parseInt(d_str, 10).toString();
                            text += ` ${{dataDay}} ${{y}}/${{m_str}}/${{d_str}} ${{y}}/${{m_int}}/${{d_int}} ${{m_str}}/${{d_str}} ${{m_int}}/${{d_int}} ${{m_int}}月${{d_int}}日 ${{m_str}}${{d_str}}`;
                        }}

                        let isMatch = false;
                        for (let k of keywords) {{
                            let target_kws = k.trim().toUpperCase().split(/\\s+/).filter(w => w.length > 0);
                            let currentGroupMatch = true;
                            for (let w of target_kws) {{
                                if (!text.includes(w)) {{ currentGroupMatch = false; break; }}
                            }}
                            if (currentGroupMatch) {{ isMatch = true; break; }}
                        }}
                        if (isMatch) validDates.push(d);
                    }}
                }}

                if (validDates.length === 0) return "NO_MATCH_DATE";

                // 🔥 實裝日期排序邏輯
                let targetDate = validDates[0];
                if (mode.includes("random") || mode.includes("隨機")) {{
                    targetDate = validDates[Math.floor(Math.random() * validDates.length)];
                }} else if (mode.includes("bottom") || mode.includes("下")) {{
                    targetDate = validDates[validDates.length - 1];
                }} else if (mode.includes("center") || mode.includes("中")) {{
                    targetDate = validDates[Math.floor(validDates.length / 2)];
                }}

                // 如果計算出的目標日期「沒有被選中」，才發動點擊
                if (!targetDate.classList.contains('on')) {{
                    let dateBtn = targetDate.querySelector('button');
                    if (dateBtn) {{
                        dateBtn.click();
                        return "CLICK_DATE|" + (targetDate.innerText || "").replace(/\\n/g, ' ').trim();
                    }}
                }}

                // 3. 🔥 選擇時間 (同樣重構：找出目標時間，沒被選中才點)
                let times = Array.from(document.querySelectorAll('#list_time li'));
                if (times.length === 0) return "WAITING_TIME";

                let validTimes = [];
                if (keywords.length === 0 || keywords[0] === "") {{
                    validTimes = times;
                }} else {{
                    for (let t of times) {{
                        let text = (t.innerText || "").toUpperCase();
                        let timeMatch = text.match(/(\\d{{2}}):(\\d{{2}})\\s*(AM|PM)/);
                        if (timeMatch) {{
                            let hr = parseInt(timeMatch[1], 10);
                            let min = timeMatch[2];
                            let ampm = timeMatch[3];
                            if (ampm === 'PM' && hr < 12) hr += 12;
                            if (ampm === 'AM' && hr === 12) hr = 0;
                            let hr24 = hr.toString().padStart(2, '0');
                            text += ` ${{hr24}}:${{min}} ${{hr24}}${{min}}`;
                        }}

                        let isMatch = false;
                        for (let k of keywords) {{
                            let target_kws = k.trim().toUpperCase().split(/\\s+/).filter(w => w.length > 0);
                            let currentGroupMatch = true;
                            for (let w of target_kws) {{
                                if (!text.includes(w)) {{ currentGroupMatch = false; break; }}
                            }}
                            if (currentGroupMatch) {{ isMatch = true; break; }}
                        }}
                        if (isMatch) validTimes.push(t);
                    }}
                }}

                if (validTimes.length === 0) validTimes = times; // 時間沒中，降級選所有時間

                let targetTime = validTimes[0];
                if (mode.includes("random") || mode.includes("隨機")) {{
                    targetTime = validTimes[Math.floor(Math.random() * validTimes.length)];
                }} else if (mode.includes("bottom") || mode.includes("下")) {{
                    targetTime = validTimes[validTimes.length - 1];
                }} else if (mode.includes("center") || mode.includes("中")) {{
                    targetTime = validTimes[Math.floor(validTimes.length / 2)];
                }}

                if (!targetTime.classList.contains('on')) {{
                    let timeBtn = targetTime.querySelector('button') || targetTime.children[0];
                    if (timeBtn) {{
                        timeBtn.click();
                        return "CLICK_TIME|" + (targetTime.innerText || "").replace(/\\n/g, ' ').trim();
                    }}
                }}

                // 4. 點擊 / 聚焦送出按鈕
                if (ticketBtn) {{
                    const isBtnDisabled = ticketBtn.disabled || ticketBtn.classList.contains('disabled') || ticketBtn.classList.contains('disable');
                    if (!isBtnDisabled) {{
                        ticketBtn.focus();
                        return "FOCUS_SUBMIT";
                    }}
                }}

                return "WAITING_BTN";

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_script)
            import asyncio

            if isinstance(result, str):
                if result == "REFRESH_PAGE":
                    print(
                        f">>> [Melon] ⏳ 偵測到「尚未開賣 (預訂開啟)」，{reload_interval} 秒後自動重新整理...")
                    await asyncio.sleep(reload_interval)
                    await active_tab.reload()

                elif result.startswith("ALERT_CAUGHT|"):
                    msg = result.split("|", 1)[1]
                    print(f"\n>>> [Melon-日期頁] 🛑 攔截到系統彈窗：【{msg}】！已自動點擊確認過關！")
                    await asyncio.sleep(0.2)

                elif result == "WAITING_DOM" or result == "WAITING_TIME":
                    await asyncio.sleep(0.1)

                elif result == "NO_MATCH_DATE":
                    if not hasattr(self, 'date_warn_count'):
                        self.date_warn_count = 0
                    self.date_warn_count += 1
                    if self.date_warn_count % 20 == 0:
                        print(f">>> [Melon] ⚠️ 找不到符合條件「{raw_keyword}」的日期！")
                    await asyncio.sleep(0.1)

                elif result.startswith("CLICK_DATE|"):
                    date_name = result.split("|")[1]
                    print(f">>> [Melon] 📅 已鎖定目標日期【{date_name}】並發動點擊！等待場次時間...")
                    await asyncio.sleep(0.3)

                elif result.startswith("CLICK_TIME|"):
                    time_name = result.split("|")[1]
                    print(
                        f">>> [Melon] ⏰ 已鎖定目標時間【{time_name}】並發動點擊！準備 Get Tickets...")
                    await asyncio.sleep(0.3)

                elif result == "FOCUS_SUBMIT":
                    print(">>> [Melon] 🚀 日期確認完畢！發送底層「實體鍵盤 Enter」！")

                    import nodriver.cdp.input_ as input_cdp
                    await active_tab.send(input_cdp.dispatch_key_event(
                        type_="keyDown",
                        windows_virtual_key_code=13,
                        key="Enter",
                        text="\r"
                    ))
                    await active_tab.send(input_cdp.dispatch_key_event(
                        type_="keyUp",
                        windows_virtual_key_code=13,
                        key="Enter"
                    ))

                    self.is_date_time_selected = True
                    await asyncio.sleep(1.0)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 發生內部 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_date_and_time 發生例外: {e}")

    async def select_area(self, active_tab):
        """[Melon 第二階段] 神級字尾狙擊 + 自動輪詢記憶版 (補齊 Confirm 攔截)"""
        import json
        import time
        import random
        import asyncio

        if not hasattr(self, 'cooldown_base'):
            self.cooldown_base = 15
        if not hasattr(self, 'cooldown_until'):
            self.cooldown_until = 0
        if time.time() < self.cooldown_until:
            await asyncio.sleep(0.5)
            return

        raw_keyword = self.config.get("area_auto_select", {}).get(
            "area_keyword", "").strip()
        area_mode = self.config.get("area_auto_select", {}).get(
            "mode", "top-down").lower()
        base_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))

        is_random_mode = self.config.get("advanced", {}).get(
            "auto_reload_random_mode", False)
        jitter = float(self.config.get("advanced", {}).get(
            "auto_reload_random_range", "0.2")) if is_random_mode else 0.0

        keyword_list = []
        if len(raw_keyword) > 0:
            try:
                if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                    keyword_list = json.loads(raw_keyword)
                else:
                    keyword_list = json.loads("[" + raw_keyword + "]")
            except:
                keyword_list = [raw_keyword]
        else:
            keyword_list = [""]

        js_keywords = json.dumps(keyword_list, ensure_ascii=False)

        js_area = f"""
        (function() {{
            try {{
                let frame = document.getElementById('oneStopFrame');
                if (!frame) return "NO_FRAME";
                let doc = frame.contentWindow.document;

                // 🔥 新增：補齊 Confirm 的攔截
                if (!frame.contentWindow._alertHooked_area) {{
                    frame.contentWindow.originalAlert = frame.contentWindow.alert;
                    frame.contentWindow.alert = function(msg) {{ frame.contentWindow._lastAlert = msg; }};
                    frame.contentWindow.originalConfirm = frame.contentWindow.confirm;
                    frame.contentWindow.confirm = function(msg) {{ frame.contentWindow._lastAlert = msg; return true; }};
                    frame.contentWindow._alertHooked_area = true;
                }}
                if (frame.contentWindow._lastAlert) {{
                    let msg = frame.contentWindow._lastAlert;
                    frame.contentWindow._lastAlert = "";
                    return "COOLDOWN|" + msg;
                }}

                let loader = doc.querySelector('.seatLoading');
                if (loader && window.getComputedStyle(loader).display !== 'none') return "LOADING";

                const normalizeText = (str) => {{
                    return (str || "").toUpperCase()
                        .replace(/[區구역]/g, ' ')
                        .replace(/[^A-Z0-9\u4e00-\u9fa5\uac00-\ud7a3]/g, ' ')
                        .replace(/\s+/g, ' ').trim();
                }};

                const rawKeywords = {js_keywords};
                const keywords = rawKeywords.map(k => normalizeText(k)).filter(k => k.length > 0);
                const mode = "{area_mode}";

                let sectionToOpen = doc.querySelector(".seat_name:not(.open)");
                if (sectionToOpen) sectionToOpen.click();

                // ==========================================
                // 1. 一般區域比對 (area_tit)
                // ==========================================
                let areaTits = doc.querySelectorAll(".area_tit");
                let validAreas = [];

                if (areaTits.length > 0) {{
                    for (let i = 0; i < areaTits.length; i++) {{
                        let clickTarget = areaTits[i].closest('li') || areaTits[i].parentElement;
                        let rawText = areaTits[i].innerText || areaTits[i].innerHTML;
                        let normText = normalizeText(rawText);
                        let paddedNormText = " " + normText + " ";

                        let isMatch = false;
                        if (keywords.length === 0) {{
                            isMatch = true;
                        }} else {{
                            for (let k of keywords) {{
                                let paddedKeyword = " " + k + " ";
                                if (paddedNormText.endsWith(paddedKeyword)) {{
                                    isMatch = true; break;
                                }}
                                if (k.length > 2 && paddedNormText.includes(paddedKeyword)) {{
                                    isMatch = true; break;
                                }}
                            }}
                        }}

                        if (isMatch) {{
                            validAreas.push({{
                                target: clickTarget,
                                text: rawText.replace(/<[^>]*>?/gm, '').trim()
                            }});
                        }}
                    }}

                    if (validAreas.length > 0) {{
                        let selectedArea = null;
                        if (mode === "random") {{
                            let randomIndex = Math.floor(Math.random() * validAreas.length);
                            selectedArea = validAreas[randomIndex];
                        }} else {{
                            if (typeof window._melon_area_idx === 'undefined') window._melon_area_idx = 0;
                            selectedArea = validAreas[window._melon_area_idx %
                                validAreas.length];
                            window._melon_area_idx++;
                        }}

                        selectedArea.target.click();
                        return "AREA_CLICKED|" + selectedArea.text;
                    }}
                }}

                // ==========================================
                // 2. 零星票區比對 (partSeatGrade)
                // ==========================================
                let singleGrades = doc.querySelectorAll('#partSeatGrade > tr');
                if (singleGrades.length > 0) {{
                    let matchedGrades = [];
                    for (let g of singleGrades) {{
                        let rawText = g.innerText || "";
                        let normText = normalizeText(rawText);
                        let paddedNormText = " " + normText + " ";

                        let isMatch = false;
                        if (keywords.length === 0) {{
                            isMatch = true;
                        }} else {{
                            for (let k of keywords) {{
                                let paddedKeyword = " " + k + " ";
                                if (paddedNormText.endsWith(paddedKeyword) || (k.length > 2 && paddedNormText.includes(paddedKeyword))) {{
                                    isMatch = true; break;
                                }}
                            }}
                        }}
                        if (isMatch) matchedGrades.push(g);
                    }}

                    if (matchedGrades.length > 0) {{
                        let targetGrade = null;
                        if (mode === "random") {{
                            let randomIndex = Math.floor(Math.random() * matchedGrades.length);
                            targetGrade = matchedGrades[randomIndex];
                        }} else {{
                            if (typeof window._melon_grade_idx === 'undefined') window._melon_grade_idx = 0;
                            targetGrade = matchedGrades[window._melon_grade_idx %
                                matchedGrades.length];
                            window._melon_grade_idx++;
                        }}
                        targetGrade.click();
                        return "AREA_CLICKED|" + (targetGrade.innerText || "").replace(/\\n/g, ' ').trim();
                    }}
                }}

                return "WAITING_DOM";

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_area)

            if isinstance(result, str):
                if result.startswith("COOLDOWN|"):
                    msg = result.split("|")[1] if "|" in result else "不明錯誤"
                    print(f">>> [Melon] 🛑 觸發區域伺服器阻擋警告/視窗: 【{msg}】")
                    print(
                        f">>> [Melon] ❄️ 進入強制休息冷卻期 {self.cooldown_base} 秒...")
                    self.cooldown_until = time.time() + self.cooldown_base
                    self.cooldown_base *= 2
                    return

                elif result.startswith("AREA_CLICKED|"):
                    area_name = result.split("|")[1]
                    print(f">>> [Melon] 🎯 強制點擊區域更新：【{area_name}】！呼叫座位掃描...")

                    self.is_area_selected = True
                    self.cooldown_base = 15

                    human_delay = base_interval + \
                        random.uniform(-jitter, jitter)
                    human_delay = max(0.1, human_delay)
                    await asyncio.sleep(human_delay)

                elif result == "WAITING_DOM":
                    await asyncio.sleep(0.1)

                elif result in ["LOADING", "NO_FRAME"]:
                    if not hasattr(self, 'area_wait_count'):
                        self.area_wait_count = 0
                    self.area_wait_count += 1
                    if self.area_wait_count % 20 == 0:
                        print(">>> [Melon] ⏳ 區域資料載入中，持續極速掃描 DOM...")
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 區域選擇 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] select_area: {e}")

    async def select_seat(self, active_tab):
        """[Melon 第三階段] 掃描 SVG 抓取空位 (包含 Confirm 全域攔截)"""

        js_seat = """
        (function() {
            try {
                let frame = document.getElementById('oneStopFrame');
                if (!frame) return "NO_FRAME";
                let doc = frame.contentWindow.document;

                // 🔥 新增：確保座位層 iframe 中的 Confirm 與 Alert 都有攔截保護
                if (!frame.contentWindow._alertHooked_seat) {
                    frame.contentWindow.originalAlert = frame.contentWindow.alert;
                    frame.contentWindow.alert = function(msg) { frame.contentWindow._lastAlert = msg; };
                    frame.contentWindow.originalConfirm = frame.contentWindow.confirm;
                    // 同樣讓 confirm 自動回傳 true
                    frame.contentWindow.confirm = function(msg) { frame.contentWindow._lastAlert = msg; return true; };
                    frame.contentWindow._alertHooked_seat = true;
                }

                // 1. 攔截 Alert 或 Confirm (被別人搶走時常跳出的警告)
                if (frame.contentWindow._lastAlert) {
                    let msg = frame.contentWindow._lastAlert;
                    frame.contentWindow._lastAlert = null;
                    window._melon_seat_submitted = 0; // 解除等待鎖定
                    return "ALERT_CAUGHT|" + msg;
                }

                // 2. 🔥 驗證階段：判斷是否真的成功跳轉了
                if (window._melon_seat_submitted) {
                    let canvasStillExists = doc.getElementById("ez_canvas");
                    let isCanvasVisible = canvasStillExists && window.getComputedStyle(canvasStillExists).display !== 'none';

                    // 狀況 A：座位圖消失了，代表成功進入下一步(結帳或票價頁面)
                    if (!isCanvasVisible) {
                        window._melon_seat_submitted = 0;
                        return "SEAT_SUBMITTED_SUCCESS";
                    }

                    // 狀況 B：等了超過 2 秒座位圖都還在，代表被別人搶走但系統沒跳 Alert，或是卡住了
                    if (Date.now() - window._melon_seat_submitted > 2000) {
                        window._melon_seat_submitted = 0; // 重置鎖定
                        return "SEAT_TAKEN_RETRY";
                    }

                    // 狀況 C：還在 2 秒內，繼續等
                    return "WAITING_TRANSITION";
                }

                // 3. 檢查載入中動畫
                let loader = doc.querySelector('.seatLoading');
                if (loader && window.getComputedStyle(loader).display !== 'none') {
                    window._seatEmptyCount = 0;
                    return "LOADING";
                }

                let canvas = doc.getElementById("ez_canvas");
                if (!canvas) return "NO_SEAT";

                // 4. 尋找空位
                let seats = Array.from(canvas.querySelectorAll("rect, polygon, circle, path")).filter(s => {
                    let fill = s.getAttribute("fill");
                    if (!fill) return false;
                    let fUpper = fill.toUpperCase();
                    // 排除背景色與不可點選色
                    return fUpper !== "#DDDDDD" && fUpper !== "#CCCCCC" && fUpper !== "NONE" && fUpper !== "#FFFFFF";
                });

                if (seats.length === 0) {
                    if (!window._seatEmptyCount) window._seatEmptyCount = 0;
                    window._seatEmptyCount++;
                    if (window._seatEmptyCount > 5) {
                        window._seatEmptyCount = 0;
                        return "NO_SEAT";
                    }
                    return "WAITING_RECT";
                }

                window._seatEmptyCount = 0;
                let targetSeat = seats[0];

                // 發動點擊
                targetSeat.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: frame.contentWindow }));

                // 點擊下一步
                let nextBtn = doc.getElementById("nextTicketSelection") || doc.getElementById("btnNext");
                if (nextBtn) {
                    nextBtn.click();
                    // 🔥 標記送出時間，進入「跳轉驗證模式」
                    window._melon_seat_submitted = Date.now();
                    return "CLICKED_NEXT_WAITING";
                }

                return "WAITING_BTN";

            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        try:
            result = await active_tab.evaluate(js_seat)
            import asyncio

            if isinstance(result, str):

                if result == "CLICKED_NEXT_WAITING":
                    print(">>> [Melon] 🖱️ 已點選座位並送出，等待伺服器驗證...")
                    await asyncio.sleep(0.1)

                elif result == "WAITING_TRANSITION":
                    if not hasattr(self, 'verify_wait_count'):
                        self.verify_wait_count = 0
                    self.verify_wait_count += 1
                    if self.verify_wait_count % 10 == 0:
                        print(">>> [Melon] ⏳ 伺服器驗證中，確認是否成功進入結帳...")
                    await asyncio.sleep(0.1)

                # 🔥 真正成功：確定畫面跳轉了才發通知
                elif result == "SEAT_SUBMITTED_SUCCESS":
                    print(">>> [Melon] 🎉 驗證通過！成功突破座位防線！進入結帳畫面...")
                    self.is_seat_selected = True

                    if not getattr(self, 'is_telegram_sent', False):
                        await self.send_telegram_message(" <b>[Melon Ticket]</b> 🎉 搶票成功！\n機器人已成功點擊空位並送出，請立刻回視窗查看結帳！")
                        self.is_telegram_sent = True
                    await asyncio.sleep(0.5)

                # 🔥 假成功/無回應：直接退回重刷
                elif result == "SEAT_TAKEN_RETRY":
                    print(">>> [Melon] ⚠️ 點擊送出後無反應 (座位可能已被秒殺)！退回重新選區...")
                    self.is_area_selected = False
                    self.is_seat_selected = False
                    await asyncio.sleep(0.2)

                # 攔截警告
                elif result.startswith("ALERT_CAUGHT|"):
                    msg = result.split("|", 1)[1]
                    print(f"\n>>> [系統] ⚠️ 攔截到 Melon 系統警告/視窗：【{msg}】")
                    print(">>> [系統] 🔄 座位已被搶走或失效！已自動點擊確認，準備退回重新點選區域...")
                    self.is_area_selected = False
                    self.is_seat_selected = False
                    await asyncio.sleep(0.2)

                # 真的沒位子
                elif result == "NO_SEAT":
                    print(">>> [Melon] ❌ 該區目前無空位！退回重選區域...")
                    self.is_area_selected = False
                    self.is_seat_selected = False

                    base_interval = float(self.config.get("advanced", {}).get(
                        "auto_reload_page_interval", 0.5) or 0.5)
                    is_random_mode = self.config.get("advanced", {}).get(
                        "auto_reload_random_mode", False)
                    import random
                    jitter = float(self.config.get("advanced", {}).get(
                        "auto_reload_random_range", 0.2) or 0.2) if is_random_mode else 0.0

                    human_delay = base_interval + \
                        random.uniform(-jitter, jitter)
                    human_delay = max(0.1, human_delay)
                    await asyncio.sleep(human_delay)

                elif result in ["LOADING", "WAITING_SVG", "WAITING_RECT", "WAITING_BTN", "NO_FRAME"]:
                    if not hasattr(self, 'seat_wait_count'):
                        self.seat_wait_count = 0
                    self.seat_wait_count += 1
                    if self.seat_wait_count % 5 == 0:
                        print(f">>> [Melon] ⏳ 座位圖掃描中，狀態: {result} ...")
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 找座位 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] select_seat: {e}")


# ==========================================
# [Melon Ticket 搶票]
# ==========================================

class BillboardLiveBot:

    def __init__(self, driver, config):
        """初始化設定與狀態鎖"""
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 暫停機制 (讀取全域暫停檔案)
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # ==========================================
        # 🚦 狀態變數鎖 (對應你的 5 個流程)
        # ==========================================
        self.is_event_selected = False   # 1. 場次是否已選
        self.is_date_selected = False    # 2. 日期是否已選
        self.is_data_filled = False      # 3. 資料是否已填寫送出
        self.is_seat_selected = False    # 4. 座位是否已選
        self.is_success_notified = False  # 5. 是否已發送成功通知

    async def run(self):
        """總控主迴圈：持續監聽網址與分發任務"""
        print(f">>> [BillboardLive] 機器人啟動！(目標張數: {self.ticket_number})")

        while True:
            try:
                # 1. 暫停攔截 (手動控制暫停/繼續)
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                # 2. 獲取當前網址
                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                # 3. 網址切換日誌 (方便除錯)
                if current_url != getattr(self, 'last_url', ''):
                    print(f"\n>>> [系統] 偵測到頁面切換: {current_url}")
                    self.last_url = current_url

                    # 💡 小技巧：如果發現退回首頁，可以自動重置所有狀態鎖
                    # if "首頁特徵網址" in current_url:
                    #     self.reset_all_states()

                # 4. 任務分發
                await self.dispatch_action(current_url, self.tab)

            except Exception as e:
                err_msg = str(e)
                # 攔截常見的底層斷線錯誤 (瀏覽器跳轉或重整時的瞬間斷線)，直接靜音略過
                if "1225" in err_msg or "10061" in err_msg or "10054" in err_msg or "WinError" in err_msg:
                    pass
                # else:
                    # 只有真正不可預期的錯誤才印出來
                    # print(f">>> [主迴圈例外] BillboardLiveBot 發生錯誤: {e}")

            # 確保每次迴圈都有極短的休息，避免 CPU 飆高
            import asyncio
            await asyncio.sleep(0.05)

    async def dispatch_action(self, url, active_tab):
        """任務分發中心：根據網址特徵決定現在該做什麼"""
        upper_url = url.upper()

        # ==========================================
        # 流程 1：場次頁面 (包含 /EVENTS/ 且不含下一步的 /REGISTRATIONS/)
        # ==========================================
        if '/EVENTS/' in upper_url and '/REGISTRATIONS/' not in upper_url:

            # 🔥 退回首頁重置機制：如果我們身上帶著「已選日期/已填資料/已選位」的標記
            # 但網址卻在第一關，代表我們被系統踢出來，或是手動按了上一頁！
            if getattr(self, 'is_date_selected', False) or getattr(self, 'is_data_filled', False) or getattr(self, 'is_seat_selected', False):
                print(">>> [系統] 🔄 偵測到退回場次頁面！已強制解除所有任務鎖定，重新開始搶票！")
                self.is_event_selected = False
                self.is_date_selected = False
                self.is_data_filled = False
                self.is_seat_selected = False

            # 取消原本 Python 的 if not self.is_event_selected 擋箭牌
            # 讓程式永遠進入 select_event，由前端 JS 來判斷要不要點擊
            await self.select_event(active_tab)

        # ==========================================
        # 流程 2、3、4：日期 ➔ 資料 ➔ 座位 (因為網址都有 /REGISTRATIONS/)
        # ==========================================
        elif '/REGISTRATIONS/' in upper_url:
            # 這裡維持順序接關的狀態機不變
            if not getattr(self, 'is_date_selected', False):
                await self.select_date(active_tab)

            elif not getattr(self, 'is_data_filled', False):
                await self.fill_data(active_tab)

            elif not getattr(self, 'is_seat_selected', False):
                await self.select_seat(active_tab)

        # ==========================================
        # 流程 5：搶票成功 (結帳) 頁面
        # ==========================================
        elif '/ORDERS/' in upper_url or '/CHECKOUT/' in upper_url:
            if not getattr(self, 'is_success_notified', False):
                print(">>> [Billboard] 🎉 搶票大成功！進入結帳頁面！")
                self.is_success_notified = True

                if getattr(self, 'config', {}).get("advanced", {}).get("telegram_enable", False):
                    if hasattr(self, 'send_telegram_message'):
                        await self.send_telegram_message("🎟️ <b>[Billboard Live]</b> 🎉 座位點選成功！\n機器人已為您鎖定座位並進入結帳，請立刻回視窗付款！")
    # ==========================================
    # 以下為具體執行的非同步函數 (等待填入 JS 邏輯)
    # ==========================================

    async def select_event(self, active_tab):
        """[流程 1] 掃描並點擊「立即購票」，支援熱重載與前端防卡死"""
        import asyncio

        reload_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))
        if reload_interval <= 0:
            reload_interval = 0.5

        js_event = """
        (function() {
            try {
                // 1. 尋找「立即購票」按鈕
                let links = Array.from(document.querySelectorAll('a'));
                let buyBtn = links.find(el => el.innerText && el.innerText.includes('立即購票'));

                if (buyBtn) {
                    // 🔥 加入前端防連點鎖：只有在沒點過的情況下才點擊
                    if (!window._maxbot_event_clicked) {
                        buyBtn.click();
                        window._maxbot_event_clicked = true;
                        return "CLICK_BUY";
                    }
                    return "WAITING_TRANSITION"; // 已經點了，安靜等待跳轉
                }

                // 2. 如果沒看到按鈕，尋找是否有「開賣」的倒數提示
                let spans = Array.from(document.querySelectorAll('span'));
                let notOnSaleSpan = spans.find(el => el.innerText && el.innerText.includes('開賣'));

                if (notOnSaleSpan) {
                    return "NOT_ON_SALE|" + notOnSaleSpan.innerText.trim();
                }

                return "WAITING_DOM";

            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        try:
            result = await active_tab.evaluate(js_event)

            if isinstance(result, str):
                if result == "CLICK_BUY":
                    print(">>> [Billboard] 🚀 偵測到「立即購票」！已極速點擊，準備進入下一步...")
                    self.is_event_selected = True
                    await asyncio.sleep(0.5)

                elif result == "WAITING_TRANSITION":
                    # 已經點了按鈕，安靜等待網頁跳轉，不印 log 避免洗版
                    await asyncio.sleep(0.05)

                elif result.startswith("NOT_ON_SALE|"):
                    msg = result.split("|")[1]

                    # 執行熱重載邏輯
                    try:
                        import os
                        import json
                        try:
                            import util
                            config_path = os.path.join(
                                util.get_app_root(), "settings.json")
                        except:
                            config_path = "settings.json"

                        if os.path.exists(config_path):
                            current_mtime = os.path.getmtime(config_path)
                            if not hasattr(self, '_last_config_mtime'):
                                self._last_config_mtime = current_mtime
                            elif self._last_config_mtime != current_mtime:
                                with open(config_path, 'r', encoding='utf-8') as f:
                                    self.config = json.load(f)
                                self._last_config_mtime = current_mtime
                                print(
                                    "\n>>> [系統] 🔄 偵測到 settings.json 變更，已成功熱重載最新戰術！")
                                reload_interval = float(self.config.get(
                                    "advanced", {}).get("auto_reload_page_interval", 0.5))
                                if reload_interval <= 0:
                                    reload_interval = 0.5
                    except Exception as e:
                        pass

                    print(
                        f">>> [Billboard] ⏳ 尚未開賣 ({msg})，{reload_interval} 秒後自動重新整理...")
                    await asyncio.sleep(reload_interval)
                    await active_tab.reload()

                elif result == "WAITING_DOM":
                    await asyncio.sleep(0.1)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 場次頁面腳本錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] select_event 發生錯誤: {e}")

    async def select_date(self, active_tab):
        """[流程 2] 處理日期與票種的連動下拉選單"""
        import json
        import asyncio

        # 1. 讀取設定檔的關鍵字
        # 日期關鍵字 (例如 "1st", "18:00")
        raw_date_kw = self.config.get("date_auto_select", {}).get(
            "date_keyword", "").strip()
        # 票種關鍵字 (使用設定檔中的 user_guess_string，例如 "雙人席", "3000")
        raw_ticket_kw = self.config.get("advanced", {}).get(
            "user_guess_string", "").strip()

        # 格式化為 List
        def parse_kw(raw_str):
            if not raw_str:
                return [""]
            try:
                if raw_str.startswith("[") and raw_str.endswith("]"):
                    return json.loads(raw_str)
                else:
                    return json.loads("[" + raw_str + "]")
            except:
                return [raw_str.replace('"', '').strip()]

        date_keywords = parse_kw(raw_date_kw)
        ticket_keywords = parse_kw(raw_ticket_kw)

        js_keywords = json.dumps({
            "date": date_keywords,
            "ticket": ticket_keywords
        }, ensure_ascii=False)

        # 2. 核心 JS 邏輯 (處理雙重下拉選單)
        js_date_selection = f"""
        (function() {{
            try {{
                const kws = {js_keywords};
                const normalizeText = (str) => (str || "").toUpperCase().replace(/\\s+/g, '');

                // 尋找畫面上所有的下拉式選單 (Combobox)
                let comboboxes = document.querySelectorAll('button[role="combobox"]');
                if (comboboxes.length < 2) return "WAITING_DOM";

                let dateBox = comboboxes[0];
                let ticketBox = comboboxes[1];

                // ==========================================
                // 步驟 A：選擇日期
                // ==========================================
                if (!window._maxbot_date_picked) {{
                    // 如果選單還沒展開，先點擊展開
                    if (dateBox.getAttribute('aria-expanded') !== 'true') {{
                        dateBox.click();
                        return "OPENING_DATE_BOX";
                    }}

                    // 尋找展開後的選項
                    let listbox = dateBox.nextElementSibling;
                    if (!listbox) return "WAITING_DATE_LIST";
                    let options = Array.from(listbox.querySelectorAll('div[role="option"]'));
                    if (options.length === 0) return "WAITING_DATE_OPTIONS";

                    let targetOption = options[0]; // 預設選第一個
                    for (let opt of options) {{
                        let text = normalizeText(opt.innerText);
                        let isMatch = false;
                        if (kws.date.length === 0 || kws.date[0] === "") {{
                            isMatch = true;
                        }} else {{
                            isMatch = kws.date.some(k => k && text.includes(normalizeText(k)));
                        }}
                        if (isMatch) {{ targetOption = opt; break; }}
                    }}

                    targetOption.click();
                    window._maxbot_date_picked = true;
                    return "DATE_CLICKED";
                }}

                // ==========================================
                // 步驟 B：選擇票種 (等待票種載入)
                // ==========================================
                if (window._maxbot_date_picked && !window._maxbot_ticket_picked) {{
                    // 點擊日期後，票種選單可能會 disabled 或 loading，需要等待
                    if (ticketBox.disabled) return "WAITING_TICKET_UNLOCK";

                    if (ticketBox.getAttribute('aria-expanded') !== 'true') {{
                        ticketBox.click();
                        return "OPENING_TICKET_BOX";
                    }}

                    let listbox = ticketBox.nextElementSibling;
                    if (!listbox) return "WAITING_TICKET_LIST";
                    let options = Array.from(listbox.querySelectorAll('div[role="option"]'));
                    if (options.length === 0) return "WAITING_TICKET_OPTIONS";

                    let targetOption = options[0]; // 預設選第一個
                    for (let opt of options) {{
                        let text = normalizeText(opt.innerText);
                        let isMatch = false;
                        if (kws.ticket.length === 0 || kws.ticket[0] === "") {{
                            isMatch = true;
                        }} else {{
                            isMatch = kws.ticket.some(k => k && text.includes(normalizeText(k)));
                        }}
                        if (isMatch) {{ targetOption = opt; break; }}
                    }}

                    targetOption.click();
                    window._maxbot_ticket_picked = true;
                    return "TICKET_CLICKED";
                }}

                // ==========================================
                // 步驟 C：點擊下一步 / 送出
                // ==========================================
                if (window._maxbot_date_picked && window._maxbot_ticket_picked) {{
                    // ⚠️ 注意：這裡假設有一個 "下一步" 或 "確認" 的按鈕。
                    // 尋找常見的送出按鈕 (type="submit" 或是文字包含 下一步/結帳/確認 等)
                    let btns = Array.from(document.querySelectorAll('button'));
                    let submitBtn = btns.find(b =>
                        b.type === 'submit' ||
                        (b.innerText && b.innerText.includes('下一步')) ||
                        (b.innerText && b.innerText.includes('確認'))
                    );

                    if (submitBtn && !submitBtn.disabled) {{
                        submitBtn.click();
                        return "FORM_SUBMITTED";
                    }}
                    return "WAITING_SUBMIT_BTN";
                }}

                return "WAITING_DOM";

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_date_selection)

            if isinstance(result, str):
                if result == "OPENING_DATE_BOX":
                    await asyncio.sleep(0.05)  # 給下拉動畫一點時間
                elif result == "DATE_CLICKED":
                    print(">>> [Billboard] 📅 日期場次已選擇！等待票種資料載入...")
                    await asyncio.sleep(0.1)
                elif result == "OPENING_TICKET_BOX":
                    await asyncio.sleep(0.05)
                elif result == "TICKET_CLICKED":
                    print(">>> [Billboard] 🎟️ 票種已成功選擇！準備進入下一步...")
                    await asyncio.sleep(0.1)
                elif result == "FORM_SUBMITTED":
                    print(">>> [Billboard] 🚀 日期與票種已送出！切換至資料填寫階段...")
                    self.is_date_selected = True  # 放行，交給下一個路由
                    await asyncio.sleep(0.5)

                # 等待狀態 (不印出 Log 避免洗版)
                elif result in ["WAITING_DOM", "WAITING_DATE_LIST", "WAITING_DATE_OPTIONS", "WAITING_TICKET_UNLOCK", "WAITING_TICKET_LIST", "WAITING_TICKET_OPTIONS", "WAITING_SUBMIT_BTN"]:
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 選擇日期 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] select_date 發生錯誤: {e}")

    async def fill_data(self, active_tab):
        """[流程 3] 資料填寫頁面：無須填寫，極速點擊「下一步」略過"""
        import asyncio

        js_fill = """
        (function() {
            try {
                // 尋找畫面上所有的 button
                let btns = Array.from(document.querySelectorAll('button'));

                // 尋找文字包含「下一步」且沒有被 disabled 的按鈕
                let nextBtn = btns.find(b =>
                    b.innerText &&
                    b.innerText.includes('下一步') &&
                    !b.disabled &&
                    !b.classList.contains('disabled')
                );

                if (nextBtn) {
                    // 加入防連點機制，確保只點擊一次
                    if (!window._maxbot_data_submitted) {
                        nextBtn.click();
                        window._maxbot_data_submitted = true;
                        return "NEXT_CLICKED";
                    }
                    return "WAITING_TRANSITION"; // 已經點了，正在等網頁跳轉
                }

                return "WAITING_DOM"; // 還沒找到按鈕，網頁可能還在轉圈圈

            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        try:
            result = await active_tab.evaluate(js_fill)

            if isinstance(result, str):
                if result == "NEXT_CLICKED":
                    print(">>> [Billboard] ⏩ 無須填寫資料！已極速點擊「下一步」略過，準備進入選位畫面...")
                    self.is_data_filled = True  # 放行，交接給下一個路由
                    await asyncio.sleep(0.3)    # 給網頁一點跳轉的時間

                elif result == "WAITING_TRANSITION":
                    # 已經點擊，安靜等待跳轉，不印出 Log 避免洗版
                    await asyncio.sleep(0.05)

                elif result == "WAITING_DOM":
                    # 尚未找到按鈕，持續極速掃描
                    if not hasattr(self, 'data_wait_count'):
                        self.data_wait_count = 0
                    self.data_wait_count += 1
                    if self.data_wait_count % 10 == 0:  # 每 0.5 秒印一次心跳
                        print(">>> [Billboard] ⏳ 等待「下一步」按鈕載入中...")
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 資料填寫 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] fill_data 發生錯誤: {e}")

    async def select_seat(self, active_tab):
        """[流程 4] 掃描座位、精準關鍵字匹配，加入 DOM 延遲防護 (修復下一步卡死版)"""
        import json
        import asyncio
        import random

        target_count = self.ticket_number
        reload_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))
        if reload_interval <= 0:
            reload_interval = 0.5

        raw_keyword = self.config.get("area_auto_select", {}).get(
            "area_keyword", "").strip()
        keyword_list = []
        if len(raw_keyword) > 0:
            try:
                if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                    keyword_list = json.loads(raw_keyword)
                else:
                    keyword_list = json.loads("[" + raw_keyword + "]")
            except:
                keyword_list = [raw_keyword]
        else:
            keyword_list = [""]

        js_keywords = json.dumps(keyword_list, ensure_ascii=False)

        js_seat = f"""
        (function() {{
            try {{
                const kws = {js_keywords};
                const targetCount = {target_count};
                const normalizeText = (str) => (str || "").toUpperCase().replace(/\\s+/g, '').replace(/-/g, '');

                // ==========================================
                // 階段 A：如果已經點選過座位，專心等待「下一步」按鈕解鎖
                // ==========================================
                if (window._maxbot_seats_clicked) {{
                    let btns = Array.from(document.querySelectorAll('button'));
                    let nextBtn = btns.find(b =>
                        b.innerText &&
                        (b.innerText.includes('下一步') || b.innerText.includes('確認')) &&
                        !b.disabled &&
                        !b.hasAttribute('disabled')
                    );

                    if (nextBtn) {{
                        nextBtn.click();
                        return "SEAT_SUBMITTED";
                    }}
                    return "WAITING_NEXT_BTN";
                }}

                // ==========================================
                // 階段 B：精準偵測「座位圖容器」是否已出現
                // ==========================================
                // 🚀 使用你提供的特徵：尋找帶有 cursor-grab (可拖曳) 的座位圖主容器
                let seatContainer = document.querySelector('div.cursor-grab');

                if (!seatContainer) {{
                    return "WAITING_SEAT_MAP"; // 容器連影子都沒有，網頁還在載入中
                }}

                // 容器出現了！我們只抓容器裡面的座位按鈕
                let allSeats = Array.from(seatContainer.querySelectorAll('button[title]'));

                if (allSeats.length === 0) {{
                    // 容器出現了，但按鈕還沒長出來 (給 React 0.5 秒的渲染時間)
                    if (!window._seatRenderWait) window._seatRenderWait = 0;
                    window._seatRenderWait++;
                    if (window._seatRenderWait > 10) {{
                        window._seatRenderWait = 0;
                        return "NO_SEAT"; // 0.5 秒還是沒按鈕，判定為空
                    }}
                    return "WAITING_SEATS_RENDER";
                }}

                // ==========================================
                // 階段 C：零延遲判定！座位已渲染，直接決勝負
                // ==========================================
                let availableSeats = allSeats.filter(btn =>
                    !btn.disabled &&
                    !btn.hasAttribute('disabled') &&
                    !btn.classList.contains('cursor-not-allowed')
                );

                // 🚨 只要空位數量不足，【不再等待 3 秒】，瞬間回傳觸發重整！
                if (availableSeats.length < targetCount) {{
                    return "NO_SEAT";
                }}

                // 關鍵字過濾
                let matchedSeats = [];
                if (kws.length === 0 || (kws.length === 1 && kws[0] === "")) {{
                    matchedSeats = availableSeats;
                }} else {{
                    for (let seat of availableSeats) {{
                        let title = seat.getAttribute('title').trim().toUpperCase();
                        let normTitle = normalizeText(title);
                        let rowPrefix = title.split('-')[0].trim();

                        let isMatch = false;
                        for (let k of kws) {{
                            let normK = normalizeText(k);
                            if (normTitle === normK || rowPrefix === normK) {{
                                isMatch = true;
                                break;
                            }}
                        }}
                        if (isMatch) matchedSeats.push(seat);
                    }}
                }}

                // 🚨 找不到符合關鍵字的座位，【不再等待】，瞬間回傳觸發重整！
                if (matchedSeats.length < targetCount) {{
                    return "NO_MATCHED_SEAT";
                }}

                // 找到足夠座位，發動點擊！
                for (let i = 0; i < targetCount; i++) {{
                    matchedSeats[i].click();
                }}

                window._maxbot_seats_clicked = true;
                return "SEATS_CLICKED";

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_seat)

            if isinstance(result, str):
                if result == "SEATS_CLICKED":
                    print(
                        f">>> [Billboard] 🎯 成功鎖定 {target_count} 個座位！等待下一步按鈕解鎖...")
                    await asyncio.sleep(0.05)

                elif result == "SEAT_SUBMITTED":
                    print(">>> [Billboard] 🎉 座位確認送出！準備進入結帳階段...")
                    self.is_seat_selected = True

                    if getattr(self, 'config', {}).get("advanced", {}).get("telegram_enable", False):
                        if not getattr(self, 'is_telegram_sent', False):
                            if hasattr(self, 'send_telegram_message'):
                                await self.send_telegram_message("🎟️ <b>[Billboard Live]</b> 🎉 座位點選成功！\n機器人已為您鎖定座位並進入結帳，請立刻回視窗付款！")
                            self.is_telegram_sent = True
                    await asyncio.sleep(0.5)

                elif result in ["NO_SEAT", "NO_MATCHED_SEAT"]:
                    msg = "該區已無空位" if result == "NO_SEAT" else "找不到符合關鍵字的座位"
                    print(
                        f">>> [Billboard] ❌ {msg}！{reload_interval} 秒後原地自動重刷...")
                    await asyncio.sleep(reload_interval)

                    await active_tab.reload()
                    await asyncio.sleep(1.0)

                elif result in ["WAITING_SEAT_MAP", "WAITING_AVAILABLE_SEATS", "WAITING_MATCHED_SEATS", "WAITING_NEXT_BTN"]:
                    if not hasattr(self, 'seat_wait_count'):
                        self.seat_wait_count = 0
                    self.seat_wait_count += 1
                    if self.seat_wait_count % 10 == 0:
                        print(f">>> [Billboard] ⏳ 座位圖載入與比對中 ({result})...")
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 座位掃描 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] select_seat 發生錯誤: {e}")

    def reset_all_states(self):
        """重置所有進度 (當需要退回重刷時呼叫)"""
        self.is_event_selected = False
        self.is_date_selected = False
        self.is_data_filled = False
        self.is_seat_selected = False
        self.is_success_notified = False


# ==========================================
# [Billboard 搶票]
# ==========================================


class TsgHawksBot:
    def __init__(self, driver, config):
        """初始化台鋼雄鷹機器人 (支援暫停與自動重啟版)"""
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        self.ticket_number = int(self.config.get("ticket_number", 1))
        self.last_url = ""

        self.is_event_selected = False
        self.is_area_selected = False
        self.is_seat_selected = False

        self.cooldown_until = 0
        self._wait_counts = {}

        # 🔥 建立 GUI 暫停檔案的偵測路徑
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

    def _log_wait(self, msg):
        """智能防洗版日誌系統"""
        self._wait_counts[msg] = self._wait_counts.get(msg, 0) + 1
        if self._wait_counts[msg] % 20 == 1:
            print(f">>> [TSG] ⏳ {msg}")

    def _parse_keyword(self, dict_key, default_val):
        """安全解析設定檔，防呆到底"""
        try:
            sub_dict = self.config.get(dict_key, {})
            if isinstance(sub_dict, dict):
                raw_val = sub_dict.get(dict_key.replace(
                    "auto_select", "keyword"), default_val)
            else:
                raw_val = default_val

            if isinstance(raw_val, list):
                res = str(raw_val[0]).strip() if len(raw_val) > 0 else ""
            else:
                raw_str = str(raw_val).strip()
                if raw_str.startswith("[") and raw_str.endswith("]"):
                    try:
                        res = str(json.loads(raw_str)[0]).strip()
                    except:
                        res = raw_str
                else:
                    res = raw_str
            return res.replace('"', '').replace("'", "").strip()
        except Exception:
            return default_val

    async def run(self):
        print(f">>> [TSG Hawks] 🦅 絕不漏接日誌版啟動！(目標: {self.ticket_number} 張)")

        while True:
            try:
                # 🔥 1. GUI 暫停功能偵測
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                if current_url != self.last_url:
                    print(f"\n>>> [系統] 網址變更: {current_url}")
                    self.last_url = current_url

                # 將目前網址傳給分發中心來決定任務
                await self.dispatch_action(current_url)

            except Exception as e:
                err_msg = str(e)
                if "1225" not in err_msg and "10061" not in err_msg and "10054" not in err_msg:
                    pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, current_url):
        if time.time() < self.cooldown_until:
            return

        upper_url = current_url.upper()

        # 🔥 2. 退回重啟機制：如果網址裡面沒有 BUYTICKET，代表我們被踢回首頁/場次頁了！
        if 'BUYTICKET' not in upper_url:
            # 如果我們身上還有之前選過位子的標記，強制洗掉它
            if self.is_event_selected or self.is_area_selected or self.is_seat_selected:
                print(">>> [系統] 🔄 偵測到退回場次選擇頁面！已清除進度鎖定，重新開始尋找場次！")
                self.is_event_selected = False
                self.is_area_selected = False
                self.is_seat_selected = False

            await self.select_event()

        # 如果網址有 BUYTICKET，代表已經在選區或選位的流程中
        else:
            if not self.is_area_selected:
                await self.select_area()
            elif not self.is_seat_selected:
                await self.select_seat()

    async def select_event(self):
        """[流程 1] 拆解式選擇場次 (加入自動重刷機制)"""
        import asyncio
        import time

        # 取得日期與 GUI 設定的刷新秒數
        date_keyword = self._parse_keyword("date_auto_select", "5/22")
        reload_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))
        if reload_interval <= 0:
            reload_interval = 0.5

        if not date_keyword or '/' not in date_keyword:
            self._log_wait(f"日期格式錯誤: 【{date_keyword}】。請設定如 5/22")
            return

        try:
            month_int = int(date_keyword.split('/')[0])
            day_int = int(date_keyword.split('/')[1])
            month_str = str(month_int) + "月"
            day_str = str(day_int)
        except ValueError:
            self._log_wait(f"日期包含非數字: 【{date_keyword}】。請設定如 5/22")
            return

        # ==========================================
        # 步驟 A: 尋找並點擊月份
        # ==========================================
        js_month = f"""
        (function() {{
            let targetMonth = '{month_str}';
            let spans = Array.from(document.querySelectorAll('.tab_btn span.tab-a3'));
            if (spans.length === 0) return "NO_DOM";

            let target = spans.find(s => (s.textContent || "").includes(targetMonth));
            if (target) {{
                let btn = target.closest('.tab_btn');
                if (btn && !btn.classList.contains('active')) {{
                    btn.click();
                    return "CLICKED_MONTH";
                }}
                return "MONTH_IS_ACTIVE";
            }}
            return "MONTH_NOT_FOUND";
        }})();
        """

        try:
            res_month = await asyncio.wait_for(self.tab.evaluate(js_month), timeout=1.5)

            if res_month == "CLICKED_MONTH":
                print(f">>> [TSG] 📅 已切換至 【{month_str}】，等待場次更新...")
                self.cooldown_until = time.time() + 0.5
                return
            elif res_month == "MONTH_IS_ACTIVE":
                pass
            elif res_month == "NO_DOM":
                self._log_wait("等待網頁載入月份標籤...")
                return
            elif res_month == "MONTH_NOT_FOUND":
                # 🔥 找不到月份 ➔ 觸發重整！
                print(
                    f">>> [TSG] ⏳ 畫面上還沒有 【{month_str}】 的頁籤，{reload_interval} 秒後自動重刷...")
                await asyncio.sleep(reload_interval)
                await self.tab.reload()
                return
            else:
                self._log_wait(f"月份腳本未處理的狀態: {res_month}")
                return
        except asyncio.TimeoutError:
            print(">>> [警告] 尋找月份時腳本無回應，強制解除死鎖！")
            return

        # ==========================================
        # 步驟 B: 尋找日期並點擊購票
        # ==========================================
        js_date = f"""
        (function() {{
            let targetDay = '{day_str}';
            let dateSpans = Array.from(document.querySelectorAll('span.match-date-num'));
            if (dateSpans.length === 0) return "NO_DOM";

            let foundDay = false;
            for (let d of dateSpans) {{
                if ((d.textContent || "").trim() === targetDay) {{
                    foundDay = true;
                    let curr = d;
                    for (let i = 0; i < 8; i++) {{
                        if (!curr) break;
                        curr = curr.parentElement;
                        let btn = curr.querySelector('div.main_small-btn[role="button"]');
                        if (btn) {{
                            // 若按鈕被設定為 disabled 或 disable，代表無法購買
                            if (btn.classList.contains('disabled') || btn.classList.contains('disable')) {{
                                return "BTN_DISABLED";
                            }}
                            btn.click();
                            return "CLICKED_BUY";
                        }}
                    }}
                }}
            }}
            return foundDay ? "NO_BTN_NEAR_DATE" : "DATE_NOT_FOUND";
        }})();
        """

        try:
            res_date = await asyncio.wait_for(self.tab.evaluate(js_date), timeout=1.5)

            if res_date == "CLICKED_BUY":
                print(
                    f">>> [TSG] 🚀 成功點擊 {month_str} {day_str}號 的「購票」按鈕！進入下階段...")
                self.is_event_selected = True
                self.cooldown_until = time.time() + 1.0
            elif res_date == "NO_DOM":
                self._log_wait("等待場次日期載入...")

            # 🔥 找不到日期、按鈕還沒出、按鈕是灰色的 ➔ 通通觸發重整！
            elif res_date in ["NO_BTN_NEAR_DATE", "BTN_DISABLED", "DATE_NOT_FOUND"]:
                if res_date == "NO_BTN_NEAR_DATE":
                    msg = f"找到 {day_str} 號，但還沒有開放購票按鈕"
                elif res_date == "BTN_DISABLED":
                    msg = f"{day_str} 號的購票按鈕為灰色無法點擊"
                else:
                    msg = f"{month_str} 頁面中尚未出現 {day_str} 號的賽程"

                print(f">>> [TSG] ⏳ {msg}，{reload_interval} 秒後自動重刷...")
                await asyncio.sleep(reload_interval)
                await self.tab.reload()

            else:
                self._log_wait(f"日期腳本未處理的狀態: {res_date}")
        except asyncio.TimeoutError:
            print(">>> [警告] 尋找日期時腳本無回應，強制解除死鎖！")

    async def select_area(self):
        """[流程 2] 展開與選擇區域"""
        area_keyword = self._parse_keyword("area_auto_select", "2")
        target_count = self.ticket_number

        js_area = f"""
        (function() {{
            let infoBtn = document.querySelector('.seat-infor-open');
            let tableExists = document.querySelector('.table .tr_group');

            if (infoBtn && !tableExists) {{
                infoBtn.click();
                return "CLICKED_INFO";
            }}

            let rows = Array.from(document.querySelectorAll('.table .tr_group .tr'));
            if (rows.length === 0) return "WAITING_TABLE";

            let rawKeywordStr = "{area_keyword}";
            let keywords = rawKeywordStr.split(',').map(k => k.trim()).filter(k => k.length > 0);

            for (let r of rows) {{
                let cols = r.querySelectorAll('.td');
                if (cols.length >= 3) {{
                    let areaName = cols[0].textContent.trim();
                    let remainCount = parseInt(cols[1].textContent.trim(), 10);
                    let buyBtn = cols[2].querySelector('.small_icon-btn');

                    let isMatch = keywords.length === 0 || keywords.some(k => areaName.includes(k));

                    if (isMatch && remainCount >= {target_count} && buyBtn) {{
                        buyBtn.click();
                        return "CLICKED_AREA|" + areaName;
                    }}
                }}
            }}
            return "NO_MATCH";
        }})();
        """

        try:
            res = await asyncio.wait_for(self.tab.evaluate(js_area), timeout=1.5)
            if res == "CLICKED_INFO":
                self.cooldown_until = time.time() + 0.3
            elif res.startswith("CLICKED_AREA|"):
                area_name = res.split("|")[1]
                print(f">>> [TSG] 🏟️ 成功鎖定並點擊區域：【{area_name}】")
                self.is_area_selected = True
                self.cooldown_until = time.time() + 1.0
            elif res == "WAITING_TABLE":
                self._log_wait("等待區域表格展開...")
            elif res == "NO_MATCH":
                self._log_wait(
                    f"找不到關鍵字 '{area_keyword}' 且張數 ({target_count}) 足夠的區域...")
            else:
                self._log_wait(f"選區腳本未處理狀態: {res}")
        except asyncio.TimeoutError:
            pass

    async def select_seat(self):
        """[流程 3] 座位選擇 (加入二維座標分群演算法，就近包場)"""
        import asyncio
        import time

        target_count = self.ticket_number
        reload_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))
        if reload_interval <= 0:
            reload_interval = 0.5

        js_seat = f"""
        (function() {{
            try {{
                const targetCount = {target_count};

                // 1. 確認按鈕保護：已點擊過座位才允許按確認
                if (window._tsg_seats_clicked) {{
                    let confirmBtn = document.querySelector('.ticket-buy-open');
                    if (confirmBtn && !confirmBtn.disabled && !confirmBtn.classList.contains('disabled')) {{
                        confirmBtn.click();
                        return "CLICKED_CONFIRM";
                    }}
                    return "WAITING_CONFIRM_BTN";
                }}

                let rows = Array.from(document.querySelectorAll('.seat_list .flex.h-7'));
                if (rows.length === 0) return "WAITING_SEATS";

                let allAvailableSeats = [];
                let seatsToClick = [];

                // 2. 賦予座標並尋找絕對連號
                for (let rIdx = 0; rIdx < rows.length; rIdx++) {{
                    let row = rows[rIdx];
                    let seats = Array.from(row.children);
                    let currentContiguous = [];

                    for (let cIdx = 0; cIdx < seats.length; cIdx++) {{
                        let seat = seats[cIdx];
                        // 尋找真實座位框架
                        let inner = seat.classList.contains('seat_frame') ? seat : seat.querySelector('.seat_frame');
                        let html = seat.outerHTML.toLowerCase();

                        // 判斷是否為空位
                        let isAvailable = inner && !html.includes('sold') && !html.includes('disabled');

                        if (isAvailable) {{
                            // 記錄每個空位的 DOM 與二維座標 (排, 列)
                            let seatData = {{ el: inner, r: rIdx, c: cIdx }};
                            allAvailableSeats.push(seatData);
                            currentContiguous.push(seatData);

                            // 若找到完美連號，立刻鎖定並跳出！
                            if (currentContiguous.length === targetCount && seatsToClick.length === 0) {{
                                seatsToClick = [...currentContiguous];
                            }}
                        }} else {{
                            // 遇到走道或已售出，連號中斷
                            currentContiguous = [];
                        }}
                    }}
                }}

                // 3. 總量檢查
                if (allAvailableSeats.length < targetCount) {{
                    return "NOT_ENOUGH_SEATS_TOTAL";
                }}

                let isScattered = false;

                // 4. 備案：就近分群演算法 (當找不到完美連號時)
                if (seatsToClick.length === 0) {{
                    isScattered = true;
                    let bestSpread = Infinity;
                    let bestCluster = [];

                    // 將每個空位輪流當作「中心點」
                    for (let i = 0; i < allAvailableSeats.length; i++) {{
                        let center = allAvailableSeats[i];

                        // 計算所有空位到此中心點的「曼哈頓距離」並排序
                        // (排的物理距離通常比較遠，所以跨排的權重設為 2)
                        let sortedByDistance = [...allAvailableSeats].sort((a, b) => {{
                            let distA = Math.abs(a.r - center.r) * 2 + Math.abs(a.c - center.c);
                            let distB = Math.abs(b.r - center.r) * 2 + Math.abs(b.c - center.c);
                            return distA - distB;
                        }});

                        // 抓取離這個中心點最近的 N 個座位 (包含自己)
                        let cluster = sortedByDistance.slice(0, targetCount);

                        // 計算這個群組的總擴散程度 (分數越低代表越密集)
                        let spread = cluster.reduce((sum, s) => sum + Math.abs(s.r - center.r) * 2 + Math.abs(s.c - center.c), 0);

                        if (spread < bestSpread) {{
                            bestSpread = spread;
                            bestCluster = cluster;
                        }}
                    }}
                    seatsToClick = bestCluster;
                }}

                // 5. 發動點擊
                for (let s of seatsToClick) {{
                    s.el.click();
                }}

                window._tsg_seats_clicked = true;
                return isScattered ? "CLICKED_CLUSTER" : "CLICKED_CONTIGUOUS";

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            res = await asyncio.wait_for(self.tab.evaluate(js_seat), timeout=1.5)

            if res == "CLICKED_CONTIGUOUS":
                print(f">>> [TSG] 🎯 成功鎖定 {target_count} 個【完美連號】座位！等待確認...")
                self.cooldown_until = time.time() + 0.5

            elif res == "CLICKED_CLUSTER":
                print(
                    f">>> [TSG] ⚠️ 無法湊齊同排連號，已啟動空間演算法：成功鎖定 {target_count} 個【距離最近】的座位！")
                self.cooldown_until = time.time() + 0.5

            elif res == "CLICKED_CONFIRM":
                print(f">>> [TSG] 🎉 選位確認送出！請接手處理後續結帳！")
                self.is_seat_selected = True
                self.cooldown_until = time.time() + 2.0

            elif res == "WAITING_SEATS":
                self._log_wait("等待座位圖載入...")

            elif res == "WAITING_CONFIRM_BTN":
                self._log_wait("座位已點選，等待「確認選位」按鈕解鎖...")

            elif res == "NOT_ENOUGH_SEATS_TOTAL":
                print(
                    f">>> [TSG] ❌ 該區總空位不足 {target_count} 張！{reload_interval} 秒後自動重整...")
                await asyncio.sleep(reload_interval)
                await self.tab.reload()

            elif res.startswith("ERROR"):
                print(f">>> [DEBUG] 選位腳本出錯: {res}")

            else:
                self._log_wait(f"選位腳本未處理狀態: {res}")

        except asyncio.TimeoutError:
            pass
# ==========================================
# [台鋼雄鷹 搶票]
# ==========================================


class NolBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態變數鎖
        self.is_activity_clicked = False
        self.is_gate_passed = False
        self.is_date_selected = False
        self.is_seat_selected = False

        # 日期關鍵字設定 (例如 "2" 或 "17")
        self.date_keyword = str(self.config.get(
            "date_auto_select", {}).get("date_keyword", "2")).strip()
        self.refresh_sec = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.1))
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

    async def run(self):
        print(
            f">>> [NOL 公園半自動] 機器人啟動！(目標張數: {self.ticket_number} | 鎖定日期: {self.date_keyword})")
        print(">>> [系統] 🛡️ 已啟動「動態分頁追蹤」、「新舊介面自動相容」與「手動接管無縫接軌」模式！")

        while True:
            try:
                # 1. 暫停攔截：若偵測到暫停檔，則卡在這邊等待
                if os.path.exists(self.PAUSE_FILE):
                    if not getattr(self, 'is_printing_pause', False):
                        print("\n>>> [NOL] ⏸️ 程式已暫停！等待您在 GUI 按下接續...")
                        self.is_printing_pause = True
                    await asyncio.sleep(0.5)
                    continue
                self.is_printing_pause = False

                # 2. 永遠抓取「最後開啟/最上層」的分頁
                active_tab = self.driver.tabs[-1]
                current_url = await active_tab.evaluate("window.location.href")

                if current_url and current_url != self.last_url:
                    print(f">>> [系統] 偵測到頁面切換: {current_url}")
                    self.last_url = current_url

                if current_url:
                    await self.dispatch_action(current_url, active_tab)

            except Exception as e:
                pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, url, active_tab):
        """NOL 任務分發中心 (完美相容舊版 iframe 架構與新版 React/SPA 架構)"""
        upper_url = url.upper()

        # Step 1: 活動主頁
        if 'WORLD.NOL.COM' in upper_url:
            await self.step1_activity_page(active_tab)

        # Step 2: 排隊閘門
        elif 'TICKETS.INTERPARK.COM/GATES' in upper_url:
            await self.step2_waiting_gate(active_tab)

        # 排隊中保護
        elif 'WAITINGSERVICESESSION.ASP' in upper_url:
            if not hasattr(self, 'queue_wait_log'):
                self.queue_wait_log = 0
            self.queue_wait_log += 1
            if self.queue_wait_log % 40 == 0:
                print(
                    ">>> [NOL-排隊] 🚶‍♂️ 正在神聖的排隊序列中！(機器人已進入待命保護模式，絕對不會重整，請靜候綠條跑完...)")
            await asyncio.sleep(0.05)

       # =========================================================================
        # 🔥 新版改版網頁檢測 (`/onestop/` 或 `/booking/` 或 `/seat?step=price`)
        # =========================================================================
        elif 'TICKETS.INTERPARK.COM/ONESTOP' in upper_url or 'TICKETS.INTERPARK.COM/BOOKING' in upper_url or 'STEP=PRICE' in upper_url:
            phase = await self.detect_new_ui_phase(active_tab)

            # 🔥 1. 成功進入選價/結帳頁面 (直接鎖死停止一切動作)
            if phase == "SUCCESS_PHASE":
                if not getattr(self, 'ticket_locked_printed', False):
                    print(
                        "\n>>> [NOL-新版] 🎉🎉🎉 鎖票成功！已進入 Select Price / Place Order 付款階段！")
                    print(">>> [系統] 🛡️ 機器人已完全停止點擊，請您安心在限制時間內完成付款！")
                    self.ticket_locked_printed = True
                    self.is_seat_selected = True
                await asyncio.sleep(1.0)
                return

            # 2. OCR 驗證提示保護
            elif phase == "CAPTCHA_PHASE":
                if not getattr(self, 'captcha_printed', False):
                    print(
                        ">>> [NOL-新版] 🛡️ 偵測到「OCR 驗證碼」視窗！機器人暫停自動點擊，請您手動輸入驗證碼...")
                    self.captcha_printed = True
                await asyncio.sleep(0.2)

            # 3. 日期選擇階段
            elif phase == "DATE_PHASE_NEW":
                self.captcha_printed = False
                await self.step3_select_date_new(active_tab)

            # 4. 座位選擇階段
            elif phase == "SEAT_PHASE_NEW":
                self.captcha_printed = False
                await self.step4_select_seat_new(active_tab)

            else:
                self.captcha_printed = False
                await asyncio.sleep(0.05)

        # =========================================================================
        # 傳統舊版 ASP 網頁檢測 (`BOOKMAIN.ASP` + `ifrmBookStep`)
        # =========================================================================
        elif 'GPOTICKET.GLOBALINTERPARK.COM' in upper_url and 'BOOKMAIN.ASP' in upper_url:
            js_check_old_phase = """
            (function() {
                try {
                    let doc = document;
                    let frame = document.getElementById('ifrmBookStep');
                    if (frame && frame.contentWindow && frame.contentWindow.document) {
                        doc = frame.contentWindow.document;
                    }
                    let divMain = doc.getElementById('divBookMain') || document.getElementById('divBookMain');
                    let divSeat = doc.getElementById('divBookSeat') || document.getElementById('divBookSeat');
                    let mainDisplay = divMain ? window.getComputedStyle(divMain).display : 'none';
                    let seatDisplay = divSeat ? window.getComputedStyle(divSeat).display : 'none';

                    if (mainDisplay !== 'none') return "DATE_PHASE";
                    else if (seatDisplay !== 'none') return "SEAT_PHASE";
                    return "WAITING";
                } catch(e) { return "WAITING"; }
            })();
            """
            phase = await active_tab.evaluate(js_check_old_phase)

            if phase == "DATE_PHASE":
                if getattr(self, 'is_seat_selected', False):
                    self.is_seat_selected = False
                    try:
                        await active_tab.evaluate("window._nol_seat_clicked = false;")
                    except:
                        pass
                await self.step3_select_date(active_tab)

            elif phase == "SEAT_PHASE":
                await self.step4_select_seat(active_tab)
            else:
                await asyncio.sleep(0.05)

    # =========================================================================
    # 🔥 新版 UI 專用邏輯
    # =========================================================================

    async def detect_new_ui_phase(self, active_tab):
        """新版介面階段偵測器：整合 step=price 路由與英/韓語系付款標籤檢測"""
        js_phase_new = """
        (function() {
            try {
                function isVisible(el) {
                    if (!el) return false;
                    let rect = el.getBoundingClientRect();
                    let style = window.getComputedStyle(el);
                    if (rect.width === 0 || rect.height === 0 || style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                        return false;
                    }
                    let curr = el;
                    while (curr && curr !== document.body) {
                        let pStyle = window.getComputedStyle(curr);
                        if (pStyle.display === 'none' || pStyle.visibility === 'hidden' || pStyle.opacity === '0') {
                            return false;
                        }
                        curr = curr.parentElement;
                    }
                    return true;
                }

                // 1. 🔥 優先判定：是否為成功階段 (URL 包含 step=price、出現倒數計時器或 Select Price / Place Order 按鈕)
                let isPriceUrl = window.location.href.toLowerCase().includes('step=price');
                let priceWrap = document.querySelector('div[class*="PriceContent_layerWrap"], div[class*="Timer_timerMo"]');
                let orderBtn = Array.from(document.querySelectorAll('button')).find(b => {
                    let text = (b.innerText || "").trim().toUpperCase();
                    return text === "PLACE ORDER" || text === "訂購" || text === "PAY" || text === "CHECKOUT" || text === "ORDER";
                });
                
                if (isPriceUrl || isVisible(priceWrap) || isVisible(orderBtn)) {
                    return "SUCCESS_PHASE";
                }

                // 2. 判定 OCR 驗證碼彈窗是否真正顯示在螢幕上
                let captchaWrap = document.querySelector('div.ModalCaptchaText_layerWrap__jn1bV, input.ModalCaptchaText_captchaInput__DC7Gz');
                if (isVisible(captchaWrap)) {
                    return "CAPTCHA_PHASE";
                }

                // 3. 檢查是否有新版 SVG 座位圖可點選 (`circle.js-seat`)
                let svgSeats = document.querySelectorAll('circle.js-seat');
                if (svgSeats && svgSeats.length > 0) {
                    return "SEAT_PHASE_NEW";
                }

                // 4. 檢查是否有新版日曆元素
                let dateItems = document.querySelectorAll('li.EntCalendar_dateItem__ZC7uF button.EntCalendar_dateButton__6TxQi');
                if (dateItems && dateItems.length > 0) {
                    return "DATE_PHASE_NEW";
                }

                return "WAITING_NEW_DOM";
            } catch(e) { return "ERROR"; }
        })();
        """
        return await active_tab.evaluate(js_phase_new)

    async def step3_select_date_new(self, active_tab):
        """[新版第三階段] 選擇日期並自動按下「下一步」"""
        clean_date_keyword = self.date_keyword.replace(
            '"', '').replace("'", "").strip()
        js_date_new = f"""
        (function() {{
            try {{
                const targetDateRaw = '{clean_date_keyword}';
                const targetDateNum = parseInt(targetDateRaw.replace(/[^0-9]/g, ''), 10);
                const isBlank = targetDateRaw === "";

                // React 事件模擬點擊函數
                function reactClick(el) {{
                    if (!el) return;
                    el.scrollIntoView({{block: 'center', inline: 'center'}});
                    el.focus();
                    el.dispatchEvent(new PointerEvent('pointerdown', {{ bubbles: true, cancelable: true, pointerType: 'mouse' }}));
                    el.dispatchEvent(new PointerEvent('pointerup', {{ bubbles: true, cancelable: true, pointerType: 'mouse' }}));
                    el.dispatchEvent(new MouseEvent('click', {{ bubbles: true, cancelable: true, view: window }}));
                    el.click();
                }}

                // 取得所有日期按鈕
                let buttons = Array.from(document.querySelectorAll('li.EntCalendar_dateItem__ZC7uF button.EntCalendar_dateButton__6TxQi'));
                
                // 過濾掉休假或不可選的
                let validButtons = buttons.filter(btn => {{
                    let isDisabled = btn.disabled || btn.hasAttribute('disabled') || btn.classList.contains('EntCalendar_holiday__z4D4F');
                    return !isDisabled;
                }});

                if (validButtons.length === 0) return "WAITING_VALID_DATES";

                let targetBtn = null;
                for (let btn of validButtons) {{
                    let numSpan = btn.querySelector('span.EntCalendar_number__5Ag2T');
                    let text = numSpan ? numSpan.innerText : btn.innerText;
                    let cellNum = parseInt(text.replace(/[^0-9]/g, ''), 10);
                    
                    if (!isNaN(cellNum) && (isBlank || cellNum === targetDateNum)) {{
                        targetBtn = btn;
                        break;
                    }}
                }}

                if (!targetBtn && isBlank) {{
                    targetBtn = validButtons[0];
                }}

                if (targetBtn) {{
                    // 若按鈕尚未為選取狀態 (aria-pressed !== 'true')，發動點擊
                    if (targetBtn.getAttribute('aria-pressed') !== 'true') {{
                        reactClick(targetBtn);
                        let numSpan = targetBtn.querySelector('span.EntCalendar_number__5Ag2T');
                        let clickedNum = numSpan ? numSpan.innerText : targetDateRaw;
                        return "DATE_CLICKED_NEW|" + clickedNum;
                    }}

                    // 當期日確定選好 (aria-pressed === 'true')，立即點選「下一步」
                    let nextBtns = Array.from(document.querySelectorAll('button.EntButton_primary__UOX1_, button.entButtonGlobal, button'));
                    let nextBtn = nextBtns.find(b => {{
                        let text = (b.innerText || "").trim().toUpperCase();
                        return (text.includes("下一步") || text.includes("NEXT") || text === "다음") &&
                               !b.disabled && !b.hasAttribute('disabled');
                    }});
                    
                    if (nextBtn) {{
                        reactClick(nextBtn);
                        return "NEXT_CLICKED_NEW";
                    }}
                    return "WAITING_NEXT_BTN_NEW";
                }}

                return "DATE_NOT_FOUND_NEW";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        result = await active_tab.evaluate(js_date_new)

        if isinstance(result, str):
            if result.startswith("DATE_CLICKED_NEW|"):
                print(
                    f">>> [NOL-新版日期] 📅 已選取日期「{result.split('|')[1]}日」，準備點擊下一步...")
                await asyncio.sleep(0.2)
            elif result == "NEXT_CLICKED_NEW":
                print(">>> [NOL-新版日期] 🚀 已成功點擊「下一步」！前往座位選擇或驗證階段...")
                self.is_date_selected = True
                await asyncio.sleep(0.5)
            elif result == "DATE_NOT_FOUND_NEW":
                if not hasattr(self, 'date_new_not_found_log'):
                    self.date_new_not_found_log = 0
                self.date_new_not_found_log += 1
                if self.date_new_not_found_log % 20 == 0:
                    print(
                        f">>> [NOL-新版日期] ⚠️ 畫面上找不到指定的日期: {clean_date_keyword}")
                await asyncio.sleep(0.05)

    async def step4_select_seat_new(self, active_tab):
        """[新版第四階段] SVG 座位與 Submit：實裝 DevTools 測試 A 驗證成功的 PointerEvent 穿透點擊"""
        import asyncio
        import time

        # 1. 進入座位頁時給予短暫初始載入緩衝
        if not getattr(self, '_step4_new_entered', False):
            self._step4_new_entered = True
            self._step4_new_enter_time = time.time()
        if time.time() - self._step4_new_enter_time < 0.35:
            await asyncio.sleep(0.05)
            return

        ticket_number = self.ticket_number
        js_seat_new = f"""
        (function() {{
            try {{
                // 🔥 (1) 成功進入結帳流程攔截：網址含有 step=price 或出現 Select Price / Place Order
                let isPriceUrl = window.location.href.toLowerCase().includes('step=price');
                let priceWrap = document.querySelector('div[class*="PriceContent_layerWrap"], div[class*="Timer_timerMo"]');
                let orderBtn = Array.from(document.querySelectorAll('button')).find(b => {{
                    let text = (b.innerText || "").trim().toUpperCase();
                    return text === "PLACE ORDER" || text === "訂購" || text === "PAY";
                }});
                if (isPriceUrl || priceWrap || orderBtn) {{
                    return "TICKET_LOCKED_SUCCESS";
                }}

                // 🔥 (2) 吐司警告阻擋退避 ("Processing your request...")
                let toastEl = document.querySelector('div.nds-e-toast__content');
                if (toastEl && window.getComputedStyle(toastEl).display !== 'none') {{
                    let toastMsg = (toastEl.innerText || "").trim();
                    if (toastMsg.includes("Processing your request") || toastMsg.includes("try again")) {{
                        return "TOAST_RATE_LIMIT|" + toastMsg;
                    }}
                }}

                const targetCount = {ticket_number};
                let allSeats = Array.from(document.querySelectorAll('circle.js-seat'));
                if (allSeats.length === 0) return "WAITING_SVG_SEATS";

                // 🔥 (3) 判斷不可選座位 (灰色 #edeff3 或 disabled 樣式)
                function isDisabled(el) {{
                    let fill = (el.getAttribute('fill') || "").toLowerCase();
                    return el.classList.contains('SeatMap_disabled__AZO_T') || 
                           fill === '#edeff3' || 
                           fill === '#dddddd' || 
                           fill === 'none';
                }}
                
                // 🔥 (4) 判斷已選座位 (排除一般票種的紫/藍/綠，識別選取後的紅/橘高亮或 React 狀態)
                function isSelected(el) {{
                    let fill = (el.getAttribute('fill') || "").toLowerCase();
                    return el.classList.contains('selected') || 
                           el.classList.contains('active') || 
                           el.getAttribute('aria-pressed') === 'true' || 
                           el.getAttribute('data-nol-picked') === 'true' ||
                           fill === '#f11054' || 
                           fill === '#ff0000' || 
                           fill === '#fe4848';
                }}

                // 🔥 (5) 實裝測試 A 驗證成功的 PointerEvent 穿透點擊 (絕不調用 scrollIntoView，零畫面抖動！)
                function reactPointerClick(el) {{
                    if (!el) return;
                    el.dispatchEvent(new PointerEvent('pointerdown', {{ bubbles: true, cancelable: true, pointerType: 'mouse' }}));
                    el.dispatchEvent(new PointerEvent('pointerup', {{ bubbles: true, cancelable: true, pointerType: 'mouse' }}));
                    el.dispatchEvent(new MouseEvent('click', {{ bubbles: true, cancelable: true, view: window }}));
                }}

                let selectedSeats = allSeats.filter(isSelected);
                let availableSeats = allSeats.filter(el => !isDisabled(el) && !isSelected(el));

                if ((selectedSeats.length + availableSeats.length) < targetCount) {{
                    return "NO_SEATS_LEFT_NEW";
                }}

                let now = Date.now();

                // 🔥 (6) 優先判定：右下角 SUBMIT 按鈕啟用或已選足張數 -> 送出！
                let confirmBtns = Array.from(document.querySelectorAll('button.EntButton_primary__UOX1_, button.entButtonGlobal, button'));
                let confirmBtn = confirmBtns.find(b => {{
                    let text = (b.innerText || "").trim().toUpperCase();
                    return (text === "SUBMIT" || text.includes("完成選擇") || text.includes("完成") || text === "선택완료") &&
                           !b.disabled && !b.hasAttribute('disabled');
                }});
                
                if (confirmBtn || selectedSeats.length >= targetCount) {{
                    if (!confirmBtn) return "WAITING_CONFIRM_BTN_NEW";
                    
                    // 送出後冷卻 3.5 秒，避免伺服器收到重複表單
                    if (window._nol_last_confirm_time && (now - window._nol_last_confirm_time < 3500)) {{
                        return "WAITING_CONFIRM_COOLDOWN";
                    }}

                    // 選完座後強迫等待 400 毫秒，等候 Interpark 鎖座 AJAX 成功
                    if (window._nol_last_seat_time && (now - window._nol_last_seat_time < 400)) {{
                        return "WAITING_API_LOCK_SETTLE";
                    }}

                    reactPointerClick(confirmBtn);
                    window._nol_last_confirm_time = now;
                    return "SUBMIT_CLICKED|" + selectedSeats.length;
                }}

                // 🔥 (7) 點擊可售空位：利用 PointerEvent 精準秒選第一顆空球
                if (!window._nol_last_seat_time || (now - window._nol_last_seat_time > 300)) {{
                    let targetSeat = availableSeats[0];
                    if (!targetSeat) return "NO_SEATS_LEFT_NEW";

                    reactPointerClick(targetSeat);
                    targetSeat.setAttribute('data-nol-picked', 'true');
                    window._nol_last_seat_time = now;

                    let seatId = targetSeat.getAttribute('id') || 'SEAT';
                    return "SEAT_CLICKED|" + seatId + "|" + (selectedSeats.length + 1) + "/" + targetCount;
                }}

                return "WAITING_CLICK_COOLDOWN";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        try:
            result = await active_tab.evaluate(js_seat_new)

            if isinstance(result, str):
                # 🎉 鎖票成功進入結帳頁
                if result == "TICKET_LOCKED_SUCCESS":
                    if not getattr(self, 'ticket_locked_printed', False):
                        print(
                            "\n>>> [NOL-新版] 🎉🎉🎉 鎖票成功！已進入 Select Price / Place Order 付款階段！")
                        print(">>> [系統] 🛡️ 機器人已完全停止點擊，請您安心在限制時間內完成付款！")
                        self.ticket_locked_printed = True
                        self.is_seat_selected = True
                    await asyncio.sleep(1.0)
                    return

                # ⚠️ 攔截到 Processing 吐司警告 -> 退避 1 秒並重置狀態
                elif result.startswith("TOAST_RATE_LIMIT|"):
                    print(
                        f">>> [NOL-新版] ⚠️ 攔截到系統提示: 【{result.split('|')[1]}】 -> 啟動防阻擋退避 1 秒...")
                    await active_tab.evaluate("window._nol_last_confirm_time = 0; window._nol_last_seat_time = 0;")
                    await asyncio.sleep(1.0)
                    return

                # 🪑 成功使用 PointerEvent 點擊座位
                elif result.startswith("SEAT_CLICKED|"):
                    parts = result.split("|")
                    seat_id = parts[1]
                    seat_progress = parts[2]
                    print(
                        f">>> [NOL-新版座位] 🪑 PointerEvent 成功選中第 {seat_progress} 張座位 ({seat_id})...")
                    await asyncio.sleep(0.15)

                # 🚀 成功點擊 SUBMIT
                elif result.startswith("SUBMIT_CLICKED|"):
                    count = result.split("|")[1]
                    print(
                        f">>> [NOL-新版座位] 🎯 已選滿 {count} 張，成功發送「Submit」請求！等待伺服器進入結帳頁...")
                    await asyncio.sleep(0.5)

                elif result == "NO_SEATS_LEFT_NEW":
                    if not hasattr(self, 'seat_new_wait_log'):
                        self.seat_new_wait_log = 0
                    self.seat_new_wait_log += 1
                    if self.seat_new_wait_log % 20 == 0:
                        print(">>> [NOL-新版座位] ❌ SVG 座位表上可選座位不足，強力監控釋票中...")
                    await asyncio.sleep(0.05)

        except Exception:
            pass

    # =========================================================================
    # 傳統舊版共用邏輯 (原樣保留)
    # =========================================================================

    async def step1_activity_page(self, active_tab):
        """[第一階段] 活動頁面點擊 Buy Now"""
        js_activity = """
        (function() {
            try {
                let closeBtn = document.querySelector('button.nds-e-modal-bottom-sheet__actionButton');
                if (closeBtn) closeBtn.click();

                let allBtns = Array.from(document.querySelectorAll('button.nds-e-rectangle-button--variant_filled_primary'));
                if (allBtns.length === 0) {
                    allBtns = Array.from(document.querySelectorAll('button')).filter(b => {
                        let text = (b.innerText || "").toUpperCase();
                        return text.includes('BUY NOW') || text.includes('立即购买') || text.includes('立即購票');
                    });
                }

                let visibleBtn = allBtns.find(b => {
                    let rect = b.getBoundingClientRect();
                    let style = window.getComputedStyle(b);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                });

                if (visibleBtn) {
                    if (!visibleBtn.disabled && !visibleBtn.hasAttribute('disabled')) {
                        visibleBtn.scrollIntoView({block: 'center', inline: 'center'});
                        visibleBtn.focus();
                        let pointerDown = new PointerEvent('pointerdown', { bubbles: true, cancelable: true, pointerType: 'mouse' });
                        let pointerUp = new PointerEvent('pointerup', { bubbles: true, cancelable: true, pointerType: 'mouse' });
                        let clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
                        visibleBtn.dispatchEvent(pointerDown);
                        visibleBtn.dispatchEvent(pointerUp);
                        visibleBtn.dispatchEvent(clickEvent);
                        visibleBtn.click();
                        return "CLICKED_BUY";
                    }
                    return "WAITING_BUY_ENABLE";
                }
                return "WAITING_DOM";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """
        result = await active_tab.evaluate(js_activity)
        if result == "CLICKED_BUY":
            print(">>> [NOL] 🚀 成功點擊「立即購買/Buy now」！準備進入排隊閘門...")
            await asyncio.sleep(1.0)

    async def step2_waiting_gate(self, active_tab):
        """[第二階段] 排隊閘門通關"""
        js_gate = """
        (function() {
            try {
                let btn = document.querySelector('div.buttons > button') ||
                          document.querySelector('#root > div > main > div > div > div.buttons > button');
                if (btn) {
                    let isDisabled = btn.disabled || btn.classList.contains('_disabled_10rzo_34') || btn.hasAttribute('disabled');
                    let btnText = (btn.innerText || "").toUpperCase();
                    let isOpen = !isDisabled ||
                                 btnText.includes("BOOK NOW") ||
                                 btnText.includes("GET TICKET") ||
                                 btnText.includes("BUY") ||
                                 btnText === "예매하기";
                    if (isOpen) {
                        btn.removeAttribute('disabled');
                        btn.classList.remove('_disabled_10rzo_34');
                        btn.style.pointerEvents = "auto";
                        btn.focus();
                        btn.click();
                        btn.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true, pointerType: 'mouse' }));
                        btn.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true, pointerType: 'mouse' }));
                        btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                        return "SNIPER_CLICKED";
                    } else {
                        try { btn.click(); } catch(e) {}
                        return "WAITING_OPEN";
                    }
                }
                return "WAITING_DOM";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """
        result = await active_tab.evaluate(js_gate)
        if result == "SNIPER_CLICKED":
            print(">>> [NOL-排隊] ⚡ 開賣瞬間捕捉！防護網已強拆，穿透點擊成功發射！")
            await asyncio.sleep(1.0)
        elif result == "WAITING_OPEN":
            if not hasattr(self, 'gate_wait_log'):
                self.gate_wait_log = 0
            self.gate_wait_log += 1
            if self.gate_wait_log % 20 == 0:
                print(">>> [NOL-排隊] ⏳ 狙擊手就位... (同步啟動 20次/秒 盲狙模式探測中)")
            await asyncio.sleep(0.05)
        elif result == "WAITING_DOM":
            await asyncio.sleep(0.05)

    async def step3_select_date(self, active_tab):
        """[舊版第三階段] 日期選擇與下一步"""
        clean_date_keyword = self.date_keyword.replace(
            '"', '').replace("'", "").strip()
        js_date = f"""
        (function() {{
            try {{
                let doc = document;
                let frame = document.getElementById('ifrmBookStep');
                let targetWin = window;
                if (frame && frame.contentWindow && frame.contentWindow.document) {{
                    doc = frame.contentWindow.document;
                    targetWin = frame.contentWindow;
                }}
                if (!targetWin._ipHooked_Date) {{
                    targetWin._lastAlert = "";
                    targetWin.originalAlert = targetWin.alert;
                    targetWin.alert = function(msg) {{ targetWin._lastAlert = msg; }};
                    targetWin._ipHooked_Date = true;
                }}
                if (targetWin._lastAlert !== "") {{
                    let msg = targetWin._lastAlert;
                    targetWin._lastAlert = "";
                    window._nol_date_clicked = false;
                    window._nol_next_clicked = false;
                    return "ALERT|" + msg;
                }}
                const targetDateRaw = '{clean_date_keyword}';
                const targetDateNum = parseInt(targetDateRaw.replace(/[^0-9]/g, ''), 10);
                const isBlank = targetDateRaw === "";
                let dateCells = Array.from(doc.querySelectorAll('a#CellPlayDate, a[name="CellPlayDate"]'))
                                     .concat(Array.from(document.querySelectorAll('a#CellPlayDate, a[name="CellPlayDate"]')));

                if (dateCells.length > 0) {{
                    let foundDate = false;
                    for (let cell of dateCells) {{
                        let cellText = (cell.childNodes.length > 0 && cell.childNodes[0].nodeType === 3)
                                       ? cell.childNodes[0].nodeValue : cell.innerText;
                        let cellNum = parseInt(cellText.replace(/[^0-9]/g, ''), 10);
                        if (!isNaN(cellNum)) {{
                            if (isBlank || cellNum === targetDateNum) {{
                                foundDate = true;
                                if (!window._nol_date_clicked) {{
                                    cell.click();
                                    window._nol_date_clicked = true;
                                    return "DATE_CLICKED|" + cellNum;
                                }}
                                let nextBtn = doc.querySelector('#LargeNextBtnImage') ||
                                              document.querySelector('#LargeNextBtnImage') ||
                                              doc.querySelector('img[src*="btn_next_on"]') ||
                                              document.querySelector('img[src*="btn_next_on"]');
                                if (nextBtn) {{
                                    if (!window._nol_next_clicked) {{
                                        let parentA = nextBtn.closest('a');
                                        parentA ? parentA.click() : nextBtn.click();
                                        window._nol_next_clicked = true;
                                        window._nol_next_click_time = Date.now();
                                        return "NEXT_CLICKED";
                                    }}
                                }}
                                if (window._nol_next_clicked && (Date.now() - window._nol_next_click_time > 5000)) {{
                                    window._nol_next_clicked = false;
                                }}
                                return "WAITING_TRANSITION";
                            }}
                        }}
                    }}
                    if (!foundDate) return "DATE_NOT_FOUND";
                }}
                return "WAITING_DOM";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        result = await active_tab.evaluate(js_date)
        if isinstance(result, str):
            if result.startswith("ALERT|"):
                print(f">>> [系統] 💥 攔截到警告: 【{result.split('|')[1]}】，已解除鎖定。")
                self.is_date_selected = False
                await asyncio.sleep(0.1)
            elif result.startswith("DATE_CLICKED|"):
                print(
                    f">>> [NOL-日期] 📅 已點選日期「{result.split('|')[1]}號」，尋找下一步...")
            elif result == "NEXT_CLICKED":
                print(">>> [NOL-日期] 🚀 已點擊下一步！強制鎖定，將控制權切換至座位掃描...")
                self.is_date_selected = True

    async def step4_select_seat(self, active_tab):
        """[舊版第四階段] 座位選擇 (含餘票不足防卡死)"""
        ticket_number = self.ticket_number
        js_seat = f"""
        (function() {{
            try {{
                let doc = document;
                let frame = document.getElementById('ifrmBookStep');
                if (frame && frame.contentWindow) {{
                    try {{ doc = frame.contentWindow.document; }} catch(e) {{}}
                }}
                let divSeat = doc.getElementById('divBookSeat') || document.getElementById('divBookSeat');
                if (!divSeat || window.getComputedStyle(divSeat).display === 'none') {{
                    return "WAITING_PHASE_SWITCH";
                }}
                let ifrmSeat = doc.getElementById('ifrmSeat') || document.getElementById('ifrmSeat');
                if (!ifrmSeat) return "WAITING_IFRAME_1";

                let seatDoc1;
                try {{
                    seatDoc1 = ifrmSeat.contentWindow.document;
                    if (!ifrmSeat.contentWindow._ipHooked_Seat) {{
                        ifrmSeat.contentWindow._lastAlert = "";
                        ifrmSeat.contentWindow.originalAlert = ifrmSeat.contentWindow.alert;
                        ifrmSeat.contentWindow.alert = function(msg) {{ ifrmSeat.contentWindow._lastAlert = msg; }};
                        ifrmSeat.contentWindow._ipHooked_Seat = true;
                    }}
                    if (ifrmSeat.contentWindow._lastAlert !== "") {{
                        let msg = ifrmSeat.contentWindow._lastAlert;
                        ifrmSeat.contentWindow._lastAlert = "";
                        window._nol_last_click_time = 0;
                        return "ALERT|" + msg;
                    }}
                }} catch(e) {{ return "WAITING_IFRAME_1_READY"; }}

                let seatDoc2 = seatDoc1;
                let ifrmSeatDetail = seatDoc1.getElementById('ifrmSeatDetail');
                if (ifrmSeatDetail) {{
                    try {{ seatDoc2 = ifrmSeatDetail.contentWindow.document; }}
                    catch(e) {{ return "WAITING_IFRAME_2_READY"; }}
                }}

                function isSelected(el) {{
                    let bw = el.style && el.style.borderWidth;
                    let hasBorder = !!bw && bw !== '0px' && bw !== '';
                    return hasBorder || el.classList.contains('selected') || el.classList.contains('active');
                }}

                let allSeatN = Array.from(seatDoc2.querySelectorAll('span.SeatN'));
                if (allSeatN.length === 0) allSeatN = Array.from(seatDoc1.querySelectorAll('span.SeatN'));
                if (allSeatN.length === 0) allSeatN = Array.from(doc.querySelectorAll('span.SeatN'));

                let seatMapTable = seatDoc2.querySelector('#TmgsTable') || seatDoc1.querySelector('#TmgsTable');
                if (!seatMapTable && allSeatN.length === 0) return "WAITING_SEAT_MAP";

                let selectedSeats = allSeatN.filter(isSelected);
                let availableSeats = allSeatN.filter(el => !isSelected(el));
                const targetCount = {ticket_number};

                if ((selectedSeats.length + availableSeats.length) < targetCount) {{
                    window._nol_last_click_time = 0;
                    return "NO_SEATS_LEFT";
                }}

                if (selectedSeats.length >= targetCount) {{
                    let nextBtn = seatDoc1.querySelector('#NextStepImage') ||
                                  seatDoc1.querySelector('img[src*="btn_seat_confirm"]') ||
                                  doc.querySelector('#NextStepImage') ||
                                  doc.querySelector('img[src*="btn_seat_confirm"]');
                    if (nextBtn) {{
                        let parentA = nextBtn.closest('a');
                        parentA ? parentA.click() : nextBtn.click();
                        return "SEAT_SELECTED|" + selectedSeats.length;
                    }}
                    return "WAITING_NEXT_BTN";
                }}

                if (availableSeats.length > 0) {{
                    let now = Date.now();
                    if (!window._nol_last_click_time || (now - window._nol_last_click_time > 150)) {{
                        availableSeats[0].click();
                        window._nol_last_click_time = now;
                        return "SEAT_CLICKED|" + (selectedSeats.length + 1) + "/" + targetCount;
                    }}
                    return "WAITING_CLICK_COOLDOWN";
                }}

                window._nol_last_click_time = 0;
                return "NO_SEATS_LEFT";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        result = await active_tab.evaluate(js_seat)
        if isinstance(result, str):
            if result.startswith("ALERT|"):
                await active_tab.evaluate("window._nol_last_click_time = 0;")
                await asyncio.sleep(0.1)
            elif result.startswith("SEAT_CLICKED|"):
                print(f">>> [NOL-座位] 🪑 已選取第 {result.split('|')[1]} 張座位...")
                await asyncio.sleep(0.1)
            elif result.startswith("SEAT_SELECTED|"):
                print(
                    f">>> [NOL-座位] 🎯 已選滿 {result.split('|')[1]} 張座位並送出！等待跳轉...")
                await asyncio.sleep(0.5)

# ==========================================
# [公園 搶票 半自動]
# ==========================================


class NolBot_AUTO:

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態變數鎖
        self.is_activity_clicked = False
        self.is_gate_passed = False
        self.is_date_selected = False
        self.is_seat_selected = False

        # 日期關鍵字設定 (例如 "2")
        self.date_keyword = str(self.config.get(
            "date_auto_select", {}).get("date_keyword", "2")).strip()
        self.refresh_sec = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.1))
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

    async def run(self):
        print(
            f">>> [NOL 公園全自動] 機器人啟動！(目標張數: {self.ticket_number} | 鎖定日期: {self.date_keyword})")
        print(">>> [系統] 🛡️ 已啟動「動態分頁追蹤」與「手動接管無縫接軌」模式！")
        import asyncio

        while True:
            try:
                # ==========================================
                # 🔥 新增：暫停攔截機制
                # ==========================================
                if os.path.exists(self.PAUSE_FILE):
                    if not getattr(self, 'is_printing_pause', False):
                        print("\n>>> [NOL 自動化] ⏸️ 程式已暫停！(已停止自動重整與點擊，等待接續...)")
                        self.is_printing_pause = True
                    await asyncio.sleep(0.5)
                    continue
                self.is_printing_pause = False

                # ------------------------------------------
                # 下面是你原本的 Nol 自動化邏輯 (例如獲取 tab、自動刷票、點擊座位等)
                # ------------------------------------------
                active_tab = self.driver.tabs[-1]
                current_url = await active_tab.evaluate("window.location.href")

                # 動態調整掃描頻率
                loop_delay = 0.05
                if "BOOKMAIN.ASP" in current_url.upper():
                    loop_delay = 0.03  # 進入選位區，全力衝刺
                elif "WAITING" in current_url.upper():
                    loop_delay = 0.5   # 排隊中，放慢速度降低 CPU 負載與特徵

                await self.dispatch_action(current_url, active_tab)
                await asyncio.sleep(loop_delay)
            except:
                await asyncio.sleep(0.1)

    async def dispatch_action(self, url, active_tab):
        """NOL 任務分發中心 (修正圖層判斷優先級，完美支援上一頁與逾時重啟)"""
        upper_url = url.upper()

        if 'WORLD.NOL.COM' in upper_url:
            # 🔥 [新增] 被踢回首頁時，徹底洗掉進度標記，完成閉環重啟
            if getattr(self, 'is_date_selected', False) or getattr(self, 'is_area_selected', False) or getattr(self, 'is_seat_selected', False):
                print(">>> [系統] 🔄 偵測到回到活動頁，已重置所有狀態，準備發起新一輪排隊！")
                self.is_date_selected = False
                self.is_area_selected = False
                self.is_seat_selected = False
                self._step4_entered = False

            await self.step1_activity_page(active_tab)

        elif 'TICKETS.INTERPARK.COM/GATES' in upper_url:
            await self.step2_waiting_gate(active_tab)

        elif 'WAITINGSERVICESESSION.ASP' in upper_url:
            if not hasattr(self, 'queue_wait_log'):
                self.queue_wait_log = 0
            self.queue_wait_log += 1
            if self.queue_wait_log % 40 == 0:
                print(
                    ">>> [NOL-排隊] 🚶‍♂️ 正在神聖的排隊序列中！(機器人已進入待命保護模式，絕對不會重整，請靜候綠條跑完...)")
            import asyncio
            await asyncio.sleep(0.05)

        elif 'GPOTICKET.GLOBALINTERPARK.COM' in upper_url and 'BOOKMAIN.ASP' in upper_url:

            # ========================================================
            # 🔥 [新增] 頂層全域彈窗攔截：處理 9分鐘警告 與 10分鐘踢出彈窗
            # ========================================================
            js_global_alert = """
            (function() {
                if (!window._topAlertHooked) {
                    window._topLastAlert = "";
                    // 攔截原生 alert，讓它不卡死執行緒，直接假裝按下 OK
                    window._originalTopAlert = window.alert;
                    window.alert = function(msg) { window._topLastAlert = msg; };
                    window._topAlertHooked = true;
                }
                let msg = window._topLastAlert;
                window._topLastAlert = "";
                return msg;
            })();
            """
            import asyncio
            top_alert = await active_tab.evaluate(js_global_alert)
            if top_alert:
                print(f">>> [系統] ⚠️ 攔截到網頁彈窗: 【{top_alert}】")
                if "1 minute" in top_alert or "1分鐘" in top_alert:
                    print(">>> [系統] ⏱️ 9分鐘警告！已自動按下 OK (隱藏彈窗)，繼續最後衝刺！")
                elif "expired" in top_alert or "逾時" in top_alert or "10-minute" in top_alert:
                    print(">>> [系統] 💀 10分鐘時間到！已自動按下 OK，等待被踢回活動頁面重啟循環...")
                    # 預先洗掉狀態，原網頁 JS 會在背後自動執行跳轉踢人
                    self.is_area_selected = False
                    self.is_seat_selected = False
                    self.is_date_selected = False

            # 以下保留你原本的 js_check_phase 邏輯
            js_check_phase = """
            (function() {
                try {
                    let doc = document;
                    let seatFrame = document.getElementById('ifrmSeat');
                    let seatDoc = seatFrame && seatFrame.contentWindow ? seatFrame.contentWindow.document : null;

                    // 1. 穿透檢查：驗證碼是否真實可見？
                    let captchaDiv = doc.querySelector('.capchaInner');
                    if (!captchaDiv && seatDoc) {
                        captchaDiv = seatDoc.querySelector('.capchaInner');
                    }

                    if (captchaDiv) {
                        // 🔥 嚴格檢查：必須不是 display: none 且 visibility 不是 hidden
                        let style = window.getComputedStyle(captchaDiv);
                        if (seatDoc && captchaDiv.ownerDocument === seatDoc) {
                            style = seatDoc.defaultView.getComputedStyle(
                                captchaDiv);
                        }

                        if (style.display !== 'none' && style.visibility !== 'hidden' && captchaDiv.offsetWidth > 0) {
                            return "CAPTCHA_PHASE";
                        }
                    }

                    // 2. 如果驗證碼消失了，才判斷是日期還是座位階段
                    let divMain = doc.getElementById('divBookMain');
                    let divSeat = doc.getElementById('divBookSeat');

                    let mainDisplay = divMain ? window.getComputedStyle(divMain).display : 'none';
                    let seatDisplay = divSeat ? window.getComputedStyle(divSeat).display : 'none';

                    if (mainDisplay !== 'none') {
                        return "DATE_PHASE";
                    }
                    else if (seatDisplay !== 'none') {
                        return "SEAT_PHASE";
                    }

                    return "WAITING";
                } catch(e) { return "WAITING"; }
            })();
            """
            phase = await active_tab.evaluate(js_check_phase)

            if phase == "CAPTCHA_PHASE":
                await self.step3_5_solve_captcha(active_tab)

            elif phase == "DATE_PHASE":
                if getattr(self, 'is_seat_selected', False) or getattr(self, 'is_area_selected', False):
                    print(">>> [系統] 偵測到返回操作！啟動 2.5 秒防禦冷卻，清洗機器人特徵...")
                    self.is_seat_selected = False
                    self.is_area_selected = False
                    await asyncio.sleep(3)  # 🔥 強制大洗牌冷卻
                    try:
                        await active_tab.evaluate("window._nol_seat_clicked = false;")
                    except:
                        pass
                await self.step3_select_date(active_tab)

            elif phase == "SEAT_PHASE":
                if not getattr(self, 'is_area_selected', False):
                    await self.step3_8_select_area(active_tab)
                else:
                    await self.step4_select_seat(active_tab)

            else:
                await asyncio.sleep(0.05)

    async def step1_activity_page(self, active_tab):
        """[第一階段] 關閉底部彈窗並點擊 Buy Now / 立即購買"""
        js_activity = """
        (function() {
            try {
                // 1. 關閉底部干擾彈窗
                let closeBtn = document.querySelector('button.nds-e-modal-bottom-sheet__actionButton');
                if (closeBtn) closeBtn.click();

                // 2. 抓取所有符合特徵的按鈕 (先用精確 Class，若無則用語意化文本)
                let allBtns = Array.from(document.querySelectorAll('button.nds-e-rectangle-button--variant_filled_primary'));

                if (allBtns.length === 0) {
                    allBtns = Array.from(document.querySelectorAll('button')).filter(b => {
                        let text = (b.innerText || "").toUpperCase();
                        return text.includes('BUY NOW') || text.includes('立即购买') || text.includes('立即購票');
                    });
                }

                // 3. 🎯 核心修正：過濾出「真正在畫面上可見」的按鈕 (排除隱藏的 RWD 備用按鈕)
                let visibleBtn = allBtns.find(b => {
                    let rect = b.getBoundingClientRect();
                    let style = window.getComputedStyle(b);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                });

                if (visibleBtn) {
                    // 不再檢查 Tailwind 的 css class，只檢查真實的 HTML disabled 屬性
                    if (!visibleBtn.disabled && !visibleBtn.hasAttribute('disabled')) {

                        // 4. 🔥 發送完整的模擬滑鼠點擊事件 (破解 React 框架的事件攔截)
                        visibleBtn.scrollIntoView(
                            {block: 'center', inline: 'center'});
                        visibleBtn.focus();

                        let pointerDown = new PointerEvent('pointerdown', { bubbles: true, cancelable: true, pointerType: 'mouse' });
                        let pointerUp = new PointerEvent('pointerup', { bubbles: true, cancelable: true, pointerType: 'mouse' });
                        let clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });

                        visibleBtn.dispatchEvent(pointerDown);
                        visibleBtn.dispatchEvent(pointerUp);
                        visibleBtn.dispatchEvent(clickEvent);
                        visibleBtn.click(); // 保底點擊

                        return "CLICKED_BUY";
                    }
                    return "WAITING_BUY_ENABLE";
                }
                return "WAITING_DOM";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """
        import asyncio
        result = await active_tab.evaluate(js_activity)
        if result == "CLICKED_BUY":
            print(">>> [NOL] 🚀 成功點擊「立即購買/Buy now」！準備進入排隊閘門...")
            # 增加跳轉緩衝時間，避免在原頁面瘋狂重複觸發點擊
            await asyncio.sleep(1.0)

    async def step2_waiting_gate(self, active_tab):
        """[第二階段] 排隊閘門 (伺服器對時極限狙擊 + 20CPS 脈衝盲狙備用方案)"""
        js_gate = """
        (function() {
            try {
                // 精準鎖定排隊閘門的按鈕
                let btn = document.querySelector('div.buttons > button') ||
                          document.querySelector(
                              '#root > div > main > div > div > div.buttons > button');

                if (btn) {
                    let isDisabled = btn.disabled ||
                                     btn.classList.contains('_disabled_10rzo_34') ||
                                     btn.hasAttribute('disabled');
                    let btnText = (btn.innerText || "").toUpperCase();

                    // 🛡️ 防禦升級：擴大判定範圍。只要出現以下任何字眼，都視為開賣！
                    let isOpen = !isDisabled ||
                                 btnText.includes("BOOK NOW") ||
                                 btnText.includes("GET TICKET") ||
                                 btnText.includes("BUY") ||
                                 btnText === "예매하기";

                    if (isOpen) {
                        // ==========================================
                        // 🔥 狙擊發動：強拆防護網與穿透點擊
                        // ==========================================
                        btn.removeAttribute('disabled');
                        btn.classList.remove('_disabled_10rzo_34');
                        btn.style.pointerEvents = "auto";

                        btn.focus();
                        btn.click();

                        let pointerDown = new PointerEvent('pointerdown', { bubbles: true, cancelable: true, pointerType: 'mouse' });
                        let pointerUp = new PointerEvent('pointerup', { bubbles: true, cancelable: true, pointerType: 'mouse' });
                        let clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });

                        btn.dispatchEvent(pointerDown);
                        btn.dispatchEvent(pointerUp);
                        btn.dispatchEvent(clickEvent);

                        return "SNIPER_CLICKED";
                    } else {
                        // ==========================================
                        // 🔫 備用方案 (Plan B)：20 CPS 脈衝盲狙
                        // ==========================================
                        // 就算我們判定還沒開賣，依然每 0.05 秒對它發送一次最基本的點擊。
                        // 只要網站偷偷解鎖，這發盲狙就能立功！
                        try { btn.click(); } catch(e) {}

                        return "WAITING_OPEN";
                    }
                }
                return "WAITING_DOM";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """

        import asyncio
        result = await active_tab.evaluate(js_gate)

        if result == "SNIPER_CLICKED":
            print(">>> [NOL-排隊] ⚡ 開賣瞬間捕捉！防護網已強拆，穿透點擊成功發射！")
            await asyncio.sleep(1.0)  # 給予跳轉緩衝，避免重複擊發

        elif result == "WAITING_OPEN":
            if not hasattr(self, 'gate_wait_log'):
                self.gate_wait_log = 0
            self.gate_wait_log += 1
            if self.gate_wait_log % 20 == 0:
                print(">>> [NOL-排隊] ⏳ 狙擊手就位... (同步啟動 20次/秒 盲狙模式探測中)")

            # 極速監控：維持 0.05 秒的超高頻率掃描與盲狙
            await asyncio.sleep(0.05)

        elif result == "WAITING_DOM":
            await asyncio.sleep(0.05)

    async def step3_select_date(self, active_tab):
        """[第三階段] 專職：日期選擇 (修復空白自動點選首個日期 Bug)"""
        clean_date_keyword = self.date_keyword.replace(
            '"', '').replace("'", "").strip()

        js_date = f"""
        (function() {{
            try {{
                let doc = document;
                let frame = document.getElementById('ifrmBookStep');
                let targetWin = window;

                if (frame && frame.contentWindow && frame.contentWindow.document) {{
                    doc = frame.contentWindow.document;
                    targetWin = frame.contentWindow;
                }}

                if (!targetWin._ipHooked_Date) {{
                    targetWin._lastAlert = "";
                    targetWin.originalAlert = targetWin.alert;
                    targetWin.alert = function(msg) {{ targetWin._lastAlert = msg; }};
                    targetWin._ipHooked_Date = true;
                }}
                if (targetWin._lastAlert !== "") {{
                    let msg = targetWin._lastAlert;
                    targetWin._lastAlert = "";
                    window._nol_date_clicked = false;
                    window._nol_next_clicked = false;
                    return "ALERT|" + msg;
                }}

                const targetDateRaw = '{clean_date_keyword}';
                const targetDateNum = parseInt(targetDateRaw.replace(/[^0-9]/g, ''), 10);

                // 🔥 新增：判斷設定是否為空白
                const isBlank = targetDateRaw === "";

                let dateCells = Array.from(doc.querySelectorAll('a#CellPlayDate, a[name="CellPlayDate"]'))
                                .concat(Array.from(document.querySelectorAll('a#CellPlayDate, a[name="CellPlayDate"]')));

                if (dateCells.length > 0) {{
                    let foundDate = false;
                    for (let cell of dateCells) {{
                        let cellText = (cell.childNodes.length > 0 && cell.childNodes[0].nodeType === 3)
                                     ? cell.childNodes[0].nodeValue : cell.innerText;
                        let cellNum = parseInt(cellText.replace(/[^0-9]/g, ''), 10);

                        // 🔥 修正邏輯：如果日期有數字，且 (設定是空白 OR 數字相符) 就點擊！
                        if (!isNaN(cellNum)) {{
                            if (isBlank || cellNum === targetDateNum) {{
                                foundDate = true;

                                if (!window._nol_date_clicked) {{
                                    cell.click();
                                    window._nol_date_clicked = true;
                                    return "DATE_CLICKED|" + cellNum;
                                }}

                                let nextBtn = doc.querySelector('#LargeNextBtnImage') || document.querySelector('#LargeNextBtnImage') ||
                                              doc.querySelector('img[src*="btn_next_on"]') || document.querySelector('img[src*="btn_next_on"]');
                                if (nextBtn) {{
                                    if (!window._nol_next_clicked) {{
                                        let parentA = nextBtn.closest('a');
                                        parentA ? parentA.click() : nextBtn.click();
                                        window._nol_next_clicked = true;
                                        window._nol_next_click_time = Date.now();
                                        return "NEXT_CLICKED";
                                    }}
                                }}

                                if (window._nol_next_clicked && (Date.now() - window._nol_next_click_time > 5000)) {{
                                    window._nol_next_clicked = false;
                                }}
                                return "WAITING_TRANSITION";
                            }}
                        }}
                    }}
                    if (!foundDate) return "DATE_NOT_FOUND";
                }}
                return "WAITING_DOM";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        import asyncio
        result = await active_tab.evaluate(js_date)

        if isinstance(result, str):
            if result.startswith("ALERT|"):
                print(f">>> [系統] 💥 攔截到警告: 【{result.split('|')[1]}】，已解除鎖定。")
                self.is_date_selected = False  # 被退回就取消通關標記
                await asyncio.sleep(0.1)

            elif result.startswith("DATE_CLICKED|"):
                print(
                    f">>> [NOL-日期] 📅 已點選日期「{result.split('|')[1]}號」，尋找下一步...")

            elif result == "NEXT_CLICKED":
                print(">>> [NOL-日期] 🚀 已點擊下一步！強制鎖定，將控制權切換至座位掃描...")
                self.is_date_selected = True

            elif result == "DATE_NOT_FOUND":
                if not hasattr(self, 'date_not_found_log'):
                    self.date_not_found_log = 0
                self.date_not_found_log += 1
                if self.date_not_found_log % 20 == 0:
                    keyword_display = clean_date_keyword if clean_date_keyword else "[空白/隨機首日]"
                    print(f">>> [NOL-日期] ⚠️ 找不到設定的日期: {keyword_display}")

    async def step3_5_solve_captcha(self, active_tab):
        """[第 3.5 階段] 專職：破解防不當訂票驗證碼 (修復 display:none 對焦與打字亂碼 Bug)"""
        import asyncio
        import base64
        import re
        import random

        js_captcha = """
        (function() {
            try {
                let doc = document;
                let frame = document.getElementById('ifrmSeat');
                if (frame && frame.contentWindow) {
                    doc = frame.contentWindow.document;
                }

                let captchaImg = doc.getElementById('imgCaptcha');
                let captchaInput = doc.getElementById('txtCaptcha');

                // 如果找不到元素，直接跳出等 DOM 載入
                if (!captchaImg || !captchaInput) return "WAITING_DOM";

                // 檢查圖片是否已經載入 base64
                if (!captchaImg.src || !captchaImg.src.includes('base64')) {
                    return "WAITING_IMG";
                }

                // 如果已經標記為送出中
                if (window._nol_captcha_submitted) {
                    return "SUBMITTING_WAIT";
                }

                return "CAPTCHA_PENDING|" + captchaImg.src;

            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """

        try:
            result = await active_tab.evaluate(js_captcha)

            if isinstance(result, str):
                if result.startswith("WAITING_"):
                    await asyncio.sleep(0.1)
                    return

                elif result == "SUBMITTING_WAIT":
                    check_fail_js = """
                    (function() {
                        let doc = document;
                        let frame = document.getElementById('ifrmSeat');
                        let win = window;
                        if (frame && frame.contentWindow) {
                            doc = frame.contentWindow.document;
                            win = frame.contentWindow;
                        }

                        // 參考插件 hooks.js：檢查是否有產出 sessionID 或驗證通過標記
                        let isVerified = win.isCaptchaVerified === true ||
                                        (win.__BTS_GPO_INTERNAL__ && win.__BTS_GPO_INTERNAL__.store.captchaVerified);

                        if (isVerified) return "SUCCESS";

                        let captchaDiv = doc.querySelector('.capchaInner');
                        let input = doc.getElementById('txtCaptcha');

                        if (!captchaDiv || !input) return "SUCCESS";

                        // 檢查是否因為錯誤被清空
                        if (input.value === "" && window._nol_captcha_submitted) {
                            window._nol_captcha_submitted = false;
                            return "FAILED";
                        }
                        return "WAITING";
                    })();
                    """
                    status = await active_tab.evaluate(check_fail_js)

                    if status == "FAILED":
                        print(">>> [NOL-驗證碼] ⚠️ 驗證碼錯誤，系統已自動刷新圖片，準備重新辨識...")
                        self.last_captcha_src = ""
                        await asyncio.sleep(0.3)
                    elif status == "SUCCESS":
                        print(">>> [NOL-驗證碼] 🎉 驗證成功！視窗已消失，準備進入區域選擇...")
                        await active_tab.evaluate("window._nol_captcha_submitted = false;")
                        await asyncio.sleep(0.2)
                    else:
                        await asyncio.sleep(0.1)
                    return

                elif result.startswith("CAPTCHA_PENDING|"):
                    base64_src = result.split("|")[1]

                    if getattr(self, 'last_captcha_src', '') == base64_src:
                        if not hasattr(self, 'captcha_wait_count'):
                            self.captcha_wait_count = 0
                        self.captcha_wait_count += 1
                        if self.captcha_wait_count > 10:
                            print(">>> [NOL-驗證碼] ⚠️ 驗證碼疑似卡住，嘗試自動點擊刷新按鈕換圖...")
                            refresh_js = """
                                (function() {
                                    let doc = document;
                                    let frame = document.getElementById('ifrmSeat');
                                    if (frame && frame.contentWindow) doc = frame.contentWindow.document;
                                    let refreshBtn = doc.querySelector('a.refreshBtn') || doc.querySelector('a[onclick*="fnCapchaRefresh"]');
                                    if (refreshBtn) refreshBtn.click();
                                })();
                            """
                            await active_tab.evaluate(refresh_js)
                            self.captcha_wait_count = 0
                            await asyncio.sleep(0.5)
                        return

                    self.last_captcha_src = base64_src
                    print(">>> [NOL-驗證碼] 🛡️ 遭遇驗證碼防線！啟動 ddddocr 嘗試破解...")

                    try:
                        if getattr(self, 'ocr', None) is None:
                            print(">>> [NOL-驗證碼] ⚙️ 首次載入 ddddocr 模型...")
                            import ddddocr
                            self.ocr = ddddocr.DdddOcr(show_ad=False)

                        img_data = base64_src.split(
                            ',')[1] if ',' in base64_src else base64_src
                        img_bytes = base64.b64decode(img_data)

                        raw_text = self.ocr.classification(img_bytes)
                        clean_text = re.sub(r'[^A-Za-z]', '', raw_text).upper()

                        print(
                            f">>> [NOL-驗證碼] 🤖 ddddocr 辨識結果: 【{clean_text}】 (原始: {raw_text}, 長度: {len(clean_text)})")

                        if len(clean_text) == 6:
                            # =========================================================
                            # 🔥 核心修正 1：針對 display:none 的暴力拆解與座標轉移
                            # =========================================================
                            get_coords_js = """
                            (function() {
                                let doc = document;
                                let frame = document.getElementById('ifrmSeat');
                                if (frame && frame.contentWindow) doc = frame.contentWindow.document;

                                let input = doc.getElementById('txtCaptcha');
                                let submitBtn = doc.querySelector('.capchaBtns a[onclick*="fnCheck"]');

                                if (input && submitBtn) {
                                    // 強制拔除隱藏屬性，並主動上焦
                                    input.style.display = 'inline-block';
                                    input.value = '';
                                    input.focus();

                                    // 抓取包含 input 的外層框 .validationTxt (這是人類真正點擊的視覺目標)
                                    let clickTarget = doc.querySelector('.validationTxt') || input;

                                    function getAbsCenter(el) {
                                        el.scrollIntoView(
                                            {block: 'center', inline: 'center'});
                                        let rect = el.getBoundingClientRect();

                                        // 預防萬一寬高是 0，改抓父元素的寬高
                                        if (rect.width === 0 && el.parentElement) {
                                            rect = el.parentElement.getBoundingClientRect();
                                        }

                                        let x = rect.left + rect.width / 2;
                                        let y = rect.top + rect.height / 2;
                                        let win = doc.defaultView || window;
                                        while (win && win !== window.top) {
                                            if (win.frameElement) {
                                                let fRect = win.frameElement.getBoundingClientRect();
                                                x += fRect.left;
                                                y += fRect.top;
                                            }
                                            win = win.parent;
                                        }
                                        return Math.round(x) + "|" + Math.round(y);
                                    }
                                    return getAbsCenter(clickTarget) + "|" + getAbsCenter(submitBtn);
                                }
                                return false;
                            })();
                            """
                            coords = await active_tab.evaluate(get_coords_js)

                            if coords and isinstance(coords, str):
                                parts = coords.split("|")
                                ix, iy = int(parts[0]), int(
                                    parts[1])  # 視覺輸入框容器的座標
                                sx, sy = int(parts[2]), int(
                                    parts[3])  # 送出按鈕的座標

                                import nodriver.cdp.input_ as cdp_input
                                mouse_btn = cdp_input.MouseButton.LEFT

                                # 1. 真實滑鼠移動並點擊「視覺容器」，觸發網頁原生對焦機制
                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=ix, y=iy))
                                await asyncio.sleep(0.05)
                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mousePressed", x=ix, y=iy, button=mouse_btn, click_count=1))
                                await asyncio.sleep(random.uniform(0.03, 0.08))
                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseReleased", x=ix, y=iy, button=mouse_btn, click_count=1))
                                await asyncio.sleep(0.1)  # 給予游標閃爍反應時間

                                # =========================================================
                                # 🔥 核心修正 2：淨化鍵盤敲擊事件，根除打字亂碼
                                # =========================================================
                                for char in clean_text:
                                    # 只送出 keyDown 與 keyUp，讓 Chrome 自行產生字元，不重複發送 char
                                    await active_tab.send(cdp_input.dispatch_key_event(type_="keyDown", text=char))
                                    await asyncio.sleep(random.uniform(0.01, 0.03))
                                    await active_tab.send(cdp_input.dispatch_key_event(type_="keyUp", text=char))
                                    # 擬真人打字停頓
                                    await asyncio.sleep(random.uniform(0.05, 0.12))

                                await asyncio.sleep(0.1)

                                # 3. 生成滑鼠軌跡滑動到「送出」按鈕
                                steps = random.randint(8, 12)
                                for i in range(steps):
                                    t = i / steps
                                    ease_t = t * (2 - t)
                                    cur_x = ix + (sx - ix) * \
                                        ease_t + random.uniform(-2, 2)
                                    cur_y = iy + (sy - iy) * \
                                        ease_t + random.uniform(-2, 2)
                                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=int(cur_x), y=int(cur_y)))
                                    await asyncio.sleep(random.uniform(0.008, 0.012))

                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=sx, y=sy))
                                await asyncio.sleep(random.uniform(0.05, 0.1))

                                # 4. 真實滑鼠點擊送出
                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mousePressed", x=sx, y=sy, button=mouse_btn, click_count=1))
                                await asyncio.sleep(random.uniform(0.05, 0.1))
                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseReleased", x=sx, y=sy, button=mouse_btn, click_count=1))

                                await active_tab.evaluate("window._nol_captcha_submitted = true;")
                                print(
                                    ">>> [NOL-驗證碼] 🚀 已透過 CDP 真實打字並送出！等待伺服器放行...")

                        else:
                            print(
                                f">>> [NOL-驗證碼] ⚠️ 辨識結果長度異常 ({len(clean_text)} 個字)，直接自動刷新換圖...")
                            refresh_js = """
                                (function() {
                                    let doc = document;
                                    let frame = document.getElementById('ifrmSeat');
                                    if (frame && frame.contentWindow) doc = frame.contentWindow.document;

                                    let refreshBtn = doc.querySelector('a.refreshBtn') ||
                                                     doc.querySelector('a[onclick*="fnCapchaRefresh"]');
                                    if (refreshBtn) refreshBtn.click();
                                })();
                            """
                            await active_tab.evaluate(refresh_js)
                            await asyncio.sleep(0.3)
                            self.last_captcha_src = ""

                    except Exception as ocr_err:
                        print(f">>> [NOL-驗證碼] ⚠️ 執行發生例外錯誤: {ocr_err}")
                        await asyncio.sleep(0.5)

        except Exception as e:
            pass

    def _mark_current_area_exhausted(self, cooldown_sec: float = 4.0):
        """把目前選中的區塊加進排除清單，冷卻為 4 秒"""
        import time
        if not hasattr(self, 'area_exclude'):
            self.area_exclude = {}
        key = getattr(self, 'current_area_key', None)
        if key:
            self.area_exclude[key] = time.time() + cooldown_sec
            print(
                f">>> [NOL-防呆] 🚫 區域【{key}】無可用座位，暫時排除 {cooldown_sec} 秒，繼續往後巡邏...")

    async def step3_8_select_area(self, active_tab):
        """[第 3.8 階段] 區域選擇 (真餘票極速狙擊 + 全場輪序記憶盲刷 + 跨層展開 VIP/R/S Seat)"""
        import asyncio
        import time
        import json
        import random

        if hasattr(self, 'last_area_action_time'):
            elapsed = time.time() - self.last_area_action_time
            if elapsed < 1.8:  # 換區節奏 1.8 秒
                await asyncio.sleep(random.uniform(1.8, 2.2) - elapsed)

        if not hasattr(self, 'area_exclude'):
            self.area_exclude = {}

        # 清除已過期的排除項目
        now = time.time()
        self.area_exclude = {k: v for k,
                             v in self.area_exclude.items() if v > now}
        excluded_keys = list(self.area_exclude.keys())
        js_excluded = json.dumps(excluded_keys, ensure_ascii=False)

        area_auto_select = self.config.get("area_auto_select", {})
        raw_keyword = area_auto_select.get("area_keyword", "").strip()
        area_mode = area_auto_select.get("mode", "from top to bottom").lower()

        keyword_list = [
            raw_keyword] if raw_keyword and not raw_keyword.startswith("[") else []
        if raw_keyword.startswith("["):
            try:
                keyword_list = json.loads(raw_keyword)
            except:
                keyword_list = [""]

        clean_keywords = [str(k).replace('"', '').replace(
            "'", "").strip() for k in keyword_list]
        js_keywords = json.dumps(clean_keywords, ensure_ascii=False)

        # 取得上一次點擊的記憶點，傳入 JS 進行輪循
        last_key = getattr(self, 'last_patrol_key', '')

        js_click_area = f"""
        (function() {{
            try {{
                let doc = document;
                let frame = document.getElementById('ifrmSeat');
                if (frame && frame.contentWindow) doc = frame.contentWindow.document;

                const keywords = {js_keywords}.map(k => k.trim().toUpperCase());
                const mode = "{area_mode}";
                const excluded = new Set({js_excluded});
                const lastKey = "{last_key}";

                let allGradeDetails = Array.from(doc.querySelectorAll('td[id="GradeDetail"]'));
                if (allGradeDetails.length === 0) return "WAITING_DOM";

                // --- 階段 1：真正有餘票的優先狙擊 (Priority Check) ---
                for (let detailTd of allGradeDetails) {{
                    let remainRaw = detailTd.getAttribute('remaincnt') || '0';
                    let remaincnt = parseInt(remainRaw.replace(/[^0-9]/g, ''), 10) || 0;
                    if (remaincnt <= 0) continue; 

                    let gradeName = (detailTd.getAttribute('seatgradename') || '').toUpperCase();
                    let isVisible = window.getComputedStyle(detailTd).display !== 'none';

                    // 該等級有票且已展開 -> 找出第一個未排除的區域秒殺！
                    if (isVisible) {{
                        let links = Array.from(detailTd.querySelectorAll('a[href*="fnBlockSeatUpdate"], a[onclick*="fnBlockSeatUpdate"]'));
                        for (let l of links) {{
                            let src = l.getAttribute('onclick') || l.getAttribute('href') || '';
                            let m = src.match(/fnBlockSeatUpdate\\([*'"]*,[*'"]*,[*'"]*([^'"]+)[*'"]*\\)/);
                            let blockId = m ? m[1] : l.innerText.trim();
                            let seatgrade = detailTd.getAttribute('seatgrade') || '';
                            let key = seatgrade + "-" + blockId;
                            let text = l.innerText.toUpperCase().replace(/\\s/g, '');

                            let isMatch = keywords.length === 0 || keywords[0] === "" ||
                                          keywords.some(k => text.includes(k) || gradeName.includes(k) || blockId.includes(k));
                            if (isMatch && !excluded.has(key)) {{
                                l.scrollIntoView({{block: 'center', inline: 'center'}});
                                l.dispatchEvent(new MouseEvent('click', {{ bubbles: true, cancelable: true, view: window }}));
                                return "CLICKED_REAL|" + key + "|" + gradeName + " " + l.innerText.trim();
                            }}
                        }}
                    }} else {{
                        // 該等級有票卻是被折疊的 -> 立刻點擊上方的大標題展開！
                        let gradeRow = detailTd.previousElementSibling;
                        if (gradeRow) {{
                            let swapBtn = gradeRow.querySelector('span.select') || gradeRow.querySelector('a') || gradeRow;
                            swapBtn.click();
                            return "EXPANDED_REAL_GRADE|" + gradeName;
                        }}
                    }}
                }}

                // --- 階段 2：全場 0 票時，同層輪序記憶盲刷與跨層展開 ---
                let currentGradeIdx = allGradeDetails.findIndex(td => window.getComputedStyle(td).display !== 'none');
                if (currentGradeIdx === -1) currentGradeIdx = 0;

                let currentDetailTd = allGradeDetails[currentGradeIdx];
                let currentGradeName = (currentDetailTd.getAttribute('seatgradename') || '').toUpperCase();
                let currentGradeNum = currentDetailTd.getAttribute('seatgrade') || '';

                // 收集當前展開等級中，所有符合關鍵字的區域
                let visibleLinks = Array.from(currentDetailTd.querySelectorAll('a[href*="fnBlockSeatUpdate"], a[onclick*="fnBlockSeatUpdate"]'));
                let validBlocks = [];
                for (let l of visibleLinks) {{
                    let src = l.getAttribute('onclick') || l.getAttribute('href') || '';
                    let m = src.match(/fnBlockSeatUpdate\\([*'"]*,[*'"]*,[*'"]*([^'"]+)[*'"]*\\)/);
                    let blockId = m ? m[1] : l.innerText.trim();
                    let key = currentGradeNum + "-" + blockId;
                    let text = l.innerText.toUpperCase().replace(/\\s/g, '');

                    let isMatch = keywords.length === 0 || keywords[0] === "" ||
                                  keywords.some(k => text.includes(k) || currentGradeName.includes(k) || blockId.includes(k));
                    if (isMatch) {{
                        validBlocks.push({{ el: l, text: l.innerText.trim(), key: key, gradeName: currentGradeName }});
                    }}
                }}

                let lastIdx = validBlocks.findIndex(b => b.key === lastKey);

                // 🔥 核心判斷：如果：
                // 1) 剛剛已經點到這個等級的「最後一個區域」(lastIdx === validBlocks.length - 1)，或者
                // 2) 這個等級沒有任何符合的區域 (validBlocks.length === 0)，
                // 我們就主動觸發切換到「下一個座位等級 (如 R -> S -> VIP)」！
                let shouldSwapGrade = (validBlocks.length === 0) || (lastIdx !== -1 && lastIdx === validBlocks.length - 1);

                // 嘗試在目前等級中，尋找「下一個未被排除」的區域 (Round-Robin 輪循)
                if (!shouldSwapGrade && validBlocks.length > 0) {{
                    let startIdx = (lastIdx === -1) ? 0 : (lastIdx + 1);
                    if (mode === "random") startIdx = Math.floor(Math.random() * validBlocks.length);

                    for (let i = 0; i < validBlocks.length; i++) {{
                        let idx = (startIdx + i) % validBlocks.length;
                        let target = validBlocks[idx];
                        if (!excluded.has(target.key)) {{
                            target.el.scrollIntoView({{block: 'center', inline: 'center'}});
                            target.el.dispatchEvent(new MouseEvent('click', {{ bubbles: true, cancelable: true, view: window }}));
                            return "CLICKED_BLIND|" + target.key + "|" + target.gradeName + " " + target.text;
                        }}
                    }}
                    // 如果跑完迴圈都沒有 return，代表當前等級所有符合的區域都在冷卻中 -> 觸發換層！
                    shouldSwapGrade = true;
                }}

                // --- 階段 3：執行跨層切換 (Swap Grade) ---
                if (shouldSwapGrade && allGradeDetails.length > 1) {{
                    for (let step = 1; step <= allGradeDetails.length; step++) {{
                        let nextIdx = (currentGradeIdx + step) % allGradeDetails.length;
                        let nextTd = allGradeDetails[nextIdx];
                        let nextGradeName = (nextTd.getAttribute('seatgradename') || '').toUpperCase();
                        
                        let gradeMatch = keywords.length === 0 || keywords[0] === "" ||
                                         keywords.some(k => nextGradeName.includes(k) || "VIP R S".includes(k) || k.length <= 4);
                        
                        if (gradeMatch) {{
                            let gradeRow = nextTd.previousElementSibling;
                            if (gradeRow) {{
                                let swapBtn = gradeRow.querySelector('span.select') || gradeRow.querySelector('a') || gradeRow;
                                swapBtn.click();
                                return "SWAPPED_GRADE|" + nextGradeName;
                            }}
                        }}
                    }}
                }}

                // 保底：如果都不符合，點擊當前清單的第一個維持刷新
                if (validBlocks.length > 0) {{
                    let target = validBlocks[0];
                    target.el.scrollIntoView({{block: 'center', inline: 'center'}});
                    target.el.dispatchEvent(new MouseEvent('click', {{ bubbles: true, cancelable: true, view: window }}));
                    return "CLICKED_FORCE|" + target.key + "|" + target.gradeName + " " + target.text;
                }}

                return "WAITING_DOM";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_click_area)

            if isinstance(result, str):
                if result.startswith("CLICKED_REAL|") or result.startswith("CLICKED_BLIND|") or result.startswith("CLICKED_FORCE|"):
                    parts = result.split("|")
                    self.last_patrol_key = parts[1]  # 🔥 記住本次點擊的位置
                    self.current_area_key = parts[1]
                    mode_msg = "⚡ 發現餘票" if "REAL" in result else "🔄 輪序盲刷"
                    print(
                        f">>> [NOL-區域] {mode_msg} -> 點擊區域：【{parts[2]}】(Key: {parts[1]})")
                    self.last_area_action_time = time.time()
                    self.is_area_selected = True
                    await asyncio.sleep(0.8)
                    return

                elif result.startswith("EXPANDED_REAL_GRADE|") or result.startswith("SWAPPED_GRADE|"):
                    parts = result.split("|")
                    grade_name = parts[1]
                    action_msg = "⚡ 偵測到餘票，展開等級" if "REAL" in result else "📂 當前等級巡邏完畢，自動切換展開等級"
                    print(
                        f">>> [NOL-區域] {action_msg}：【{grade_name}】(等待 AJAX 載入區域清單...)")
                    self.last_patrol_key = ""  # 🔥 換等級後重置記憶點，從新等級的第一個開始掃
                    self.last_area_action_time = time.time()
                    await asyncio.sleep(0.8)
                    return

        except Exception:
            pass

        if not getattr(self, 'is_area_selected', False):
            await asyncio.sleep(max(0.5, float(self.config.get("advanced", {}).get("auto_reload_page_interval", 0.5))))

    async def step4_select_seat_new(self, active_tab):
        """[新版第四階段] SVG 座位與 Submit 專用：CDP 真實物理滑鼠點擊 + 吐司警告防護"""
        import asyncio
        import time

        # 1. 剛切換至座位頁時給予 350ms 載入緩衝
        if not getattr(self, '_step4_new_entered', False):
            self._step4_new_entered = True
            self._step4_new_enter_time = time.time()
        if time.time() - self._step4_new_enter_time < 0.35:
            await asyncio.sleep(0.05)
            return

        # 2. 全局 CDP 點擊頻率限制 (最短間隔 250ms，避免滑鼠連點過速)
        if hasattr(self, 'last_cdp_new_click_time'):
            if time.time() - self.last_cdp_new_click_time < 0.25:
                await asyncio.sleep(0.05)
                return

        ticket_number = self.ticket_number
        js_seat_new = f"""
        (function() {{
            try {{
                // 🔥 (1) 保底成功攔截：網址含有 step=price 或出現 Select Price / Place Order
                let isPriceUrl = window.location.href.toLowerCase().includes('step=price');
                let priceWrap = document.querySelector('div[class*="PriceContent_layerWrap"], div[class*="Timer_timerMo"]');
                let orderBtn = Array.from(document.querySelectorAll('button')).find(b => {{
                    let text = (b.innerText || "").trim().toUpperCase();
                    return text === "PLACE ORDER" || text === "訂購" || text === "PAY";
                }});
                if (isPriceUrl || priceWrap || orderBtn) {{
                    return "TICKET_LOCKED_SUCCESS";
                }}

                // 🔥 (2) 偵測是否被 Toast 警告阻擋 ("Processing your request...")
                let toastEl = document.querySelector('div.nds-e-toast__content');
                if (toastEl && window.getComputedStyle(toastEl).display !== 'none') {{
                    let toastMsg = (toastEl.innerText || "").trim();
                    if (toastMsg.includes("Processing your request") || toastMsg.includes("try again")) {{
                        return "TOAST_RATE_LIMIT|" + toastMsg;
                    }}
                }}

                const targetCount = {ticket_number};
                let allSeats = Array.from(document.querySelectorAll('circle.js-seat'));
                if (allSeats.length === 0) return "WAITING_SVG_SEATS";

                function isDisabled(el) {{
                    return el.classList.contains('SeatMap_disabled__AZO_T') || el.getAttribute('fill') === '#edeff3';
                }}
                
                function isSelected(el) {{
                    return el.classList.contains('selected') || 
                           el.classList.contains('active') || 
                           el.getAttribute('data-selected') === 'true' ||
                           el.getAttribute('aria-pressed') === 'true';
                }}

                // 取得元素在當前視窗的絕對螢幕座標 (供 CDP 實體滑鼠使用)
                function getAbs(el) {{
                    let rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) return null;
                    return {{ x: Math.round(rect.left + rect.width / 2), y: Math.round(rect.top + rect.height / 2) }};
                }}

                let selectedSeats = allSeats.filter(isSelected);
                let availableSeats = allSeats.filter(el => !isDisabled(el) && !isSelected(el));

                if ((selectedSeats.length + availableSeats.length) < targetCount) {{
                    return "NO_SEATS_LEFT_NEW";
                }}

                let now = Date.now();

                // 🔥 (3) 已選滿目標張數 -> 回傳 SUBMIT 按鈕的座標進行 CDP 物理點擊
                if (selectedSeats.length >= targetCount) {{
                    // 送出冷卻鎖 3.5 秒，避免伺服器判定連點
                    if (window._nol_last_confirm_time && (now - window._nol_last_confirm_time < 3500)) {{
                        return "WAITING_CONFIRM_COOLDOWN";
                    }}

                    // 選座後強迫等候 600 毫秒，等候 Interpark 鎖座 API 與 React 狀態寫入完畢
                    if (window._nol_last_seat_time && (now - window._nol_last_seat_time < 600)) {{
                        return "WAITING_API_LOCK_SETTLE";
                    }}

                    let confirmBtns = Array.from(document.querySelectorAll('button.EntButton_primary__UOX1_, button.entButtonGlobal, button'));
                    let confirmBtn = confirmBtns.find(b => {{
                        let text = (b.innerText || "").trim().toUpperCase();
                        return (text === "SUBMIT" || text.includes("完成選擇") || text.includes("完成") || text === "선택완료") &&
                               !b.disabled && !b.hasAttribute('disabled');
                    }});
                    
                    if (confirmBtn) {{
                        let pos = getAbs(confirmBtn);
                        if (!pos) return "WAITING_BTN_VISIBILITY";
                        window._nol_last_confirm_time = now;
                        return "READY_SUBMIT|" + pos.x + "|" + pos.y + "|" + selectedSeats.length;
                    }}
                    return "WAITING_CONFIRM_BTN_NEW";
                }}

                // 🔥 (4) 張數未滿 -> 回傳 SVG 座位圓點的座標進行 CDP 物理點擊
                if (!window._nol_last_seat_time || (now - window._nol_last_seat_time > 200)) {{
                    let targetSeat = availableSeats[0];
                    let pos = getAbs(targetSeat);
                    if (!pos) return "WAITING_SEAT_VISIBILITY";

                    targetSeat.setAttribute('data-selected', 'true');
                    window._nol_last_seat_time = now;
                    return "READY_SEAT|" + pos.x + "|" + pos.y + "|" + (selectedSeats.length + 1) + "/" + targetCount;
                }}

                return "WAITING_CLICK_COOLDOWN";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        try:
            result = await active_tab.evaluate(js_seat_new)

            if isinstance(result, str):
                import nodriver.cdp.input_ as cdp_input
                mouse_btn = cdp_input.MouseButton.LEFT

                # 🎉 成功鎖票進付款頁
                if result == "TICKET_LOCKED_SUCCESS":
                    if not getattr(self, 'ticket_locked_printed', False):
                        print(
                            "\n>>> [NOL-新版] 🎉🎉🎉 鎖票成功！已進入 Select Price / Place Order 付款階段！")
                        print(">>> [系統] 🛡️ 機器人已完全停止點擊，請您安心在限制時間內完成付款！")
                        self.ticket_locked_printed = True
                        self.is_seat_selected = True
                    await asyncio.sleep(1.0)
                    return

                # ⚠️ 攔截到 Processing 吐司警告 -> 冷卻 1 秒並重置點擊狀態
                elif result.startswith("TOAST_RATE_LIMIT|"):
                    print(
                        f">>> [NOL-新版] ⚠️ 攔截到系統提示: 【{result.split('|')[1]}】 -> 啟動防阻擋退避 1 秒...")
                    await active_tab.evaluate("window._nol_last_confirm_time = 0; window._nol_last_seat_time = 0;")
                    await asyncio.sleep(1.0)
                    return

                # ⚡ 發動 CDP 真實物理滑鼠點擊 (選取座位)
                elif result.startswith("READY_SEAT|"):
                    parts = result.split("|")
                    sx, sy = float(parts[1]), float(parts[2])
                    seat_info = parts[3]

                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=int(sx), y=int(sy)))
                    await asyncio.sleep(0.01)
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mousePressed", x=int(sx), y=int(sy), button=mouse_btn, click_count=1))
                    await asyncio.sleep(0.02)
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseReleased", x=int(sx), y=int(sy), button=mouse_btn, click_count=1))

                    self.last_cdp_new_click_time = time.time()
                    print(
                        f">>> [NOL-新版座位] 🪑 物理滑鼠點擊第 {seat_info} 張座位 (x:{int(sx)}, y:{int(sy)})...")
                    await asyncio.sleep(0.1)

                # 🚀 發動 CDP 真實物理滑鼠點擊 (送出 Submit)
                elif result.startswith("READY_SUBMIT|"):
                    parts = result.split("|")
                    nx, ny = float(parts[1]), float(parts[2])

                    print(">>> [NOL-新版座位] 🎯 準備送出「Submit」！發動 CDP 真實滑鼠確認點擊...")
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=int(nx), y=int(ny)))
                    await asyncio.sleep(0.01)
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mousePressed", x=int(nx), y=int(ny), button=mouse_btn, click_count=1))
                    await asyncio.sleep(0.02)
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseReleased", x=int(nx), y=int(ny), button=mouse_btn, click_count=1))

                    self.last_cdp_new_click_time = time.time()
                    await asyncio.sleep(0.5)

                elif result == "NO_SEATS_LEFT_NEW":
                    if not hasattr(self, 'seat_new_wait_log'):
                        self.seat_new_wait_log = 0
                    self.seat_new_wait_log += 1
                    if self.seat_new_wait_log % 20 == 0:
                        print(">>> [NOL-新版座位] ❌ SVG 座位表上可選座位不足，強力監控釋票中...")
                    await asyncio.sleep(0.05)

        except Exception:
            pass

# ==========================================
# [公園 搶票 全自動]
# ==========================================


class FubonBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        # 1. 抓取路徑
        self.settings_path = config.get("config_filepath", "settings.json")

        # 🔥 新增這行 Debug Log，這能讓你立刻知道是誰的錯
        print(f">>> [系統檢查] 機器人目前綁定的設定檔路徑為: {self.settings_path}")

        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態鎖變數
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_seat_selected = False

        self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        print(">>> [富邦悍將] 正在載入 ddddocr 辨識模型...")
        import ddddocr
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    async def reload_config_if_changed(self):
        """讀取最新設定檔"""
        # 🔥 把寫死的字串，換成剛剛存好的動態變數
        settings_path = self.settings_path
        try:
            if not os.path.exists(settings_path):
                return
            with open(settings_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)

            # 同步更新變數
            for key in ["area_auto_select", "date_auto_select", "advanced", "keyword_exclude", "ticket_number"]:
                if key in new_config:
                    self.config[key] = new_config[key]
            self.ticket_number = int(new_config.get("ticket_number", 1))
        except:
            pass

    async def run(self):
        print(f">>> [富邦悍將] 機器人啟動！(目標張數: {self.ticket_number})")
        while True:
            try:
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                current_url = await self.tab.evaluate("window.location.href")

                if current_url and current_url != self.last_url:
                    upper_url = current_url.upper()

                    # 1. 區域選擇頁 (UTK0204)
                    if 'UTK0204_' in upper_url:
                        pass  # 進入區域不重置日期鎖

                    # 2. 日期選擇頁 (UTK0201，嚴格排除 0204/0205)
                    elif 'UTK0201_' in upper_url and 'UTK0204_' not in upper_url and 'UTK0205_' not in upper_url:
                        if getattr(self, 'is_date_selected', False):
                            print(">>> [系統] 退回日期選擇頁，重置日期鎖！")
                            self.is_date_selected = False
                        await self.reload_config_if_changed()

                    # 3. 票數/座位圖選擇頁 (新增 UTK0203_)
                    elif ('UTK0202_' in upper_url or 'UTK0203_' in upper_url or 'UTK0205_' in upper_url) and getattr(self, 'is_seat_selected', False):
                        print(">>> [系統] 退回票數/座位頁，重置座位鎖！")
                        self.is_seat_selected = False

                    self.last_url = current_url

                if current_url:
                    await self.dispatch_action(current_url)

            except Exception as e:
                pass
            await asyncio.sleep(0.05)

    async def dispatch_action(self, url):
        """任務分發中心"""
        upper_url = url.upper()

        if 'UTK0204_' in upper_url:
            self.is_seat_selected = False
            if not getattr(self, 'is_area_selected', False):
                await self.select_area()

        elif 'UTK0201_' in upper_url and 'UTK0204_' not in upper_url:
            self.is_area_selected = False
            self.is_seat_selected = False
            if not getattr(self, 'is_date_selected', False):
                await self.select_date()

        # (新增 UTK0203_)
        elif 'UTK0202_' in upper_url or 'UTK0203_' in upper_url or 'UTK0205_' in upper_url:
            if not getattr(self, 'is_seat_selected', False):
                seat_success = await self.select_tickets()
                if seat_success:
                    import asyncio
                    await asyncio.sleep(0.5)

                    ocr_success = await self.process_captcha()

                    if ocr_success:
                        await self.tab.evaluate("let btn=document.querySelector('#addcart'); if(btn) btn.click();")
                    else:
                        print(">>> [系統] ⚠️ OCR 辨識失敗，解除座位鎖，準備重新選位！")
                        self.is_seat_selected = False

    async def select_date(self):
        """[第一階段] 日期選擇"""
        date_auto_select = self.config.get("date_auto_select", {})
        raw_keyword = date_auto_select.get("date_keyword", "").strip()
        js_keywords = json.dumps(
            [x.strip() for x in raw_keyword.split(',') if x.strip()], ensure_ascii=False)

        js_date = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                let rows = Array.from(document.querySelectorAll('table tbody tr'));
                let candidates = [];

                for (let row of rows) {{
                    let btn = row.querySelector('button#buy_btn');
                    if (!btn) continue;

                    let btnText = (btn.innerText || "").toUpperCase();
                    if (btnText.includes('售完') || btn.disabled) continue;

                    let spanText = row.querySelector('td:nth-child(3) span');
                    let rowText = spanText ? spanText.innerText.toUpperCase() : row.innerText.toUpperCase();

                    let isMatch = keywords.length === 0;
                    if (!isMatch) {{
                        for (let k of keywords) {{
                            if (rowText.includes(k.toUpperCase())) {{
                                isMatch = true; break;
                            }}
                        }}
                    }}

                    if (isMatch && btnText.includes('購買')) {{
                        candidates.push(btn);
                    }}
                }}

                if (candidates.length > 0) {{
                    candidates[0].click();
                    return 1; // 成功點擊
                }}
                return 2; // 找不到或售完，需要重整
            }} catch(e) {{ return -1; }}
        }})();
        """
        result = await self.tab.evaluate(js_date)
        if result == 1:
            print(">>> [日期] 🎉 成功點擊購買！等待跳轉...")
            self.is_date_selected = True
            await asyncio.sleep(0.5)
        elif result == 2:
            base_wait = float(self.config.get("advanced", {}).get(
                "auto_reload_page_interval", 0.5))
            print(">>> [日期] 尚未開賣或已售完，準備刷新...")
            await self.tab.reload()
            await asyncio.sleep(base_wait if base_wait > 0 else 0.2)

    async def select_area(self):
        """[第二階段] 區域選擇 (Angular 穿透讀取 + 無敵字串清洗防呆)"""
        area_auto_select = self.config.get("area_auto_select", {})

        # ==========================================
        # 🔥 防呆 1：最強字串清洗機 (暴力拔除所有多餘的空白與引號)
        # ==========================================
        def parse_and_clean(raw_val):
            if not raw_val:
                return []
            # 如果傳進來就已經是陣列 (List)
            if isinstance(raw_val, list):
                # 連續脫掉 空白 -> 雙引號 -> 單引號 -> 空白
                return [str(x).strip().strip('"').strip("'").strip() for x in raw_val if str(x).strip()]

            # 如果傳進來是一長串字串
            val_str = str(raw_val).replace('，', ',').strip()

            # 嘗試解開像 '["A5", "A6"]' 這樣的 JSON 格式
            if val_str.startswith('[') and val_str.endswith(']'):
                import json
                try:
                    parsed = json.loads(val_str)
                    return [str(x).strip().strip('"').strip("'").strip() for x in parsed if str(x).strip()]
                except:
                    pass

            # 用逗號切開，並強制脫去每一項的引號
            return [x.strip().strip('"').strip("'").strip() for x in val_str.split(',') if x.strip()]

        # 清洗包含與排除的關鍵字
        raw_keyword = area_auto_select.get("area_keyword", "")
        k_list = parse_and_clean(raw_keyword)

        raw_exclude = self.config.get("keyword_exclude", "")
        e_list = parse_and_clean(raw_exclude)

        import json
        js_keywords = json.dumps(k_list, ensure_ascii=False)
        js_excludes = json.dumps(e_list, ensure_ascii=False)
        ticket_num = self.ticket_number

        js_area = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                const excludes = {js_excludes};
                const reqNum = {ticket_num};
                
                let rows = Array.from(document.querySelectorAll('table tbody tr'));
                
                // 🔥 防呆 2：Angular 渲染防護
                if (rows.length === 0) return 0; 
                let hasData = rows.some(r => r.textContent.includes('區') || r.textContent.match(/\d/));
                if (!hasData) return 0; // 資料還沒生出來，原地等待！

                let candidates = [];

                for (let row of rows) {{
                    // 使用 textContent 穿透讀取
                    let fullText = (row.textContent || "").replace(/,/g, '').toUpperCase();
                    let areaTag = (row.getAttribute('data-area-tag') || "").toUpperCase();
                    fullText += " " + areaTag;

                    if (!fullText.includes('區') && !fullText.includes('票') && !fullText.includes('席')) continue;

                    // 1. 排除關鍵字
                    let isExcluded = false;
                    for (let exc of excludes) {{
                        if (exc && fullText.includes(exc.toUpperCase())) {{ isExcluded = true; break; }}
                    }}
                    if (isExcluded) continue;

                    // 2. 包含關鍵字
                    let isMatch = keywords.length === 0;
                    if (!isMatch) {{
                        for (let k of keywords) {{
                            if (k && fullText.includes(k.toUpperCase())) {{ isMatch = true; break; }}
                        }}
                    }}
                    
                    if (isMatch) {{
                        // 3. 判斷空位狀態評分
                        let seatText = "";
                        let seatTd = Array.from(row.querySelectorAll('td')).find(td => td.getAttribute('data-title') && td.getAttribute('data-title').includes('空位'));
                        
                        if (seatTd) {{
                            seatText = seatTd.textContent.trim();
                        }} else {{
                            let seatEl = row.querySelector('#SEAT');
                            if (seatEl) seatText = seatEl.textContent.trim();
                            else seatText = fullText; 
                        }}

                        let score = 0;
                        if (seatText.includes("熱賣中")) score = 3;
                        else if (seatText.includes("售完") || seatText.includes("已售完")) score = 1; 
                        else {{
                            let numMatch = seatText.match(/\d+/);
                            if (numMatch) {{
                                let num = parseInt(numMatch[0]);
                                if (num >= reqNum) score = 2; // 數量足夠
                                else score = 1.5; // 數量不足
                            }} else {{
                                score = 1;
                            }}
                        }}

                        candidates.push({{ element: row, score: score }});
                    }}
                }}

                if (candidates.length > 0) {{
                    candidates.sort((a, b) => b.score - a.score);
                    candidates[0].element.click();
                    return 1;
                }}
                
                return 2;
            }} catch(e) {{ return -1; }}
        }})();
        """
        import asyncio
        result = await self.tab.evaluate(js_area)

        if result == 1:
            print(">>> [區域] 👉 成功鎖定區域並點擊！")
            self.is_area_selected = True
            await asyncio.sleep(0.3)

        elif result == 0:
            if not hasattr(self, 'area_wait_log'):
                self.area_wait_log = 0
            self.area_wait_log += 1
            if self.area_wait_log % 10 == 0:
                print(">>> [區域] ⏳ 網頁資料載入中 (等待 Angular 渲染)...")
            await asyncio.sleep(0.1)

        elif result == 2:
            # 這裡顯示的是清洗過後乾淨的字串，不再有引號了
            clean_kws = ", ".join(k_list) if k_list else "任意"
            print(f">>> [區域] 畫面上沒有符合 [{clean_kws}] 的區域，刷新頁面...")
            await self.tab.reload()
            await asyncio.sleep(0.5)

    async def select_tickets(self):
        """[第三階段] 票數與座位選擇 (雙模式相容 + 強制鎖定全票 + 無差別空位辨識)"""
        ticket_num = self.ticket_number
        raw_exclude = self.config.get("keyword_exclude", "")

        # 清洗排除關鍵字 (支援陣列與字串)
        if isinstance(raw_exclude, list):
            e_list = [str(x).strip() for x in raw_exclude if str(x).strip()]
        else:
            e_list = [x.strip() for x in str(raw_exclude).replace(
                '，', ',').split(',') if x.strip()]

        import json
        js_excludes = json.dumps(e_list, ensure_ascii=False)

        js_tickets = f"""
        (function() {{
            try {{
                const targetTickets = {ticket_num};
                const excludes = {js_excludes};
                
                // =====================================
                // 模式 A：座位圖模式
                // =====================================
                let seatTable = document.querySelector('#TBL');
                if (seatTable) {{
                    
                    // 防禦 1：Angular 渲染確認
                    let allSeatsInTable = document.querySelectorAll('#TBL td[title]');
                    if (allSeatsInTable.length === 0) return 0; // 資料還在路上，原地等待！

                    // ==========================================
                    // 🔥 修正：強制鎖定「全票」並確實擊發
                    // ==========================================
                    let typeBtns = Array.from(document.querySelectorAll('div.seatype button, button.f1'));
                    let targetBtn = null;

                    // 優先策略：直接尋找包含「全票」的按鈕，且避開身心障礙
                    for (let btn of typeBtns) {{
                        let btnText = (btn.textContent || "").toUpperCase();
                        if (btnText.includes('全票') && !btnText.includes('身心') && !btnText.includes('障礙')) {{
                            targetBtn = btn;
                            break;
                        }}
                    }}

                    // 備用策略：如果真的沒有叫全票的，用排除法抓第一個合法的
                    if (!targetBtn) {{
                        for (let btn of typeBtns) {{
                            let isExc = false;
                            let btnText = (btn.textContent || "").toUpperCase();
                            for (let ex of excludes) {{
                                if (ex && btnText.includes(ex.toUpperCase())) {{ isExc = true; break; }}
                            }}
                            if (!isExc) {{ targetBtn = btn; break; }}
                        }}
                    }}
                    
                    // 霸道點擊：不管它是不是 active，為了確保系統有收到 setType 的訊號，直接再點一次！
                    if (targetBtn) {{
                        targetBtn.click();
                    }}
                    // ==========================================

                    // 防禦 2：無差別空位辨識法
                    function isAvailable(cell) {{
                        let bg = (cell.getAttribute('style') || "").toLowerCase();
                        let hasTitle = cell.hasAttribute('title');
                        let notSold = !bg.includes('people') && !bg.includes('lock');
                        let isEmptyIcon = bg.includes('empty');
                        let isClickable = bg.includes('cursor: pointer') || cell.style.cursor === 'pointer';
                        
                        return hasTitle && notSold && (isEmptyIcon || isClickable);
                    }}

                    // 尋找空位 (優先找連號)
                    let rows = document.querySelectorAll('#TBL tbody tr');
                    let targetSeats = [];
                    for (let row of rows) {{
                        let cells = row.querySelectorAll('td');
                        let consec = [];
                        for (let cell of cells) {{
                            if (isAvailable(cell)) {{
                                consec.push(cell);
                                if (consec.length === targetTickets) {{ targetSeats = consec; break; }}
                            }} else if (cell.hasAttribute('title') || (cell.getAttribute('style') || "").includes('people')) {{
                                consec = []; 
                            }}
                        }}
                        if (targetSeats.length > 0) break;
                    }}
                    
                    // 防呆：沒有連號就全場硬抓
                    if (targetSeats.length === 0) {{
                        let allEmpty = Array.from(document.querySelectorAll('#TBL td')).filter(c => isAvailable(c));
                        if (allEmpty.length >= targetTickets) {{
                            targetSeats = allEmpty.slice(0, targetTickets);
                        }}
                    }}

                    // 點擊座位並聚焦驗證碼
                    if (targetSeats.length === targetTickets) {{
                        targetSeats.forEach(s => s.click());
                        let chk = document.querySelector('#CHK') || document.querySelector('#ctl00_ContentPlaceHolder1_CHK');
                        if(chk) chk.focus();
                        return 1; // 成功
                    }}
                    return 2; // 真的是沒票了
                }}
                
                // =====================================
                // 模式 B：張數選擇模式 (無座位圖)
                // =====================================
                let rows = Array.from(document.querySelectorAll('table tbody tr'));
                if (rows.length <= 1) return 0; // 渲染防護

                for(let row of rows) {{
                    let rowText = (row.textContent || "").toUpperCase();
                    let isExc = false;
                    for (let ex of excludes) {{
                        if (ex && rowText.includes(ex.toUpperCase())) {{ isExc = true; break; }}
                    }}
                    if (isExc) continue;

                    let input = row.querySelector('input.numbox[type="number"]');
                    if (input && !input.disabled) {{
                        input.value = targetTickets;
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        if (typeof checkNum === "function") checkNum(input);
                        
                        let chk = document.querySelector('#CHK') || document.querySelector('#ctl00_ContentPlaceHolder1_CHK');
                        if(chk) chk.focus();
                        return 1;
                    }}
                }}
                return 2;

            }} catch(e) {{ return -1; }}
        }})();
        """
        import asyncio
        result = await self.tab.evaluate(js_tickets)

        if result == 1:
            print(f">>> [票數/座位] ✅ 成功鎖定 {ticket_num} 張「全票」並點選座位！準備 OCR...")
            self.is_seat_selected = True
            return True

        elif result == 0:
            if not hasattr(self, 'seat_wait_log'):
                self.seat_wait_log = 0
            self.seat_wait_log += 1
            if self.seat_wait_log % 10 == 0:
                print(">>> [票數/座位] ⏳ 座位圖渲染中，請稍候...")
            await asyncio.sleep(0.1)
            return False

        elif result == 2:
            print(f">>> [票數/座位] ❌ 殘念...剩餘空位不足 {ticket_num} 張！準備重新整理頁面...")
            try:
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                if base_wait <= 0:
                    base_wait = 0.2
                await self.tab.reload()
                await asyncio.sleep(base_wait)
            except:
                pass
            return False

        return False

    async def process_captcha(self):
        """處理圖形驗證碼 (完整 Debug 版 + 圖片載入防護)"""
        print(">>> [OCR] 啟動驗證碼辨識程序...")
        js_get_image = """
            (function() {
                try {
                    var img = document.querySelector('#chk_pic');
                    if (!img) return "ERROR_NO_IMG";
                    // 檢查圖片是否真的載入完成了
                    if (!img.complete || img.naturalWidth === 0) return "ERROR_NOT_LOADED";
                    
                    var canvas = document.createElement('canvas');
                    canvas.width = img.naturalWidth || img.width;
                    canvas.height = img.naturalHeight || img.height;
                    var ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    return canvas.toDataURL('image/png').split(',')[1];
                } catch(e) {
                    return "ERROR_CANVAS";
                }
            })();
            """

        try:
            for attempt in range(3):
                import asyncio
                base64_data = await self.tab.evaluate(js_get_image)

                if base64_data == "ERROR_NO_IMG":
                    print(">>> [OCR] 找不到驗證碼圖片，網頁可能還沒載入完畢...")
                    await asyncio.sleep(0.5)
                    continue
                elif base64_data == "ERROR_NOT_LOADED":
                    print(">>> [OCR] 圖片還在轉圈圈，等它一下...")
                    await asyncio.sleep(0.5)
                    continue
                elif str(base64_data).startswith("ERROR_CANVAS") or not base64_data:
                    print(">>> [OCR] 畫布擷取失敗，可能被瀏覽器安全機制擋下。")
                    return False

                import base64
                img_bytes = base64.b64decode(base64_data)

                # 呼叫 ddddocr 進行辨識
                ocr_answer = self.ocr.classification(img_bytes)
                ocr_answer = ocr_answer.strip() if ocr_answer else ""
                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                if len(ocr_answer) == 4:
                    js_fill = f"""
                        (function() {{
                            let el = document.querySelector('#CHK'); 
                            if(el) {{ 
                                el.value = '{ocr_answer}'; 
                                el.dispatchEvent(new Event('input', {{bubbles:true}})); 
                                el.dispatchEvent(new Event('change', {{bubbles:true}})); 
                                return true; 
                            }} 
                            return false;
                        }})();
                        """
                    if await self.tab.evaluate(js_fill):
                        print(f">>> [OCR] ✅ 已自動填入驗證碼: {ocr_answer}")
                        return True
                    else:
                        print(">>> [OCR] 找不到驗證碼輸入框 (#CHK)！")

                # 辨識失敗換圖
                print(">>> [OCR] ⚠️ 辨識長度不對，點擊圖片重新整理...")
                await self.tab.evaluate("let img = document.querySelector('#chk_pic'); if(img) img.click();")
                await asyncio.sleep(0.8)  # 換圖需要一點時間讀取

            return False
        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False
# ==========================================
# [富邦棒球搶票]
# ==========================================


class FunoneBot:
    """FunOne Tickets 專用機器人 (直攻張數選擇頁面掛機版)"""

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.settings_path = config.get("config_filepath", "settings.json")
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 唯一的狀態鎖
        self.is_ticket_assigned = False

        # 暫停鎖
        import os
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

    async def run(self):
        print(f">>> [FunOne] 機器人啟動！(目標張數: {self.ticket_number})")
        print(">>> [FunOne] 💡 戰術提示：請手動進入「目標區域」的張數選擇頁面，機器人會在此幫您掛機刷新撿漏！")
        import asyncio
        import os

        while True:
            try:
                # 1. 暫停攔截
                if os.path.exists(self.PAUSE_FILE):
                    if not getattr(self, 'is_printing_pause', False):
                        print("\n>>> [系統] ⏸️ 程式已暫停！等待您在 GUI 按下繼續...")
                        self.is_printing_pause = True
                    await asyncio.sleep(0.5)
                    continue
                self.is_printing_pause = False

                # 2. 確保連線活著
                if hasattr(self.driver, 'main_tab'):
                    self.tab = self.driver.main_tab
                active_tab = self.tab

                current_url = await active_tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                # 3. 網址狀態機 (防呆解鎖與 SPA 狀態重置)
                if current_url != getattr(self, 'last_url', ''):
                    print(f">>> [路由] 偵測到頁面切換: {current_url}")
                    self.last_url = current_url

                    self.is_ticket_assigned = False

                    reset_js = """
                    (function() {
                        window._funone_ticket_added = false;
                        window._funone_agreed = false;
                        window._funone_submit_clicked = false;
                        window._funone_refresh_clicked = false;
                        window._funone_socket_refresh_clicked = false;
                    })();
                    """
                    try:
                        await active_tab.evaluate(reset_js)
                    except:
                        pass

                # =========================================================
                # 🔥 核心修復：放寬 URL 檢查，相容 has_map 與 no_map (無座位圖) 版型
                # =========================================================
                if '/purchase/purchase_choose_ticket_' in current_url.lower() or '/purchase/purchase_fill_form/' in current_url.lower():
                    await self.dispatch_action(active_tab)
                else:
                    await asyncio.sleep(0.1)

            except Exception as e:
                err_str = str(e)
                if "500" in err_str or "closed" in err_str:
                    await asyncio.sleep(0.1)
                else:
                    pass
            await asyncio.sleep(0.05)

    async def dispatch_action(self, active_tab):
        """[FunOne] 單一任務分發：只處理錯誤彈窗與選票階段"""
        js_scout = """
        (function() {
            try {
                let doc = document;
                
                // 1. 偵測錯誤彈窗 (最高優先級)
                let popups = document.querySelectorAll('div[role="dialog"]');
                for (let dialog of popups) {
                    if (dialog.offsetParent !== null) {
                        let text = dialog.innerText || "";
                        if (text.includes('失敗') || text.includes('售完') || text.includes('我知道了')) {
                            return "STAGE_ERROR";
                        }
                    }
                }

                // 2. 判斷是否在「選票數與結帳 / 開賣倒數」畫面
                let buyBtn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('立即購買'));
                let refreshBtn = doc.querySelector('button.web_round_info_refresh');
                
                // 🔥 核心修改：擴大特徵偵測，相容「有座位圖」與「無座位圖(多票種清單)」兩種版型
                let hasMapContainer = doc.querySelector('.choose_ticket_has_map');
                let noMapContainer = doc.querySelector('.choose_ticket_no_seat');
                let plusSvg = doc.querySelector('svg path[d^="M11 13H6C5"]'); 
                
                if (buyBtn || refreshBtn || hasMapContainer || noMapContainer || plusSvg) {
                    if (window._funone_submit_clicked) {
                        return "STAGE_TICKET_DONE"; 
                    }
                    return "STAGE_TICKET"; 
                }

                return "WAITING_DOM";
            } catch(e) { return "ERROR"; }
        })();
        """
        import asyncio
        scout_result = await active_tab.evaluate(js_scout)

        if scout_result == "STAGE_ERROR":
            print(">>> [FunOne-系統] 💥 偵測到「購票失敗/售完」彈窗！重置狀態準備撿漏...")
            self.is_ticket_assigned = False
            await active_tab.reload()
            await asyncio.sleep(0.5)

        elif scout_result == "STAGE_TICKET":
            if not getattr(self, 'is_ticket_assigned', False):
                await self.select_tickets(active_tab)
            else:
                await asyncio.sleep(0.1)

        elif scout_result == "STAGE_TICKET_DONE":
            self.is_ticket_assigned = True
            await asyncio.sleep(0.1)

        elif scout_result == "WAITING_DOM":
            await asyncio.sleep(0.05)

    async def dispatch_action(self, active_tab):
        """[FunOne] 單一任務分發：只處理錯誤彈窗與選票階段"""
        js_scout = """
        (function() {
            try {
                let doc = document;
                
                // 1. 偵測錯誤彈窗 (最高優先級)
                let popups = document.querySelectorAll('div[role="dialog"]');
                for (let dialog of popups) {
                    if (dialog.offsetParent !== null) {
                        let text = dialog.innerText || "";
                        if (text.includes('失敗') || text.includes('售完') || text.includes('我知道了')) {
                            return "STAGE_ERROR";
                        }
                    }
                }

                // 2. 判斷是否在「選票數與結帳 / 開賣倒數」畫面
                let buyBtn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('立即購買'));
                let refreshBtn = doc.querySelector('button.web_round_info_refresh');
                let plusSvg = doc.querySelector('svg path[d^="M11 13H6C5"]'); 
                
                if (buyBtn || refreshBtn || plusSvg) {
                    return "STAGE_TICKET";
                }

                return "WAITING_DOM";
            } catch(e) { return "ERROR"; }
        })();
        """

        scout_result = await active_tab.evaluate(js_scout)

        if scout_result == "STAGE_ERROR":
            print(">>> [FunOne-系統] 💥 偵測到「購票失敗/售完」彈窗！重置狀態準備撿漏...")
            self.is_ticket_assigned = False
            await active_tab.reload()
            await asyncio.sleep(0.5)

        elif scout_result == "STAGE_TICKET":
            # 確保還沒結帳才進去執行
            if not getattr(self, 'is_ticket_assigned', False):
                await self.select_tickets(active_tab)
            else:
                await asyncio.sleep(0.1)

        elif scout_result == "WAITING_DOM":
            await asyncio.sleep(0.05)

    async def assign_tickets(self):
        """選擇票種/票價張數、驗證碼OCR與打勾確認"""

        area_auto_select = getattr(
            self, 'config', {}).get("area_auto_select", {})
        raw_keyword = area_auto_select.get("area_keyword", "").strip()
        raw_keyword_exclude = self.config.get("keyword_exclude", "")
        if not raw_keyword_exclude:
            raw_keyword_exclude = area_auto_select.get(
                "area_keyword_exclude", "")

        def parse_keywords(kw_str):
            if not kw_str:
                return [""]
            try:
                if kw_str.startswith("[") and kw_str.endswith("]"):
                    return json.loads(kw_str)
                if '"' in kw_str or "'" in kw_str:
                    return json.loads("[" + kw_str + "]")
            except:
                pass
            return [x.strip() for x in kw_str.split(',') if x.strip()]

        js_keywords = json.dumps(parse_keywords(
            raw_keyword), ensure_ascii=False)
        js_excludes = json.dumps(parse_keywords(
            str(raw_keyword_exclude).strip()), ensure_ascii=False)
        ticket_number = self.ticket_number

        js_select = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                const excludes = {js_excludes};
                const targetTickets = {ticket_number};
                
                let rows = Array.from(document.querySelectorAll('tr.gridc'));
                let targetSelect = null;
                
                if (rows.length === 0) return "WAITING_DOM";
                
                for (let row of rows) {{
                    let text = row.innerText.toUpperCase();
                    
                    let isExcluded = false;
                    if (excludes.length > 0 && excludes[0] !== "") {{
                        for (let exc of excludes) {{
                            let cleanExc = exc.trim().toUpperCase();
                            if (cleanExc.length > 0 && text.includes(cleanExc)) {{
                                isExcluded = true; break;
                            }}
                        }}
                    }}
                    if (isExcluded) continue;
                    
                    let isMatch = false;
                    if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                        isMatch = true;
                    }} else {{
                        for (let k of keywords) {{
                            let target_kws = k.trim().split(/\\s+/).filter(w => w.length > 0);
                            let currentGroupMatch = true;
                            for (let w of target_kws) {{
                                if (!text.includes(w.toUpperCase())) {{
                                    currentGroupMatch = false; break;
                                }}
                            }}
                            if (currentGroupMatch) {{ isMatch = true; break; }}
                        }}
                    }}
                    
                    if (isMatch) {{
                        let selectEl = row.querySelector('select.mobile-select');
                        if (selectEl && !selectEl.disabled) {{
                            let hasOption = Array.from(selectEl.options).some(opt => parseInt(opt.value) >= targetTickets);
                            if (hasOption) {{
                                targetSelect = selectEl;
                                break;
                            }}
                        }}
                    }}
                }}
                
                if (targetSelect) {{
                    targetSelect.value = targetTickets;
                    targetSelect.dispatchEvent(new Event('change', {{bubbles: true}}));
                    
                    let agreeCheckbox = document.querySelector('#TicketForm_agree');
                    if (agreeCheckbox && !agreeCheckbox.checked) {{
                        agreeCheckbox.click();
                    }}
                    return "READY";
                }}
                return "RELOAD";
            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_select)
            if result == "READY":
                print(
                    f">>> [Indievox-票數] 🎉 成功鎖定目標票種/套票，且已調整為 {ticket_number} 張！")

                # 執行辨識
                ocr_success = await self.process_captcha()
                if ocr_success:
                    await asyncio.sleep(0.3)

                    # 【核心修正】：覆寫網頁原生的 alert 函數，攔截錯誤彈窗，防止程式卡死
                    await self.tab.evaluate("""
                        window._lastAlertMsg = null;
                        if (!window._alertOverridden) {
                            window.alert = function(msg) {
                                window._lastAlertMsg = msg;
                            };
                            window._alertOverridden = true;
                        }
                    """)

                    js_submit = """
                    (function() {
                        let btn = document.querySelector('.btn-check[type="submit"]') || document.querySelector('button.btn-check');
                        if (btn && !btn.disabled) {
                            btn.click();
                            return true;
                        }
                        return false;
                    })();
                    """
                    if await self.tab.evaluate(js_submit):
                        print(">>> [Indievox-票數] 👉 確認張數按鈕已送出！檢查驗證碼是否正確...")

                        # 迴圈等待看是否有 Alert 被我們攔截到
                        for _ in range(15):  # 總共等 1.5 秒
                            await asyncio.sleep(0.1)
                            alert_msg = await self.tab.evaluate("window._lastAlertMsg")
                            if alert_msg:
                                break

                        alert_msg = await self.tab.evaluate("window._lastAlertMsg")
                        if alert_msg:
                            print(f">>> [Indievox-票數] ❌ 網頁跳出提示: {alert_msg}")
                            # 如果確定是驗證碼錯誤，立刻幫忙刷新並重來
                            if "驗證碼" in alert_msg or "不正確" in alert_msg or "錯誤" in alert_msg:
                                print(">>> [Indievox-票數] 🔄 準備刷新驗證碼重新辨識...")
                                js_refresh_err = """
                                (function() {
                                    window._lastAlertMsg = null;
                                    let img = document.querySelector('#TicketForm_verifyCode-image');
                                    let input = document.querySelector('#TicketForm_verifyCode');
                                    if(img) img.click();
                                    if(input) input.value = '';
                                })();
                                """
                                await self.tab.evaluate(js_refresh_err)
                                await asyncio.sleep(1.0)  # 延長等待新圖片載入
                                # 不設定 True，讓主迴圈下一秒重新呼叫本函數
                            else:
                                await asyncio.sleep(1)
                                self.is_ticket_assigned = False
                        else:
                            print(">>> [Indievox-票數] ✅ 無錯誤彈窗，等待系統跳轉結帳頁...")
                            self.is_ticket_assigned = True

            elif result == "RELOAD":
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                if base_wait <= 0:
                    base_wait = 0.2
                print(">>> [Indievox-票數] ❌ 找不到符合關鍵字或足夠張數的票種！準備刷新...")
                await self.tab.reload()
                await asyncio.sleep(base_wait)

            elif result == "WAITING_DOM":
                await asyncio.sleep(0.1)
        except Exception as e:
            pass

    async def process_captcha(self):
        """擷取圖片並執行 ddddocr，失敗則自動換圖"""
        print(">>> [OCR] 開始處理 Indievox 圖形驗證碼...")

        js_get_image = """
        (function() {
            var img = document.querySelector('#TicketForm_verifyCode-image');
            if (!img) return null;
            if (!img.complete || img.naturalWidth === 0) return "NOT_LOADED";
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """

        try:
            for attempt in range(5):  # 加碼最多嘗試 5 次
                base64_data = await self.tab.evaluate(js_get_image)
                if not base64_data:
                    print(">>> [OCR] 找不到驗證碼圖片 (#TicketForm_verifyCode-image)")
                    return False
                if base64_data == "NOT_LOADED":
                    await asyncio.sleep(0.5)
                    continue

                img_bytes = base64.b64decode(base64_data)

                if self.ocr:
                    ocr_answer = self.ocr.classification(img_bytes)
                    ocr_answer = ocr_answer.strip() if ocr_answer else ""
                else:
                    return False

                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                # 如果字數正確，嘗試填寫
                if len(ocr_answer) == 4:
                    js_fill_input = f"""
                    (function() {{
                        var input = document.querySelector('#TicketForm_verifyCode');
                        if (input) {{
                            input.value = '{ocr_answer}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }})();
                    """
                    if await self.tab.evaluate(js_fill_input):
                        print(f">>> [OCR] ✅ 已自動填入驗證碼: {ocr_answer}")
                        return True

                print(">>> [OCR] ⚠️ 辨識可能不準確，點擊圖片換一張...")
                js_refresh = """
                (function() {
                    let img = document.querySelector('#TicketForm_verifyCode-image');
                    let input = document.querySelector('#TicketForm_verifyCode');
                    if(img) {
                        // 使用 DispatchEvent 確保點擊事件觸發更新
                        let ev = new MouseEvent('click', {bubbles: true, cancelable: true, view: window});
                        img.dispatchEvent(ev);
                        img.click(); // 雙重保險
                    }
                    if(input) input.value = '';
                })();
                """
                await self.tab.evaluate(js_refresh)
                # 【核心修正】：增加等待時間 1.0 秒，確保網路真的拉取完新圖片，否則抓到的還是舊圖
                await asyncio.sleep(1.0)

            return False
        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False

# ==========================================
# [Funone搶票]
# ==========================================

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        self.settings_path = config.get("config_filepath", "settings.json")
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態控制鎖
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_ticket_assigned = False
        self.captcha_error_flag = False  # 新增：驗證碼錯誤攔截標記

        try:

            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        print(">>> [Indievox] 正在載入 ddddocr 辨識模型...")
        try:

            self.ocr = ddddocr.DdddOcr(show_ad=False)
        except Exception as e:
            print(f">>> [系統] ddddocr 載入失敗: {e}")
            self.ocr = None

    async def bind_dialog_handler(self):
        """【核心新增】綁定底層 CDP 攔截器，強制關閉任何卡死彈窗"""
        try:
            import nodriver.cdp.page as cdp_page

            async def dialog_handler(event: cdp_page.JavascriptDialogOpening):
                msg = getattr(event, "message", "")
                print(f"\n>>> [底層彈窗攔截] 網頁跳出提示: '{msg}'")

                # 強制自動點擊「確定」
                # 【修正】：nodriver 底層函式名稱為 handle_java_script_dialog
                await self.tab.send(cdp_page.handle_java_script_dialog(accept=True))

                # 如果判定為驗證碼錯誤，解開鎖定狀態讓系統重試
                if "驗證碼" in msg or "不正確" in msg or "錯誤" in msg or "失敗" in msg:
                    self.is_ticket_assigned = False
                    self.captcha_error_flag = True

            self.tab.add_handler(
                cdp_page.JavascriptDialogOpening, dialog_handler)
            print(">>> [系統] ✅ 已啟用底層 CDP 彈窗防護機制 (自動解除卡死)")
        except Exception as e:
            print(f">>> [系統] ⚠️ 綁定 CDP 彈窗防護失敗 (將使用第二層 JS 防護): {e}")

    async def run(self):
        print(f">>> [Indievox] 機器人啟動！(目標張數: {self.ticket_number})")
        print(">>> [系統] 💡 請自行登入完成，並挑選進入目標活動頁面，機器人會接管後續步驟！")

        # 啟動時立刻綁定彈窗攔截器
        await self.bind_dialog_handler()

        while True:
            try:
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                if current_url != getattr(self, 'last_url', ''):
                    self.last_url = current_url
                    lower_url = current_url.lower()

                    if '/activity/detail/' in lower_url or '/activity/game/' in lower_url:
                        self.is_date_selected = False
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                    elif '/ticket/area/' in lower_url:
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                    elif '/ticket/ticket/' in lower_url:
                        self.is_ticket_assigned = False

                    await self.reload_settings(silent=True)

                await self.dispatch_action(current_url)

            except Exception as e:
                pass
            await asyncio.sleep(0.05)

    async def reload_settings(self, silent=False):

        try:
            config_path = getattr(self, 'settings_path', 'settings.json')
            if not os.path.exists(config_path):
                return
            mtime = os.path.getmtime(config_path)
            if getattr(self, 'last_settings_mtime', 0) == mtime:
                return
            self.last_settings_mtime = mtime
            with open(config_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)

            if "area_auto_select" in new_config:
                self.config["area_auto_select"] = new_config["area_auto_select"]
            if "date_auto_select" in new_config:
                self.config["date_auto_select"] = new_config["date_auto_select"]
            if "advanced" in new_config:
                self.config["advanced"] = new_config["advanced"]
            if "keyword_exclude" in new_config:
                self.config["keyword_exclude"] = new_config["keyword_exclude"]
            if "ticket_number" in new_config:
                self.config["ticket_number"] = new_config["ticket_number"]
                self.ticket_number = int(new_config.get("ticket_number", 1))

            if not silent:
                print(f">>> [系統] Indievox 設定已更新！")
        except Exception:
            pass

    async def dispatch_action(self, url):
        lower_url = url.lower()
        if '/activity/detail/' in lower_url:
            await self.redirect_to_game()
        elif '/activity/game/' in lower_url:
            if not getattr(self, 'is_date_selected', False):
                await self.select_date()
        elif '/ticket/area/' in lower_url:
            if not getattr(self, 'is_area_selected', False):
                await self.select_area()
        elif '/ticket/ticket/' in lower_url:
            if not getattr(self, 'is_ticket_assigned', False):
                await self.assign_tickets()

    async def redirect_to_game(self):
        js_redirect = """
        (function() {
            let url = window.location.href;
            if (url.includes('/activity/detail/')) {
                window.location.href = url.replace('/activity/detail/', '/activity/game/');
                return true;
            }
            return false;
        })();
        """
        try:
            if await self.tab.evaluate(js_redirect):
                print(">>> [Indievox] 已將網址從 /detail 轉向至 /game (展開場次列表)...")

                await asyncio.sleep(0.5)
        except:
            pass

    async def select_date(self):

        date_auto_select = self.config.get("date_auto_select", {})
        if not date_auto_select.get("enable", True):
            return
        raw_keyword = date_auto_select.get("date_keyword", "").strip()

        def parse_keywords(kw_str):
            if not kw_str:
                return [""]
            try:
                if kw_str.startswith("[") and kw_str.endswith("]"):
                    return json.loads(kw_str)
                if '"' in kw_str or "'" in kw_str:
                    return json.loads("[" + kw_str + "]")
            except:
                pass
            return [x.strip() for x in kw_str.split(',') if x.strip()]

        js_keywords = json.dumps(parse_keywords(
            raw_keyword), ensure_ascii=False)
        js_mode = f"'{date_auto_select.get('mode', 'from top to bottom')}'"

        js_script = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                const mode = {js_mode};
                let rows = Array.from(document.querySelectorAll('#gameList > table > tbody > tr'));
                let candidates = [];
                if (rows.length === 0) return "WAITING_DOM";
                for (let row of rows) {{
                    let rowText = row.innerText.toUpperCase();
                    let btn = row.querySelector('td:nth-child(4) > button') || row.querySelector('button.btn-next');
                    if (!btn || btn.disabled || rowText.includes('售完')) continue;
                    let isMatch = false;
                    if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{ isMatch = true; }} else {{
                        for (let k of keywords) {{
                            let target_kws = k.trim().split(/\\s+/).filter(w => w.length > 0);
                            let currentGroupMatch = true;
                            for (let w of target_kws) {{ if (!rowText.includes(w.toUpperCase())) {{ currentGroupMatch = false; break; }} }}
                            if (currentGroupMatch) {{ isMatch = true; break; }}
                        }}
                    }}
                    if (isMatch) candidates.push(btn);
                }}
                if (candidates.length === 0) return "RELOAD";
                if (mode === "from bottom to top") {{ candidates.reverse(); }} else if (mode === "random") {{
                    for (let i = candidates.length - 1; i > 0; i--) {{
                        const j = Math.floor(Math.random() * (i + 1));
                        [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
                    }}
                }}
                let targetBtn = candidates[0];
                let href = targetBtn.getAttribute('data-href');
                if (href) {{ window.location.href = href; }} else {{ targetBtn.click(); }}
                return "SUCCESS";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        try:
            result = await self.tab.evaluate(js_script)
            if result == "SUCCESS":
                print(">>> [Indievox-日期] 🎉 成功鎖定日期！發動點擊與跳轉...")
                self.is_date_selected = True
                await asyncio.sleep(0.5)
            elif result == "RELOAD":
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                print(">>> [Indievox-日期] 找不到符合關鍵字的開賣場次，準備刷新...")
                await self.tab.reload()
                await asyncio.sleep(base_wait if base_wait > 0 else 0.2)
            elif result == "WAITING_DOM":
                await asyncio.sleep(0.1)
        except:
            pass

    async def select_area(self):

        area_auto_select = getattr(
            self, 'config', {}).get("area_auto_select", {})
        if not area_auto_select.get("enable", True):
            return
        raw_keyword = area_auto_select.get("area_keyword", "").strip()
        raw_keyword_exclude = self.config.get(
            "keyword_exclude", "") or area_auto_select.get("area_keyword_exclude", "")

        def parse_keywords(kw_str):
            if not kw_str:
                return [""]
            try:
                if kw_str.startswith("[") and kw_str.endswith("]"):
                    return json.loads(kw_str)
                if '"' in kw_str or "'" in kw_str:
                    return json.loads("[" + kw_str + "]")
            except:
                pass
            return [x.strip() for x in kw_str.split(',') if x.strip()]

        js_keywords = json.dumps(parse_keywords(
            raw_keyword), ensure_ascii=False)
        js_excludes = json.dumps(parse_keywords(
            str(raw_keyword_exclude).strip()), ensure_ascii=False)
        js_mode = f"'{area_auto_select.get('mode', 'from top to bottom')}'"

        js_script = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                const excludes = {js_excludes};
                const mode = {js_mode};
                
                // 【核心修正】：改為抓取所有區域 <li> (包含已售完與未售完的)，解決卡在 WAITING_DOM 的問題
                let allItems = Array.from(document.querySelectorAll('ul.area-list > li'));
                let candidates = [];
                
                // 只有當整個列表都沒有 <li> 時，才判定為網頁尚未載入完成
                if (allItems.length === 0) return "WAITING_DOM";
                
                for (let li of allItems) {{
                    let text = li.innerText.toUpperCase();
                    
                    // 1. 檢查排除關鍵字
                    let isExcluded = false;
                    if (excludes.length > 0 && excludes[0] !== "") {{
                        for (let exc of excludes) {{ 
                            if (exc.trim().length > 0 && text.includes(exc.trim().toUpperCase())) {{ 
                                isExcluded = true; break; 
                            }} 
                        }}
                    }}
                    if (isExcluded) continue;
                    
                    // 2. 檢查目標關鍵字是否符合
                    let isMatch = false;
                    if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{ 
                        isMatch = true; 
                    }} else {{
                        for (let k of keywords) {{
                            let target_kws = k.trim().split(/\\s+/).filter(w => w.length > 0);
                            let currentGroupMatch = true;
                            for (let w of target_kws) {{ 
                                if (!text.includes(w.toUpperCase())) {{ 
                                    currentGroupMatch = false; break; 
                                }} 
                            }}
                            if (currentGroupMatch) {{ isMatch = true; break; }}
                        }}
                    }}
                    
                    // 3. 關鍵字符合後，檢查該區域是否「還有票」(不能有售完字眼，且必須有可點擊的 <a> 標籤)
                    if (isMatch) {{
                        if (text.includes('售完') || text.includes('剩餘 0')) continue;
                        let link = li.querySelector('a');
                        if (link) candidates.push(link);
                    }}
                }}
                
                // 列表載入完成，但「符合您關鍵字的區域」目前已售完或無票 -> 回傳 RELOAD 觸發自動重整！
                if (candidates.length === 0) return "RELOAD";
                
                if (mode === "from bottom to top") {{ candidates.reverse(); }} else if (mode === "random") {{
                    for (let i = candidates.length - 1; i > 0; i--) {{
                        const j = Math.floor(Math.random() * (i + 1));
                        [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
                    }}
                }}
                candidates[0].click();
                return "SUCCESS";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        try:
            result = await self.tab.evaluate(js_script)
            if result == "SUCCESS":
                print(">>> [Indievox-區域] 🎉 成功鎖定票區並點擊！")
                self.is_area_selected = True
                await asyncio.sleep(0.5)
            elif result == "RELOAD":
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                print(">>> [Indievox-區域] 🔄 目標區域已售完或目前無釋票，自動刷新頁面排隊中...")
                await self.tab.reload()
                await asyncio.sleep(base_wait if base_wait > 0 else 0.2)
            elif result == "WAITING_DOM":
                await asyncio.sleep(0.1)
        except:
            pass

    async def assign_tickets(self):

        area_auto_select = getattr(
            self, 'config', {}).get("area_auto_select", {})
        raw_keyword = area_auto_select.get("area_keyword", "").strip()
        raw_keyword_exclude = self.config.get(
            "keyword_exclude", "") or area_auto_select.get("area_keyword_exclude", "")

        def parse_keywords(kw_str):
            if not kw_str:
                return [""]
            try:
                if kw_str.startswith("[") and kw_str.endswith("]"):
                    return json.loads(kw_str)
                if '"' in kw_str or "'" in kw_str:
                    return json.loads("[" + kw_str + "]")
            except:
                pass
            return [x.strip() for x in kw_str.split(',') if x.strip()]

        js_keywords = json.dumps(parse_keywords(
            raw_keyword), ensure_ascii=False)
        js_excludes = json.dumps(parse_keywords(
            str(raw_keyword_exclude).strip()), ensure_ascii=False)
        ticket_number = self.ticket_number

        js_select = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                const excludes = {js_excludes};
                const targetTickets = {ticket_number};
                
                let rows = Array.from(document.querySelectorAll('tr.gridc'));
                let targetSelect = null;
                
                if (rows.length === 0) return "WAITING_DOM";
                
                for (let row of rows) {{
                    // 【核心修正】：將逗號移除，讓 "2,400" 變成 "2400"
                    let text = row.innerText.toUpperCase().replace(/,/g, '');
                    
                    let isExcluded = false;
                    if (excludes.length > 0 && excludes[0] !== "") {{
                        for (let exc of excludes) {{ 
                            // 排除關鍵字比對時也移除逗號
                            let cleanExc = exc.trim().toUpperCase().replace(/,/g, '');
                            if (cleanExc.length > 0 && text.includes(cleanExc)) {{ 
                                isExcluded = true; break; 
                            }} 
                        }}
                    }}
                    if (isExcluded) continue;
                    
                    let isMatch = false;
                    if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{ 
                        isMatch = true; 
                    }} else {{
                        for (let k of keywords) {{
                            // 目標關鍵字比對時也移除逗號
                            let cleanK = k.replace(/,/g, '');
                            let target_kws = cleanK.trim().split(/\\s+/).filter(w => w.length > 0);
                            let currentGroupMatch = true;
                            for (let w of target_kws) {{ 
                                if (!text.includes(w.toUpperCase())) {{ 
                                    currentGroupMatch = false; break; 
                                }} 
                            }}
                            if (currentGroupMatch) {{ isMatch = true; break; }}
                        }}
                    }}
                    
                    if (isMatch) {{
                        let selectEl = row.querySelector('select.mobile-select');
                        if (selectEl && !selectEl.disabled) {{
                            let hasOption = Array.from(selectEl.options).some(opt => parseInt(opt.value) >= targetTickets);
                            if (hasOption) {{ targetSelect = selectEl; break; }}
                        }}
                    }}
                }}
                
                if (targetSelect) {{
                    targetSelect.value = targetTickets;
                    targetSelect.dispatchEvent(new Event('change', {{bubbles: true}}));
                    let agreeCheckbox = document.querySelector('#TicketForm_agree');
                    if (agreeCheckbox && !agreeCheckbox.checked) agreeCheckbox.click();
                    return "READY";
                }}
                return "RELOAD";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        try:
            result = await self.tab.evaluate(js_select)
            if result == "READY":
                print(f">>> [Indievox-票數] 🎉 成功鎖定目標票種，且已調整為 {ticket_number} 張！")
                self.captcha_error_flag = False
                ocr_success = await self.process_captcha()

                if ocr_success:
                    await asyncio.sleep(0.3)
                    js_submit = """
                    (function() {
                        window._lastAlertMsg = null;
                        if (!window._alertOverridden) {
                            window.alert = function(msg) { window._lastAlertMsg = msg; };
                            window._alertOverridden = true;
                        }
                        
                        let btn = document.querySelector('.btn-check[type="submit"]') || document.querySelector('button.btn-check');
                        if (btn && !btn.disabled) { 
                            setTimeout(function() { btn.click(); }, 50);
                            return true; 
                        }
                        return false;
                    })();
                    """
                    if await self.tab.evaluate(js_submit):
                        print(">>> [Indievox-票數] 👉 確認張數按鈕已送出！等待系統判定...")
                        self.is_ticket_assigned = True

                        for _ in range(20):
                            await asyncio.sleep(0.1)
                            try:
                                alert_msg = await self.tab.evaluate("window._lastAlertMsg")
                                if alert_msg:
                                    print(f">>> [JS攔截] 網頁跳出提示: '{alert_msg}'")
                                    await self.tab.evaluate("window._lastAlertMsg = null;")
                                    if "驗證碼" in alert_msg or "不正確" in alert_msg or "錯誤" in alert_msg or "失敗" in alert_msg:
                                        self.captcha_error_flag = True
                                        self.is_ticket_assigned = False
                            except:
                                pass

                            if not getattr(self, 'is_ticket_assigned', True) or getattr(self, 'captcha_error_flag', False):
                                break

                        if not getattr(self, 'is_ticket_assigned', True) or getattr(self, 'captcha_error_flag', False):
                            print(
                                ">>> [Indievox-票數] 🔄 驗證碼錯誤或卡死彈窗已被解除！準備重新辨識...")
                            self.is_ticket_assigned = False
                            self.captcha_error_flag = False

                            js_refresh_err = """
                            (function() {
                                let img = document.querySelector('#TicketForm_verifyCode-image');
                                let input = document.querySelector('#TicketForm_verifyCode');
                                if(img) {
                                    let ev = new MouseEvent('click', {bubbles: true, cancelable: true, view: window});
                                    img.dispatchEvent(ev);
                                    img.click();
                                }
                                if(input) input.value = '';
                            })();
                            """
                            try:
                                await self.tab.evaluate(js_refresh_err)
                            except:
                                pass
                            await asyncio.sleep(1.2)
                        else:
                            print(">>> [Indievox-票數] ✅ 無錯誤彈窗，順利跳轉或排隊中...")
                            self.is_ticket_assigned = True

            elif result == "RELOAD":
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                print(">>> [Indievox-票數] ❌ 找不到符合關鍵字或足夠張數的票種！準備刷新...")
                await self.tab.reload()
                await asyncio.sleep(base_wait if base_wait > 0 else 0.2)
            elif result == "WAITING_DOM":
                await asyncio.sleep(0.1)
        except:
            pass

    async def process_captcha(self):
        print(">>> [OCR] 開始處理 Indievox 圖形驗證碼...")

        js_get_image = """
        (function() {
            var img = document.querySelector('#TicketForm_verifyCode-image');
            if (!img) return null;
            if (!img.complete || img.naturalWidth === 0) return "NOT_LOADED";
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """
        try:
            for attempt in range(5):
                base64_data = await self.tab.evaluate(js_get_image)
                if not base64_data:
                    return False
                if base64_data == "NOT_LOADED":
                    await asyncio.sleep(0.5)
                    continue

                img_bytes = base64.b64decode(base64_data)
                if self.ocr:
                    ocr_answer = self.ocr.classification(img_bytes)
                    ocr_answer = ocr_answer.strip() if ocr_answer else ""
                else:
                    return False

                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                if len(ocr_answer) == 4:
                    js_fill_input = f"""
                    (function() {{
                        var input = document.querySelector('#TicketForm_verifyCode');
                        if (input) {{
                            input.value = '{ocr_answer}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }})();
                    """
                    if await self.tab.evaluate(js_fill_input):
                        print(f">>> [OCR] ✅ 已自動填入驗證碼: {ocr_answer}")
                        return True

                print(">>> [OCR] ⚠️ 辨識可能不準確，點擊圖片換一張...")
                js_refresh = """
                (function() {
                    let img = document.querySelector('#TicketForm_verifyCode-image');
                    let input = document.querySelector('#TicketForm_verifyCode');
                    if(img) {
                        let ev = new MouseEvent('click', {bubbles: true, cancelable: true, view: window});
                        img.dispatchEvent(ev);
                        img.click();
                    }
                    if(input) input.value = '';
                })();
                """
                await self.tab.evaluate(js_refresh)
                await asyncio.sleep(1.0)
            return False
        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False

# ==========================================
# [獨立音樂網 Indievox 搶票機器人]
# ==========================================


class KlookBOT:

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        self.settings_path = config.get("config_filepath", "settings.json")
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 讀取刷新秒數 (支援 auto_reload_page_interval 與 auto_reload_interval)
        self.auto_reload_interval = float(
            config.get("auto_reload_page_interval")
            or config.get("auto_reload_interval")
            or config.get("refresh_interval")
            or 1.5
        )

        # 讀取設定參數
        self.date_auto_select = config.get("date_auto_select", {})
        self.area_auto_select = config.get("area_auto_select", {})

        self.date_mode = self.date_auto_select.get(
            "mode", "from top to bottom")
        self.date_keyword = self.date_auto_select.get(
            "date_keyword", ""
        ).strip()
        self.area_mode = self.area_auto_select.get(
            "mode", "from top to bottom")
        self.area_keyword = self.area_auto_select.get(
            "area_keyword", ""
        ).strip()
        self.keyword_exclude = config.get(
            "keyword_exclude", ""
        ) or self.area_auto_select.get("area_keyword_exclude", "")

        print("\n" + "=" * 50)
        print(">>> [KlookBOT] 🤖 機器人初始化完成，啟動設定如下：")
        print(f">>> 📅 【日期選擇邏輯】：{self.date_mode}")
        print(f">>> 📅 【日期關鍵字】 ：'{self.date_keyword}'")
        print(
            f">>> 🎫 【區域選擇邏輯】：{self.area_mode} (用於時間/套餐/組合/票種)"
        )
        print(f">>> 🎫 【區域關鍵字】 ：'{self.area_keyword}'")
        print(f">>> 🚫 【排除關鍵字】 ：'{self.keyword_exclude}'")
        print(f">>> 🔢 【目標預訂張數】：{self.ticket_number} 張")
        print(f">>> 🔄 【倒數刷新頻率】：{self.auto_reload_interval} 秒")
        print("=" * 50 + "\n")
        print(
            ">>> [系統] 💡 請自行登入並挑選進入 Klook"
            " 活動頁面，機器人將自動接管購票！"
        )

    async def run(self):
        try:
            import util

            pause_file = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt"
            )
        except:
            pause_file = "MAXBOT_INT28_IDLE.txt"

        while True:
            try:
                if os.path.exists(pause_file):
                    await asyncio.sleep(0.5)
                    continue

                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                # 只要在 Klook 網域且符合活動或排隊頁面，持續執行
                if "klook.com" in current_url.lower():
                    if (
                        "/event-detail/" in current_url.lower()
                        or "/activity/" in current_url.lower()
                        or "queue" in current_url.lower()
                    ):
                        await self.process_ticket_selection()

            except Exception as e:
                pass
            await asyncio.sleep(0.05)

    async def process_ticket_selection(self):
        """執行 Klook 頁面自動化：排隊、倒數、選票、庫存切換與下一步"""

        def parse_keywords(kw_str):
            if not kw_str:
                return []
            try:
                if kw_str.startswith("[") and kw_str.endswith("]"):
                    return json.loads(kw_str)
                if '"' in kw_str or "'" in kw_str:
                    return json.loads("[" + kw_str + "]")
            except:
                pass
            return [x.strip() for x in kw_str.split(",") if x.strip()]

        js_date_kws = json.dumps(
            parse_keywords(self.date_keyword), ensure_ascii=False
        )
        js_area_kws = json.dumps(
            parse_keywords(self.area_keyword), ensure_ascii=False
        )
        js_excludes = json.dumps(
            parse_keywords(self.keyword_exclude), ensure_ascii=False
        )

        js_script = f"""
        (function() {{
            try {{
                const dateKws = {js_date_kws};
                const areaKws = {js_area_kws};
                const excludes = {js_excludes};
                const dateMode = '{self.date_mode}';
                const areaMode = '{self.area_mode}';
                const targetTickets = {self.ticket_number};

                // ==========================================
                // 優先關卡 0-A：排隊成功「輪到你囉」-> 點擊「繼續預訂」
                // ==========================================
                let buyBtn = document.querySelector('button.buy_button') || 
                             document.querySelector('button[data-spm-module*="ConfirmBookingBtn"]') ||
                             Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('繼續預訂'));
                if (buyBtn && !buyBtn.disabled && !buyBtn.className.includes('disabled')) {{
                    buyBtn.click();
                    return "CLICKED_CONFIRM_BOOKING";
                }}

                // ==========================================
                // 優先關卡 0-B：排隊模組 (#queue_module) -> 倒數完畢秒點「排隊購票」
                // ==========================================
                let queueModule = document.querySelector('#queue_module');
                if (queueModule) {{
                    let queueBtn = queueModule.querySelector('button.queue_button') || 
                                   queueModule.querySelector('button[data-spm-module*="EnterQueueBtn"]') ||
                                   Array.from(queueModule.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('排隊購票'));
                    
                    let presaleCd = queueModule.querySelector('.presale-countdown');
                    let cdText = presaleCd ? presaleCd.innerText.trim() : "";
                    
                    if (queueBtn && !queueBtn.disabled && !queueBtn.className.includes('disabled')) {{
                        if (!cdText || cdText === "00:00:00" || cdText.includes("00:00:00")) {{
                            queueBtn.click();
                            return "CLICKED_ENTER_QUEUE";
                        }} else {{
                            return "QUEUE_COUNTDOWN|" + cdText;
                        }}
                    }} else if (presaleCd && cdText) {{
                        return "QUEUE_COUNTDOWN|" + cdText;
                    }}
                }}

                // ==========================================
                // 優先關卡 0-C：一般頁面開賣倒數 (.countdown-content)
                // ==========================================
                let countdownEl = document.querySelector('.countdown-content, [class*="countdown-content"]');
                if (countdownEl && countdownEl.offsetParent !== null) {{
                    let label = countdownEl.querySelector('.countdown-label, [class*="countdown-label"]');
                    let isCounting = label ? label.innerText.includes("開賣倒數") : true;
                    if (isCounting) {{
                        let timeBlocks = Array.from(countdownEl.querySelectorAll('.time-block, [class*="time-block"]')).map(el => el.innerText.trim());
                        let timeStr = timeBlocks.join(":");
                        return "COUNTDOWN_DETECTED|" + (timeStr || "計算中");
                    }}
                }}

                // ==========================================
                // 輔助函式：日期正規化與關鍵字比對
                // ==========================================
                function normalizeDateStr(str) {{
                    if (!str) return "";
                    return str.toString()
                        .replace(/(\\d{{1,4}})[年/.-](\\d{{1,2}})[月/.-](\\d{{1,2}})日?/g, (m, y, mo, d) => `${{parseInt(mo)}}/${{parseInt(d)}}`)
                        .replace(/(\\d{{1,2}})[月/.-](\\d{{1,2}})日?/g, (m, mo, d) => `${{parseInt(mo)}}/${{parseInt(d)}}`)
                        .toUpperCase()
                        .trim();
                }}

                function isMatch(text, keywords, isDateField = false) {{
                    if (!keywords || keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) return true;
                    let rawText = text.toUpperCase();
                    let normText = isDateField ? normalizeDateStr(text) : rawText;

                    for (let k of keywords) {{
                        let rawK = k.trim().toUpperCase();
                        let normK = isDateField ? normalizeDateStr(k) : rawK;

                        if (rawText.includes(rawK)) return true;
                        if (isDateField && normText.includes(normK)) return true;

                        let target_kws = rawK.split(/\\s+/).filter(w => w.length > 0);
                        if (target_kws.length > 1) {{
                            let allMatch = target_kws.every(w => {{
                                let normW = isDateField ? normalizeDateStr(w) : w;
                                return rawText.includes(w) || (isDateField && normText.includes(normW));
                            }});
                            if (allMatch) return true;
                        }}
                    }}
                    return false;
                }}

                function isExcluded(text) {{
                    if (!excludes || excludes.length === 0 || (excludes.length === 1 && excludes[0] === "")) return false;
                    for (let exc of excludes) {{
                        if (exc.trim().length > 0 && text.toUpperCase().includes(exc.trim().toUpperCase())) {{
                            return true;
                        }}
                    }}
                    return false;
                }}

                function pickCandidate(candidates, mode) {{
                    if (candidates.length === 0) return null;
                    if (mode === "from bottom to top") {{
                        return candidates[candidates.length - 1];
                    }} else if (mode === "random") {{
                        return candidates[Math.floor(Math.random() * candidates.length)];
                    }}
                    return candidates[0];
                }}

                // ==========================================
                // 優先關卡 A：處理選位圖與彈窗攔截
                // ==========================================
                let seatContainer = document.querySelector('#__Seat') || 
                                    document.querySelector('[class*="seats-"]') || 
                                    document.querySelector('[class*="seatMap"]');
                if (seatContainer) {{
                    return "SUCCESS_SEAT_MAP";
                }}

                let modalContainer = document.querySelector('.klk-modal') || document.querySelector('.el-dialog__wrapper:not([style*="display: none"])');
                if (modalContainer && modalContainer.offsetParent !== null) {{
                    let modalText = modalContainer.innerText || "";
                    let modalConfirmBtn = modalContainer.querySelector('.confirm-button') || 
                                          modalContainer.querySelector('.klk-button-primary') ||
                                          modalContainer.querySelector('.el-button--primary') ||
                                          modalContainer.querySelector('button');
                    if (modalConfirmBtn) {{
                        modalConfirmBtn.click();
                        return "MODAL_DISMISSED|" + modalText.substring(0, 30);
                    }}
                }}

                // ==========================================
                // 優先關卡 B：張數選擇
                // ==========================================
                let quantityBody = document.querySelector('.quantityBody') || document.querySelector('[class*="quantityBody"]');
                let isQuantityReady = false;

                if (quantityBody) {{
                    let rows = Array.from(quantityBody.querySelectorAll('[class*="eventUnit-"], [class*="eventUnit"]'));
                    let validRows = [];
                    
                    for (let row of rows) {{
                        let textEl = row.querySelector('[class*="type-"], [class*="unitName"]');
                        let text = textEl ? textEl.innerText.toUpperCase() : "";
                        if (!isExcluded(text) && isMatch(text, areaKws, false)) {{
                            validRows.push(row);
                        }}
                    }}

                    let targetRow = pickCandidate(validRows, areaMode) || validRows[0] || rows[0];
                    if (targetRow) {{
                        let valEl = targetRow.querySelector('[class*="value-"], [class*="count"], input');
                        let currentVal = 0;
                        if (valEl) {{
                            currentVal = parseInt(valEl.value !== undefined ? valEl.value : valEl.innerText) || 0;
                        }}
                        
                        if (currentVal < targetTickets) {{
                            let plusBtn = targetRow.querySelectorAll('[class*="btn-"]')[1] || 
                                          targetRow.querySelector('[class*="icon_other_plus"]')?.closest('[class*="btn-"]') ||
                                          targetRow.querySelector('button:last-of-type');
                            
                            let isBtnDisabled = !plusBtn || 
                                                plusBtn.disabled || 
                                                plusBtn.className.includes('Disabled') || 
                                                plusBtn.className.includes('disabled') ||
                                                plusBtn.getAttribute('aria-disabled') === 'true';

                            if (plusBtn && !isBtnDisabled) {{
                                plusBtn.click();
                                return "CLICKED_PLUS|" + (currentVal + 1);
                            }} else {{
                                isQuantityReady = true;
                            }}
                        }} else {{
                            isQuantityReady = true;
                        }}
                    }}
                }}

                // ==========================================
                // 優先關卡 C：點擊「下一步」按鈕 (針對最新 HTML 結構修復版)
                // ==========================================
                // 1. 透過父層模組 data-spm-module="TicketOptionsNext" 尋找
                // 2. 透過最新的 class "next-btn" 尋找
                // 3. 透過按鈕內的文字 "下一步" 暴力尋找
                let nextBtn = document.querySelector('div[data-spm-module="TicketOptionsNext"] button') || 
                              document.querySelector('button.next-btn') || 
                              document.querySelector('.credits button.klk-button-primary') ||
                              Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('下一步'));
                              
                if (nextBtn) {{
                    let isBtnDisabled = nextBtn.disabled || nextBtn.className.includes('disabled');
                    
                    if (!isBtnDisabled) {{
                        if (!quantityBody || isQuantityReady) {{
                            nextBtn.click();
                            return "SUCCESS_NEXT";
                        }}
                    }}
                }}

                // ==========================================
                // 優先關卡 D：處理所有未選選項 (日期、時間、票種、組合套餐)
                // ==========================================
                let skuGroups = Array.from(document.querySelectorAll('[class*="skuGroup"]'));
                for (let group of skuGroups) {{
                    let titleEl = group.querySelector('[class*="name-"], [class*="groupName"], [class*="title"]');
                    let title = titleEl ? titleEl.innerText.trim() : "";
                    
                    let alreadySelected = group.querySelector('[class*="active"], [class*="selected"], [class*="Checked"]');
                    if (alreadySelected) continue;

                    let isDateField = title.includes("日期");
                    let kwsToUse = isDateField ? dateKws : areaKws;
                    let modeToUse = isDateField ? dateMode : areaMode;

                    // D-1：月曆模式
                    let dateSelectBox = group.querySelector('[class*="date-select-box"]');
                    if (isDateField && dateSelectBox) {{
                        let displayEl = dateSelectBox.querySelector('[class*="date-display"]');
                        if (displayEl && displayEl.innerText.includes("選擇日期")) {{
                            dateSelectBox.click();
                            return "OPENED_DATE_PICKER";
                        }}
                        
                        let popper = document.querySelector('[class*="klk-poptip-popper"], [class*="date-picker-popper"]');
                        if (popper) {{
                            let validDates = [];
                            let dateCells = Array.from(popper.querySelectorAll('[class*="klk-date-picker-date"]:not([class*="disabled"]):not([class*="empty"])'));
                            
                            for (let cell of dateCells) {{
                                let inner = cell.querySelector('[class*="klk-date-picker-date-inner"]') || cell;
                                let dateNum = inner ? inner.innerText.trim() : "";
                                let cellDateAttr = cell.getAttribute('data-date') || cell.getAttribute('title') || dateNum;
                                
                                if (isMatch(cellDateAttr, dateKws, true) || isMatch(dateNum, dateKws, false)) {{
                                    validDates.push(cell);
                                }}
                            }}
                            
                            let targetDate = pickCandidate(validDates, dateMode);
                            if (targetDate) {{
                                targetDate.click();
                                return "SELECTED_DATE_PICKER";
                            }}
                        }}
                        continue;
                    }}

                    // D-2：一般按鈕選項
                    let options = Array.from(group.querySelectorAll('[class*="spec-"]:not([class*="disabled"]):not([class*="Disabled"]), [class*="specItem"]:not([class*="disabled"])'));
                    let validOptions = [];
                    
                    for (let opt of options) {{
                        let text = opt.innerText.trim();
                        if (!isExcluded(text) && isMatch(text, kwsToUse, isDateField)) {{
                            validOptions.push(opt);
                        }}
                    }}
                    
                    let targetOption = pickCandidate(validOptions, modeToUse);
                    if (targetOption) {{
                        targetOption.click();
                        return "SELECTED_OPTION|" + title + " -> " + targetOption.innerText.replace(/\\n/g, ' ');
                    }}
                }}

                // ==========================================
                // 優先關卡 E：無票刷票機制 (全部選項已點選，但無法出票時隨機切換)
                // ==========================================
                let allGroupsSelected = skuGroups.length > 0 && skuGroups.every(g => g.querySelector('[class*="active"], [class*="selected"], [class*="Checked"]'));
                if (allGroupsSelected && (!quantityBody || (nextBtn && (nextBtn.disabled || nextBtn.className.includes('disabled'))))) {{
                    // 尋找票種或套票群組
                    let targetGroups = skuGroups.filter(g => {{
                        let t = g.querySelector('[class*="name-"], [class*="groupName"], [class*="title"]')?.innerText || "";
                        return t.includes("票種") || t.includes("套餐") || t.includes("套票") || t.includes("組合");
                    }});
                    
                    if (targetGroups.length === 0) targetGroups = skuGroups;
                    let randGroup = targetGroups[Math.floor(Math.random() * targetGroups.length)];
                    let groupTitle = randGroup.querySelector('[class*="name-"], [class*="groupName"]')?.innerText.trim() || "選項";
                    
                    // 優先切換其他可選項目
                    let otherOptions = Array.from(randGroup.querySelectorAll('[class*="spec-"]:not([class*="active"]):not([class*="selected"]):not([class*="disabled"]):not([class*="Disabled"])'));
                    if (otherOptions.length > 0) {{
                        let switchOpt = otherOptions[Math.floor(Math.random() * otherOptions.length)];
                        switchOpt.click();
                        return "SOLDOUT_SWITCH_OPTION|" + groupTitle + " -> " + switchOpt.innerText.replace(/\\n/g, ' ');
                    }} else {{
                        // 如果沒其他選項，重新點擊當前選項刷新
                        let currentOpt = randGroup.querySelector('[class*="active"], [class*="selected"]');
                        if (currentOpt) {{
                            currentOpt.click();
                            return "SOLDOUT_RECLICK_OPTION|" + groupTitle;
                        }}
                    }}
                }}

                return "WAITING_DOM";
            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_script)

            # 1. 排隊成功 -> 繼續預訂
            if result == "CLICKED_CONFIRM_BOOKING":
                print(">>> [KlookBOT] 🎊 排隊輪到你囉！已秒按「繼續預訂」！")
                await asyncio.sleep(0.2)

            # 2. 排隊模組倒數中 / 秒按排隊購票
            elif result == "CLICKED_ENTER_QUEUE":
                print(
                    ">>> [KlookBOT] ⚡ 倒數結束，已火速點擊【排隊購票】進入佇列！"
                )
                await asyncio.sleep(0.2)

            elif isinstance(result, str) and result.startswith(
                "QUEUE_COUNTDOWN|"
            ):
                cd = result.split("|")[1]
                # 倒數極速監聽 (不重新整理頁面，避免斷開 WebSocket 排隊通道)
                await asyncio.sleep(0.08)

            # 3. 傳統頁面倒數 -> 自動刷新
            elif isinstance(result, str) and result.startswith(
                "COUNTDOWN_DETECTED|"
            ):
                time_left = result.split("|")[1]
                print(
                    f">>> [KlookBOT] ⏳ 尚未開賣 (倒數: {time_left})，等待 {self.auto_reload_interval} 秒後重新整理..."
                )
                await asyncio.sleep(self.auto_reload_interval)
                await self.tab.evaluate("window.location.reload()")
                await asyncio.sleep(0.5)

            # 4. 成功進入選位
            elif result == "SUCCESS_SEAT_MAP":
                print(
                    ">>> [KlookBOT] 🎉 成功出現選位圖！代表有搶到進入結帳流程的資格！"
                )
                await asyncio.sleep(0.5)  # 保持輕微延遲，不卡死循環

            # 5. 阻擋彈窗處理
            elif isinstance(result, str) and result.startswith(
                "MODAL_DISMISSED|"
            ):
                msg = result.split("|")[1]
                print(
                    f">>> [KlookBOT] ⚠️ 攔截到 Klook 彈窗 (內容: {msg}...)，已自動關閉！"
                )
                await asyncio.sleep(0.2)

            # 6. 成功點擊下一步
            elif result == "SUCCESS_NEXT":
                print(">>> [KlookBOT] 🎉 成功點擊「下一步」按鈕！等待系統判定...")
                await asyncio.sleep(0.5)

            # 7. 張數遞增
            elif isinstance(result, str) and result.startswith("CLICKED_PLUS|"):
                next_count = result.split("|")[1]
                print(
                    f">>> [KlookBOT] ➕ 正在增加票券張數 (已點選至: {next_count} / 目標: {self.ticket_number} 張)..."
                )
                await asyncio.sleep(0.08)

            # 8. 選取選項
            elif isinstance(result, str) and result.startswith(
                "SELECTED_OPTION|"
            ):
                detail = result.split("|")[1]
                print(f">>> [KlookBOT] 👉 成功選取：【{detail}】")
                await asyncio.sleep(0.15)

            # 9. 沒票切換刷票
            elif isinstance(result, str) and (
                result.startswith("SOLDOUT_SWITCH_OPTION|")
                or result.startswith("SOLDOUT_RECLICK_OPTION|")
            ):
                detail = result.split("|")[1]
                print(
                    f">>> [KlookBOT] 🔄 目前組合暫無票券，切換選項刷票中：【{detail}】"
                )
                await asyncio.sleep(0.15)

            # 10. 日期選擇器操作
            elif result == "SELECTED_DATE_PICKER":
                print(">>> [KlookBOT] 📅 成功從月曆表點選目標日期！")
                await asyncio.sleep(0.15)

            elif result == "OPENED_DATE_PICKER":
                print(">>> [KlookBOT] 📅 正在展開日期選擇月曆...")
                await asyncio.sleep(0.15)

            elif isinstance(result, str) and result.startswith("ERROR|"):
                print(f">>> [KlookBOT 錯誤] JS 執行異常: {result}")
                await asyncio.sleep(0.3)

            elif result == "WAITING_DOM":
                await asyncio.sleep(0.05)

        except Exception as e:
            print(f">>> [KlookBOT 例外] {e}")

# ==========================================
# [Klook 客路 搶票機器人]
# ==========================================


class yes24Bot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        # 讀取設定檔
        self.ticket_number = int(config.get("ticket_number", 1))
        self.date_keyword = str(self.config.get(
            "date_auto_select", {}).get("date_keyword", "")).strip()
        self.time_mode = str(self.config.get("time_auto_select", {}).get(
            "mode", "from top to bottom")).lower()
        self.refresh_sec = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))

        # 🌟 新增：讀取 GUI 區域/金額關鍵字與選位模式
        self.area_mode = str(self.config.get("area_auto_select", {}).get(
            "mode", "random")).lower()
        self.area_keyword = str(self.config.get("area_auto_select", {}).get(
            "area_keyword", "")).strip()

        self.last_url = ""
        self._bot_entered_time = time.time()

        # 修正後的暫停檔案名稱
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

    async def run(self):
        print(
            f">>> [YES24 半自動] 機器人啟動！(目標張數: {self.ticket_number} | 鎖定日期: {self.date_keyword})")
        print(">>> [系統] 🛡️ 已啟動「動態分頁追蹤」與「防 이선좌 (已售出) 2秒退避冷卻」模式！")

        while True:
            try:
                # 1. 暫停攔截
                if os.path.exists(self.PAUSE_FILE):
                    if not getattr(self, 'is_printing_pause', False):
                        print("\n>>> [YES24] ⏸️ 程式已暫停！等待您在 GUI 按下接續...")
                        self.is_printing_pause = True
                    await asyncio.sleep(0.5)
                    continue
                self.is_printing_pause = False

                # 2. 永遠抓取「最後開啟/最上層」的分頁 (支援 YES24 點擊 Booking 後跳出的新視窗)
                active_tab = self.driver.tabs[-1]
                current_url = await active_tab.evaluate("window.location.href")

                if current_url and current_url != self.last_url:
                    print(f">>> [系統] 偵測到頁面切換: {current_url}")
                    self.last_url = current_url

                if current_url:
                    await self.dispatch_action(current_url, active_tab)

            except Exception as e:
                pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, url, active_tab):
        """YES24 任務分發中心"""
        upper_url = url.upper()

        phase = await self.detect_yes24_phase(active_tab)

        if phase == "SUCCESS_PHASE":
            if not getattr(self, 'success_printed', False):
                print(
                    "\n>>> [YES24-系統] 🎉🎉🎉 鎖票成功！已進入 Discount/Coupon (할인/쿠폰) 結帳階段！")
                print(">>> [系統] 🛡️ 機器人已完全停止點擊，請您安心完成後續付款！")
                self.success_printed = True
            await asyncio.sleep(1.0)
            return

        elif phase == "MAIN_PAGE":
            self.success_printed = False
            await self.step1_main_page(active_tab)

        elif phase == "DATE_TIME_PHASE":
            self.success_printed = False
            await self.step2_select_date_time(active_tab)

        elif phase == "SEAT_PHASE":
            self.success_printed = False
            await self.step3_select_seat(active_tab)

        else:
            await asyncio.sleep(0.05)

    async def detect_yes24_phase(self, active_tab):
        """YES24 頁面特徵偵測器：支援 iframe 穿透與特徵判斷"""
        js_phase = """
        (function() {
            try {
                function isVisible(el) {
                    return el && (el.offsetWidth > 0 || el.offsetHeight > 0);
                }
                
                // 🌟 讓探測器可以看透 iframe
                const queryAllDocs = (selector) => {
                    let docs = [document];
                    try {
                        let iframes = document.querySelectorAll('iframe');
                        for (let f of iframes) {
                            try {
                                if (f.contentWindow && f.contentWindow.document) {
                                    let d = f.contentWindow.document;
                                    docs.push(d);
                                    let inner = d.querySelectorAll('iframe');
                                    for (let inf of inner) {
                                        try { if (inf.contentWindow && inf.contentWindow.document) docs.push(inf.contentWindow.document); } catch(e) {}
                                    }
                                }
                            } catch(e) {}
                        }
                    } catch(e) {}
                    
                    for (let doc of docs) {
                        let el = doc.querySelector(selector);
                        if (isVisible(el)) return el;
                    }
                    return null;
                };

                let url = window.location.href.toLowerCase();
                
                // 1. 活動主頁面
                if (!url.includes('fnperfsaleprocess')) {
                    let mainBtn = document.querySelector('div.sbkBtn, a#hlkPurchase');
                    if (isVisible(mainBtn)) return "MAIN_PAGE";
                }

                // 2. 成功進入折扣/付款頁面
                let step3 = queryAllDocs('#step03');
                let step4 = queryAllDocs('#step04');
                let step5 = queryAllDocs('#step05');
                let promo = queryAllDocs('#spanPromotionSeat, input[name="rdoPromotionSeat"], li.m03.on');
                if (step3 || step4 || step5 || promo) {
                    return "SUCCESS_PHASE";
                }
                
                // 3. 座位選擇頁面 (Seat Map) - 穿透尋找座位或送出按鈕
                let seatArray = queryAllDocs('#divSeatArray, div[name="tk"]');
                let choiceEndBtn = queryAllDocs('a[href*="ChoiceEnd"], img.booking');
                
                if (seatArray || choiceEndBtn) {
                    if (window._yes_next_clicked) window._yes_next_clicked = false;
                    return "SEAT_PHASE";
                }

                // 4. 日期與時間選擇頁面 (Date & Time)
                let step1Date = queryAllDocs('#step01_date');
                let step1Time = queryAllDocs('#step01_time');
                let calDate = queryAllDocs('a[onclick*="fdc_CalDateClick"]');
                if (step1Date || step1Time || calDate) {
                    window._yes_next_clicked = false;
                    return "DATE_TIME_PHASE";
                }
                
                return "WAITING_DOM";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """
        return await active_tab.evaluate(js_phase)

    async def step1_main_page(self, active_tab):
        """[階段一] 主頁面：持續重整等待 Booking 按鈕出現"""
        js_main = """
        (function() {
            try {
                let btn = document.querySelector('a#hlkPurchase');
                if (btn && window.getComputedStyle(btn).display !== 'none') {
                    let text = (btn.innerText || "").toUpperCase();
                    if (text.includes("BOOKING") || btn.classList.contains("ebtn_mgt")) {
                        btn.click();
                        return "CLICKED_BOOKING";
                    }
                }
                return "WAITING_BTN";
            } catch(e) { return "ERROR"; }
        })();
        """
        result = await active_tab.evaluate(js_main)

        if result == "CLICKED_BOOKING":
            print(">>> [YES24-主頁] 🚀 成功點擊「Booking」按鈕！等待彈出新視窗...")
            await asyncio.sleep(1.0)
        elif result == "WAITING_BTN":
            # 尚未開賣，按照設定的秒數自動重整
            now = time.time()
            if not hasattr(self, 'last_reload_time'):
                self.last_reload_time = now
            if now - self.last_reload_time > self.refresh_sec:
                print(f">>> [YES24-主頁] ⏳ 尚未開賣，執行自動重整等待按鈕出現...")
                await active_tab.reload()
                self.last_reload_time = time.time()
                await asyncio.sleep(0.5)

    async def step2_select_date_time(self, active_tab):
        """[階段二] 彈窗內選擇日期、時間與下一步 (針對國際版 DOM 特化)"""
        # 🔥 破案關鍵：清除設定檔中多餘的雙引號與補零，避免造成 JS 語法錯誤崩潰
        clean_keyword = self.date_keyword.replace(
            '"', '').replace("'", "").lstrip("0").strip()

        js_date_time = f"""
        (function() {{
            try {{
                if (!window._yes_hook_date) {{
                    window._lastAlert = "";
                    window.originalAlert = window.alert;
                    window.alert = function(m) {{ window._lastAlert = m; }};
                    window._yes_hook_date = true;
                }}
                if (window._lastAlert) {{
                    let m = window._lastAlert; window._lastAlert = "";
                    return "ALERT|" + m;
                }}

                function isVisible(el) {{
                    return el && window.getComputedStyle(el).display !== 'none';
                }}

                let step1Date = document.getElementById('step01_date');
                let step1Time = document.getElementById('step01_time');
                
                // (1) 判斷「時間選單」區塊是否顯示 (代表日期已經選好)
                if (isVisible(step1Time)) {{
                    let times = Array.from(document.querySelectorAll('ul#ulTime li')).filter(isVisible);
                    if (times.length > 0) {{
                        let selectedTime = times.find(t => t.classList.contains('on'));
                        // 若尚未選取時間
                        if (!selectedTime) {{
                            let mode = "{self.time_mode}";
                            let targetIdx = 0;
                            if (mode.includes("random")) targetIdx = Math.floor(Math.random() * times.length);
                            else if (mode.includes("bottom") || mode.includes("下")) targetIdx = times.length - 1;
                            
                            times[targetIdx].click();
                            return "TIME_CLICKED|" + times[targetIdx].innerText.trim();
                        }} else {{
                            // 時間已選定，點擊「Select Seats」藍色按鈕 或 「Next」按鈕
                            let selectSeatBtn = document.getElementById('btnSeatSelect'); // 國際版藍色按鈕
                            let nextBtn = document.querySelector('a[onclick*="fdc_VerifySelSeatNumber"]'); // 右下角 Next
                            
                            let btnToClick = isVisible(selectSeatBtn) ? selectSeatBtn : (isVisible(nextBtn) ? nextBtn : null);
                            
                            if (btnToClick) {{
                                if (!window._yes_next_clicked) {{
                                    btnToClick.click();
                                    window._yes_next_clicked = true;
                                    return "NEXT_CLICKED";
                                }}
                                return "WAITING_TRANSITION";
                            }}
                        }}
                    }}
                }} 
                
                // (2) 若時間區塊還沒出來，代表要先選日期
                if (isVisible(step1Date)) {{
                    let dates = Array.from(document.querySelectorAll('td.select a.dcursor, td.term a.dcursor')).filter(isVisible);
                    
                    let validDates = dates.filter(d => {{
                        let t = (d.title || "").toLowerCase();
                        return !t.includes("no show") && !t.includes("없습");
                    }});
                    
                    if (validDates.length === 0) return "WAITING_VALID_DATES";
                    
                    // 將洗乾淨的關鍵字放入 JS 中
                    let keyword = "{clean_keyword}";
                    let targetDate = validDates.find(d => d.innerText.trim() === keyword);
                    if (!targetDate) targetDate = validDates[0];
                    
                    if (targetDate) {{
                        targetDate.click();
                        return "DATE_CLICKED|" + targetDate.innerText.trim();
                    }}
                }}
                return "WAITING_DOM";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        result = await active_tab.evaluate(js_date_time)

        if isinstance(result, str):
            if result.startswith("ALERT|"):
                print(f">>> [YES24-系統] 💥 攔截到視窗警告: 【{result.split('|')[1]}】")
                await active_tab.evaluate("window._yes_next_clicked = false;")
                await asyncio.sleep(0.5)
            elif result.startswith("DATE_CLICKED|"):
                print(
                    f">>> [YES24-日期] 📅 已選取日期「{result.split('|')[1]}號」，加載場次時間中...")
                await asyncio.sleep(0.2)
            elif result.startswith("TIME_CLICKED|"):
                print(f">>> [YES24-時間] ⏰ 已根據邏輯選取場次「{result.split('|')[1]}」...")
                await asyncio.sleep(0.2)
            elif result == "NEXT_CLICKED":
                print(">>> [YES24-日期時間] 🚀 已點擊「Select Seats / Next」！準備進入座位圖搶票...")
                await asyncio.sleep(0.5)
            elif result.startswith("ERROR|"):
                print(f">>> [DEBUG] Date JS Error: {result}")

    async def detect_yes24_phase(self, active_tab):
        """YES24 頁面特徵偵測器：直擊 ifrmSeatFrame 核心"""
        js_phase = """
        (function() {
            try {
                function isVisible(el) {
                    if (!el) return false;
                    let style = window.getComputedStyle(el);
                    return style.display !== 'none' && (el.offsetWidth > 0 || el.offsetHeight > 0);
                }

                let docs = [document];
                
                // 🔥 終極解法：直接精準抓取 YES24 截圖中的 ifrmSeatFrame
                try {
                    let seatFrame = document.getElementById('ifrmSeatFrame');
                    if (seatFrame && seatFrame.contentDocument) {
                        docs.push(seatFrame.contentDocument);
                    } else if (window.frames['ifrmSeatFrame'] && window.frames['ifrmSeatFrame'].document) {
                        docs.push(window.frames['ifrmSeatFrame'].document);
                    }
                } catch(e) {}

                // 備用：掃描其餘可能的 iframe
                try {
                    let iframes = document.querySelectorAll('iframe');
                    for (let f of iframes) {
                        try { if (f.contentDocument && !docs.includes(f.contentDocument)) docs.push(f.contentDocument); } catch(e) {}
                    }
                } catch(e) {}

                let url = window.location.href.toLowerCase();
                
                // 1. 活動主頁面
                if (!url.includes('fnperfsaleprocess')) {
                    let mainBtn = document.querySelector('div.sbkBtn, a#hlkPurchase');
                    if (isVisible(mainBtn)) return "MAIN_PAGE";
                }

                // 2. 結帳頁面
                for (let doc of docs) {
                    if (isVisible(doc.getElementById('step03')) || isVisible(doc.getElementById('step04'))) {
                        return "SUCCESS_PHASE";
                    }
                }
                
                // 3. 座位選擇頁面 (SEAT_PHASE) - 直接檢查 docs 裡有沒有 divSeatArray
                for (let doc of docs) {
                    let seatMap = doc.getElementById('divSeatArray');
                    let anySeat = doc.querySelector('div[name="tk"]');
                    let choiceBtn = doc.querySelector('a[href*="ChoiceEnd"], img.booking');
                    
                    if (seatMap || anySeat || choiceBtn) {
                        if (window._yes_next_clicked) window._yes_next_clicked = false;
                        return "SEAT_PHASE";
                    }
                }

                // 4. 日期與時間選擇頁面 (因為找不到座位圖，退而求其次判斷日期)
                for (let doc of docs) {
                    let step1Date = doc.getElementById('step01_date');
                    let step1Time = doc.getElementById('step01_time');
                    if (isVisible(step1Date) || isVisible(step1Time)) {
                        return "DATE_TIME_PHASE";
                    }
                }
                
                return "WAITING_DOM";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """
        return await active_tab.evaluate(js_phase)

    async def step3_select_seat(self, active_tab):
        """[階段三] 座位選擇：實裝價位/區域關鍵字過濾 與 隨機/指定排序選位"""
        ticket_number = self.ticket_number
        # 處理關鍵字，避免破壞 JS 語法
        clean_area_keyword = self.area_keyword.replace(
            "'", "\\'").replace("\n", "")
        js_seat = f"""
        (function() {{
            try {{
                if (!window.top._lastAlert) window.top._lastAlert = "";
                
                const hookWindow = (win) => {{
                    if (win && !win._yes_hook_seat) {{
                        win._yes_hook_seat = true;
                        win.originalAlert = win.alert;
                        win.alert = function(m) {{ window.top._lastAlert = m; }};
                        win.originalConfirm = win.confirm;
                        win.confirm = function(m) {{ window.top._lastAlert = m; return true; }};
                    }}
                }};
                
                hookWindow(window);
                let docs = [document];
                
                try {{
                    let seatFrame = document.getElementById('ifrmSeatFrame');
                    if (seatFrame) {{
                        if (seatFrame.contentWindow) hookWindow(seatFrame.contentWindow);
                        if (seatFrame.contentDocument) docs.push(seatFrame.contentDocument);
                    }} else if (window.frames['ifrmSeatFrame']) {{
                        hookWindow(window.frames['ifrmSeatFrame']);
                        if (window.frames['ifrmSeatFrame'].document) docs.push(window.frames['ifrmSeatFrame'].document);
                    }}
                }} catch(e) {{}}
                try {{
                    let iframes = document.querySelectorAll('iframe');
                    for (let f of iframes) {{
                        try {{ 
                            if (f.contentWindow) hookWindow(f.contentWindow);
                            if (f.contentDocument && !docs.includes(f.contentDocument)) docs.push(f.contentDocument); 
                        }} catch(e) {{}}
                    }}
                }} catch(e) {{}}
                let now = Date.now();
                if (window.top._lastAlert) {{
                    let m = window.top._lastAlert; 
                    window.top._lastAlert = ""; 
                    window._clicked_count = 0;  
                    window._last_submit = 0;
                    
                    if (window._last_seat_id) {{
                        window._banned_seats = window._banned_seats || [];
                        window._banned_seats.push({{ id: window._last_seat_id, time: now }});
                    }}
                    
                    for (let doc of docs) {{
                        let resetBtn = doc.querySelector('a[href*="ChoiceReset"]');
                        if (resetBtn) resetBtn.click();
                    }}
                    return "ALERT|" + m;
                }}
                let targetCount = {ticket_number};
                let allAvailableSeats = [];
                let actualSelectedCount = 0;
                let submitBtn = null;
                // 🌟 解析區域/價位關鍵字
                let rawKw = '{clean_area_keyword}';
                let kws = rawKw.split(',').map(k => k.trim().replace(/"/g, '').toLowerCase()).filter(k => k);
                for (let doc of docs) {{
                    // 抓取所有尚未被選走的座位
                    let rawSeats = Array.from(doc.querySelectorAll('div[name="tk"]:not(.s13):not(.son)'));
                    
                    // 🌟 如果有設定關鍵字，進行過濾
                    if (kws.length > 0) {{
                        rawSeats = rawSeats.filter(s => {{
                            // 將 title(如 1 Floor A Block) 與 grade(如 R석) 合併成一組字串比對
                            let seatInfo = (s.getAttribute('title') || "") + " " + (s.getAttribute('grade') || "");
                            seatInfo = seatInfo.toLowerCase();
                            
                            // 支援 GUI 邏輯：逗號為 OR，空格為 AND
                            return kws.some(group => {{
                                let andKws = group.split(' ').filter(k => k);
                                return andKws.every(ak => seatInfo.includes(ak));
                            }});
                        }});
                    }}
                    
                    if (rawSeats.length > 0) allAvailableSeats = allAvailableSeats.concat(rawSeats);
                    
                    let selected = Array.from(doc.querySelectorAll('div[name="tk"].son'));
                    actualSelectedCount += selected.length;
                    
                    if (!submitBtn) {{
                        let btn = doc.querySelector('a[href*="ChoiceEnd"], img.booking, img[src*="btn_booking2.gif"]');
                        if (btn) submitBtn = btn;
                    }}
                }}
                window._yes_seat_cache = window._yes_seat_cache || [];
                window._yes_seat_cache = window._yes_seat_cache.filter(c => (now - c.time) < 2000);
                window._banned_seats = window._banned_seats || [];
                window._banned_seats = window._banned_seats.filter(b => (now - b.time) < 10000);
                let safeSeats = allAvailableSeats.filter(s => 
                    !window._banned_seats.some(b => b.id === s.id) && 
                    !window._yes_seat_cache.some(c => c.id === s.id)
                );
                if (!window._clicked_count) window._clicked_count = 0;
                if (actualSelectedCount > window._clicked_count) {{
                    window._clicked_count = actualSelectedCount;
                }}
                if (window._clicked_count >= targetCount || actualSelectedCount >= targetCount) {{
                    if (submitBtn) {{
                        let btnEl = submitBtn.closest('a') || submitBtn;
                        if (window._last_submit && (now - window._last_submit < 2500)) {{
                            return "WAITING_SUBMIT_COOLDOWN";
                        }}
                        btnEl.click();
                        window._last_submit = now;
                        return "SUBMIT_CLICKED";
                    }}
                    return "WAITING_SUBMIT_BTN";
                }}
                if (safeSeats.length > 0) {{
                    if (window._last_seat_click && (now - window._last_seat_click < 150)) {{
                        return "WAITING_SEAT_COOLDOWN";
                    }}
                    
                    // 🌟 實裝 4 種排序模式邏輯 (修復字串誤判)
                    let targetIdx = 0;
                    let mode = "{self.area_mode}".toLowerCase();
                    
                    if (mode.includes("random") || mode.includes("隨機")) {{
                        // 1. 隨機選位
                        targetIdx = Math.floor(Math.random() * safeSeats.length);
                    }} else if (mode.includes("top to bottom") || mode.includes("由上至下") || mode === "top") {{
                        // 2. 由上至下 (優先攔截 top to bottom，避免被 bottom 誤判)
                        targetIdx = 0;
                    }} else if (mode.includes("bottom") || mode.includes("下")) {{
                        // 3. 由下至上 (最後一個元素)
                        targetIdx = safeSeats.length - 1;
                    }} else if (mode.includes("center") || mode.includes("中") || mode.includes("置中")) {{
                        // 4. 置中 (從中間開始拿)
                        targetIdx = Math.floor(safeSeats.length / 2);
                    }} else {{
                        // 預設為由上至下
                        targetIdx = 0;
                    }}
                    
                    let targetSeat = safeSeats[targetIdx];
                    window._last_seat_id = targetSeat.id; 
                    targetSeat.click();
                    
                    window._yes_seat_cache.push({{id: targetSeat.id, time: now}});
                    window._clicked_count++;
                    window._last_seat_click = now;
                    
                    let seatTitle = targetSeat.getAttribute('title') || targetSeat.id;
                    let seatGrade = targetSeat.getAttribute('grade') || "";
                    return "SEAT_CLICKED|" + seatTitle + " [" + seatGrade + "]|" + window._clicked_count + "/" + targetCount;
                }}
                return "NO_SEATS_LEFT";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        result = await active_tab.evaluate(js_seat)
        if isinstance(result, str):
            if result.startswith("ALERT|"):
                alert_msg = result.split('|')[1]
                print(f">>> [YES24-系統] 💥 攔截到視窗彈出: 【{alert_msg}】")
                print(">>> [YES24-選位] 🔄 該座位已被搶走！已將其加入 10 秒冷卻黑名單，並立即尋找新空位...")
                await asyncio.sleep(0.1)
            elif result.startswith("SEAT_CLICKED|"):
                parts = result.split("|")
                seat_title = parts[1]
                progress = parts[2]

                # 🌟 Python 端：同步修復 LOG 的 4 種排序模式判斷
                mode_lower = self.area_mode.lower() if self.area_mode else ""
                if "random" in mode_lower or "隨機" in mode_lower:
                    mode_zh = "隨機"
                elif "top to bottom" in mode_lower or "由上至下" in mode_lower or mode_lower == "top":
                    mode_zh = "由上至下"
                elif "bottom" in mode_lower or "下" in mode_lower:
                    mode_zh = "由下至上"
                elif "center" in mode_lower or "中" in mode_lower or "置中" in mode_lower:
                    mode_zh = "置中"
                else:
                    mode_zh = "由上至下"  # 預設顯示

                print(
                    f">>> [YES24-選位] 🪑 成功以【{mode_zh}】模式點擊 {progress} 張座位: 【{seat_title}】")
                await asyncio.sleep(0.1)
            elif result == "SUBMIT_CLICKED":
                print(
                    ">>> [YES24-選位] 🎯 已達標！成功點擊「Seat Selection Completed」送出按鈕！等待驗證...")
                await asyncio.sleep(0.5)
            elif result == "NO_SEATS_LEFT":
                if not hasattr(self, 'yes24_seat_log'):
                    self.yes24_seat_log = 0
                self.yes24_seat_log += 1
                if self.yes24_seat_log % 20 == 0:
                    kw_text = f" (條件: {self.area_keyword})" if self.area_keyword else ""
                    print(
                        f">>> [YES24-選位] ❌ 當前畫面查無符合條件的空位{kw_text}，持續掃描監控中...")
                await asyncio.sleep(0.05)
            elif result.startswith("ERROR|"):
                print(f">>> [DEBUG] Seat JS Error: {result}")

# ==========================================
# [yes24 搶票機器人]
# ==========================================


class TicketlinkBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.ticket_number = int(config.get("ticket_number", 1))

        # 讀取日期與區域(時間)的排序與關鍵字
        self.date_keyword = str(self.config.get(
            "date_auto_select", {}).get("date_keyword", "")).strip()
        self.date_mode = str(self.config.get(
            "date_auto_select", {}).get("mode", "top-down")).lower()

        self.last_url = ""
        self._bot_entered_time = time.time()

        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # 狀態鎖
        self.is_popup_opened = False
        self.popup_tab = None

        # ==============================================
        # 🛑 [已暫停] 初始化 OCR
        # ==============================================
        # try:
        #     import ddddocr
        #     self.custom_ocr = ddddocr.DdddOcr(show_ad=False)
        # except:
        #     pass

    async def run(self):
        print(
            f">>> [Ticketlink] 🚀 機器人啟動！(目標張數: {self.ticket_number} | 日期邏輯: {self.date_mode})")

        # 🔥 導入 nodriver 的 CDP Page 模組，用來執行跨頁面腳本注入
        import nodriver.cdp.page as cdp_page

        while True:
            try:
                # 1. 暫停攔截
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                # 2. 處理新視窗 (彈窗) 邏輯
                tab_count = len(self.driver.tabs)
                if tab_count > 1 and not self.is_popup_opened:
                    print(">>> [Ticketlink] 🪟 偵測到購票新視窗/彈窗！視角切換中...")
                    self.popup_tab = self.driver.tabs[-1]
                    self.is_popup_opened = True

                    # =========================================================
                    # 🕷️ 核心：為彈出視窗注入「網路攔截器」，無論怎麼跳轉都會持續側錄 JSON！
                    # =========================================================
                    interceptor_js = """
                    const originalFetch = window.fetch;
                    window.fetch = async function(...args) {
                        const response = await originalFetch.apply(this, args);
                        const clone = response.clone();
                        clone.json().then(data => {
                            if (data && data.data && data.data.able) {
                                window._tl_seat_data = data.data.able; // 將空位存入全域變數
                            }
                        }).catch(e => {});
                        return response;
                    };

                    const originalXHR = window.XMLHttpRequest.prototype.open;
                    window.XMLHttpRequest.prototype.open = function(method, url) {
                        this.addEventListener('load', function() {
                            try {
                                let data = JSON.parse(this.responseText);
                                if (data && data.data && data.data.able) {
                                    window._tl_seat_data = data.data.able;
                                }
                            } catch(e) {}
                        });
                        originalXHR.apply(this, arguments);
                    };
                    """
                    await self.popup_tab.send(cdp_page.add_script_to_evaluate_on_new_document(source=interceptor_js))
                    await asyncio.sleep(1.0)

                elif tab_count == 1 and self.is_popup_opened:
                    print(">>> [Ticketlink] ⚠️ 彈出視窗已關閉！已解鎖狀態...")
                    self.is_popup_opened = False
                    self.popup_tab = None

                active_tab = self.popup_tab if self.is_popup_opened else self.tab
                current_url = await active_tab.evaluate("window.location.href")

                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                if current_url != self.last_url:
                    print(f">>> [系統] 偵測到頁面切換: {current_url}")
                    self.last_url = current_url

                # 3. 任務分發
                await self.dispatch_action(current_url, active_tab)

            except Exception as e:
                pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, url, active_tab):
        """任務分發中心"""
        phase = await self.detect_phase(active_tab)

        if phase == "DATE_TIME_PHASE":
            await asyncio.sleep(0.5)

        elif phase == "CAPTCHA_PHASE":
            await asyncio.sleep(0.5)

        elif phase == "SEAT_PHASE":
            if not getattr(self, 'seat_phase_printed', False):
                print(">>> [Ticketlink] 🪑 成功進入座位圖階段！(程式已準備好接管座位掃描...)")
                self.seat_phase_printed = True

            # 🔥 就是少了這一行！現在補上了，程式才會開始掃描與點擊
            await self.select_seat(active_tab)

        else:
            await asyncio.sleep(0.1)

    async def detect_phase(self, active_tab):
        """特徵偵測：用 URL 加上 DOM 雙重保險"""
        js_phase = """
        (function() {
            try {
                let url = window.location.href;
                
                // 🔥 1. 最強判斷：只要網址有 schedule，100% 是選座位
                if (url.includes('/reserve/plan/schedule')) {
                    return "SEAT_PHASE";
                }

                // 2. 驗證碼階段
                let captchaImg = document.getElementById('captcha_img');
                if (captchaImg && window.getComputedStyle(captchaImg).display !== 'none') {
                    return "CAPTCHA_PHASE";
                }

                // 3. 日期選擇階段
                let datePicker = document.querySelector('.react-datepicker__day');
                if (datePicker) {
                    return "DATE_TIME_PHASE";
                }

                return "WAITING_DOM";
            } catch(e) { return "ERROR"; }
        })();
        """
        return await active_tab.evaluate(js_phase)

    async def select_date_and_time(self, active_tab):
        """[第一階段 - Ticketlink專用] 選擇日期、時間 (防2026年誤判 + 連續物理軌跡 + 半自動手動購票)"""
        import json
        import asyncio

        # 清除 GUI 輸入框可能自帶的雙引號與單引號
        keyword_list = []
        if self.date_keyword:
            cleaned_keyword = self.date_keyword.replace(
                '"', '').replace("'", "")
            keyword_list = [k.strip() for k in cleaned_keyword.split(',')]
        js_keywords = json.dumps(keyword_list, ensure_ascii=False)

        js_datetime = f"""
        (async function() {{
            try {{
                const keywords = {js_keywords};
                const mode = "{self.date_mode}";

                // 1. 抓取 Ticketlink 專屬日期 DOM
                let allDays = Array.from(document.querySelectorAll('.react-datepicker__day:not(.react-datepicker__day--disabled):not(.react-datepicker__day--outside-month)'));
                if (allDays.length === 0) return "WAITING_DATE_DOM";

                let validDates = [];
                if (keywords.length === 0 || keywords[0] === "") {{
                    validDates = allDays;
                }} else {{
                    for (let d of allDays) {{
                        let innerNum = (d.innerText || "").trim();
                        let ariaLabel = d.getAttribute('aria-label') || "";
                        let fullText = innerNum + " " + ariaLabel;
                        
                        let isMatch = keywords.some(k => {{
                            let kStr = k.toString().trim();
                            // 🔥 嚴格數字比對：如果是純數字，只比對格子裡的號碼，無視 "2026年" 的陷阱
                            if (/^\\d+$/.test(kStr)) {{
                                return parseInt(innerNum, 10) === parseInt(kStr, 10);
                            }}
                            return fullText.includes(kStr);
                        }});
                        
                        if (isMatch) validDates.push(d);
                    }}
                }}

                if (validDates.length === 0) return "NO_MATCH_DATE";

                let targetDate = validDates[0];
                if (mode.includes("random") || mode.includes("隨機")) {{
                    targetDate = validDates[Math.floor(Math.random() * validDates.length)];
                }} else if (mode.includes("bottom") || mode.includes("下")) {{
                    targetDate = validDates[validDates.length - 1];
                }} else if (mode.includes("center") || mode.includes("中")) {{
                    targetDate = validDates[Math.floor(validDates.length / 2)];
                }}

                // 無視預設選取狀態，強制進行物理點擊喚醒 AJAX
                let text = targetDate.innerText.trim();
                if (window._ticketlink_date_clicked !== text) {{
                    targetDate.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    await new Promise(r => setTimeout(r, 500)); 
                    
                    let rect = targetDate.getBoundingClientRect();
                    window._ticketlink_date_clicked = text;
                    window._ticketlink_time_clicked = null; 
                    return "NATIVE_CLICK_DATE|" + rect.x + "|" + rect.y + "|" + rect.width + "|" + rect.height + "|" + text;
                }}

                // 2. 抓取 Ticketlink 專屬時間 DOM
                let times = Array.from(document.querySelectorAll('.product_time'));
                if (times.length > 0) {{
                    let targetTime = times[0];
                    if (mode.includes("random") || mode.includes("隨機")) {{
                        targetTime = times[Math.floor(Math.random() * times.length)];
                    }} else if (mode.includes("bottom") || mode.includes("下")) {{
                        targetTime = times[times.length - 1];
                    }} else if (mode.includes("center") || mode.includes("中")) {{
                        targetTime = times[Math.floor(times.length / 2)];
                    }}

                    let timeText = targetTime.innerText.trim();
                    if (window._ticketlink_time_clicked !== timeText) {{
                        targetTime.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        await new Promise(r => setTimeout(r, 400));
                        
                        let rect = targetTime.getBoundingClientRect();
                        window._ticketlink_time_clicked = timeText;
                        return "NATIVE_CLICK_TIME|" + rect.x + "|" + rect.y + "|" + rect.width + "|" + rect.height + "|" + timeText;
                    }}
                }}

                // 3. 尋找「购票」按鈕並通知手動接管
                let buyBtns = Array.from(document.querySelectorAll('a.common_btn'));
                let targetBuyBtn = buyBtns.find(el => el.innerText.includes('购票') || el.innerText.includes('예매하기'));
                
                if (targetBuyBtn) {{
                    if (!window._manual_buy_notified) {{
                        targetBuyBtn.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        window._manual_buy_notified = true;
                        return "WAITING_MANUAL_BUY";
                    }}
                }}

                return "WAITING_NEXT_STEP";

            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_datetime)

            if isinstance(result, str):
                if result == "NO_MATCH_DATE":
                    if not hasattr(self, '_date_warn_log'):
                        self._date_warn_log = 0
                    self._date_warn_log += 1
                    if self._date_warn_log % 20 == 0:
                        print(
                            f">>> [日期] ⚠️ 找不到符合關鍵字 {self.date_keyword} 的可選日期！")

                elif result == "WAITING_MANUAL_BUY":
                    print("\n>>> [系統] 🛑 程式已極速選妥！請「手動」點擊購票按鈕與確認彈窗！")

                elif result.startswith("NATIVE_CLICK_DATE|") or result.startswith("NATIVE_CLICK_TIME|"):
                    parts = result.split("|")
                    action = parts[0]
                    x, y, w, h = float(parts[1]), float(
                        parts[2]), float(parts[3]), float(parts[4])

                    import random
                    import nodriver.cdp.input_ as cdp_input

                    def safe_enum(class_name, value):
                        if hasattr(cdp_input, class_name):
                            return getattr(cdp_input, class_name)(value)
                        return value

                    m_moved = safe_enum("DispatchMouseEventType", "mouseMoved")
                    m_pressed = safe_enum(
                        "DispatchMouseEventType", "mousePressed")
                    m_released = safe_enum(
                        "DispatchMouseEventType", "mouseReleased")
                    btn_left = safe_enum("MouseButton", "left")

                    target_x = x + (w / 2) + random.uniform(-w/4, w/4)
                    target_y = y + (h / 2) + random.uniform(-h/4, h/4)

                    if action == "NATIVE_CLICK_DATE":
                        print(
                            f">>> [日期] 📅 座標 ({target_x:.1f}, {target_y:.1f}) 啟動連續軌跡點擊: 【{parts[5]}】")
                    elif action == "NATIVE_CLICK_TIME":
                        print(
                            f">>> [時間] ⏰ 座標 ({target_x:.1f}, {target_y:.1f}) 啟動連續軌跡點擊: 【{parts[5]}】")

                    if not hasattr(self, 'current_mouse_x'):
                        self.current_mouse_x = random.uniform(300, 700)
                        self.current_mouse_y = random.uniform(200, 500)

                    start_x = self.current_mouse_x
                    start_y = self.current_mouse_y

                    steps = random.randint(15, 22)
                    for i in range(steps):
                        t = i / steps
                        ease_t = t * (2 - t)

                        cur_x = start_x + (target_x - start_x) * \
                            ease_t + random.uniform(-2, 2)
                        cur_y = start_y + (target_y - start_y) * \
                            ease_t + random.uniform(-2, 2)

                        await active_tab.send(cdp_input.dispatch_mouse_event(type_=m_moved, x=int(cur_x), y=int(cur_y)))
                        await asyncio.sleep(random.uniform(0.008, 0.015))

                    self.current_mouse_x = target_x
                    self.current_mouse_y = target_y

                    await asyncio.sleep(random.uniform(0.1, 0.2))
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_=m_pressed, x=int(target_x), y=int(target_y), button=btn_left, click_count=1))
                    await asyncio.sleep(random.uniform(0.05, 0.12))
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_=m_released, x=int(target_x), y=int(target_y), button=btn_left, click_count=1))
                    await asyncio.sleep(0.4)

        except Exception as e:
            print(f">>> [例外] 選擇日期時間錯誤: {e}")

    async def select_date_and_time(self, active_tab):
        """[第一階段] 優化版 - 日期時間選擇 (解決卡死、精準定位)"""
        import json
        import asyncio
        import random
        import nodriver.cdp.input_ as cdp_input

        # 處理關鍵字
        keyword_list = []
        if self.date_keyword:
            cleaned_keyword = self.date_keyword.replace(
                '"', '').replace("'", "")
            keyword_list = [k.strip() for k in cleaned_keyword.split(',')]
        js_keywords = json.dumps(keyword_list, ensure_ascii=False)

        js_datetime = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                const mode = "{self.date_mode}";

                // 1. ============ 處理日期 ============
                let allDays = Array.from(document.querySelectorAll('.react-datepicker__day:not(.react-datepicker__day--disabled):not(.react-datepicker__day--outside-month)'));
                if (allDays.length > 0) {{
                    let validDates = [];
                    if (keywords.length === 0 || keywords[0] === "") {{
                        validDates = allDays;
                    }} else {{
                        for (let d of allDays) {{
                            let innerNum = (d.innerText || "").trim();
                            let ariaLabel = d.getAttribute('aria-label') || "";
                            let fullText = innerNum + " " + ariaLabel;
                            
                            let isMatch = keywords.some(k => {{
                                let kStr = k.toString().trim();
                                // 純數字嚴格比對 (例如 "25")
                                if (/^\\d+$/.test(kStr)) {{
                                    return parseInt(innerNum, 10) === parseInt(kStr, 10);
                                }}
                                return fullText.includes(kStr);
                            }});
                            if (isMatch) validDates.push(d);
                        }}
                    }}

                    if (validDates.length === 0) return "NO_MATCH_DATE";

                    let targetDate = validDates[0];
                    if (mode.includes("random") || mode.includes("隨機")) targetDate = validDates[Math.floor(Math.random() * validDates.length)];
                    else if (mode.includes("bottom") || mode.includes("下")) targetDate = validDates[validDates.length - 1];
                    else if (mode.includes("center") || mode.includes("中")) targetDate = validDates[Math.floor(validDates.length / 2)];

                    // 🔥 重大修復1：判斷是否「已經被選取」，如果選好了就跳過點擊，直接進入選時間！
                    let isSelected = targetDate.classList.contains('react-datepicker__day--selected') || targetDate.getAttribute('aria-selected') === 'true';
                    let text = targetDate.innerText.trim();

                    if (!isSelected && window._ticketlink_date_clicked !== text) {{
                        // 🔥 重大修復2：使用 instant 取代 smooth，確保座標擷取絕對精準！
                        targetDate.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                        let rect = targetDate.getBoundingClientRect();
                        window._ticketlink_date_clicked = text;
                        window._ticketlink_time_clicked = null; // 重置時間
                        return "CLICK_DATE|" + rect.x + "|" + rect.y + "|" + rect.width + "|" + rect.height + "|" + text;
                    }}
                }}

                // 2. ============ 處理時間 ============
                let times = Array.from(document.querySelectorAll('.product_time'));
                if (times.length > 0) {{
                    let targetTime = times[0];
                    if (mode.includes("random") || mode.includes("隨機")) targetTime = times[Math.floor(Math.random() * times.length)];
                    else if (mode.includes("bottom") || mode.includes("下")) targetTime = times[times.length - 1];
                    else if (mode.includes("center") || mode.includes("中")) targetTime = times[Math.floor(times.length / 2)];

                    let isTimeSelected = targetTime.classList.contains('selected') || targetTime.getAttribute('aria-selected') === 'true'; // 視真實情況調整
                    let timeText = targetTime.innerText.trim();

                    if (!isTimeSelected && window._ticketlink_time_clicked !== timeText) {{
                        targetTime.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                        let rect = targetTime.getBoundingClientRect();
                        window._ticketlink_time_clicked = timeText;
                        return "CLICK_TIME|" + rect.x + "|" + rect.y + "|" + rect.width + "|" + rect.height + "|" + timeText;
                    }}
                }}

                // 3. ============ 處理購票按鈕 ============
                let buyBtns = Array.from(document.querySelectorAll('a.common_btn'));
                let targetBuyBtn = buyBtns.find(el => el.innerText.includes('购票') || el.innerText.includes('예매하기'));
                
                if (targetBuyBtn && !window._manual_buy_notified) {{
                    targetBuyBtn.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                    window._manual_buy_notified = true;
                    return "WAITING_MANUAL_BUY";
                }}

                return "WAITING_NEXT_STEP";
            }} catch(e) {{ 
                return "ERROR|" + e.toString(); 
            }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_datetime)

            if not isinstance(result, str) or result == "WAITING_NEXT_STEP" or result == "WAITING_DOM":
                return

            if result == "NO_MATCH_DATE":
                if not hasattr(self, '_date_warn_log'):
                    self._date_warn_log = 0
                self._date_warn_log += 1
                if self._date_warn_log % 20 == 0:
                    print(f">>> [日期] ⚠️ 找不到符合關鍵字 {self.date_keyword} 的可選日期！")

            elif result == "WAITING_MANUAL_BUY":
                print("\n>>> [系統] 🛑 程式已極速選妥日期時間！請「手動」點擊購票按鈕與確認彈窗！")

            elif result.startswith("CLICK_DATE|") or result.startswith("CLICK_TIME|"):
                parts = result.split("|")
                action = parts[0]
                x, y, w, h = float(parts[1]), float(
                    parts[2]), float(parts[3]), float(parts[4])
                text = parts[5]

                # 計算中心點，加一點微小隨機偏移防偵測
                target_x = x + (w / 2) + random.uniform(-w/4, w/4)
                target_y = y + (h / 2) + random.uniform(-h/4, h/4)

                if action == "CLICK_DATE":
                    print(f">>> [日期] 📅 點擊日期: 【{text}】")
                else:
                    print(f">>> [時間] ⏰ 點擊時間: 【{text}】")

                # ============ 簡化的物理點擊邏輯 ============
                def safe_enum(class_name, value):
                    return getattr(cdp_input, class_name)(value) if hasattr(cdp_input, class_name) else value

                m_moved = safe_enum("DispatchMouseEventType", "mouseMoved")
                m_pressed = safe_enum("DispatchMouseEventType", "mousePressed")
                m_released = safe_enum(
                    "DispatchMouseEventType", "mouseReleased")
                btn_left = safe_enum("MouseButton", "left")

                # 快速移動滑鼠 (減少迴圈次數，避免太慢被搶票)
                if not hasattr(self, 'current_mouse_x'):
                    self.current_mouse_x = random.uniform(300, 700)
                    self.current_mouse_y = random.uniform(200, 500)

                # 簡單兩步移動，快速抵達目標
                await active_tab.send(cdp_input.dispatch_mouse_event(
                    type_=m_moved, x=int((self.current_mouse_x + target_x)/2), y=int((self.current_mouse_y + target_y)/2)))
                await asyncio.sleep(0.02)
                await active_tab.send(cdp_input.dispatch_mouse_event(
                    type_=m_moved, x=int(target_x), y=int(target_y)))
                await asyncio.sleep(0.05)

                # 點擊
                await active_tab.send(cdp_input.dispatch_mouse_event(
                    type_=m_pressed, x=int(target_x), y=int(target_y), button=btn_left, click_count=1))
                await asyncio.sleep(random.uniform(0.03, 0.08))
                await active_tab.send(cdp_input.dispatch_mouse_event(
                    type_=m_released, x=int(target_x), y=int(target_y), button=btn_left, click_count=1))

                self.current_mouse_x, self.current_mouse_y = target_x, target_y

                # 點擊完等待一下讓 React 渲染新元件 (非常重要)
                await asyncio.sleep(0.3)

        except Exception as e:
            print(f">>> [例外] 選擇日期時間錯誤: {e}")

    async def solve_captcha_and_seat(self, active_tab):
        """[第二階段] 手動輸入驗證碼階段 (等待使用者完成)"""
        import asyncio

        # 使用一個簡單的計數器來印出提示，避免洗頻
        if not hasattr(self, '_captcha_warn_log'):
            self._captcha_warn_log = 0

        if self._captcha_warn_log % 25 == 0:
            print(">>> [驗證碼] 🛑 偵測到驗證碼！請「手動」輸入並送出，程式等待中...")

        self._captcha_warn_log += 1

        # 暫停一下，讓出資源等待使用者手動操作
        # 一旦你在畫面上輸入完成並送出，驗證碼區塊消失後，
        # detect_phase 就會自動將狀態切換到 SEAT_PHASE，接續之後的動作！
        await asyncio.sleep(0.1)

    async def select_seat(self, active_tab):
        """[第三階段] 支援手動與自動的 Canvas 點擊"""
        import json
        import asyncio
        import random
        import nodriver.cdp.input_ as cdp_input

        def safe_enum(class_name, value):
            return getattr(cdp_input, class_name)(value) if hasattr(cdp_input, class_name) else value

        m_moved = safe_enum("DispatchMouseEventType", "mouseMoved")
        m_pressed = safe_enum("DispatchMouseEventType", "mousePressed")
        m_released = safe_enum("DispatchMouseEventType", "mouseReleased")
        btn_left = safe_enum("MouseButton", "left")

        # =========================================================
        # 1. 優先檢查「下一步」按鈕 (支援你手動點位子)
        # =========================================================
        js_check_btn = """
        (function() {
            try {
                // 尋找下一步按鈕
                let nextBtn = document.querySelector("a.btn_next, a[ng-click='right.next()']");
                // 如果按鈕存在，且有 btn_next (亮起狀態)，且沒有 btn_prev (灰暗狀態)
                if (nextBtn && nextBtn.classList.contains("btn_next") && !nextBtn.classList.contains("btn_prev")) {
                    let btnRect = nextBtn.getBoundingClientRect();
                    return "CLICK_NEXT|" + btnRect.x + "|" + btnRect.y + "|" + btnRect.width + "|" + btnRect.height;
                }
                return "NOT_READY";
            } catch(e) { return "ERROR"; }
        })();
        """
        try:
            btn_result = await active_tab.evaluate(js_check_btn)
            if isinstance(btn_result, str) and btn_result.startswith("CLICK_NEXT|"):
                parts = btn_result.split("|")
                x, y, w, h = float(parts[1]), float(
                    parts[2]), float(parts[3]), float(parts[4])
                target_x = x + (w / 2) + random.uniform(-5, 5)
                target_y = y + (h / 2) + random.uniform(-5, 5)

                print(f">>> [座位] ✅ 「下一步」按鈕已亮起！發動點擊進入結帳...")
                await active_tab.send(cdp_input.dispatch_mouse_event(type_=m_moved, x=int(target_x), y=int(target_y)))
                await asyncio.sleep(0.02)
                await active_tab.send(cdp_input.dispatch_mouse_event(type_=m_pressed, x=int(target_x), y=int(target_y), button=btn_left, click_count=1))
                await asyncio.sleep(0.05)
                await active_tab.send(cdp_input.dispatch_mouse_event(type_=m_released, x=int(target_x), y=int(target_y), button=btn_left, click_count=1))

                self.is_seat_selected = True
                await asyncio.sleep(1.0)
                return  # 點完下一步就結束這一輪
        except Exception:
            pass

        # =========================================================
        # 2. 自動攔截 JSON 座標並點擊座位
        # =========================================================
        if not hasattr(self, 'target_coords') or not self.target_coords:
            # 呼叫我們在 run() 裡面注入的攔截器變數
            seat_data = await active_tab.evaluate("window._tl_seat_data;")

            if seat_data:
                self.target_coords = []
                for block_key, seats in seat_data.items():
                    for seat in seats:
                        if "position" in seat:
                            self.target_coords.append(seat["position"])

                print(f">>> [座位] 🎯 攔截成功！共取得 {len(self.target_coords)} 個空位座標！")
            else:
                if not hasattr(self, '_json_wait_log'):
                    self._json_wait_log = 0
                self._json_wait_log += 1
                if self._json_wait_log % 10 == 0:
                    print(">>> [座位] ⏳ 等待底層 JSON 座位資料載入中...")
                await asyncio.sleep(0.2)
                return

        if not self.target_coords:
            if not hasattr(self, '_no_seat_log'):
                self._no_seat_log = 0
            self._no_seat_log += 1
            if self._no_seat_log % 10 == 0:
                print(">>> [座位] ⚠️ 目前該區域沒有空位，請手動重整或切換區域...")
            await asyncio.sleep(0.5)
            return

        # 準備點擊張數
        coords_to_click = self.target_coords[:self.ticket_number]
        js_coords = json.dumps(coords_to_click)

        js_seat = f"""
        (function() {{
            try {{
                let mainView = document.getElementById("main_view");
                let canvas = document.getElementById("ez_canvas");
                if (!canvas && mainView) {{
                    let canvases = Array.from(mainView.querySelectorAll("canvas"));
                    canvas = canvases.find(c => c.style.zIndex === '5' && c.style.display === 'block') || canvases[canvases.length - 1];
                }}
                if (!canvas) return "NO_CANVAS";

                let targetCoords = {js_coords};
                let rect = canvas.getBoundingClientRect();
                let clickPoints = [];

                for (let i = 0; i < targetCoords.length; i++) {{
                    let clickX = rect.left + targetCoords[i].x;
                    let clickY = rect.top + targetCoords[i].y;
                    clickPoints.push({{x: clickX, y: clickY}});
                }}

                // 為了避免瘋狂連點同一個位子，讀取完就清空 JS 端變數，等待下一輪重抓
                window._tl_seat_data = null; 
                return "CLICK_CANVAS|" + JSON.stringify(clickPoints);

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_seat)
            if not isinstance(result, str):
                return

            if result.startswith("CLICK_CANVAS|"):
                points = json.loads(result.split("|")[1])
                print(f">>> [座位] 🪑 自動鎖定 {len(points)} 個座位，啟動光速點擊...")

                for p in points:
                    target_x, target_y = p["x"], p["y"]
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_=m_moved, x=int(target_x), y=int(target_y)))
                    await asyncio.sleep(0.01)
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_=m_pressed, x=int(target_x), y=int(target_y), button=btn_left, click_count=1))
                    await asyncio.sleep(random.uniform(0.02, 0.05))
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_=m_released, x=int(target_x), y=int(target_y), button=btn_left, click_count=1))

                    print(
                        f">>> [座位] 🟢 成功點擊座標 (X: {target_x:.1f}, Y: {target_y:.1f})")
                    await asyncio.sleep(0.1)

                # 清空 Python 端的座標快取，這樣下一輪迴圈才會去檢查「下一步按鈕是否亮起」
                self.target_coords = []

        except Exception as e:
            pass

# ==========================================
# [Ticketlink 搶票機器人]
# ==========================================


class TicketmasterBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.settings_path = config.get("config_filepath", "settings.json")
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態控制鎖
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_ticket_assigned = False
        self.captcha_error_event = asyncio.Event()
        self.captcha_error_flag = False

        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

#        print(">>> [Ticketmaster SG] 正在載入 ddddocr 辨識模型...")
#        try:
#            import ddddocr
#            self.ocr = ddddocr.DdddOcr(show_ad=False)
#        except Exception as e:
#            print(f">>> [系統] ddddocr 載入失敗: {e}")
#            self.ocr = None

        print(">>> [Ticketmaster SG] 正在載入 Dog_ocr 辨識模型...")
        try:
            # 替換為專案客製化的 Dog_ocr 模型
            import Dog_ocr
            self.ocr = Dog_ocr.Ocr()
        except Exception as e:
            print(f">>> [系統] Dog_ocr 載入失敗: {e}")
            self.ocr = None

    async def bind_dialog_handler(self):
        """綁定底層 CDP 攔截器，強制關閉任何卡死彈窗"""
        try:
            import nodriver.cdp.page as cdp_page

            async def dialog_handler(event: cdp_page.JavascriptDialogOpening):
                msg = getattr(event, "message", "")
                print(f"\n>>> [底層彈窗攔截] 網頁跳出提示: '{msg}'")
                await self.tab.send(cdp_page.handle_java_script_dialog(accept=True))

                lower_msg = msg.lower()
                if "code" in lower_msg or "verification" in lower_msg or "驗證碼" in lower_msg or "incorrect" in lower_msg or "error" in lower_msg:
                    self.is_ticket_assigned = False
                    # 【優化】0 延遲觸發事件，瞬間喚醒正在等待的 OCR 迴圈
                    self.captcha_error_event.set()
                    print(">>> [系統] ⚠️ 偵測到驗證碼錯誤，已自動解除鎖定，準備重新辨識...")

            self.tab.add_handler(
                cdp_page.JavascriptDialogOpening, dialog_handler)
            print(">>> [系統] ✅ 已啟用底層 CDP 彈窗防護機制")
        except Exception as e:
            print(f">>> [系統] ⚠️ 綁定 CDP 彈窗防護失敗: {e}")

    async def run(self):
        print(f">>> [Ticketmaster SG] 機器人啟動！(目標張數: {self.ticket_number})")
        await self.bind_dialog_handler()

        while True:
            try:
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                if current_url != getattr(self, 'last_url', ''):
                    self.last_url = current_url
                    lower_url = current_url.lower()

                    # 網址跳轉狀態重置
                    if '/activity/detail/' in lower_url:
                        self.is_date_selected = False
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                    elif '/ticket/area/' in lower_url:
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                    elif '/ticket/check-captcha/' in lower_url:
                        self.is_ticket_assigned = False

                await self.reload_settings(silent=True)
                await self.dispatch_action(current_url)
            except Exception as e:
                pass
            await asyncio.sleep(0.05)

    async def reload_settings(self, silent=False):
        try:
            if not os.path.exists(self.settings_path):
                return
            mtime = os.path.getmtime(self.settings_path)
            if getattr(self, 'last_settings_mtime', 0) == mtime:
                return
            self.last_settings_mtime = mtime

            with open(self.settings_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)

            for key in ["area_auto_select", "date_auto_select", "advanced", "keyword_exclude", "ticket_number"]:
                if key in new_config:
                    self.config[key] = new_config[key]
            self.ticket_number = int(new_config.get("ticket_number", 1))

            if not silent:
                print(f">>> [系統] Ticketmaster SG 設定已更新！")
        except Exception:
            pass

    async def dispatch_action(self, url):
        lower_url = url.lower()
        if '/activity/detail/' in lower_url:
            if not getattr(self, 'is_date_selected', False):
                await self.select_date()
        elif '/ticket/area/' in lower_url:
            if not getattr(self, 'is_area_selected', False):
                await self.select_area_and_qty()
        elif '/ticket/check-captcha/' in lower_url:
            if not getattr(self, 'is_ticket_assigned', False):
                await self.process_captcha_and_submit()

    async def select_date(self):
        """日期選擇：處理 '20 Nov 2026 (Fri.)' 轉換為 '11/20' 或 'fri' 匹配"""
        date_auto_select = self.config.get("date_auto_select", {})
        if not date_auto_select.get("enable", True):
            return

        raw_keyword = date_auto_select.get("date_keyword", "").strip()

        def parse_keywords(kw_str):
            if not kw_str:
                return [""]
            try:
                if kw_str.startswith("[") and kw_str.endswith("]"):
                    return json.loads(kw_str)
            except:
                pass
            return [x.strip() for x in kw_str.split(',') if x.strip()]

        js_keywords = json.dumps(parse_keywords(
            raw_keyword), ensure_ascii=False)
        js_mode = f"'{date_auto_select.get('mode', 'from top to bottom')}'"

        # 將轉換邏輯下放給 JS 執行 (減輕 IPC 負擔)
        js_script = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                const mode = {js_mode};
                
                // 月份轉換表
                const monthMap = {{'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}};
                
                let rows = Array.from(document.querySelectorAll('#gameList > table > tbody > tr'));
                let candidates = [];
                if (rows.length === 0) return "WAITING_DOM";
                
                for (let row of rows) {{
                    let dateTd = row.querySelector('td:nth-child(1)');
                    let btnTd = row.querySelector('td:last-child');
                    if (!dateTd || !btnTd) continue;
                    
                    let btn = btnTd.querySelector('a.btn-primary') || btnTd.querySelector('button');
                    // 如果還是倒數計時狀態 (無按鈕) 則跳過
                    if (!btn || btnTd.querySelector('.event-unavailable')) continue;
                    
                    let dateText = dateTd.innerText.trim();
                    let formattedDate = "";
                    let weekday = "";
                    
                    // 解析 "20 Nov 2026 (Fri.)"
                    let match = dateText.match(/(\\d+)\\s+([A-Za-z]+)\\s+\\d+\\s+\\(([A-Za-z]+)\\.\\)/);
                    if (match) {{
                        let d = parseInt(match[1]);
                        let m = monthMap[match[2]] || 0;
                        weekday = match[3].toLowerCase();
                        formattedDate = m + "/" + d; // e.g., "11/20"
                    }}
                    
                    let searchStr = (dateText + " " + formattedDate + " " + weekday).toUpperCase();
                    
                    let isMatch = false;
                    if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{ 
                        isMatch = true; 
                    }} else {{
                        for (let k of keywords) {{
                            let target_kws = k.trim().split(/\\s+/).filter(w => w.length > 0);
                            let currentGroupMatch = true;
                            for (let w of target_kws) {{ 
                                if (!searchStr.includes(w.toUpperCase())) {{ currentGroupMatch = false; break; }} 
                            }}
                            if (currentGroupMatch) {{ isMatch = true; break; }}
                        }}
                    }}
                    
                    if (isMatch) candidates.push(btn);
                }}
                
                if (candidates.length === 0) return "RELOAD";
                
                if (mode === "from bottom to top") {{ candidates.reverse(); }} 
                else if (mode === "random") {{
                    for (let i = candidates.length - 1; i > 0; i--) {{
                        const j = Math.floor(Math.random() * (i + 1));
                        [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
                    }}
                }}
                
                let targetBtn = candidates[0];
                let href = targetBtn.getAttribute('data-href') || targetBtn.getAttribute('href');
                if (href) {{ window.location.href = href; }} else {{ targetBtn.click(); }}
                return "SUCCESS";
                
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        try:
            result = await self.tab.evaluate(js_script)
            if result == "SUCCESS":
                print(">>> [Ticketmaster SG-日期] 🎉 成功鎖定日期！發動跳轉...")
                self.is_date_selected = True
                await asyncio.sleep(0.5)
            elif result == "RELOAD":
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                print(">>> [Ticketmaster SG-日期] 找不到符合或已開賣場次，準備刷新...")
                await self.tab.reload()
                await asyncio.sleep(base_wait if base_wait > 0 else 0.2)
            elif result == "WAITING_DOM":
                await asyncio.sleep(0.1)
        except:
            pass

    async def select_area_and_qty(self):
        """SVG 區域選擇與張數設定：兩階段 JS 處理 (進階防呆版 + 支援票價搜尋 + 自動處理同意彈窗)"""

        area_auto_select = getattr(
            self, 'config', {}).get("area_auto_select", {})
        if not area_auto_select.get("enable", True):
            return

        raw_keyword = area_auto_select.get("area_keyword", "").strip()
        raw_keyword_exclude = self.config.get(
            "keyword_exclude", "") or area_auto_select.get("area_keyword_exclude", "")

        def parse_keywords(kw_str):
            if not kw_str:
                return [""]
            kw_str = kw_str.replace("，", ",")
            cleaned = re.sub(r'[\'"”“‘’]', '', kw_str)
            return [x.strip() for x in cleaned.split(',') if x.strip()]

        js_keywords = json.dumps(parse_keywords(
            raw_keyword), ensure_ascii=False)
        js_excludes = json.dumps(parse_keywords(
            str(raw_keyword_exclude).strip()), ensure_ascii=False)
        js_mode = f"'{area_auto_select.get('mode', 'from top to bottom')}'"
        ticket_number = self.ticket_number

        js_script = f"""
        (function() {{
            try {{
                // ==========================================
                // 【新增】階段 0：秒殺 IMPORTANT NOTICE 彈窗
                // ==========================================
                let noticePopup = document.querySelector('.mfp-outerbox');
                let noticeCheckbox = document.querySelector('.mfp-outerbox input.chBx[type="checkbox"]');
                let noticeSubmit = document.querySelector('.mfp-outerbox button.submitok');
                
                // 如果偵測到彈窗存在且可見
                if (noticePopup && noticeCheckbox && noticeSubmit) {{
                    // 確保可見性 (有些系統會用 display:none 隱藏而非移除 DOM)
                    if (noticePopup.closest('.mfp-wrap') && window.getComputedStyle(noticePopup.closest('.mfp-wrap')).display !== 'none') {{
                        if (!noticeCheckbox.checked) {{
                            noticeCheckbox.click();
                        }}
                        noticeSubmit.click();
                        return "NOTICE_HANDLED"; // 處理完畢，讓 Python 稍微喘息一下等待動畫結束
                    }}
                }}

                // 階段 1：檢查票價選單是否出現
                let selectEl = document.querySelector('select[name^="TicketForm[ticketPrice]"]');
                let autoModeBtn = document.querySelector('#autoMode');
                
                if (selectEl && autoModeBtn && !selectEl.disabled) {{
                    let hasOption = Array.from(selectEl.options).some(opt => parseInt(opt.value) >= {ticket_number});
                    if (hasOption) {{
                        selectEl.value = {ticket_number};
                        selectEl.dispatchEvent(new Event('change', {{bubbles: true}}));
                        autoModeBtn.click();
                        return "READY";
                    }} else {{
                        return "RELOAD|NO_ENOUGH_TICKETS";
                    }}
                }}

                // 階段 2：地圖點擊
                if (typeof window.zone === 'undefined') return "WAITING_DOM";
                
                const keywords = {js_keywords};
                const excludes = {js_excludes};
                const mode = {js_mode};
                let candidates = [];
                let availableButExcluded = []; 
                
                for (let key in window.zone) {{
                    let zInfo = window.zone[key];
                    if (zInfo.areaStatus === "UNAVAILABLE") continue;
                    
                    let priceStr = "";
                    if (zInfo.price && zInfo.price.length > 0) {{
                        priceStr = zInfo.price.map(p => p.ticketPrice + " " + p.ticketPriceText).join(" ");
                    }}
                    
                    let text = (zInfo.description + " " + zInfo.groupName + " " + priceStr).toUpperCase();
                    
                    let isExcluded = false;
                    if (excludes.length > 0 && excludes[0] !== "") {{
                        for (let exc of excludes) {{ 
                            if (exc.trim().length > 0 && text.includes(exc.trim().toUpperCase())) {{ 
                                isExcluded = true; break; 
                            }} 
                        }}
                    }}
                    
                    if (isExcluded) {{
                        availableButExcluded.push(zInfo.description);
                        continue;
                    }}
                    
                    let isMatch = false;
                    if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{ 
                        isMatch = true; 
                    }} else {{
                        for (let k of keywords) {{
                            let target_kws = k.trim().split(/\\s+/).filter(w => w.length > 0);
                            let currentGroupMatch = true;
                            for (let w of target_kws) {{ 
                                if (!text.includes(w.toUpperCase())) {{ currentGroupMatch = false; break; }} 
                            }}
                            if (currentGroupMatch) {{ isMatch = true; break; }}
                        }}
                    }}
                    
                    if (isMatch) candidates.push(key);
                }}
                
                if (candidates.length === 0) {{
                    let availStr = availableButExcluded.length > 0 ? "有票但被過濾擋下:" + Array.from(new Set(availableButExcluded)).join(",") : "無符合區域";
                    return "RELOAD|" + availStr;
                }}
                
                if (mode === "from bottom to top") {{ candidates.reverse(); }} 
                else if (mode === "random") {{
                    for (let i = candidates.length - 1; i > 0; i--) {{
                        const j = Math.floor(Math.random() * (i + 1));
                        [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
                    }}
                }}
                
                let targetId = candidates[0];
                let gElement = document.getElementById(targetId);
                
                if (gElement) {{
                    let ev = new MouseEvent('click', {{bubbles:true, view:window}});
                    gElement.dispatchEvent(ev);
                    return "MAP_CLICKED";
                }}
                
                return "WAITING_DOM";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_script)

            if result == "NOTICE_HANDLED":
                print(
                    ">>> [Ticketmaster SG-區域] ⚡ 偵測到 IMPORTANT NOTICE 彈窗，已自動打勾並送出！")
                await asyncio.sleep(0.2)  # 給彈窗消失的動畫與後端載入票價一點點時間
            elif result == "MAP_CLICKED":
                print(">>> [Ticketmaster SG-區域] 🎯 已點擊目標地圖區域，等待票價表單載入...")
                await asyncio.sleep(0.3)
            elif result == "READY":
                print(
                    f">>> [Ticketmaster SG-票數] 🎉 成功鎖定票種，調整為 {ticket_number} 張並送出！")
                self.is_area_selected = True
                await asyncio.sleep(0.5)
            elif str(result).startswith("RELOAD"):
                debug_msg = result.split("|")[1] if "|" in result else ""
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))

                if "被過濾擋下" in debug_msg:
                    print(
                        f">>> [Ticketmaster SG-區域] ⚠️ 注意：{debug_msg} (請檢查您的「排除關鍵字」是否設定了 Restricted View 等字眼)")
                else:
                    print(">>> [Ticketmaster SG-區域] 🔄 目標區域已售完或無足夠張數，自動刷新排隊中...")

                await self.tab.reload()
                await asyncio.sleep(base_wait if base_wait > 0 else 0.2)
            elif result == "WAITING_DOM":
                await asyncio.sleep(0.1)
        except Exception as e:
            pass

    async def process_captcha_and_submit(self):
        """擷取驗證碼圖片、辨識、填入並送出 (極速多執行緒版)"""
        print(">>> [OCR] 開始處理 Ticketmaster 圖形驗證碼...")

        js_get_image = """
        (function() {
            var img = document.querySelector('#TicketForm_verifyCode-image');
            if (!img) return null;
            if (!img.complete || img.naturalWidth === 0) return "NOT_LOADED";
            
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """

        js_force_refresh = """
        (function() {
            let img = document.querySelector('#TicketForm_verifyCode-image');
            if (img) {
                let ev = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
                img.dispatchEvent(ev);
                img.click(); 
            }
            let inp = document.querySelector('#TicketForm_verifyCode');
            if (inp) inp.value = '';
        })();
        """

        try:

            attempt = 0

            while True:
                attempt += 1

                # 【優化】直接讀取 tab.url，省去 JS 執行的 IPC 延遲
                current_url = self.tab.url
                if not current_url or '/ticket/check-captcha/' not in current_url.lower():
                    return True

                # 遇到錯誤標記，強制點擊圖片換一張
                if self.captcha_error_event.is_set():
                    print(">>> [OCR] 🔄 執行刷新驗證碼圖片...")
                    await self.tab.evaluate(js_force_refresh)
                    self.captcha_error_event.clear()
                    await asyncio.sleep(1.0)  # 給新圖片載入時間

                base64_data = await self.tab.evaluate(js_get_image)
                if not base64_data or base64_data == "NOT_LOADED":
                    await asyncio.sleep(0.1)  # 降低等待時間，加快輪詢速度
                    continue

                img_bytes = base64.b64decode(base64_data)

                if self.ocr:
                    # 【極速優化】將 CPU 運算丟給背景 Thread，確保 CDP 事件不卡頓
                    ocr_answer = await asyncio.to_thread(self.ocr.predict, img_bytes)
                    ocr_answer = ocr_answer.strip() if ocr_answer else ""
                else:
                    return False

                print(f">>> [OCR] 第 {attempt} 次辨識結果: '{ocr_answer}'")

                if len(ocr_answer) == 4:
                    js_fill_and_submit = f"""
                    (function() {{
                        var input = document.querySelector('#TicketForm_verifyCode');
                        var agree = document.querySelector('#TicketForm_agree');
                        var submitBtn = document.querySelector('#captchaBox button[type="submit"]');
                        
                        if (input && agree && submitBtn) {{
                            input.value = '{ocr_answer}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            if (!agree.checked) {{ agree.click(); }}
                            submitBtn.click();
                            return true;
                        }}
                        return false;
                    }})();
                    """

                    self.captcha_error_event.clear()  # 送出前確保鎖被清空

                    if await self.tab.evaluate(js_fill_and_submit):
                        print(
                            f">>> [OCR] ✅ 已自動填寫 {ocr_answer} 勾選同意並送出！等待系統判定...")
                        self.is_ticket_assigned = True

                        try:
                            # 【極速優化】等待事件觸發，最多等 2.5 秒。只要彈窗一出，瞬間解除等待！
                            await asyncio.wait_for(self.captcha_error_event.wait(), timeout=2.5)
                            # 如果等到了 Event 被 set，代表出錯了，直接進入下一輪迴圈
                            continue
                        except asyncio.TimeoutError:
                            # 2.5秒內都沒跳錯誤彈窗，代表順利進入結帳頁了！
                            return True
                else:
                    print(">>> [OCR] ⚠️ 辨識結果非4碼，判定為不準確，強制換圖...")
                    await self.tab.evaluate(js_force_refresh)
                    await asyncio.sleep(0.5)

        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False


# ==========================================
# [Ticketmaster 搶票機器人]
# ==========================================


async def main(args):
    print("main: 程式開始")

    config_dict = get_config_dict(args)
    if config_dict is None:
        print("Load config error! 請檢查 settings.json")
        return
    config_dict["token"] = util.get_token()

    driver = None
    tab = None
    browser_stopped = False

    # 1. 修正邏輯順序的 safe_stop_browser()
    async def safe_stop_browser():
        nonlocal driver, tab, browser_stopped

        if browser_stopped:
            return

        if driver is None:
            tab = None
            browser_stopped = True
            return

        print(">>> [系統] 正在安全關閉瀏覽器連線...")
        current_driver = driver

        try:
            result = current_driver.stop()
            if inspect.isawaitable(result):
                await result
            print(">>> [系統] 瀏覽器已正常關閉清理完畢。")
        except Exception as e:
            print(f">>> [系統] 關閉瀏覽器時發生例外: {repr(e)}")
        finally:
            driver = None
            tab = None
            browser_stopped = True

    try:
        print("正在啟動瀏覽器...")
        try:
            conf = get_extension_config(config_dict)
            nodriver_overwrite_prefs(conf)
            driver = await uc.start(conf)
            if driver is None:
                raise RuntimeError("nodriver.start() 回傳 None")
        except Exception as e:
            print(f"瀏覽器啟動失敗: {repr(e)}")
            if driver is not None:
                await safe_stop_browser()
            return

        try:
            tab = driver.main_tab
            if tab is None:
                raise RuntimeError("driver.main_tab 回傳 None")
        except Exception as e:
            print(f">>> [系統] 無法取得主分頁: {repr(e)}")
            return

        print("正在注入強力版 Shadow DOM 解鎖腳本...")
        shadow_unlock_script = """
        (function() {
            'use strict';
            if (Element.prototype._originalAttachShadow) return;
            console.log("🔥 [Bot] Shadow DOM Unlocker injected!");
            Element.prototype._originalAttachShadow = Element.prototype.attachShadow;
            Element.prototype.attachShadow = function (params) {
                let newParams = params || {};
                newParams.mode = "open";
                return this._originalAttachShadow(newParams);
            };
        })();
        """
        try:
            await tab.send(cdp.page.enable())
            await tab.send(cdp.page.add_script_to_evaluate_on_new_document(source=shadow_unlock_script))
            print(">>> Shadow DOM 解鎖腳本注入成功")
        except Exception as e:
            print(f"Shadow DOM 腳本注入失敗: {repr(e)}")

        tab = await nodriver_goto_homepage(driver, tab, config_dict)
        tab = await nodrver_block_urls(tab, config_dict)
        if not config_dict["advanced"]["headless"]:
            await nodriver_resize_window(driver, config_dict)

        url = ""
        last_url = ""
        is_quit_bot = False
        is_refresh_datetime_sent = False

        print(">>> [系統] 總路由迴圈啟動，監聽網址中...")

        while True:
            await asyncio.sleep(0.05)

            if driver is None:
                print(">>> [系統] driver 已不存在，離開主迴圈")
                break

            if not is_quit_bot:
                try:
                    url, is_quit_bot, reset_act_tab = await nodriver_current_url(driver, tab)
                    if reset_act_tab is not None:
                        tab = reset_act_tab
                except Exception as e:
                    print(f">>> [nodriver_current_url 錯誤]: {repr(e)}")
                    is_quit_bot = True

            if is_quit_bot:
                print(">>> [系統] 偵測到使用者關閉瀏覽器或斷線，準備安全退出...")
                break

            if not url:
                continue

            if not is_refresh_datetime_sent:
                try:
                    is_refresh_datetime_sent = await check_refresh_datetime_occur(driver, config_dict["refresh_datetime"])
                except Exception:
                    pass

            is_maxbot_paused = False
            if os.path.exists(CONST_MAXBOT_INT28_FILE):
                is_maxbot_paused = True
            try:
                sync_status_to_extension(not is_maxbot_paused)
            except Exception:
                pass

            if url != last_url:
                print(f"目前網址: {url}")
                try:
                    write_last_url_to_file(url)
                except:
                    pass
                if is_maxbot_paused:
                    print("MAXBOT Paused.")
                last_url = url

            try:
                await sendkey_to_browser(driver, config_dict, url)
                await eval_to_browser(driver, config_dict, url)
            except Exception:
                pass

            # ==========================================
            # Router 分發區
            # ==========================================
            if 'tix.fubonbraves.com' in url:
                print(">>> [路由] 偵測到「富邦勇士」，轉交控制權給 FubonBot...")
                try:
                    fubon_bot = FubonBot(driver, config_dict)
                    await fubon_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] FubonBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'ticket.com.tw' in url:
                print(">>> [路由] 偵測到「年代售票」，轉交控制權給 EraBot...")
                try:
                    era_bot = EraBot(driver, config_dict)
                    await era_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] EraBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'ticketplus.com.tw' in url:
                print(">>> [路由] 偵測到「遠大售票」，轉交控制權給 TicketPlusBot...")
                try:
                    ticketplus_bot = TicketPlusBot(driver, config_dict)
                    await ticketplus_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] TicketPlusBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'kktix.com' in url:
                print(">>> [路由] 偵測到「KKTIX售票」，轉交控制權給 KKTIXBot...")
                try:
                    KKTIX_Bot = KKTIXBot(driver, config_dict)
                    await KKTIX_Bot.run()
                except Exception as e:
                    print(f">>> [錯誤] KKTIXBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'kham.com.tw' in url:
                is_variant_mode = config_dict.get("advanced", {}).get(
                    "variant_ticket_enable", False)
                if is_variant_mode:
                    print(
                        ">>> [路由] 偵測到「寬宏售票」且已啟用【變種搶票 (API模式)】，轉交控制權給 KhamBot_API...")
                    try:
                        kham_bot = KhamBot_API(driver, config_dict)
                        await kham_bot.run()
                    except asyncio.CancelledError:
                        print(">>> [KhamBot_API] asyncio task 被取消")
                        raise
                    except Exception as e:
                        print(f">>> [錯誤] KhamBot_API 發生例外: {repr(e)}")
                        traceback.print_exc()
                        await asyncio.sleep(1)
                else:
                    print(">>> [路由] 偵測到「寬宏售票」【一般網頁模式】，轉交控制權給 KhamBot...")
                    try:
                        kham_bot = KhamBot(driver, config_dict)
                        await kham_bot.run()
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        print(f">>> [錯誤] KhamBot 發生例外: {repr(e)}")
                        traceback.print_exc()
                        await asyncio.sleep(1)

            elif 'melon.com' in url:
                print(">>> [路由] 偵測到「Melon Ticket」，轉交控制權給 MelonBot...")
                try:
                    if not 'melon_bot' in locals():
                        melon_bot = MelonBot(driver, config_dict)
                    await melon_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] MelonBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'billboardlivetaipei.tw' in url:
                print(
                    ">>> [路由] 偵測到「Billboard Live Taipei」，轉交控制權給 BillboardLiveBot...")
                try:
                    if not 'billboard_bot' in locals():
                        billboard_bot = BillboardLiveBot(driver, config_dict)
                    await billboard_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] BillboardLiveBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'tsghawks.com' in url:
                print(">>> [路由] 偵測到「台鋼雄鷹售票網」，轉交控制權給 TsgHawksBot...")
                try:
                    tsghawks_bot = TsgHawksBot(driver, config_dict)
                    await tsghawks_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] TsgHawksBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'nol.com' in url or 'interpark.com' in url:
                print(">>> [路由] 偵測到「NOL (公園)售票」...")
                try:
                    is_auto_mode = config_dict.get(
                        "advanced", {}).get("telegram_enable", False)
                    if is_auto_mode:
                        nol_bot = NolBot_AUTO(driver, config_dict)
                    else:
                        nol_bot = NolBot(driver, config_dict)
                    await nol_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] NOL 機器人崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'guardians.fami.life' in url:
                print(">>> [路由] 偵測到「富邦悍將售票網」，轉交控制權給 FubonBot...")
                try:
                    fubon_bot = FubonBot(driver, config_dict)
                    await fubon_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] FubonBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'funone.io' in url:
                print(">>> [路由] 偵測到「FunOne 售票」，轉交控制權給 FunoneBot...")
                try:
                    funone_bot = FunoneBot(driver, config_dict)
                    await funone_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] FunoneBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'indievox.com' in url:
                print(">>> [路由] 偵測到「獨立音樂網 (Indievox) 售票」，轉交控制權給 IndievoxBot...")
                try:
                    if not 'indievox_bot' in locals():
                        indievox_bot = IndievoxBot(driver, config_dict)
                    await indievox_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] IndievoxBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'klook.com' in url:
                print(">>> [路由] 偵測到「Klook 客路活動網頁」，轉交控制權給 KlookBOT...")
                try:
                    if not 'klook_bot' in locals():
                        klook_bot = KlookBOT(driver, config_dict)
                    await klook_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] KlookBOT 發生異常: {repr(e)}")
                    await asyncio.sleep(1)

            elif 'ticket.yes24.com' in url:
                print(">>> [路由] 偵測到「YES24 售票網頁」，轉交控制權給 yes24Bot...")
                try:
                    if not 'yes24_bot' in locals():
                        yes24_bot = yes24Bot(driver, config_dict)
                    await yes24_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] yes24Bot 發生異常: {repr(e)}")
                    await asyncio.sleep(1)

            elif 'ticketlink.co.kr' in url:
                print(">>> [路由] 偵測到「Ticketlink 售票」，轉交控制權給 TicketlinkBot...")
                try:
                    ticketlink_bot = TicketlinkBot(driver, config_dict)
                    await ticketlink_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] TicketlinkBot 崩潰: {repr(e)}")
                    await asyncio.sleep(2)

            elif 'ticketmaster.sg' in url:
                print(">>> [路由] 偵測到「Ticketmaster SG」，轉交控制權給 TicketmasterBot...")
                try:
                    if not 'ticketmaster_bot' in locals():
                        ticketmaster_bot = TicketmasterBot(driver, config_dict)
                    await ticketmaster_bot.run()
                except Exception as e:
                    print(f">>> [錯誤] TicketmasterBot 崩潰: {repr(e)}")
                    traceback.print_exc()
                    await asyncio.sleep(2)

            elif 'ticket.ibon.com.tw' in url:
                print(">>> [路由] 偵測到「ibon 售票系統」，轉交控制權給 ibon 機器人...")
                try:
                    # 檢查區域變數中是否已經實例化過，若沒有則建立新的 ibon 物件
                    if not 'ibon_bot' in locals():
                        ibon_bot = ibon(driver, config_dict)

                    # 啟動並等待 ibon 機器人的 run() 迴圈
                    await ibon_bot.run()

                except Exception as e:
                    print(f">>> [錯誤] ibon 機器人崩潰: {repr(e)}")
                    # 印出完整的錯誤追蹤訊息，方便後續除錯
                    import traceback
                    traceback.print_exc()

                    # 崩潰後休眠 2 秒，避免死迴圈狂刷錯誤
                    await asyncio.sleep(2)

    except asyncio.CancelledError:
        print(">>> [系統] 接收到中斷訊號 (Task Cancelled)，開始安全關閉瀏覽器...")
        raise
    except KeyboardInterrupt:
        print(">>> [系統] 接收到手動終止指令 (KeyboardInterrupt)，開始安全關閉瀏覽器...")
    except Exception as e:
        print(f">>> [系統] 發生未捕捉的嚴重例外: {repr(e)}")
        traceback.print_exc()
    finally:
        print(">>> [系統] 進入安全退出流程，正在徹底清理 Browser 資源...")
        await safe_stop_browser()
        print(">>> [系統] 機器人程式結束。")


async def nodriver_goto_homepage(driver, tab, config_dict):
    print("nodriver_goto_homepage")
    homepage = config_dict["homepage"]

    # 移除原本內部的 tab = None，改用傳進來的 tab
    # tab = None

    if 'kktix.c' in homepage:
        try:
            # [修改] 改用 tab.get，確保在同一個分頁操作
            await tab.get(homepage)
            await tab.sleep(5)  # 改用 tab.sleep (雖然 driver.sleep 也可以)
        except Exception as e:
            pass

        if len(config_dict["advanced"]["kktix_account"]) > 0:
            if not 'https://kktix.com/users/sign_in?' in homepage:
                homepage = CONST_KKTIX_SIGN_IN_URL % (homepage)

    if 'famiticket.com' in homepage:
        if len(config_dict["advanced"]["fami_account"]) > 0:
            homepage = CONST_FAMI_SIGN_IN_URL

    if 'kham.com' in homepage:
        if len(config_dict["advanced"]["kham_account"]) > 0:
            homepage = CONST_KHAM_SIGN_IN_URL

    if 'ticket.com.tw' in homepage:
        if len(config_dict["advanced"]["ticket_account"]) > 0:
            homepage = CONST_TICKET_SIGN_IN_URL

    try:
        # [修改] 核心關鍵：確保使用已注入腳本的 tab 進行導航
        await tab.get(homepage)
        # await driver.sleep(5)
        await asyncio.sleep(5)  # 建議改用標準 sleep 避免混淆
    except Exception as e:
        pass

    # ... (中間處理 tixcraft cookie 的部分保持不變) ...
    # 略過中間代碼...

    # 處理 ibon cookie
    if 'ibon.com' in homepage:
        # ... (Cookie 設定保持不變) ...
        pass

        if 'https://ticket.ibon.com.tw/ActivityInfo/Details/' in homepage:
            time.sleep(3)
            try:
                # [修改] 只刷新當前 tab 即可
                await tab.reload()
            except Exception as exc:
                print(exc)
                pass

    return tab


async def nodrver_block_urls(tab, config_dict):
    print("nodrver_block_urls")

    NETWORK_BLOCKED_URLS = []

    if config_dict["advanced"]["adblock"]:
        NETWORK_BLOCKED_URLS = [
            '*.clarity.ms/*',
            '*.doubleclick.net/*',
            '*.lndata.com/*',
            '*.rollbar.com/*',
            '*.twitter.com/i/*',
            '*/adblock.js',
            '*/google_ad_block.js',
            '*anymind360.com/*',
            '*cdn.cookielaw.org/*',
            '*e2elog.fetnet.net*',
            '*fundingchoicesmessages.google.com/*',
            '*google-analytics.*',
            '*googlesyndication.*',
            '*googletagmanager.*',
            '*googletagservices.*',
            '*img.uniicreative.com/*',
            '*platform.twitter.com/*',
            '*play.google.com/*',
            '*player.youku.*',
            '*syndication.twitter.com/*',
            '*youtube.com/*',
        ]

    if config_dict["advanced"]["hide_some_image"]:
        NETWORK_BLOCKED_URLS.append('*.woff')
        NETWORK_BLOCKED_URLS.append('*.woff2')
        NETWORK_BLOCKED_URLS.append('*.ttf')
        NETWORK_BLOCKED_URLS.append('*.otf')
        NETWORK_BLOCKED_URLS.append('*fonts.googleapis.com/earlyaccess/*')
        NETWORK_BLOCKED_URLS.append('*/ajax/libs/font-awesome/*')
        NETWORK_BLOCKED_URLS.append('*.ico')
        NETWORK_BLOCKED_URLS.append(
            '*ticketimg2.azureedge.net/image/ActivityImage/*')
        NETWORK_BLOCKED_URLS.append('*static.tixcraft.com/images/activity/*')
        NETWORK_BLOCKED_URLS.append(
            '*static.ticketmaster.sg/images/activity/*')
        NETWORK_BLOCKED_URLS.append(
            '*static.ticketmaster.com/images/activity/*')
        NETWORK_BLOCKED_URLS.append(
            '*ticketimg2.azureedge.net/image/ActivityImage/ActivityImage_*')
        NETWORK_BLOCKED_URLS.append('*.azureedge.net/QWARE_TICKET//images/*')
        NETWORK_BLOCKED_URLS.append('*static.ticketplus.com.tw/event/*')

        # NETWORK_BLOCKED_URLS.append('https://kktix.cc/change_locale?locale=*')
        NETWORK_BLOCKED_URLS.append('https://t.kfs.io/assets/logo_*.png')
        NETWORK_BLOCKED_URLS.append('https://t.kfs.io/assets/icon-*.png')
        NETWORK_BLOCKED_URLS.append('https://t.kfs.io/upload_images/*.jpg')

    if config_dict["advanced"]["block_facebook_network"]:
        NETWORK_BLOCKED_URLS.append('*facebook.com/*')
        NETWORK_BLOCKED_URLS.append('*.fbcdn.net/*')

    # --- [修正重點開始] ---
    try:
        await tab.send(cdp.network.enable())
        # 新版 nodriver v0.48+ 不支援直接傳字串清單，這行會導致崩潰
        # 我們將其註解掉，跳過阻擋功能以確保程式能跑
        # await tab.send(cdp.network.set_blocked_ur_ls(NETWORK_BLOCKED_URLS))
        print("已跳過廣告阻擋功能 (避免版本衝突閃退)")
    except Exception as e:
        print(f"阻擋網址設定失敗 (可忽略): {e}")
    # --- [修正重點結束] ---

    return tab


async def nodriver_resize_window(driver, config_dict):
    print("nodriver_resize_window")
    window_size = config_dict["advanced"]["window_size"]
    # print("window_size", window_size)
    if len(window_size) > 0:
        if "," in window_size:
            print("start to resize window")
            launch_counter = 1
            target_left = 0
            target_top = 30
            target_width = 480
            target_height = 1024
            size_array = window_size.split(",")
            if len(size_array) >= 2:
                target_width = int(size_array[0])
                target_height = int(size_array[1])
            if len(size_array) >= 3:
                if len(size_array[2]) > 0:
                    launch_counter = int(size_array[2])
                target_left = target_width * launch_counter
                if target_left >= 1440:
                    target_left = 0
            # tab = await driver.main_tab()
            try:
                for i, tab in enumerate(driver):
                    await tab.set_window_size(left=target_left, top=target_top, width=target_width, height=target_height)
            except Exception as exc:
                # cannot unpack non-iterable NoneType object
                print(exc)
                # print("請關閉所有視窗後，重新操作一次")
                pass


async def nodriver_current_url(driver, tab):
    print("nodriver_current_url")
    exit_bot_error_strings = [
        "server rejected WebSocket connection: HTTP 500",
        "[Errno 61] Connect call failed ('127.0.0.1',",
        "[WinError 1225] ",
    ]
    # return value
    url = ""
    is_quit_bot = False
    last_active_tab = None

    driver_info = await driver._get_targets()
    if not tab.target in driver_info:
        print("tab may closed by user before, or popup confirm dialog.")
        tab = None
        await driver
        try:
            for i, each_tab in enumerate(driver):
                target_info = each_tab.target.to_json()
                target_url = ""
                if target_info:
                    if "url" in target_info:
                        target_url = target_info["url"]
                if len(target_url) > 4:
                    if target_url[:4] == "http" or target_url == "about:blank":
                        print("found tab url:", target_url)
                        last_active_tab = each_tab
        except Exception as exc:
            print(exc)
            if str(exc) == "list index out of range":
                print("Browser closed, start to exit bot.")
                is_quit_bot = True
                tab = None
                last_active_tab = None

        if not last_active_tab is None:
            tab = last_active_tab

    if tab:
        try:
            target_info = tab.target.to_json()
            if target_info:
                if "url" in target_info:
                    url = target_info["url"]
            # url = await tab.evaluate('window.location.href')
        except Exception as exc:
            print(exc)
            str_exc = ""
            try:
                str_exc = str(exc)
            except Exception as exc2:
                pass
            if len(str_exc) > 0:
                if str_exc == "server rejected WebSocket connection: HTTP 404":
                    print("目前 nodriver 還沒準備好..., 請等到沒出現這行訊息再開始使用。")

                for each_error_string in exit_bot_error_strings:
                    if each_error_string in str_exc:
                        # print('quit bot by error:', each_error_string, driver)
                        is_quit_bot = True
    return url, is_quit_bot, last_active_tab


def nodriver_overwrite_prefs(conf):
    # print(conf.user_data_dir)
    prefs_filepath = os.path.join(conf.user_data_dir, "Default")
    if not os.path.exists(prefs_filepath):
        os.mkdir(prefs_filepath)
    prefs_filepath = os.path.join(prefs_filepath, "Preferences")

    prefs_dict = {
        "credentials_enable_service": False,
        "ack_existing_ntp_extensions": False,
        "translate": {"enabled": False}}
    prefs_dict["in_product_help"] = {}
    prefs_dict["in_product_help"]["snoozed_feature"] = {}
    prefs_dict["in_product_help"]["snoozed_feature"]["IPH_LiveCaption"] = {}
    prefs_dict["in_product_help"]["snoozed_feature"]["IPH_LiveCaption"]["is_dismissed"] = True
    prefs_dict["in_product_help"]["snoozed_feature"]["IPH_LiveCaption"]["last_dismissed_by"] = 4
    prefs_dict["media_router"] = {}
    prefs_dict["media_router"]["show_cast_sessions_started_by_other_devices"] = {}
    prefs_dict["media_router"]["show_cast_sessions_started_by_other_devices"]["enabled"] = False
    prefs_dict["net"] = {}
    prefs_dict["net"]["network_prediction_options"] = 3
    prefs_dict["privacy_guide"] = {}
    prefs_dict["privacy_guide"]["viewed"] = True
    prefs_dict["privacy_sandbox"] = {}
    prefs_dict["privacy_sandbox"]["first_party_sets_enabled"] = False
    prefs_dict["profile"] = {}
    # prefs_dict["profile"]["cookie_controls_mode"]=1
    prefs_dict["profile"]["default_content_setting_values"] = {}
    prefs_dict["profile"]["default_content_setting_values"]["notifications"] = 2
    prefs_dict["profile"]["default_content_setting_values"]["sound"] = 2
    prefs_dict["profile"]["name"] = CONST_APP_VERSION
    prefs_dict["profile"]["password_manager_enabled"] = False
    prefs_dict["safebrowsing"] = {}
    prefs_dict["safebrowsing"]["enabled"] = False
    prefs_dict["safebrowsing"]["enhanced"] = False
    prefs_dict["sync"] = {}
    prefs_dict["sync"]["autofill_wallet_import_enabled_migrated"] = False

    json_str = json.dumps(prefs_dict)
    with open(prefs_filepath, 'w') as outfile:
        outfile.write(json_str)

    state_filepath = os.path.join(conf.user_data_dir, "Local State")
    state_dict = {}
    state_dict["dns_over_https"] = {}
    state_dict["dns_over_https"]["mode"] = "off"
    json_str = json.dumps(state_dict)
    with open(state_filepath, 'w') as outfile:
        outfile.write(json_str)


def get_extension_config(config_dict):
    no_sandbox = True
    browser_args = get_nodriver_browser_args()
    if len(config_dict["advanced"]["proxy_server_port"]) > 2:
        browser_args.append('--proxy-server=%s' %
                            config_dict["advanced"]["proxy_server_port"])
    conf = Config(browser_args=browser_args, no_sandbox=no_sandbox,
                  headless=config_dict["advanced"]["headless"])
    if config_dict["advanced"]["chrome_extension"]:
        ext = get_maxbot_extension_path(CONST_MAXBOT_EXTENSION_NAME)
        if len(ext) > 0:
            clone_ext = ext.replace(CONST_MAXBOT_EXTENSION_NAME, "tmp_" +
                                    CONST_MAXBOT_EXTENSION_NAME + "_" + config_dict["token"])
            if not os.path.exists(clone_ext):
                os.mkdir(clone_ext)
            util.copytree(ext, clone_ext)

            conf.add_extension(clone_ext)
            util.dump_settings_to_maxbot_plus_extension(
                clone_ext, config_dict, CONST_MAXBOT_CONFIG_FILE)
    return conf


async def check_refresh_datetime_occur(driver, target_time):
    print("check_refresh_datetime_occur")
    is_refresh_datetime_sent = False
    if len(target_time) > 0:
        system_clock_data = datetime.now()
        current_time = system_clock_data.strftime('%H:%M:%S')
        if target_time == current_time:
            try:
                for tab in driver.tabs:
                    await tab.reload()
                    is_refresh_datetime_sent = True
                    print("send refresh at time:", current_time)
            except Exception as exc:
                print(exc)
                pass

    return is_refresh_datetime_sent


def sync_status_to_extension(status):
    # sync generated ext status.
    Root_Dir = util.get_app_root()
    webdriver_folder = os.path.join(Root_Dir, "webdriver")
    target_folder_list = os.listdir(webdriver_folder)
    for item in target_folder_list:
        if item.startswith("tmp_" + CONST_MAXBOT_EXTENSION_NAME):
            target_path = os.path.join(webdriver_folder, item)
            target_path = os.path.join(target_path, "data")
            if os.path.exists(target_path):
                target_path = os.path.join(
                    target_path, CONST_MAXBOT_EXTENSION_STATUS_JSON)
                # print("save as to:", target_path)
                status_json = {}
                status_json["status"] = status
                # print("dump json to path:", target_path)
                try:
                    with open(target_path, 'w') as outfile:
                        json.dump(status_json, outfile)
                except Exception as e:
                    pass


def write_last_url_to_file(url):
    working_dir = os.path.dirname(os.path.realpath(__file__))
    target_path = os.path.join(working_dir, CONST_MAXBOT_LAST_URL_FILE)

    util.write_string_to_file(target_path, url)


async def sendkey_to_browser(driver, config_dict, url):
    print("sendkey_to_browser")
    tmp_filepath = ""
    if "token" in config_dict:
        app_root = util.get_app_root()
        tmp_file = config_dict["token"] + "_sendkey.tmp"
        tmp_filepath = os.path.join(app_root, tmp_file)

    if os.path.exists(tmp_filepath):
        sendkey_dict = None
        try:
            with open(tmp_filepath) as json_data:
                sendkey_dict = json.load(json_data)
                print(sendkey_dict)
        except Exception as e:
            print("error on open file")
            print(e)
            pass

        if sendkey_dict:
            # print("nodriver start to sendkey")
            for each_tab in driver.tabs:
                all_command_done = await sendkey_to_browser_exist(each_tab, sendkey_dict, url)

                # must all command success to delete tmp file.
                if all_command_done:
                    try:
                        os.unlink(tmp_filepath)
                        # print("remove file:", tmp_filepath)
                    except Exception as e:
                        pass


async def sendkey_to_browser_exist(tab, sendkey_dict, url):
    print("sendkey_to_browser_exist")
    all_command_done = True
    if "command" in sendkey_dict:
        for cmd_dict in sendkey_dict["command"]:
            # print("cmd_dict", cmd_dict)
            matched_location = True
            if "location" in cmd_dict:
                if cmd_dict["location"] != url:
                    matched_location = False

            if matched_location:
                if cmd_dict["type"] == "sendkey":
                    print("sendkey")
                    target_text = cmd_dict["text"]
                    try:
                        element = await tab.query_selector(cmd_dict["selector"])
                        if element:
                            await element.click()
                            await element.apply('function (element) {element.value = ""; } ')
                            await element.send_keys(target_text)
                        else:
                            # print("element not found:", select_query)
                            pass
                    except Exception as e:
                        all_command_done = False
                        # print("click fail for selector:", select_query)
                        print(e)
                        pass

                if cmd_dict["type"] == "click":
                    print("click")
                    try:
                        element = await tab.query_selector(cmd_dict["selector"])
                        if element:
                            await element.click()
                        else:
                            # print("element not found:", select_query)
                            pass
                    except Exception as e:
                        all_command_done = False
                        # print("click fail for selector:", select_query)
                        print(e)
                        pass
            time.sleep(0.05)
    return all_command_done


async def eval_to_browser(driver, config_dict, url):
    print("eval_to_browser")
    tmp_filepath = ""
    if "token" in config_dict:
        app_root = util.get_app_root()
        tmp_file = config_dict["token"] + "_eval.tmp"
        tmp_filepath = os.path.join(app_root, tmp_file)

    if os.path.exists(tmp_filepath):
        eval_dict = None
        try:
            with open(tmp_filepath) as json_data:
                eval_dict = json.load(json_data)
                print(eval_dict)
        except Exception as e:
            print("error on open file")
            print(e)
            pass

        if eval_dict:
            # print("nodriver start to eval")
            for each_tab in driver.tabs:
                all_command_done = await eval_to_browser_exist(each_tab, eval_dict, url)

                # must all command success to delete tmp file.
                if all_command_done:
                    try:
                        os.unlink(tmp_filepath)
                        # print("remove file:", tmp_filepath)
                    except Exception as e:
                        pass


def get_nodriver_browser_args():
    browser_args = [
        "--disable-animations",
        "--disable-app-info-dialog-mac",
        "--disable-background-networking",
        "--disable-backgrounding-occluded-windows",
        "--disable-breakpad",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-dev-shm-usage",
        "--disable-device-discovery-notifications",
        "--disable-dinosaur-easter-egg",
        "--disable-domain-reliability",
        "--disable-features=IsolateOrigins,site-per-process,TranslateUI",
        "--disable-infobars",
        "--disable-logging",
        "--disable-login-animations",
        "--disable-login-screen-apps",
        "--disable-notifications",
        "--disable-password-generation",
        "--disable-popup-blocking",
        "--disable-renderer-backgrounding",
        "--disable-session-crashed-bubble",
        "--disable-smooth-scrolling",
        "--disable-suggestions-ui",
        "--disable-sync",
        "--disable-translate",
        "--hide-crash-restore-bubble",
        "--homepage=about:blank",
        "--no-default-browser-check",
        "--no-first-run",
        "--no-pings",
        "--no-service-autorun",
        "--password-store=basic",
        "--remote-debugging-host=127.0.0.1",
        # "--disable-remote-fonts",
    ]

    return browser_args


async def eval_to_browser_exist(tab, eval_dict, url):
    print("eval_to_browser_exist")
    all_command_done = True
    if "command" in eval_dict:
        for cmd_dict in eval_dict["command"]:
            # print("cmd_dict", cmd_dict)
            matched_location = True
            if "location" in cmd_dict:
                if cmd_dict["location"] != url:
                    matched_location = False

            if matched_location:
                if cmd_dict["type"] == "eval":
                    print("eval")
                    target_script = cmd_dict["script"]
                    try:
                        await tab.evaluate(target_script)
                    except Exception as e:
                        all_command_done = False
                        # print("click fail for selector:", select_query)
                        print(e)
                        pass

            time.sleep(0.05)
    return all_command_done


def get_maxbot_extension_path(extension_folder):
    app_root = util.get_app_root()
    extension_path = "webdriver"
    extension_path = os.path.join(extension_path, extension_folder)
    config_filepath = os.path.join(app_root, extension_path)
    # print("config_filepath:", config_filepath)

    # double check extesion mainfest
    path = pathlib.Path(config_filepath)
    if path.exists():
        if path.is_dir():
            # print("found extension dir")
            for item in path.rglob("manifest.*"):
                path = item.parent
            # print("final path:", path)
    return config_filepath


def cli():
    parser = argparse.ArgumentParser(description="MaxBot Launcher")
    parser.add_argument("--input", type=str)
    parser.add_argument("--homepage", type=str)
    parser.add_argument("--ticket_number", type=int)
    parser.add_argument("--tixcraft_sid", type=str)
    parser.add_argument("--kktix_account", type=str)
    parser.add_argument("--kktix_password", type=str)
    parser.add_argument("--ibonqware", type=str)
    parser.add_argument("--headless", type=str)
    parser.add_argument("--browser", type=str, default='chrome')
    parser.add_argument("--window_size", type=str)
    parser.add_argument("--proxy_server", type=str)
    args = parser.parse_args()
    uc.loop().run_until_complete(main(args))


if __name__ == "__main__":
    cli()


# 日期選擇已修復 , 區域選擇待修中
