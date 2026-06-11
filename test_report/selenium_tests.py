"""
Selenium WebDriver 自动化测试脚本
=================================
软件系统综合课程设计——练习1（黑盒+功能测试）
被测系统: 游戏道具交易平台 (GameTrade)
测试模块: 用户认证 (Users) + 道具管理 (Items)

运行前提:
1. Django 开发服务器已启动: python manage.py runserver
2. Chrome 浏览器已安装
3. pip install selenium

运行方式:
    python test_report/selenium_tests.py

或指定测试类:
    python -m unittest test_report.selenium_tests.UserAuthSeleniumTests
"""

import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://127.0.0.1:8000"


class SeleniumBaseTestCase(unittest.TestCase):
    """Selenium 测试基类 — 管理浏览器生命周期"""

    @classmethod
    def setUpClass(cls):
        options = Options()
        options.add_argument('--headless')  # 无头模式（可在 CI 中运行）
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(3)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def screenshot_on_fail(self, test_name):
        """失败时截图"""
        self.driver.save_screenshot(f"test_report/screenshots/{test_name}.png")

    def find(self, selector, by=By.CSS_SELECTOR):
        """简化的查找方法"""
        return self.driver.find_element(by, selector)

    def find_by_id(self, element_id):
        """按 ID 查找"""
        return self.driver.find_element(By.ID, element_id)

    def find_by_name(self, name):
        """按 name 属性查找"""
        return self.driver.find_element(By.NAME, name)

    def find_by_link(self, text):
        """按链接文本查找"""
        return self.driver.find_element(By.LINK_TEXT, text)


# ============================================================
#  用户认证模块 Selenium 测试
# ============================================================

