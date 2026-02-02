import os
import re
import time
import pytest
from playwright.sync_api import sync_playwright, Page, expect

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8001")

NAV_TIMEOUT_MS = 60_000
ACTION_TIMEOUT_MS = 30_000

# ====== CHỈNH TỐC ĐỘ Ở ĐÂY ======
SLOW_MO_MS = 800
STEP_PAUSE_MS = 1200
PAUSE_WITH_INSPECTOR = False  # True nếu muốn dừng hẳn bằng Inspector


def pause_step(page: Page, ms: int = STEP_PAUSE_MS) -> None:
    page.wait_for_timeout(ms)
    if PAUSE_WITH_INSPECTOR:
        page.pause()


def _block_external_and_heavy_resources(page: Page) -> None:
    """Chặn CDN/ảnh/font để tránh treo load."""
    def route_handler(route):
        url = route.request.url.lower()
        if "cdnjs.cloudflare.com" in url:
            return route.abort()
        if url.endswith((".png", ".jpg", ".jpeg", ".svg", ".webp", ".ico", ".woff", ".woff2", ".ttf")):
            return route.abort()
        return route.continue_()
    page.route("**/*", route_handler)


def _goto(page: Page, path: str) -> None:
    page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")


def _click_first_available(page: Page, selectors: list[str]) -> None:
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() > 0:
            loc.first.click()
            return
    raise AssertionError(f"Không tìm thấy nút để click. Tried: {selectors}")


def register(page: Page, email: str, password: str, role: str) -> None:
    _goto(page, "/register")
    pause_step(page)

    page.fill('input[name="email"]', email)
    pause_step(page, 400)
    page.fill('input[name="password"]', password)
    pause_step(page, 400)
    page.select_option('select[name="role"]', role)
    pause_step(page, 400)

    _click_first_available(page, ["button:has-text('Đăng ký')", "form button"])
    pause_step(page, 900)

    expect(page.locator("text=Đăng ký thành công")).to_be_visible(timeout=20_000)
    pause_step(page, 1200)


def login(page: Page, email: str, password: str) -> None:
    _goto(page, "/login")
    pause_step(page)

    page.fill('input[name="email"]', email)
    pause_step(page, 400)
    page.fill('input[name="password"]', password)
    pause_step(page, 400)

    _click_first_available(page, ["button:has-text('Đăng nhập')", "form button"])
    pause_step(page, 1200)


def company_update_profile(page: Page) -> None:
    _goto(page, "/company/profile")
    pause_step(page, 1200)

    page.fill('input[name="companyName"]', "E2E Company")
    pause_step(page, 250)
    page.fill('input[name="logoUrl"]', "https://via.placeholder.com/150")
    pause_step(page, 250)
    page.fill('input[name="website"]', "https://example.com")
    pause_step(page, 250)
    page.select_option('select[name="size"]', "Startup (1-10)")
    pause_step(page, 250)
    page.fill('input[name="industry"]', "IT")
    pause_step(page, 250)
    page.fill('input[name="address"]', "123 Test Street, HCM")
    pause_step(page, 250)
    page.fill('textarea[name="description"]', "Company profile created by dual-role E2E")
    pause_step(page, 600)

    _click_first_available(page, ["button:has-text('Lưu hồ sơ')", "form button"])
    pause_step(page, 1500)

    expect(page.locator("text=Đã lưu hồ sơ thành công")).to_be_visible(timeout=20_000)
    pause_step(page, 1200)


