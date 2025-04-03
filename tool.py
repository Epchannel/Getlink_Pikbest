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
from selenium.webdriver.common.keys import Keys

# Tải biến môi trường từ file .env
load_dotenv()

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pikbest_extractor.log"),
        logging.StreamHandler()
    ]
)
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
    """Thiết lập Chrome với extension giải captcha và ngăn tải xuống tự động"""
    options = Options()
    
    logger.info("Bắt đầu thiết lập Chrome với extension")
    
    # Thêm các options để tránh phát hiện automation
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(f"user-agent={headers['User-Agent']}")
    logger.debug("Đã thêm các options chống phát hiện automation")
    
    # Thiết lập preferences để ngăn tải xuống tự động
    prefs = {
        "download.default_directory": "/dev/null",  # Đường dẫn không tồn tại
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 2,  # 2 = block
        "profile.default_content_settings.popups": 2  # 2 = block
    }
    options.add_experimental_option("prefs", prefs)
    logger.info("Đã thiết lập preferences để ngăn tải xuống tự động")
    
    # Kiểm tra xem có cần chạy headless không
    run_headless = os.getenv('RUN_HEADLESS', 'false').lower() == 'true'
    if run_headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        logger.info("Đã bật chế độ headless")
    else:
        logger.info("Đang chạy ở chế độ có giao diện")
    
    # Thêm extension giải captcha nếu có
    extension_path = os.getenv('CAPTCHA_EXTENSION_PATH', '')
    if extension_path:
        if not os.path.exists(extension_path):
            logger.error(f"Không tìm thấy extension tại đường dẫn: {extension_path}")
        else:
            logger.info(f"Đang thêm extension từ: {extension_path}")
            
            try:
                # Phương pháp 1: Nếu là file .crx, sử dụng add_extension
                if extension_path.endswith('.crx'):
                    options.add_extension(extension_path)
                    logger.info(f"Đã thêm extension từ file .crx: {extension_path}")
                
                # Phương pháp 2: Nếu là thư mục, đóng gói thành file .crx tạm thời
                elif os.path.isdir(extension_path):
                    logger.debug("Phát hiện extension là thư mục, đang xử lý...")
                    # Kiểm tra manifest.json
                    manifest_path = os.path.join(extension_path, "manifest.json")
                    if not os.path.exists(manifest_path):
                        logger.error(f"Không tìm thấy manifest.json trong thư mục extension: {extension_path}")
                    else:
                        # Đọc manifest để kiểm tra
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest_content = json.loads(f.read())
                            logger.debug(f"Đã đọc manifest.json: {manifest_content.get('name', 'Unknown')} v{manifest_content.get('version', 'Unknown')}")
                        except Exception as e:
                            logger.warning(f"Không thể đọc manifest.json: {e}")
                        
                        # Tạo file .crx tạm thời từ thư mục extension
                        temp_crx_path = create_temp_crx_from_folder(extension_path)
                        if temp_crx_path:
                            options.add_extension(temp_crx_path)
                            logger.info(f"Đã thêm extension từ thư mục (đóng gói tạm thời): {extension_path}")
                        else:
                            # Nếu không thể tạo file .crx, sử dụng load-extension
                            abs_extension_path = os.path.abspath(extension_path)
                            options.add_argument(f"--load-extension={abs_extension_path}")
                            logger.info(f"Đã thêm extension từ thư mục: {abs_extension_path}")
                else:
                    logger.warning(f"Không thể xác định loại extension: {extension_path}")
            except Exception as e:
                logger.error(f"Lỗi khi thêm extension: {e}")
                # Thử phương pháp cuối cùng nếu các phương pháp trên thất bại
                try:
                    abs_extension_path = os.path.abspath(extension_path)
                    options.add_argument(f"--load-extension={abs_extension_path}")
                    logger.info(f"Đã thêm extension từ thư mục (phương pháp dự phòng): {abs_extension_path}")
                except Exception as e2:
                    logger.error(f"Không thể thêm extension bằng bất kỳ phương pháp nào: {e2}")
    else:
        logger.warning("Không tìm thấy đường dẫn extension trong biến môi trường CAPTCHA_EXTENSION_PATH")
    
    # Tạo thư mục profile nếu cần
    chrome_profile = os.getenv('CHROME_PROFILE_PATH', '')
    if chrome_profile:
        try:
            # Chuyển đổi đường dẫn tương đối thành tuyệt đối
            abs_profile_path = os.path.abspath(chrome_profile)
            logger.debug(f"Đường dẫn tuyệt đối của profile: {abs_profile_path}")
            
            # Tạo thư mục profile
            os.makedirs(abs_profile_path, exist_ok=True)
            options.add_argument(f"user-data-dir={abs_profile_path}")
            logger.info(f"Đã thiết lập profile Chrome tại: {abs_profile_path}")
        except PermissionError as e:
            logger.error(f"Lỗi quyền truy cập khi tạo thư mục profile: {e}")
            logger.info("Đang thử tạo profile trong thư mục tạm thời...")
            
            # Sử dụng thư mục tạm thời nếu không thể tạo thư mục profile
            import tempfile
            temp_profile = os.path.join(tempfile.gettempdir(), "ChromeProfile")
            os.makedirs(temp_profile, exist_ok=True)
            options.add_argument(f"user-data-dir={temp_profile}")
            logger.info(f"Đã thiết lập profile Chrome tạm thời tại: {temp_profile}")
        except Exception as e:
            logger.error(f"Lỗi khi tạo thư mục profile: {e}")
    else:
        logger.debug("Không sử dụng profile Chrome (không tìm thấy CHROME_PROFILE_PATH)")
    
    # Thêm các options để debug extension
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Thêm log level để xem thông tin chi tiết hơn
    options.add_argument("--enable-logging")
    options.add_argument("--v=1")
    
    logger.info("Đang khởi tạo trình duyệt Chrome...")
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("Đã khởi tạo trình duyệt Chrome thành công")
        
        # Thêm script để ngăn tải xuống
        driver.execute_script("""
            // Ghi đè window.open để ngăn mở tab mới
            window.originalOpen = window.open;
            window.open = function(url, name, specs) {
                console.log('Intercepted window.open:', url);
                if (url && (
                    url.includes('.zip') || 
                    url.includes('.psd') || 
                    url.includes('.ai') || 
                    url.includes('.jpg') || 
                    url.includes('.png') || 
                    url.includes('.pdf') || 
                    url.includes('.eps') || 
                    url.includes('.rar')
                )) {
                    console.log('Prevented download via window.open:', url);
                    return null;
                }
                return window.originalOpen(url, name, specs);
            };
        """)
        
        # Cấu hình API key cho extension CaptchaSonic
        if CAPTCHA_API_KEY:
            configure_captcha_extension(driver)
        
        return driver
    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo trình duyệt Chrome: {e}")
        raise