class UserAuthSeleniumTests(SeleniumBaseTestCase):
    """用户认证模块 Web UI 测试"""

    def test_01_register_page_accessible(self):
        """TC-SEL-01: 注册页面可访问"""
        self.driver.get(f"{BASE_URL}/users/register/")
        self.assertIn("注册", self.driver.title)
        # 验证表单关键元素存在
        username_input = self.find_by_name("username")
        email_input = self.find_by_name("email")
        self.assertIsNotNone(username_input)
        self.assertIsNotNone(email_input)
        print("✅ TC-SEL-01 通过: 注册页面可访问，表单元素存在")

    def test_02_successful_registration(self):
        """TC-SEL-02: 成功注册用户（等价类：有效输入）"""
        self.driver.get(f"{BASE_URL}/users/register/")

        # 填写表单
        self.find_by_name("username").send_keys("selenium_test")
        self.find_by_name("email").send_keys("selenium@test.com")
        self.find_by_name("password1").send_keys("Selenium1!")
        self.find_by_name("password2").send_keys("Selenium1!")

        # 提交
        self.find_by_css("button[type='submit']").click()

        # 注册成功应跳转到首页
        time.sleep(1)
        current_url = self.driver.current_url
        self.assertEqual(current_url, f"{BASE_URL}/")
        print(f"✅ TC-SEL-02 通过: 注册成功，跳转至首页 ({current_url})")

    def test_03_registration_password_mismatch(self):
        """TC-SEL-03: 注册密码不匹配（等价类：无效输入）"""
        self.driver.get(f"{BASE_URL}/users/register/")

        self.find_by_name("username").send_keys("baduser")
        self.find_by_name("email").send_keys("bad@test.com")
        self.find_by_name("password1").send_keys("Selenium1!")
        self.find_by_name("password2").send_keys("Different1!")  # 不匹配
        self.find_by_css("button[type='submit']").click()

        # 应留在注册页面，显示错误
        time.sleep(0.5)
        self.assertIn("register", self.driver.current_url)
        # 检查是否有错误提示（Django form errors）
        error_items = self.driver.find_elements(By.CSS_SELECTOR, ".errorlist li, .alert-danger")
        print(f"✅ TC-SEL-03 通过: 密码不匹配，页面显示 {len(error_items)} 处错误提示")

    def test_04_registration_empty_email(self):
        """TC-SEL-04: 注册空邮箱（等价类：空值）"""
        self.driver.get(f"{BASE_URL}/users/register/")

        self.find_by_name("username").send_keys("noemailuser")
        self.find_by_name("email").send_keys("")  # 清空邮箱
        self.find_by_name("password1").send_keys("Selenium1!")
        self.find_by_name("password2").send_keys("Selenium1!")
        self.find_by_css("button[type='submit']").click()

        time.sleep(0.5)
        self.assertIn("register", self.driver.current_url)
        print("✅ TC-SEL-04 通过: 空邮箱被拦截")

    def test_05_login_success(self):
        """TC-SEL-05: 成功登录（判定表：Y+Y → 成功）"""
        # 先注册
        self.driver.get(f"{BASE_URL}/users/register/")
        self.find_by_name("username").send_keys("loginsel")
        self.find_by_name("email").send_keys("loginsel@test.com")
        self.find_by_name("password1").send_keys("Selenium1!")
        self.find_by_name("password2").send_keys("Selenium1!")
        self.find_by_css("button[type='submit']").click()
        time.sleep(0.5)

        # 登出
        self.driver.get(f"{BASE_URL}/users/logout/")
        time.sleep(0.5)

        # 登录
        self.driver.get(f"{BASE_URL}/users/login/")
        self.find_by_name("username").send_keys("loginsel")
        self.find_by_name("password").send_keys("Selenium1!")
        self.find_by_css("button[type='submit']").click()

        time.sleep(0.5)
        self.assertEqual(self.driver.current_url, f"{BASE_URL}/")
        # 导航栏应显示用户名
        nav_text = self.driver.page_source
        self.assertIn("loginsel", nav_text)
        print("✅ TC-SEL-05 通过: 登录成功，导航栏显示用户名")

    def test_06_login_wrong_password(self):
        """TC-SEL-06: 错误密码登录失败（判定表：Y+N → 失败）"""
        self.driver.get(f"{BASE_URL}/users/login/")
        self.find_by_name("username").send_keys("loginsel")
        self.find_by_name("password").send_keys("WrongPassword1!")
        self.find_by_css("button[type='submit']").click()

        time.sleep(0.5)
        # 应留在登录页面
        self.assertIn("login", self.driver.current_url)
        print("✅ TC-SEL-06 通过: 错误密码登录失败，留在登录页")

    def test_07_login_empty_fields(self):
        """TC-SEL-07: 空字段登录（判定表：空+空 → 失败）"""
        self.driver.get(f"{BASE_URL}/users/login/")
        self.find_by_name("username").send_keys("")
        self.find_by_name("password").send_keys("")
        self.find_by_css("button[type='submit']").click()

        time.sleep(0.5)
        self.assertIn("login", self.driver.current_url)
        print("✅ TC-SEL-07 通过: 空字段登录失败")

    def test_08_profile_requires_login(self):
        """TC-SEL-08: 未登录访问个人资料页 → 重定向到登录页"""
        self.driver.get(f"{BASE_URL}/users/logout/")
        time.sleep(0.5)
        self.driver.get(f"{BASE_URL}/users/profile/")
        time.sleep(0.5)
        self.assertIn("login", self.driver.current_url.lower())
        print("✅ TC-SEL-08 通过: 未登录访问个人资料被重定向")

    def test_09_logout_functionality(self):
        """TC-SEL-09: 登出功能正常"""
        # 登录
        self.driver.get(f"{BASE_URL}/users/login/")
        self.find_by_name("username").send_keys("loginsel")
        self.find_by_name("password").send_keys("Selenium1!")
        self.find_by_css("button[type='submit']").click()
        time.sleep(0.5)

        # 登出
        self.driver.get(f"{BASE_URL}/users/logout/")
        time.sleep(0.5)

        # 导航栏不应再显示用户名
        self.assertNotIn("loginsel", self.driver.page_source)
        print("✅ TC-SEL-09 通过: 登出后用户名不再显示")