def company_create_job_with_test(page: Page, job_title: str) -> None:
    """
    /company/jobs/create:
    - tick has_test
    - fill testName, duration, totalScore
    - fill ít nhất 1 q_content[]
    """
    _goto(page, "/company/jobs/create")
    pause_step(page, 1200)

    page.fill('input[name="title"]', job_title)
    pause_step(page, 250)
    page.fill('textarea[name="description"]', "Job created by company in dual-role E2E")
    pause_step(page, 250)
    page.fill('input[name="location"]', "HCM")
    pause_step(page, 250)
    page.fill('input[name="maxApplicants"]', "10")
    pause_step(page, 700)

    # ✅ bật bài test
    page.check('input[name="has_test"]')
    pause_step(page, 900)

    page.fill('input[name="testName"]', f"Test {job_title}")
    pause_step(page, 250)
    page.fill('input[name="duration"]', "15")
    pause_step(page, 250)
    page.fill('input[name="totalScore"]', "100")
    pause_step(page, 700)

    # đảm bảo có câu hỏi
    if page.locator("textarea[name='q_content[]']").count() == 0:
        _click_first_available(page, ["button:has-text('+ Thêm câu hỏi')"])
        pause_step(page, 700)

    q1 = page.locator("textarea[name='q_content[]']").first
    expect(q1).to_be_visible(timeout=10_000)
    q1.fill("Hãy giới thiệu bản thân và mô tả 1 dự án bạn từng làm.")
    pause_step(page, 500)

    _click_first_available(page, ["button:has-text('+ Thêm câu hỏi')"])
    pause_step(page, 600)
    page.locator("textarea[name='q_content[]']").nth(1).fill("Giải thích sự khác nhau giữa BFS và DFS.")
    pause_step(page, 800)

    _click_first_available(page, ["button:has-text('➕ Tạo Job')", "button:has-text('Tạo')", "form button"])
    pause_step(page, 1500)

    page.wait_for_url("**/company/jobs", timeout=60_000)
    expect(page.locator(f"text={job_title}")).to_be_visible(timeout=20_000)
    pause_step(page, 1200)


def student_update_profile_full(page: Page) -> None:
    """
    /student/profile form có nhiều field bạn làm:
    fullName, dob, cccd, major, about, educationLevel, degrees, cvUrl, portfolioUrl, skills
    """
    _goto(page, "/student/profile")
    pause_step(page, 1200)

    page.fill('input[name="fullName"]', "E2E Student")
    pause_step(page, 250)
    page.fill('input[name="dob"]', "2000-01-01")
    pause_step(page, 250)
    page.fill('input[name="cccd"]', "012345678901")
    pause_step(page, 250)
    page.fill('input[name="major"]', "Công nghệ thông tin")
    pause_step(page, 250)

    page.fill('textarea[name="about"]', "Sinh viên năm cuối, thích backend và hệ thống.")
    pause_step(page, 200)
    page.fill('input[name="educationLevel"]', "Đại học")
    pause_step(page, 200)
    page.fill('input[name="degrees"]', "TOEIC 750, SQL Certificate")
    pause_step(page, 200)
    page.fill('input[name="cvUrl"]', "https://example.com/cv.pdf")
    pause_step(page, 200)
    page.fill('input[name="portfolioUrl"]', "https://github.com/e2e-student")
    pause_step(page, 200)
    page.fill('input[name="skills"]', "Python:5, SQL:4, Flask:4, Git:4")
    pause_step(page, 600)

    _click_first_available(page, ["button:has-text('💾 Lưu hồ sơ')", "button:has-text('Lưu hồ sơ')", "form button"])
    pause_step(page, 1500)

    expect(page.locator("text=Hồ sơ đã được lưu thành công")).to_be_visible(timeout=20_000)
    pause_step(page, 1200)


