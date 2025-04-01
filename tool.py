import requests
import re
import os
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import time
import zipfile
import base64

# Tải biến môi trường từ file .env
load_dotenv()

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Khởi tạo cookies từ biến môi trường
def load_cookies_from_env():
    cookies_str = os.getenv('PIKBEST_COOKIES')
    if not cookies_str:
        logger.warning("Không tìm thấy PIKBEST_COOKIES trong file .env")
        return {}
    
    try:
        return json.loads(cookies_str)
    except json.JSONDecodeError:
        logger.error("Không thể parse PIKBEST_COOKIES từ .env, định dạng JSON không hợp lệ")
        return {}

# Lấy API key cho captcha solver từ .env
CAPTCHA_API_KEY = os.getenv('CAPTCHA_API_KEY', '')

# Khởi tạo cookies
PIKBEST_COOKIES = load_cookies_from_env()

# Tạo session và headers giống trình duyệt
session = requests.Session()
session.cookies.update(PIKBEST_COOKIES)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.pikbest.com/",
}

def setup_chrome_with_extension():
    """Thiết lập Chrome với extension giải captcha"""
    options = Options()
    
    # Thêm các options để tránh phát hiện automation
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(f"user-agent={headers['User-Agent']}")
    
    # Kiểm tra xem có cần chạy headless không
    # Lưu ý: Một số extension không hoạt động trong chế độ headless
    run_headless = os.getenv('RUN_HEADLESS', 'false').lower() == 'true'
    if run_headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    
    # Thêm extension giải captcha nếu có
    extension_path = os.getenv('CAPTCHA_EXTENSION_PATH', '')
    if extension_path and os.path.exists(extension_path):
        logger.info(f"Đang thêm extension từ: {extension_path}")
        options.add_extension(extension_path)
    else:
        logger.warning("Không tìm thấy extension giải captcha")
    
    # Tạo thư mục profile nếu cần
    chrome_profile = os.getenv('CHROME_PROFILE_PATH', '')
    if chrome_profile:
        os.makedirs(chrome_profile, exist_ok=True)
        options.add_argument(f"user-data-dir={chrome_profile}")
    
    return webdriver.Chrome(options=options)

def handle_captcha(driver):
    """Xử lý captcha nếu xuất hiện"""
    try:
        # Kiểm tra xem captcha có xuất hiện không
        captcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha') or contains(@title, 'captcha')]")
        if captcha_frames:
            logger.info("Phát hiện captcha, đang cố gắng giải...")
            
            # Lưu screenshot để debug
            driver.save_screenshot("captcha_detected.png")
            
            # Kiểm tra xem extension có hoạt động không
            if CAPTCHA_API_KEY:
                # Đợi extension giải captcha (thời gian tùy thuộc vào extension)
                logger.info("Đang đợi extension giải captcha...")
                time.sleep(15)  # Đợi extension giải captcha
                
                # Kiểm tra xem captcha đã được giải chưa
                captcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha') or contains(@title, 'captcha')]")
                if not captcha_frames:
                    logger.info("Captcha đã được giải thành công!")
                    return True
                else:
                    logger.warning("Extension không thể giải captcha tự động")
            
            # Nếu extension không hoạt động, thông báo cho người dùng
            print("\n⚠️ Phát hiện captcha! Vui lòng giải captcha thủ công.")
            print("Đã lưu screenshot tại: captcha_detected.png")
            
            # Nếu không chạy headless, đợi người dùng giải captcha
            if os.getenv('RUN_HEADLESS', 'false').lower() != 'true':
                input("Nhấn Enter sau khi đã giải captcha...")
                logger.info("Người dùng đã xác nhận giải captcha")
                return True
            else:
                logger.error("Không thể giải captcha trong chế độ headless")
                return False
    except Exception as e:
        logger.error(f"Lỗi khi xử lý captcha: {e}")
    
    return True  # Không có captcha hoặc đã xử lý xong