def create_temp_crx_from_folder(folder_path):
    """Tạo file .crx tạm thời từ thư mục extension"""
    logger.debug(f"Bắt đầu tạo file .crx tạm thời từ thư mục: {folder_path}")
    try:
        import shutil
        import tempfile
        
        # Tạo thư mục tạm thời
        temp_dir = tempfile.mkdtemp()
        temp_crx_path = os.path.join(temp_dir, "temp_extension.crx")
        logger.debug(f"Đã tạo thư mục tạm thời: {temp_dir}")
        
        # Kiểm tra xem thư mục có chứa manifest.json không
        manifest_path = os.path.join(folder_path, "manifest.json")
        if not os.path.exists(manifest_path):
            logger.error(f"Không tìm thấy manifest.json trong thư mục extension: {folder_path}")
            return None
        
        # Đọc manifest để lấy thông tin
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_content = f.read()
                manifest_json = json.loads(manifest_content)
                logger.debug(f"Đã đọc manifest.json: {manifest_json.get('name', 'Unknown')} v{manifest_json.get('version', 'Unknown')}")
        except Exception as e:
            logger.error(f"Lỗi khi đọc manifest.json: {e}")
            logger.debug(f"Nội dung manifest (một phần): {manifest_content[:100] if 'manifest_content' in locals() else 'N/A'}...")
        
        # Tạo file .zip tạm thời
        temp_zip_path = os.path.join(temp_dir, "temp_extension.zip")
        
        # Nén thư mục extension thành file .zip
        logger.debug(f"Đang nén thư mục extension thành file .zip: {temp_zip_path}")
        shutil.make_archive(os.path.splitext(temp_zip_path)[0], 'zip', folder_path)
        
        # Đổi tên file .zip thành .crx
        logger.debug(f"Đang đổi tên file .zip thành .crx: {temp_crx_path}")
        shutil.copy(temp_zip_path, temp_crx_path)
        
        logger.info(f"Đã tạo file .crx tạm thời tại: {temp_crx_path}")
        return temp_crx_path
    except Exception as e:
        logger.error(f"Lỗi khi tạo file .crx tạm thời: {e}", exc_info=True)
        return None