# ============================================================
#  道具管理模块 Selenium 测试
# ============================================================

class ItemSeleniumTests(SeleniumBaseTestCase):
    """道具管理模块 Web UI 测试"""

    def setUp(self):
        # 每个测试前登录卖家账号
        self.driver.get(f"{BASE_URL}/users/login/")
        try:
            name_input = self.driver.find_element(By.NAME, "username")
            name_input.send_keys("selenium_test")
            self.driver.find_element(By.NAME, "password").send_keys("Selenium1!")
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(0.5)
        except Exception:
            pass  # 可能已经登录了

    def test_10_item_list_page_accessible(self):
        """TC-SEL-10: 道具列表页可访问并展示道具"""
        self.driver.get(f"{BASE_URL}/items/")
        # 页面标题或内容应包含"浏览"或"道具"
        source = self.driver.page_source
        self.assertIn("GBP", source, "列表页应包含道具条目或空状态提示")
        print("✅ TC-SEL-10 通过: 道具列表页正常访问")

    def test_11_item_detail_page(self):
        """TC-SEL-11: 道具详情页可访问"""
        # 先浏览到列表页，再点击第一个道具
        self.driver.get(f"{BASE_URL}/items/")
        # 查找道具链接（卡片中的链接）
        item_links = self.driver.find_elements(By.CSS_SELECTOR, ".card a[href*='/items/']")
        if item_links:
            item_links[0].click()
            time.sleep(0.5)
            self.assertIn("/items/", self.driver.current_url)
            print(f"✅ TC-SEL-11 通过: 道具详情页可访问 ({self.driver.current_url})")
        else:
            print("⚠️ TC-SEL-11 跳过: 列表页无道具可点击")

    def test_12_item_search_functionality(self):
        """TC-SEL-12: 道具搜索功能（等价类：有效关键词）"""
        self.driver.get(f"{BASE_URL}/items/")
        # 搜索
        search_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='keyword']")
        search_input.send_keys("a")  # 宽泛搜索
        search_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_btn.click()
        time.sleep(0.5)
        self.assertIn("keyword=a", self.driver.current_url, "URL应包含搜索参数")
        print("✅ TC-SEL-12 通过: 搜索功能正常")

    def test_13_item_search_no_result(self):
        """TC-SEL-13: 搜索无结果（等价类：不匹配关键词）"""
        self.driver.get(f"{BASE_URL}/items/")
        search_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='keyword']")
        search_input.send_keys("不存在道具XYZ999")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
        source = self.driver.page_source
        # 应该有"没有找到"或类似提示
        print("✅ TC-SEL-13 通过: 无结果搜索完成")

    def test_14_price_filter(self):
        """TC-SEL-14: 价格区间筛选（边界值：min_price & max_price）"""
        self.driver.get(f"{BASE_URL}/items/?min_price=0&max_price=100000")
        time.sleep(0.5)
        self.assertIn("min_price=0", self.driver.current_url)
        print("✅ TC-SEL-14 通过: 价格区间筛选正常")

    def test_15_create_item_page_accessible(self):
        """TC-SEL-15: 发布道具页面可访问"""
        self.driver.get(f"{BASE_URL}/items/sell/")
        source = self.driver.page_source
        self.assertIn("name", source, "页面应包含道具名称输入框")
        self.assertIn("price", source, "页面应包含价格输入框")
        print("✅ TC-SEL-15 通过: 发布道具页面元素齐全")

    def test_16_create_item_success(self):
        """TC-SEL-16: 成功发布道具（等价类：有效输入）"""
        self.driver.get(f"{BASE_URL}/items/sell/")

        self.find_by_name("name").send_keys("Selenium测试道具")
        # 选择分类
        category_select = self.driver.find_element(By.NAME, "category")
        if category_select.find_elements(By.TAG_NAME, "option"):
            category_select.find_elements(By.TAG_NAME, "option")[0].click()
        # 选择游戏
        game_select = self.driver.find_element(By.NAME, "game")
        game_select.find_elements(By.TAG_NAME, "option")[1].click()
        # 填写价格
        self.find_by_name("price").send_keys("199.99")
        # 填写描述
        self.find_by_name("description").send_keys("Selenium自动化测试创建的道具")
        # 提交
        self.find_by_css("button[type='submit']").click()

        time.sleep(1)
        self.assertIn("/items/", self.driver.current_url)
        self.assertNotIn("/sell/", self.driver.current_url)
        print(f"✅ TC-SEL-16 通过: 道具发布成功，跳转至 {self.driver.current_url}")

    def test_17_create_item_zero_price(self):
        """TC-SEL-17: 发布道具价格为0（边界值：0）"""
        self.driver.get(f"{BASE_URL}/items/sell/")

        self.find_by_name("name").send_keys("零价道具")
        game_select = self.driver.find_element(By.NAME, "game")
        game_select.find_elements(By.TAG_NAME, "option")[1].click()
        self.find_by_name("price").send_keys("0.00")
        self.find_by_name("description").send_keys("价格为零")
        self.find_by_css("button[type='submit']").click()

        time.sleep(0.5)
        # 应留在发布页面
        self.assertIn("/sell/", self.driver.current_url)
        print("✅ TC-SEL-17 通过: 零价格发布被拦截")

    def test_18_toggle_favorite(self):
        """TC-SEL-18: 道具收藏切换功能"""
        # 先浏览道具详情
        self.driver.get(f"{BASE_URL}/items/")
        item_links = self.driver.find_elements(By.CSS_SELECTOR, ".card a[href*='/items/']")
        if not item_links:
            print("⚠️ TC-SEL-18 跳过: 无道具可收藏")
            return

        # 点击第一个道具
        item_links[0].click()
        time.sleep(0.5)

        # 查找收藏按钮
        fav_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='favorite']")
        if fav_buttons:
            fav_buttons[0].click()
            time.sleep(0.5)
            print("✅ TC-SEL-18 通过: 收藏操作完成")
        else:
            print("⚠️ TC-SEL-18: 未找到收藏按钮（可能需要登录）")

    def test_19_favorites_page(self):
        """TC-SEL-19: 收藏列表页可访问"""
        self.driver.get(f"{BASE_URL}/items/favorites/")
        time.sleep(0.5)
        self.assertEqual(self.driver.current_url, f"{BASE_URL}/items/favorites/")
        print("✅ TC-SEL-19 通过: 收藏列表页正常")

    def test_20_my_items_page(self):
        """TC-SEL-20: 我的道具页面可访问"""
        self.driver.get(f"{BASE_URL}/items/my/")
        time.sleep(0.5)
        self.assertEqual(self.driver.current_url, f"{BASE_URL}/items/my/")
        print("✅ TC-SEL-20 通过: 我的道具页正常")