def get_real_download_link(file_id):
    download_api_url = f"https://pikbest.com/?m=download&id={file_id}&flag=1"
    logger.info(f"Đang truy cập URL download: {download_api_url}")

    driver = setup_chrome_with_extension()

    try:
        # Đặt kích thước cửa sổ trình duyệt
        driver.set_window_size(1920, 1080)
        
        # Thêm cookies vào trình duyệt
        driver.get("https://pikbest.com")
        logger.info("Đang thêm cookies vào trình duyệt...")
        for name, value in PIKBEST_COOKIES.items():
            driver.add_cookie({"name": name, "value": value})
        
        # Truy cập trang chính để xác nhận đăng nhập
        driver.get("https://pikbest.com/my/")
        time.sleep(3)  # Đợi để xác nhận đăng nhập
        
        # Kiểm tra xem đã đăng nhập thành công chưa
        if "login" in driver.current_url.lower():
            logger.warning("Chưa đăng nhập thành công, đang thử đăng nhập lại...")
            # Có thể thêm logic đăng nhập ở đây nếu cần
        
        # Truy cập trang download
        logger.info(f"Đang truy cập trang download: {download_api_url}")
        driver.get(download_api_url)
        
        # Đợi lâu hơn để trang load hoàn toàn và hiện nút "Click here"
        time.sleep(7)  # Đợi ít nhất 5 giây + thêm 2 giây để chắc chắn
        
        # Xử lý captcha nếu xuất hiện
        if not handle_captcha(driver):
            logger.error("Không thể xử lý captcha, đang hủy tải xuống")
            return None
        
        # Lưu screenshot để debug
        screenshot_path = "debug_screenshot.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"Đã lưu screenshot tại: {screenshot_path}")
        
        # Lưu source HTML để debug
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("Đã lưu source HTML tại: page_source.html")
        
        # Thêm script để bắt Ajax requests
        driver.execute_script("""
            window.ajaxRequests = [];
            window.downloadLinks = [];
            
            // Bắt XHR requests
            var originalXHROpen = XMLHttpRequest.prototype.open;
            var originalXHRSend = XMLHttpRequest.prototype.send;
            
            XMLHttpRequest.prototype.open = function(method, url) {
                this._url = url;
                this._method = method;
                originalXHROpen.apply(this, arguments);
            };
            
            XMLHttpRequest.prototype.send = function() {
                var xhr = this;
                this.addEventListener('load', function() {
                    try {
                        var url = xhr._url || xhr.responseURL;
                        if (url) {
                            window.ajaxRequests.push({
                                url: url,
                                method: xhr._method,
                                status: xhr.status,
                                response: xhr.responseText
                            });
                            
                            // Kiểm tra nếu là Ajax download request
                            if (url.includes('AjaxDownload') && url.includes('a=open')) {
                                console.log('Detected AjaxDownload request:', url);
                                console.log('Response:', xhr.responseText);
                                
                                // Thử parse JSON response
                                try {
                                    var jsonResponse = JSON.parse(xhr.responseText);
                                    if (jsonResponse && jsonResponse.url) {
                                        window.downloadLinks.push(jsonResponse.url);
                                    }
                                } catch (e) {
                                    console.error('Error parsing JSON:', e);
                                }
                            }
                            
                            // Kiểm tra các URL tải
                            if (url && (url.includes('.zip') || url.includes('.psd') || 
                                       url.includes('.ai') || url.includes('.jpg') || 
                                       url.includes('.png') || url.includes('.pdf') || 
                                       url.includes('.eps') || url.includes('.rar'))) {
                                if (!url.includes('logo') && !url.includes('icon') && 
                                    !url.includes('favicon') && !url.includes('avatar')) {
                                    window.downloadLinks.push(url);
                                }
                            }
                        }
                    } catch (e) {
                        console.error('Error in XHR tracking:', e);
                    }
                });
                originalXHRSend.apply(this, arguments);
            };
        """)
        
        # Phương pháp 1: Tìm và click nút "Click here" trực tiếp
        logger.info("Đang tìm nút 'Click here'...")
        try:
            # Tìm theo nhiều cách khác nhau
            click_here_selectors = [
                "/html/body/div[3]/div/div[1]/div/div[2]/div/p[1]/a",
                "//a[contains(text(), 'Click here')]",
                "//a[@onclick='if (!window.__cfRLUnblockHandlers) return false; downloadImage()']",
                "//a[contains(@onclick, 'downloadImage')]",
                "//a[contains(@class, 'download')]",
                "//button[contains(@class, 'download')]",
                "//a[contains(@href, 'javascript')]"
            ]
            
            click_here_button = None
            for selector in click_here_selectors:
                elements = driver.find_elements(By.XPATH, selector)
                if elements and elements[0].is_displayed():
                    click_here_button = elements[0]
                    logger.info(f"Tìm thấy nút tải với selector: {selector}")
                    break
            
            if click_here_button:
                logger.info(f"Đang click vào nút: {click_here_button.text}")
                # Sử dụng JavaScript để click để tránh lỗi stale element
                driver.execute_script("arguments[0].click();", click_here_button)
                time.sleep(5)  # Đợi lâu hơn sau khi click
                
                # Xử lý captcha nếu xuất hiện sau khi click
                if not handle_captcha(driver):
                    logger.error("Không thể xử lý captcha sau khi click, đang hủy tải xuống")
                    return None
                
                # Kiểm tra Ajax requests
                ajax_requests = driver.execute_script("return window.ajaxRequests;")
                if ajax_requests:
                    logger.info(f"Tìm thấy {len(ajax_requests)} Ajax requests")
                    
                    # Tìm Ajax request liên quan đến download
                    for req in ajax_requests:
                        if isinstance(req, dict) and 'url' in req:
                            url = req['url']
                            if 'AjaxDownload' in url and 'a=open' in url:
                                logger.info(f"Tìm thấy Ajax download request: {url}")
                                
                                # Kiểm tra response
                                if 'response' in req:
                                    try:
                                        response_data = json.loads(req['response'])
                                        logger.info(f"Ajax response: {response_data}")
                                        
                                        # Nếu response có URL, sử dụng nó
                                        if 'url' in response_data and response_data['url']:
                                            logger.info(f"Tìm thấy URL từ Ajax response: {response_data['url']}")
                                            return response_data['url']
                                        
                                        # Nếu response có data, thử tìm URL trong đó
                                        if 'data' in response_data and response_data['data']:
                                            if isinstance(response_data['data'], str) and 'http' in response_data['data']:
                                                logger.info(f"Tìm thấy URL từ Ajax response data: {response_data['data']}")
                                                return response_data['data']
                                    except Exception as e:
                                        logger.error(f"Lỗi khi parse Ajax response: {e}")
                                
                                # Nếu không tìm thấy URL trong response, thử gọi trực tiếp Ajax request
                                try:
                                    logger.info(f"Đang gọi trực tiếp Ajax request: {url}")
                                    ajax_response = session.get(url, headers=headers)
                                    if ajax_response.status_code == 200:
                                        try:
                                            ajax_data = ajax_response.json()
                                            logger.info(f"Ajax direct response: {ajax_data}")
                                            
                                            if 'url' in ajax_data and ajax_data['url']:
                                                logger.info(f"Tìm thấy URL từ direct Ajax: {ajax_data['url']}")
                                                return ajax_data['url']
                                                
                                            if 'data' in ajax_data and ajax_data['data']:
                                                if isinstance(ajax_data['data'], str) and 'http' in ajax_data['data']:
                                                    logger.info(f"Tìm thấy URL từ direct Ajax data: {ajax_data['data']}")
                                                    return ajax_data['data']
                                        except Exception as e:
                                            logger.error(f"Lỗi khi parse direct Ajax response: {e}")
                                except Exception as e:
                                    logger.error(f"Lỗi khi gọi trực tiếp Ajax request: {e}")
                
                # Kiểm tra download links
                download_links = driver.execute_script("return window.downloadLinks;")
                if download_links and len(download_links) > 0:
                    for link in download_links:
                        if not any(keyword in link.lower() for keyword in ['logo', 'icon', 'favicon', 'avatar']):
                            logger.info(f"Tìm thấy link tải từ download links: {link}")
                            return link
                
                # Phương pháp mới: Trích xuất hash từ HTML và tạo Ajax URL
                try:
                    logger.info("Đang tìm hash trong HTML...")
                    page_source = driver.page_source
                    
                    # Tìm hash trong HTML
                    hash_match = re.search(r'__hash__=([a-f0-9_]+)', page_source)
                    if hash_match:
                        hash_value = hash_match.group(1)
                        logger.info(f"Tìm thấy hash: {hash_value}")
                        
                        # Tạo Ajax URL
                        ajax_url = f"https://pikbest.com/?m=AjaxDownload&a=open&id={file_id}&__hash__={hash_value}&flag=1"
                        logger.info(f"Đang gọi Ajax URL: {ajax_url}")
                        
                        # Gọi Ajax URL
                        ajax_response = session.get(ajax_url, headers=headers)
                        if ajax_response.status_code == 200:
                            try:
                                ajax_data = ajax_response.json()
                                logger.info(f"Ajax response: {ajax_data}")
                                
                                if 'url' in ajax_data and ajax_data['url']:
                                    logger.info(f"Tìm thấy URL từ Ajax: {ajax_data['url']}")
                                    return ajax_data['url']
                                    
                                if 'data' in ajax_data and ajax_data['data']:
                                    if isinstance(ajax_data['data'], str) and 'http' in ajax_data['data']:
                                        logger.info(f"Tìm thấy URL từ Ajax data: {ajax_data['data']}")
                                        return ajax_data['data']
                            except Exception as e:
                                logger.error(f"Lỗi khi parse Ajax response: {e}")
                except Exception as e:
                    logger.error(f"Lỗi khi tìm hash và gọi Ajax: {e}")
        except Exception as e:
            logger.error(f"Lỗi khi tìm và click nút 'Click here': {e}")
        
        # Phương pháp 2: Tìm trong HTML và JavaScript
        logger.info("Đang tìm trong HTML và JavaScript...")
        try:
            # Tìm tất cả các script tags
            scripts = driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                try:
                    script_content = script.get_attribute("innerHTML")
                    if script_content:
                        # Tìm URL trong script
                        url_matches = re.findall(r'(https?://[^"\'\s]+\.(?:zip|psd|ai|jpg|png|pdf|eps|rar)[^"\'\s]*)', script_content)
                        for url in url_matches:
                            if "pikbest" in url and is_valid_download_file(url):
                                logger.info(f"Tìm thấy link tải trong JavaScript: {url}")
                                return url
                except Exception as e:
                    logger.error(f"Lỗi khi phân tích script: {e}")
                    continue
        except Exception as e:
            logger.error(f"Lỗi khi tìm trong JavaScript: {e}")
        
        # Phương pháp 3: Phân tích network requests
        logger.info("Đang phân tích network requests...")
        try:
            # Lấy tất cả network requests
            all_requests = driver.execute_script("return window.ajaxRequests;")
            if all_requests:
                logger.info(f"Tìm thấy {len(all_requests)} requests")
                
                # Lọc các URL có thể là link tải
                download_candidates = []
                for url in all_requests:
                    if isinstance(url, str) and "pikbest" in url:
                        if is_valid_download_file(url):
                            download_candidates.append(url)
                
                if download_candidates:
                    logger.info(f"Các URL ứng viên: {download_candidates}")
                    return download_candidates[-1]  # Trả về URL mới nhất
        except Exception as e:
            logger.error(f"Lỗi khi phân tích network requests: {e}")
        
        # Phương pháp 4: Tìm trong performance entries
        logger.info("Đang tìm trong performance entries...")
        try:
            entries = driver.execute_script("""
                var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
                var entries = performance.getEntries() || [];
                return entries;
            """)
            
            download_candidates = []
            for entry in entries:
                if isinstance(entry, dict) and 'name' in entry:
                    url = entry['name']
                    if isinstance(url, str) and "pikbest" in url:
                        ext_match = re.search(r'\.(zip|psd|ai|jpg|png|pdf|eps|rar)', url.lower())
                        if ext_match and not any(keyword in url.lower() for keyword in ['logo', 'icon', 'favicon', 'avatar']):
                            download_candidates.append(url)
            
            if download_candidates:
                logger.info(f"Các URL từ performance entries: {download_candidates}")
                return download_candidates[-1]  # Trả về URL mới nhất
        except Exception as e:
            logger.error(f"Lỗi khi tìm trong performance entries: {e}")
            
    except Exception as e:
        logger.error(f"Lỗi chung khi tìm link tải: {e}")
    finally:
        driver.quit()

    return None