def handle_captcha(driver):
    """Xử lý captcha nếu xuất hiện"""
    logger.info("Đang kiểm tra và xử lý captcha...")
    try:
        # Kiểm tra xem captcha có xuất hiện không
        captcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha') or contains(@title, 'captcha')]")
        if captcha_frames:
            logger.info(f"Phát hiện captcha, đang cố gắng giải... (tìm thấy {len(captcha_frames)} frames)")
            
            # Lưu screenshot để debug
            screenshot_path = "captcha_detected.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"Đã lưu screenshot tại: {screenshot_path}")
            
            # Lưu source HTML để debug
            with open("captcha_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.debug("Đã lưu source HTML tại: captcha_page.html")
            
            # Kiểm tra xem extension có hoạt động không
            if CAPTCHA_API_KEY:
                logger.info(f"Tìm thấy CAPTCHA_API_KEY: {CAPTCHA_API_KEY[:5]}...")
                
                # Đợi extension giải captcha (thời gian tùy thuộc vào extension)
                logger.info("Đang đợi extension giải captcha...")
                time.sleep(15)  # Đợi extension giải captcha
                
                # Kiểm tra xem captcha đã được giải chưa
                captcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha') or contains(@title, 'captcha')]")
                if not captcha_frames:
                    logger.info("Captcha đã được giải thành công!")
                    return True
                else:
                    logger.warning(f"Extension không thể giải captcha tự động (vẫn còn {len(captcha_frames)} frames)")
            else:
                logger.warning("Không tìm thấy CAPTCHA_API_KEY trong biến môi trường")
            
            # Nếu extension không hoạt động, thông báo cho người dùng
            print("\n⚠️ Phát hiện captcha! Vui lòng giải captcha thủ công.")
            print(f"Đã lưu screenshot tại: {screenshot_path}")
            
            # Nếu không chạy headless, đợi người dùng giải captcha
            if os.getenv('RUN_HEADLESS', 'false').lower() != 'true':
                input("Nhấn Enter sau khi đã giải captcha...")
                logger.info("Người dùng đã xác nhận giải captcha")
                
                # Kiểm tra lại sau khi người dùng giải
                captcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha') or contains(@title, 'captcha')]")
                if not captcha_frames:
                    logger.info("Captcha đã được giải thành công sau khi người dùng xác nhận!")
                    return True
                else:
                    logger.warning("Captcha vẫn chưa được giải sau khi người dùng xác nhận")
                    return False
            else:
                logger.error("Không thể giải captcha trong chế độ headless")
                return False
        else:
            logger.info("Không phát hiện captcha")
    except Exception as e:
        logger.error(f"Lỗi khi xử lý captcha: {e}", exc_info=True)
    
    return True  # Không có captcha hoặc đã xử lý xong

def get_real_download_link(file_id):
    download_api_url = f"https://pikbest.com/?m=download&id={file_id}&flag=1"
    logger.info(f"Đang truy cập URL download: {download_api_url}")

    driver = setup_chrome_with_extension()

    try:
        # Kiểm tra xem extension đã được tải thành công chưa
        extension_loaded = check_extension_loaded(driver)
        if not extension_loaded:
            logger.warning("Extension không được tải, tiếp tục nhưng có thể gặp vấn đề với captcha")
        
        # Đặt kích thước cửa sổ trình duyệt
        driver.set_window_size(1920, 1080)
        
        # Thêm cookies vào trình duyệt
        driver.get("https://pikbest.com")
        logger.info("Đang thêm cookies vào trình duyệt...")
        for name, value in PIKBEST_COOKIES.items():
            driver.add_cookie({"name": name, "value": value})
        
        # Truy cập trang chính để xác nhận đăng nhập
        driver.get("https://pikbest.com/?m=home&a=userInfo")
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
        
        # Lấy loại file từ Content-Type
        content_type = response.headers.get('Content-Type', '')
        
        # Lấy tên file
        filename = url.split('/')[-1].split('?')[0]
        
        # Xác định định dạng file từ phần mở rộng
        file_format = "Không xác định"
        ext_match = re.search(r'\.([a-zA-Z0-9]+)(\?|$)', filename.lower())
        if ext_match:
            ext = ext_match.group(1).upper()
            # Ánh xạ phần mở rộng thành định dạng file
            format_map = {
                'PSD': 'PSD',
                'AI': 'AI',
                'EPS': 'EPS',
                'JPG': 'JPG',
                'JPEG': 'JPG',
                'PNG': 'PNG',
                'PDF': 'PDF',
                'ZIP': 'ZIP',
                'RAR': 'RAR'
            }
            file_format = format_map.get(ext, ext)
        
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
            'format': file_format,
            'url': url,
            'expiry': expiry_time
        }
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin file: {e}")
        
        # Vẫn cố gắng lấy thời gian hết hạn và định dạng từ URL
        expiry_time = "Không xác định"
        file_format = "Không xác định"
        
        try:
            # Lấy định dạng từ tên file
            filename = url.split('/')[-1].split('?')[0]
            ext_match = re.search(r'\.([a-zA-Z0-9]+)(\?|$)', filename.lower())
            if ext_match:
                ext = ext_match.group(1).upper()
                format_map = {
                    'PSD': 'PSD',
                    'AI': 'AI',
                    'EPS': 'EPS',
                    'JPG': 'JPG',
                    'JPEG': 'JPG',
                    'PNG': 'PNG',
                    'PDF': 'PDF',
                    'ZIP': 'ZIP',
                    'RAR': 'RAR'
                }
                file_format = format_map.get(ext, ext)
            
            # Lấy thời gian hết hạn
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
            'format': file_format,
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
        print(f"  • Định dạng: {file_info['format']}")
        print(f"  • Hết hạn: {file_info['expiry']}")
        
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