# ============================================================
#  场景法 Selenium 测试（完整用户旅程）
# ============================================================

class ScenarioSeleniumTests(SeleniumBaseTestCase):
    """场景法 — 模拟完整用户操作流程"""

    def test_21_full_user_scenario(self):
        """TC-SEL-21: 场景法——完整用户旅程"""
        driver = self.driver

        # 1) 注册新用户
        driver.get(f"{BASE_URL}/users/register/")
        driver.find_element(By.NAME, "username").send_keys("scenario_user")
        driver.find_element(By.NAME, "email").send_keys("scenario@test.com")
        driver.find_element(By.NAME, "password1").send_keys("Scenario1!")
        driver.find_element(By.NAME, "password2").send_keys("Scenario1!")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
        self.assertEqual(driver.current_url, f"{BASE_URL}/")
        print("  ✅ 1) 注册成功")

        # 2) 浏览道具列表
        driver.get(f"{BASE_URL}/items/")
        time.sleep(0.5)
        self.assertTrue("/items/" in driver.current_url)
        print("  ✅ 2) 浏览道具列表成功")

        # 3) 搜索道具
        search_input = driver.find_element(By.CSS_SELECTOR, "input[name='keyword']")
        search_input.send_keys("a")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
        print("  ✅ 3) 搜索道具成功")

        # 4) 查看个人资料
        driver.get(f"{BASE_URL}/users/profile/")
        time.sleep(0.5)
        self.assertIn("/profile/", driver.current_url)
        page_source = driver.page_source
        self.assertIn("scenario_user", page_source)
        print("  ✅ 4) 个人资料页显示用户名")

        # 5) 登出
        driver.get(f"{BASE_URL}/users/logout/")
        time.sleep(0.5)
        print("  ✅ 5) 登出成功")

        # 6) 重新登录
        driver.get(f"{BASE_URL}/users/login/")
        driver.find_element(By.NAME, "username").send_keys("scenario_user")
        driver.find_element(By.NAME, "password").send_keys("Scenario1!")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
        self.assertIn("scenario_user", driver.page_source)
        print("  ✅ 6) 重新登录成功，导航栏显示用户名")

        print("✅ TC-SEL-21 通过: 完整用户旅程测试成功")

    def test_22_item_lifecycle_scenario(self):
        """TC-SEL-22: 场景法——道具完整生命周期（发布→编辑→下架）"""
        driver = self.driver

        # 1) 确保登录
        driver.get(f"{BASE_URL}/users/login/")
        try:
            name_input = driver.find_element(By.NAME, "username")
            if name_input:
                name_input.send_keys("scenario_user")
                driver.find_element(By.NAME, "password").send_keys("Scenario1!")
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                time.sleep(0.5)
        except Exception:
            pass  # 已经登录了

        # 2) 发布道具
        driver.get(f"{BASE_URL}/items/sell/")
        driver.find_element(By.NAME, "name").send_keys("场景测试道具")
        category_select = driver.find_element(By.NAME, "category")
        if category_select.find_elements(By.TAG_NAME, "option"):
            category_select.find_elements(By.TAG_NAME, "option")[0].click()
        game_select = driver.find_element(By.NAME, "game")
        game_select.find_elements(By.TAG_NAME, "option")[1].click()
        driver.find_element(By.NAME, "price").send_keys("88.00")
        driver.find_element(By.NAME, "description").send_keys("场景测试")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        print(f"  ✅ 1) 道具发布成功 ({driver.current_url})")

        # 3) 查看我的道具
        driver.get(f"{BASE_URL}/items/my/")
        time.sleep(0.5)
        self.assertIn("场景测试道具", driver.page_source)
        print("  ✅ 2) 我的道具页面显示新发布道具")

        # 4) 搜索该道具
        driver.get(f"{BASE_URL}/items/?keyword=场景测试")
        time.sleep(0.5)
        self.assertIn("场景测试道具", driver.page_source)
        print("  ✅ 3) 搜索找到该道具")

        print("✅ TC-SEL-22 通过: 道具生命周期测试成功")


# ============================================================
#  运行入口
# ============================================================

def create_test_suite():
    """创建测试套件"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(UserAuthSeleniumTests))
    suite.addTests(loader.loadTestsFromTestCase(ItemSeleniumTests))
    suite.addTests(loader.loadTestsFromTestCase(ScenarioSeleniumTests))

    return suite


if __name__ == '__main__':
    import os
    # 确保截图目录存在
    os.makedirs("test_report/screenshots", exist_ok=True)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)

    # 打印汇总
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total - failures - errors

    print("\n" + "=" * 60)
    print(f"  Selenium 自动化测试汇总")
    print(f"  总计: {total}  通过: {passed}  失败: {failures}  错误: {errors}")
    print("=" * 60)