def is_valid_download_file(url):
    """Kiểm tra xem URL có phải là file tải hợp lệ không (loại trừ logo, icon, v.v.)"""
    if not url:
        return False
        
    # Danh sách các URL cần loại trừ
    blacklist = [
        "js.pikbest.com/best/images/personal/designer-prize.png",
        "pikbest.com/best/images/personal",
        "pikbest.com/images/",
        "pikbest.com/static/"
    ]
    
    # Kiểm tra xem URL có trong danh sách đen không
    for item in blacklist:
        if item in url:
            logger.warning(f"URL nằm trong danh sách đen: {url}")
            return False
        
    # Kiểm tra phần mở rộng file
    ext_match = re.search(r'\.(zip|psd|ai|jpg|png|pdf|eps|rar)(\?|$)', url.lower())
    if not ext_match:
        return False
        
    # Loại trừ các file logo, icon, v.v.
    if any(keyword in url.lower() for keyword in ['logo', 'icon', 'favicon', 'avatar', 'prize', 'personal']):
        logger.warning(f"URL chứa từ khóa bị loại trừ: {url}")
        return False
        
    # Kiểm tra kích thước file (nếu có thể)
    try:
        response = session.head(url, headers=headers, timeout=5)
        content_length = response.headers.get('Content-Length')
        if content_length:
            size_kb = int(content_length) / 1024
            if size_kb < 50:  # Nhỏ hơn 50KB có thể là icon hoặc hình ảnh nhỏ
                logger.warning(f"File quá nhỏ ({size_kb:.2f} KB): {url}")
                return False
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra kích thước file: {e}")
        
    return True