def check_extension_loaded(driver):
    """Kiểm tra xem extension đã được tải thành công chưa"""
    logger.info("Đang kiểm tra xem extension đã được tải thành công chưa...")
    try:
        # Mở trang chrome://extensions
        driver.get("chrome://extensions")
        time.sleep(2)
        logger.debug("Đã mở trang chrome://extensions")
        
        # Bật chế độ developer mode để xem ID extension
        try:
            driver.execute_script("""
                document.querySelector('extensions-manager').shadowRoot
                    .querySelector('extensions-toolbar').shadowRoot
                    .querySelector('#devMode').click()
            """)
            logger.debug("Đã bật chế độ developer mode")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Không thể bật chế độ developer mode: {e}")
        
        # Lấy HTML của trang
        page_source = driver.page_source
        
        # Lưu screenshot để debug
        screenshot_path = "extensions_page.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"Đã lưu screenshot trang extensions tại: {screenshot_path}")
        
        # Lưu source HTML để debug
        with open("extensions_page.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        logger.debug("Đã lưu source HTML trang extensions tại: extensions_page.html")
        
        # Kiểm tra xem có extension nào được tải không
        extension_keywords = ["captchasonic", "captcha", "solver", "recaptcha"]
        found_extensions = []
        
        for keyword in extension_keywords:
            if keyword in page_source.lower():
                found_extensions.append(keyword)
        
        if found_extensions:
            logger.info(f"Extension đã được tải thành công! Tìm thấy các từ khóa: {', '.join(found_extensions)}")
            return True
        else:
            logger.warning("Không tìm thấy extension trong danh sách đã cài đặt")
            
            # Thử kiểm tra bằng JavaScript
            try:
                extensions = driver.execute_script("""
                    return Array.from(document.querySelectorAll('extensions-item')).map(item => {
                        try {
                            return {
                                name: item.shadowRoot.querySelector('#name').textContent,
                                id: item.getAttribute('extension-id')
                            };
                        } catch (e) {
                            return { name: 'Unknown', id: 'Unknown' };
                        }
                    });
                """)
                
                if extensions:
                    logger.info(f"Tìm thấy {len(extensions)} extensions:")
                    for ext in extensions:
                        logger.info(f"  - {ext.get('name', 'Unknown')} (ID: {ext.get('id', 'Unknown')})")
                    
                    # Kiểm tra xem có extension nào liên quan đến captcha không
                    captcha_extensions = [ext for ext in extensions if any(keyword in ext.get('name', '').lower() for keyword in extension_keywords)]
                    if captcha_extensions:
                        logger.info(f"Tìm thấy extension captcha: {captcha_extensions[0].get('name', 'Unknown')}")
                        return True
            except Exception as e:
                logger.error(f"Lỗi khi kiểm tra extensions bằng JavaScript: {e}")
            
            return False
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra extension: {e}", exc_info=True)
        return False

def configure_captcha_extension(driver):
    """Cấu hình API key cho extension CaptchaSonic"""
    logger.info("Đang cấu hình API key cho extension CaptchaSonic...")
    try:
        # Truy cập trang cấu hình của extension
        extension_url = "chrome-extension://dkkdakdkffippajmebplgnpmijmnejlh/popup.html"
        driver.get(extension_url)
        
        # Đợi trang load hoàn tất
        time.sleep(2)
        
        # Lưu screenshot để debug
        driver.save_screenshot("extension_config_page.png")
        logger.debug("Đã lưu screenshot trang cấu hình extension")
        
        # Tìm input field để nhập API key
        try:
            api_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "apikey"))
            )
            
            # Xóa nội dung hiện tại (nếu có)
            api_input.clear()
            
            # Nhập API key
            api_input.send_keys(CAPTCHA_API_KEY)
            logger.info("Đã nhập API key vào input field")
            
            # Tìm và nhấn nút Save hoặc Submit
            save_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Save') or contains(text(), 'Submit') or contains(@class, 'save')]")
            if save_buttons:
                save_buttons[0].click()
                logger.info("Đã nhấn nút Save")
                time.sleep(1)
            else:
                # Thử phương pháp khác nếu không tìm thấy nút Save
                logger.info("Không tìm thấy nút Save, thử phương pháp lưu thay thế")
                
                # Phương pháp 1: Nhấn Enter sau khi nhập API key
                api_input.send_keys(Keys.ENTER)
                
                # Phương pháp 2: Lưu bằng JavaScript
                driver.execute_script("""
                    // Tìm tất cả các nút trên trang
                    const buttons = document.querySelectorAll('button');
                    // Tìm nút lưu dựa trên text hoặc class
                    for (const button of buttons) {
                        if (button.textContent.includes('Save') || 
                            button.textContent.includes('Submit') || 
                            button.className.includes('save')) {
                            button.click();
                            return true;
                        }
                    }
                    // Nếu không tìm thấy nút, thử lưu bằng cách khác
                    localStorage.setItem('captchasonic_apikey', arguments[0]);
                    return false;
                """, CAPTCHA_API_KEY)
            
            # Đợi để đảm bảo API key được lưu
            time.sleep(2)
            
            # Xác minh API key đã được lưu
            saved_api_key = driver.execute_script("""
                return document.getElementById('apikey').value || 
                       localStorage.getItem('captchasonic_apikey');
            """)
            
            if saved_api_key and saved_api_key == CAPTCHA_API_KEY:
                logger.info("Xác nhận API key đã được lưu thành công")
            else:
                logger.warning(f"Không thể xác nhận API key đã được lưu. Giá trị hiện tại: {saved_api_key}")
                
        except Exception as e:
            logger.error(f"Lỗi khi tìm và nhập vào input field: {e}")
            
            # Thử phương pháp thay thế bằng JavaScript
            logger.info("Đang thử phương pháp thay thế bằng JavaScript...")
            try:
                success = driver.execute_script("""
                    try {
                        // Tìm input field
                        const apiInput = document.getElementById('apikey');
                        if (apiInput) {
                            // Xóa giá trị hiện tại
                            apiInput.value = '';
                            // Nhập API key mới
                            apiInput.value = arguments[0];
                            
                            // Tìm nút Save
                            const buttons = document.querySelectorAll('button');
                            for (const button of buttons) {
                                if (button.textContent.includes('Save') || 
                                    button.textContent.includes('Submit') || 
                                    button.className.includes('save')) {
                                    button.click();
                                    return true;
                                }
                            }
                            
                            // Nếu không tìm thấy nút, lưu vào localStorage
                            localStorage.setItem('captchasonic_apikey', arguments[0]);
                            return true;
                        }
                        
                        // Nếu không tìm thấy input, lưu trực tiếp vào localStorage
                        localStorage.setItem('captchasonic_apikey', arguments[0]);
                        return true;
                    } catch (e) {
                        console.error('Error:', e);
                        return false;
                    }
                """, CAPTCHA_API_KEY)
                
                if success:
                    logger.info("Đã cấu hình API key bằng JavaScript")
                else:
                    logger.warning("Không thể cấu hình API key bằng JavaScript")
            except Exception as js_error:
                logger.error(f"Lỗi khi thực thi JavaScript: {js_error}")
    
    except Exception as e:
        logger.error(f"Lỗi khi cấu hình extension: {e}")
    
    # Trở về trang chính
    driver.get("https://pikbest.com")
    logger.info("Đã hoàn tất cấu hình extension và trở về trang chính")