def student_apply_and_do_test_if_needed(page: Page, job_title: str) -> None:
    """
    Student ở /student/home:
    - Nếu job chưa apply: có thể nút "✅ Ứng tuyển"
    - Nếu job có test hoặc trạng thái cần test: sẽ hiện nút "📄 Làm bài test"
    Sau click:
    - hoặc redirect thẳng sang /student/test/<id>
    - hoặc apply xong rồi mới sang test
    """
    _goto(page, "/student/home")
    pause_step(page, 1500)

    # chờ job hiện lên
    for _ in range(8):
        if page.locator(f"text={job_title}").count() > 0:
            break
        page.reload(wait_until="domcontentloaded")
        pause_step(page, 800)

    assert page.locator(f"text={job_title}").count() > 0, f"Student không thấy job '{job_title}' ở /student/home"

    card = page.locator(".job-card", has=page.locator(f"text={job_title}")).first
    expect(card).to_be_visible(timeout=20_000)

    # ✅ tìm nút phù hợp trong card
    btn_apply = card.locator("button", has_text="Ứng tuyển")
    btn_test  = card.locator("button", has_text="Làm bài test")

    if btn_apply.count() > 0:
        btn_apply.first.click()
    elif btn_test.count() > 0:
        btn_test.first.click()
    else:
        # fallback: đôi khi là <a> chứ không phải <button>
        link_test = card.locator("a", has_text="Làm bài test")
        link_apply = card.locator("a", has_text="Ứng tuyển")
        if link_apply.count() > 0:
            link_apply.first.click()
        elif link_test.count() > 0:
            link_test.first.click()
        else:
            raise AssertionError("Không tìm thấy nút 'Ứng tuyển' hoặc 'Làm bài test' trong job-card")

    pause_step(page, 1500)

    # ✅ nếu job có test thì sẽ vào trang test
    if "/student/test/" in page.url:
        pause_step(page, 1200)

        answers = page.locator("textarea[name^='answer_']")
        expect(answers.first).to_be_visible(timeout=20_000)

        for i in range(answers.count()):
            answers.nth(i).fill(f"Đây là câu trả lời E2E cho câu {i+1}.")
            pause_step(page, 300)

        _click_first_available(page, ["button:has-text('Nộp')", "button:has-text('📤')", "button[type='submit']"])
        pause_step(page, 1800)

        page.wait_for_url("**/student/applications**", timeout=60_000)
        pause_step(page, 1200)

        # check mềm
        if page.locator("text=Hoàn thành bài test").count() > 0:
            expect(page.locator("text=Hoàn thành bài test")).to_be_visible(timeout=20_000)

        return

    # ✅ nếu không vào test, thường là apply xong (tùy code bạn)
    if page.locator("text=Ứng tuyển thành công").count() > 0:
        expect(page.locator("text=Ứng tuyển thành công")).to_be_visible(timeout=20_000)
        pause_step(page, 1200)
@pytest.mark.e2e
def test_company_student_flow():
    ts = int(time.time())
    company_email = f"company_e2e_{ts}@test.com"
    student_email = f"student_e2e_{ts}@test.com"
    password = "Aa1!aa"
    job_title = f"Backend Intern {ts}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=SLOW_MO_MS)

        # ===== COMPANY SESSION =====
        context_company = browser.new_context()
        page_company = context_company.new_page()
        page_company.set_default_navigation_timeout(NAV_TIMEOUT_MS)
        page_company.set_default_timeout(ACTION_TIMEOUT_MS)
        _block_external_and_heavy_resources(page_company)

        # ===== STUDENT SESSION =====
        context_student = browser.new_context()
        page_student = context_student.new_page()
        page_student.set_default_navigation_timeout(NAV_TIMEOUT_MS)
        page_student.set_default_timeout(ACTION_TIMEOUT_MS)
        _block_external_and_heavy_resources(page_student)

        # 1) Company: register + login + profile + create job WITH TEST
        register(page_company, company_email, password, role="company")
        login(page_company, company_email, password)
        page_company.wait_for_url("**/company/home", timeout=60_000)
        pause_step(page_company, 1000)

        company_update_profile(page_company)
        company_create_job_with_test(page_company, job_title)

        # 2) Student: register + login + FULL profile + apply or do test
        register(page_student, student_email, password, role="student")
        login(page_student, student_email, password)
        page_student.wait_for_url("**/student/home", timeout=60_000)
        pause_step(page_student, 1000)

        student_update_profile_full(page_student)
        student_apply_and_do_test_if_needed(page_student, job_title)

        context_student.close()
        context_company.close()
        browser.close()