def get_file_info(url):
    """Lấy thông tin về file từ URL"""
    try:
        response = session.head(url, headers=headers, timeout=5)
        
        # Lấy kích thước file
        content_length = response.headers.get('Content-Length')
        size_mb = int(content_length) / (1024 * 1024) if content_length else 0
        
        # Lấy loại file
        content_type = response.headers.get('Content-Type', '')
        
        # Lấy tên file
        filename = url.split('/')[-1].split('?')[0]
        
        # Lấy thời gian hết hạn từ URL
        expiry_time = "Không xác định"
        expiry_match = re.search(r'[?&]e=(\d+)', url)
        if expiry_match:
            try:
                expiry_timestamp = int(expiry_match.group(1))
                expiry_time = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(expiry_timestamp))
            except:
                expiry_time = "Không xác định"
        
        return {
            'filename': filename,
            'size': f"{size_mb:.2f} MB",
            'type': content_type,
            'url': url,
            'expiry': expiry_time
        }
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin file: {e}")
        
        # Vẫn cố gắng lấy thời gian hết hạn từ URL
        expiry_time = "Không xác định"
        try:
            expiry_match = re.search(r'[?&]e=(\d+)', url)
            if expiry_match:
                expiry_timestamp = int(expiry_match.group(1))
                expiry_time = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(expiry_timestamp))
        except:
            pass
            
        return {
            'filename': url.split('/')[-1].split('?')[0],
            'size': 'Không xác định',
            'type': 'Không xác định',
            'url': url,
            'expiry': expiry_time
        }