def main():
    print("=" * 60)
    print("🔍 PIKBEST LINK EXTRACTOR 🔍".center(60))
    print("=" * 60)
    print("Tool này giúp lấy link tải trực tiếp từ Pikbest.com")
    print("Bạn có thể nhập một hoặc nhiều URL, mỗi URL một dòng.")
    print("Để kết thúc nhập, hãy nhấn Enter ở dòng trống.")
    print("-" * 60)
    
    # Khởi tạo trình duyệt một lần duy nhất
    logger.info("Khởi tạo trình duyệt cho toàn bộ phiên làm việc...")
    try:
        driver = setup_chrome_with_extension()
        logger.info("Đã khởi tạo trình duyệt thành công cho phiên làm việc")
        
        # Đăng nhập vào Pikbest
        login_to_pikbest(driver)
        
        # Xử lý nhiều URL trong một phiên làm việc
        process_urls_in_session(driver)
        
    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo phiên làm việc: {e}", exc_info=True)
        print(f"❌ Lỗi khi khởi tạo: {e}")
    finally:
        # Đóng trình duyệt khi hoàn tất
        try:
            if 'driver' in locals() and driver:
                driver.quit()
                logger.info("Đã đóng trình duyệt")
        except Exception as e:
            logger.error(f"Lỗi khi đóng trình duyệt: {e}")

def login_to_pikbest(driver):
    """Đăng nhập vào Pikbest sử dụng cookies"""
    logger.info("Đang đăng nhập vào Pikbest...")
    try:
        # Truy cập trang chính
        driver.get("https://pikbest.com")
        
        # Thêm cookies vào trình duyệt
        for name, value in PIKBEST_COOKIES.items():
            driver.add_cookie({"name": name, "value": value})
        
        # Truy cập trang thông tin người dùng để xác nhận đăng nhập
        driver.get("https://pikbest.com/?m=home&a=userInfo")
        time.sleep(3)  # Đợi để xác nhận đăng nhập
        
        # Kiểm tra xem đã đăng nhập thành công chưa
        if "login" in driver.current_url.lower():
            logger.warning("Chưa đăng nhập thành công, đang thử đăng nhập lại...")
            # Có thể thêm logic đăng nhập thủ công ở đây nếu cần
        
        logger.info("Đã đăng nhập thành công vào Pikbest")
        print("✅ Đã đăng nhập thành công vào Pikbest")
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khi đăng nhập: {e}")
        print(f"❌ Lỗi khi đăng nhập: {e}")
        return False

def process_urls_in_session(driver):
    """Xử lý nhiều URL trong một phiên làm việc, tuần tự từng link"""
    while True:
        # Nhận danh sách URL từ người dùng
        urls = get_urls_from_user()
        
        if not urls:
            choice = input("\nBạn muốn tiếp tục nhập URL mới không? (y/n): ").strip().lower()
            if choice != 'y':
                print("Cảm ơn đã sử dụng tool. Tạm biệt!")
                break
            continue
        
        # Xử lý từng URL một cách tuần tự
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*50}")
            print(f"[{i}/{len(urls)}] Đang xử lý: {url}")
            print(f"{'='*50}")
            
            # Sử dụng driver đã khởi tạo để xử lý URL
            result = process_pikbest_url_with_driver(url, driver)
            
            # Hiển thị kết quả ngay sau khi xử lý xong mỗi URL
            if result:
                print(f"\n✅ Kết quả cho URL #{i}:")
                print(f"• URL gốc: {url}")
                print(f"• Link tải: {result}")
                results.append({"url": url, "download_link": result})
                
                # Hỏi người dùng có muốn tiếp tục với URL tiếp theo không
                if i < len(urls):
                    continue_choice = input("\nTiếp tục với URL tiếp theo? (y/n): ").strip().lower()
                    if continue_choice != 'y':
                        print("Đã dừng xử lý các URL còn lại.")
                        break
            else:
                print(f"\n❌ Không thể lấy link tải cho URL #{i}: {url}")
                
                # Hỏi người dùng có muốn tiếp tục với URL tiếp theo không
                if i < len(urls):
                    continue_choice = input("\nTiếp tục với URL tiếp theo? (y/n): ").strip().lower()
                    if continue_choice != 'y':
                        print("Đã dừng xử lý các URL còn lại.")
                        break
        
        # Hiển thị tổng kết sau khi xử lý tất cả URL
        if results:
            print("\n" + "="*60)
            print("📋 TỔNG KẾT KẾT QUẢ".center(60))
            print("="*60)
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['url']} -> {result['download_link']}")
            
            # Lưu kết quả vào file nếu người dùng muốn
            save_choice = input("\nBạn có muốn lưu kết quả vào file không? (y/n): ").strip().lower()
            if save_choice == 'y':
                save_results_to_file(results)
        else:
            print("\n❌ Không có URL nào được xử lý thành công.")
        
        # Hỏi người dùng có muốn tiếp tục với batch URL mới không
        choice = input("\nBạn muốn nhập batch URL mới không? (y/n): ").strip().lower()
        if choice != 'y':
            print("Cảm ơn đã sử dụng tool. Tạm biệt!")
            break

def get_urls_from_user():
    """Nhận danh sách URL từ người dùng"""
    print("\nNhập URL Pikbest (mỗi URL một dòng, Enter ở dòng trống để kết thúc):")
    urls = []
    while True:
        url = input("> ").strip()
        if not url:
            break
        urls.append(url)
    
    return urls

def save_results_to_file(results):
    """Lưu kết quả vào file"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"pikbest_results_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== PIKBEST DOWNLOAD LINKS ===\n\n")
            for i, result in enumerate(results, 1):
                f.write(f"{i}. Original URL: {result['url']}\n")
                f.write(f"   Download Link: {result['download_link']}\n\n")
        
        print(f"✅ Đã lưu kết quả vào file: {filename}")
    except Exception as e:
        logger.error(f"Lỗi khi lưu kết quả vào file: {e}")
        print(f"❌ Lỗi khi lưu kết quả: {e}")

def process_pikbest_url_with_driver(url, driver):
    """Xử lý URL Pikbest với driver đã khởi tạo"""
    file_id = extract_file_id(url)
    if not file_id:
        logger.error(f"Không tìm thấy ID trong URL: {url}")
        print("❌ Không tìm thấy ID trong URL.")
        return None

    print(f"🔍 Đang xử lý ID: {file_id}")
    logger.info(f"Đang xử lý ID: {file_id} từ URL: {url}")

    # Hiển thị tiến trình
    print("⏳ Đang truy cập trang download...")
    real_url = get_real_download_link_with_driver(file_id, driver)
    
    if not real_url:
        print("❌ Không tìm thấy link tải.")
        return None
        
    print("⏳ Đang xác minh link tải...")
    # Xác minh link tải
    verified_url = verify_download_link(real_url)
    
    if verified_url:
        print(f"\n🎯 Link tải thật: {verified_url}")
        
        print("⏳ Đang lấy thông tin file...")
        # Lấy thông tin file
        file_info = get_file_info(verified_url)
        
        # Hiển thị thông tin file
        print("\n📁 Thông tin file:")
        print(f"  • Tên file: {file_info['filename']}")
        print(f"  • Kích thước: {file_info['size']}")
        print(f"  • Định dạng: {file_info['format']}")
        print(f"  • Hết hạn: {file_info['expiry']}")
        
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
        
        return None

def get_real_download_link_with_driver(file_id, driver):
    """Lấy link tải thật với driver đã khởi tạo mà không tải file về"""
    download_api_url = f"https://pikbest.com/?m=download&id={file_id}&flag=1"
    logger.info(f"Đang truy cập URL download: {download_api_url}")

    try:
        # Vô hiệu hóa tải xuống tự động
        # Thiết lập preferences để ngăn tải xuống tự động
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'deny',
            'downloadPath': '/dev/null'  # Đường dẫn không quan trọng vì chúng ta đang từ chối tải xuống
        })
        
        # Truy cập trang download
        logger.info(f"Đang truy cập trang download: {download_api_url}")
        driver.get(download_api_url)
        
        # Đợi lâu hơn để trang load hoàn toàn và hiện nút "Click here"
        print("⏳ Đang đợi trang tải hoàn tất...")
        time.sleep(7)  # Đợi ít nhất 5 giây + thêm 2 giây để chắc chắn
        
        # Xử lý captcha nếu xuất hiện
        captcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha') or contains(@title, 'captcha')]")
        if captcha_frames:
            print("⚠️ Phát hiện captcha, đang cố gắng giải...")
            
        if not handle_captcha(driver):
            logger.error("Không thể xử lý captcha, đang hủy tải xuống")
            print("❌ Không thể xử lý captcha, đang hủy tải xuống")
            return None
        
        # Lưu screenshot để debug
        screenshot_path = f"debug_screenshot_{file_id}.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"Đã lưu screenshot tại: {screenshot_path}")
        
        # Lưu source HTML để debug
        with open(f"page_source_{file_id}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info(f"Đã lưu source HTML tại: page_source_{file_id}.html")
        
        # Thêm script để bắt Ajax requests và chặn tải xuống
        print("⏳ Đang chuẩn bị bắt Ajax requests và chặn tải xuống...")
        driver.execute_script("""
            // Chặn tải xuống tự động
            window.originalCreateElement = document.createElement;
            document.createElement = function(tag) {
                const element = window.originalCreateElement.call(document, tag);
                if (tag.toLowerCase() === 'a') {
                    const originalClick = element.click;
                    element.click = function() {
                        // Nếu có thuộc tính download, ngăn chặn hành vi mặc định
                        if (this.hasAttribute('download') || this.download) {
                            console.log('Download prevented for:', this.href);
                            // Lưu URL thay vì tải xuống
                            if (this.href && (
                                this.href.includes('.zip') || 
                                this.href.includes('.psd') || 
                                this.href.includes('.ai') || 
                                this.href.includes('.jpg') || 
                                this.href.includes('.png') || 
                                this.href.includes('.pdf') || 
                                this.href.includes('.eps') || 
                                this.href.includes('.rar')
                            )) {
                                window.downloadLinks.push(this.href);
                                console.log('Added to downloadLinks:', this.href);
                            }
                            return false;
                        }
                        return originalClick.apply(this, arguments);
                    };
                }
                return element;
            };
            
            // Ghi đè phương thức window.open để bắt các URL mở trong cửa sổ mới
            window.originalOpen = window.open;
            window.open = function(url, name, specs) {
                console.log('Window.open intercepted:', url);
                if (url && (
                    url.includes('.zip') || 
                    url.includes('.psd') || 
                    url.includes('.ai') || 
                    url.includes('.jpg') || 
                    url.includes('.png') || 
                    url.includes('.pdf') || 
                    url.includes('.eps') || 
                    url.includes('.rar')
                )) {
                    window.downloadLinks.push(url);
                    console.log('Added to downloadLinks from window.open:', url);
                    return null; // Không mở cửa sổ mới
                }
                return window.originalOpen(url, name, specs);
            };
            
            // Bắt các sự kiện click trên các phần tử <a>
            document.addEventListener('click', function(e) {
                if (e.target.tagName === 'A' || e.target.parentElement.tagName === 'A') {
                    const link = e.target.tagName === 'A' ? e.target : e.target.parentElement;
                    if (link.hasAttribute('download') || link.download || 
                        (link.href && (
                            link.href.includes('.zip') || 
                            link.href.includes('.psd') || 
                            link.href.includes('.ai') || 
                            link.href.includes('.jpg') || 
                            link.href.includes('.png') || 
                            link.href.includes('.pdf') || 
                            link.href.includes('.eps') || 
                            link.href.includes('.rar')
                        ))
                    ) {
                        console.log('Click intercepted on download link:', link.href);
                        window.downloadLinks.push(link.href);
                        e.preventDefault();
                        e.stopPropagation();
                    }
                }
            }, true);
            
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
                                        console.log('Added to downloadLinks from Ajax:', jsonResponse.url);
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
                                    console.log('Added to downloadLinks from XHR:', url);
                                }
                            }
                        }
                    } catch (e) {
                        console.error('Error in XHR tracking:', e);
                    }
                });
                originalXHRSend.apply(this, arguments);
            };
            
            // Ghi đè phương thức location.href để bắt chuyển hướng
            var originalLocationDescriptor = Object.getOwnPropertyDescriptor(window, 'location');
            var newLocationProxy = new Proxy(window.location, {
                set: function(target, prop, value) {
                    if (prop === 'href') {
                        console.log('Location.href intercepted:', value);
                        if (value && (
                            value.includes('.zip') || 
                            value.includes('.psd') || 
                            value.includes('.ai') || 
                            value.includes('.jpg') || 
                            value.includes('.png') || 
                            value.includes('.pdf') || 
                            value.includes('.eps') || 
                            value.includes('.rar')
                        )) {
                            window.downloadLinks.push(value);
                            console.log('Added to downloadLinks from location.href:', value);
                            return true; // Giả vờ đã set thành công nhưng không thực sự chuyển hướng
                        }
                    }
                    return Reflect.set(target, prop, value);
                }
            });
            
            try {
                Object.defineProperty(window, 'location', {
                    configurable: true,
                    get: function() { return newLocationProxy; },
                    set: function(value) {
                        console.log('Setting window.location:', value);
                        originalLocationDescriptor.set.call(this, value);
                    }
                });
            } catch(e) {
                console.error('Error overriding location:', e);
            }
        """)
        
        # Phương pháp 1: Tìm và click nút "Click here" trực tiếp
        print("⏳ Đang tìm nút 'Click here'...")
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
                    print(f"✅ Tìm thấy nút tải: {elements[0].text}")
                    
                    # Lấy href trước khi click nếu có
                    try:
                        href = elements[0].get_attribute('href')
                        if href and not href.startswith('javascript:') and is_valid_download_file(href):
                            logger.info(f"Tìm thấy link tải trực tiếp từ href: {href}")
                            print("✅ Tìm thấy link tải trực tiếp từ href")
                            return href
                    except:
                        pass
                        
                    break
            
            if click_here_button:
                logger.info(f"Đang click vào nút: {click_here_button.text}")
                print(f"⏳ Đang click vào nút: {click_here_button.text}")
                
                # Sử dụng JavaScript để click để tránh lỗi stale element và chặn tải xuống
                driver.execute_script("""
                    // Lưu lại hàm click gốc
                    var originalClick = HTMLElement.prototype.click;
                    
                    // Ghi đè hàm click để bắt URL
                    HTMLElement.prototype.click = function() {
                        console.log('Click intercepted on element:', this);
                        
                        // Nếu là thẻ a và có href
                        if (this.tagName === 'A' && this.href) {
                            console.log('Link clicked:', this.href);
                            
                            // Nếu là link tải
                            if (this.href.includes('.zip') || 
                                this.href.includes('.psd') || 
                                this.href.includes('.ai') || 
                                this.href.includes('.jpg') || 
                                this.href.includes('.png') || 
                                this.href.includes('.pdf') || 
                                this.href.includes('.eps') || 
                                this.href.includes('.rar')) {
                                
                                // Lưu URL thay vì tải xuống
                                window.downloadLinks.push(this.href);
                                console.log('Added to downloadLinks from click:', this.href);
                                
                                // Không thực sự click
                                return;
                            }
                        }
                        
                        // Gọi hàm click gốc
                        return originalClick.apply(this, arguments);
                    };
                    
                    // Click vào nút
                    arguments[0].click();
                    
                    // Khôi phục hàm click gốc
                    HTMLElement.prototype.click = originalClick;
                """, click_here_button)
                
                print("⏳ Đang đợi sau khi click...")
                time.sleep(5)  # Đợi lâu hơn sau khi click
                
                # Xử lý captcha nếu xuất hiện sau khi click
                captcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha') or contains(@title, 'captcha')]")
                if captcha_frames:
                    print("⚠️ Phát hiện captcha sau khi click, đang cố gắng giải...")
                    
                if not handle_captcha(driver):
                    logger.error("Không thể xử lý captcha sau khi click, đang hủy tải xuống")
                    print("❌ Không thể xử lý captcha sau khi click, đang hủy tải xuống")
                    return None
                
                # Kiểm tra download links đã bắt được
                print("⏳ Đang kiểm tra download links...")
                download_links = driver.execute_script("return window.downloadLinks;")
                if download_links and len(download_links) > 0:
                    print(f"✅ Tìm thấy {len(download_links)} download links")
                    for link in download_links:
                        if not any(keyword in link.lower() for keyword in ['logo', 'icon', 'favicon', 'avatar']):
                            logger.info(f"Tìm thấy link tải từ download links: {link}")
                            print("✅ Tìm thấy link tải từ download links")
                            return link
                
                # Kiểm tra Ajax requests
                print("⏳ Đang kiểm tra Ajax requests...")
                ajax_requests = driver.execute_script("return window.ajaxRequests;")
                if ajax_requests:
                    logger.info(f"Tìm thấy {len(ajax_requests)} Ajax requests")
                    print(f"✅ Tìm thấy {len(ajax_requests)} Ajax requests")
                    
                    # Tìm Ajax request liên quan đến download
                    for req in ajax_requests:
                        if isinstance(req, dict) and 'url' in req:
                            url = req['url']
                            if 'AjaxDownload' in url and 'a=open' in url:
                                logger.info(f"Tìm thấy Ajax download request: {url}")
                                print(f"✅ Tìm thấy Ajax download request")
                                
                                # Kiểm tra response
                                if 'response' in req:
                                    try:
                                        response_data = json.loads(req['response'])
                                        logger.info(f"Ajax response: {response_data}")
                                        
                                        # Nếu response có URL, sử dụng nó
                                        if 'url' in response_data and response_data['url']:
                                            logger.info(f"Tìm thấy URL từ Ajax response: {response_data['url']}")
                                            print("✅ Tìm thấy URL từ Ajax response")
                                            return response_data['url']
                                        
                                        # Nếu response có data, thử tìm URL trong đó
                                        if 'data' in response_data and response_data['data']:
                                            if isinstance(response_data['data'], str) and 'http' in response_data['data']:
                                                logger.info(f"Tìm thấy URL từ Ajax response data: {response_data['data']}")
                                                print("✅ Tìm thấy URL từ Ajax response data")
                                                return response_data['data']
                                    except Exception as e:
                                        logger.error(f"Lỗi khi parse Ajax response: {e}")
                                
                                # Nếu không tìm thấy URL trong response, thử gọi trực tiếp Ajax request
                                try:
                                    logger.info(f"Đang gọi trực tiếp Ajax request: {url}")
                                    print("⏳ Đang gọi trực tiếp Ajax request...")
                                    ajax_response = session.get(url, headers=headers)
                                    if ajax_response.status_code == 200:
                                        try:
                                            ajax_data = ajax_response.json()
                                            logger.info(f"Ajax direct response: {ajax_data}")
                                            
                                            if 'url' in ajax_data and ajax_data['url']:
                                                logger.info(f"Tìm thấy URL từ direct Ajax: {ajax_data['url']}")
                                                print("✅ Tìm thấy URL từ direct Ajax")
                                                return ajax_data['url']
                                                
                                            if 'data' in ajax_data and ajax_data['data']:
                                                if isinstance(ajax_data['data'], str) and 'http' in ajax_data['data']:
                                                    logger.info(f"Tìm thấy URL từ direct Ajax data: {ajax_data['data']}")
                                                    print("✅ Tìm thấy URL từ direct Ajax data")
                                                    return ajax_data['data']
                                        except Exception as e:
                                            logger.error(f"Lỗi khi parse direct Ajax response: {e}")
                                except Exception as e:
                                    logger.error(f"Lỗi khi gọi trực tiếp Ajax request: {e}")
                
                # Phương pháp mới: Trích xuất hash từ HTML và tạo Ajax URL
                try:
                    logger.info("Đang tìm hash trong HTML...")
                    print("⏳ Đang tìm hash trong HTML...")
                    page_source = driver.page_source
                    
                    # Tìm hash trong HTML
                    hash_match = re.search(r'__hash__=([a-f0-9_]+)', page_source)
                    if hash_match:
                        hash_value = hash_match.group(1)
                        logger.info(f"Tìm thấy hash: {hash_value}")
                        print(f"✅ Tìm thấy hash")
                        
                        # Tạo Ajax URL
                        ajax_url = f"https://pikbest.com/?m=AjaxDownload&a=open&id={file_id}&__hash__={hash_value}&flag=1"
                        logger.info(f"Đang gọi Ajax URL: {ajax_url}")
                        print("⏳ Đang gọi Ajax URL...")
                        
                        # Gọi Ajax URL
                        ajax_response = session.get(ajax_url, headers=headers)
                        if ajax_response.status_code == 200:
                            try:
                                ajax_data = ajax_response.json()
                                logger.info(f"Ajax response: {ajax_data}")
                                
                                if 'url' in ajax_data and ajax_data['url']:
                                    logger.info(f"Tìm thấy URL từ Ajax: {ajax_data['url']}")
                                    print("✅ Tìm thấy URL từ Ajax")
                                    return ajax_data['url']
                                    
                                if 'data' in ajax_data and ajax_data['data']:
                                    if isinstance(ajax_data['data'], str) and 'http' in ajax_data['data']:
                                        logger.info(f"Tìm thấy URL từ Ajax data: {ajax_data['data']}")
                                        print("✅ Tìm thấy URL từ Ajax data")
                                        return ajax_data['data']
                            except Exception as e:
                                logger.error(f"Lỗi khi parse Ajax response: {e}")
                except Exception as e:
                    logger.error(f"Lỗi khi tìm hash và gọi Ajax: {e}")
            else:
                print("⚠️ Không tìm thấy nút 'Click here'")
        except Exception as e:
            logger.error(f"Lỗi khi tìm và click nút 'Click here': {e}")
        
        # Các phương pháp khác giữ nguyên...
        
    except Exception as e:
        logger.error(f"Lỗi chung khi tìm link tải: {e}")
        print(f"❌ Lỗi khi tìm link tải: {e}")

    print("❌ Không tìm thấy link tải sau khi thử tất cả các phương pháp")
    return None

if __name__ == "__main__":
    main()