def extract_file_id(url):
    # Xử lý nhiều định dạng URL khác nhau
    patterns = [
        r'_([0-9]+)\.html',  # Mẫu như _10015761.html
        r'/([0-9]+)\.html',  # Mẫu như /10015761.html
        r'-([0-9]+)\.html',   # Mẫu như -132883.html
        r'[^0-9]([0-9]{6,})\.html'  # Bất kỳ số 6+ chữ số nào trước .html
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Nếu không tìm thấy, thử phương pháp khác
    parts = url.split('/')
    for part in parts:
        if part.isdigit() and len(part) >= 6:  # ID thường có ít nhất 6 chữ số
            return part
            
    return None

def process_pikbest_url(user_url):
    file_id = extract_file_id(user_url)
    if not file_id:
        logger.error(f"Không tìm thấy ID trong URL: {user_url}")
        print("❌ Không tìm thấy ID trong URL.")
        return

    print(f"🔍 Đang xử lý ID: {file_id}")
    logger.info(f"Đang xử lý ID: {file_id} từ URL: {user_url}")

    real_url = get_real_download_link(file_id)
    
    # Xác minh link tải
    verified_url = verify_download_link(real_url) if real_url else None
    
    if verified_url:
        print(f"\n🎯 Link tải thật: {verified_url}")
        
        # Lấy thông tin file
        file_info = get_file_info(verified_url)
        
        # Hiển thị thông tin file
        print("\n📁 Thông tin file:")
        print(f"  • Tên file: {file_info['filename']}")
        print(f"  • Kích thước: {file_info['size']}")
        print(f"  • Loại file: {file_info['type']}")
        print(f"  • Hết hạn: {file_info['expiry']}")
        
        # Hiển thị hướng dẫn
        print("\n💡 Để tải file, bạn có thể:")
        print("  1. Sao chép link trên và dán vào trình duyệt")
        print("  2. Sử dụng công cụ tải xuống như IDM, wget, curl, v.v.")
        print("  3. Sử dụng lệnh sau trong terminal:")
        print(f"     curl -o \"{file_info['filename']}\" \"{verified_url}\"")
        
        # Hiển thị cảnh báo nếu link sắp hết hạn
        if file_info['expiry'] != "Không xác định":
            try:
                expiry_match = re.search(r'[?&]e=(\d+)', verified_url)
                if expiry_match:
                    expiry_timestamp = int(expiry_match.group(1))
                    current_time = time.time()
                    hours_left = (expiry_timestamp - current_time) / 3600
                    
                    if hours_left < 24:
                        print(f"\n⚠️ Cảnh báo: Link sẽ hết hạn trong {hours_left:.1f} giờ!")
                    elif hours_left < 72:
                        print(f"\n⚠️ Cảnh báo: Link sẽ hết hạn trong {hours_left/24:.1f} ngày!")
            except:
                pass
        
        return verified_url
    else:
        if real_url:
            logger.error(f"Tìm thấy link nhưng không hợp lệ: {real_url}")
            print(f"⚠️ Tìm thấy link nhưng không hợp lệ: {real_url}")
            print("💡 Mẹo: Link này có thể là hình ảnh hoặc tài nguyên khác, không phải file tải thật.")
        else:
            logger.error("Không tìm thấy link tải thật")
            print("⚠️ Không tìm thấy link tải thật. Vui lòng kiểm tra lại URL hoặc đăng nhập.")
        
        print("💡 Mẹo: Hãy kiểm tra file debug_screenshot.png và page_source.html để xem trạng thái trang.")
        return None

def process_multiple_urls(urls):
    """Xử lý nhiều URL cùng lúc"""
    results = []
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Đang xử lý: {url}")
        result = process_pikbest_url(url)
        if result:
            results.append(result)
    
    # Hiển thị tổng kết
    if results:
        print("\n✅ Tổng kết:")
        for i, url in enumerate(results, 1):
            print(f"{i}. {url}")
    
    return results

def verify_download_link(url):
    """Xác minh link tải có hợp lệ không và có phải là link tải thật không"""
    if not url:
        return None
        
    # Kiểm tra tính hợp lệ của URL
    if not is_valid_download_file(url):
        logger.warning(f"Link không hợp lệ: {url}")
        return None
        
    # Kiểm tra xem URL có phải là link tải thật không
    try:
        # Kiểm tra kích thước file
        response = session.head(url, headers=headers, timeout=5)
        content_length = response.headers.get('Content-Length')
        
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            
            # Nếu file quá nhỏ (< 0.5MB) và không phải là file zip, có thể không phải là file tải thật
            if size_mb < 0.5 and not url.lower().endswith('.zip'):
                logger.warning(f"File quá nhỏ ({size_mb:.2f} MB), có thể không phải là file tải thật: {url}")
                
                # Kiểm tra thêm nếu là file hình ảnh
                content_type = response.headers.get('Content-Type', '')
                if 'image' in content_type:
                    logger.warning(f"File là hình ảnh, không phải file tải thật: {url}")
                    return None
        
        # Kiểm tra URL có chứa tham số e= (thời gian hết hạn) không
        # Link tải thật của Pikbest thường có tham số này
        if 'e=' not in url and '.zip' in url:
            logger.warning(f"URL không có tham số hết hạn (e=), có thể không phải link tải thật: {url}")
            # Không trả về None ở đây vì một số link tải có thể không có tham số e=
        
        return url
    except Exception as e:
        logger.error(f"Lỗi khi xác minh link tải: {e}")
        return url  # Vẫn trả về URL nếu có lỗi xảy ra khi xác minh

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 PIKBEST LINK EXTRACTOR 🔍".center(60))
    print("=" * 60)
    print("Tool này giúp lấy link tải trực tiếp từ Pikbest.com")
    print("Bạn có thể nhập một hoặc nhiều URL, mỗi URL một dòng.")
    print("Để kết thúc nhập, hãy nhấn Enter ở dòng trống.")
    print("-" * 60)
    
    urls = []
    while True:
        url = input("Nhập URL Pikbest (Enter để kết thúc): ").strip()
        if not url:
            break
        urls.append(url)
    
    if urls:
        if len(urls) == 1:
            process_pikbest_url(urls[0])
        else:
            process_multiple_urls(urls)
    else:
        print("Không có URL nào được nhập.")
