from locust import HttpUser, task, between
import random

class DjangoWebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Wait time between tasks

    @task
    def home_page(self):
        self.client.get("/")

    @task
    def profile_detail(self):
        slugs = ['brooke-vasquez', 'ariana-ellis', 'lisa-parks']  # List of sample slugs, update it with real slugs
        self.client.get(f"/{random.choice(slugs)}/")

    @task
    def about_page(self):
        self.client.get("/about/")

    # @task
    # def socialaccount_connections(self):
    #     self.client.get("/accounts/3rdparty/")

    # @task
    # def socialaccount_login_cancelled(self):
    #     self.client.get("/accounts/3rdparty/login/cancelled/")

    # @task
    # def socialaccount_login_error(self):
    #     self.client.get("/accounts/3rdparty/login/error/")

    # @task
    # def socialaccount_signup(self):
    #     self.client.get("/accounts/3rdparty/signup/")

    # @task
    # def account_email_verification_sent(self):
    #     self.client.get("/accounts/confirm-email/")

    # # @task
    # # def account_confirm_email(self):
    # #     key = "samplekey"  # Replace with an actual key if required
    # #     self.client.get(f"/accounts/confirm-email/{key}/")

    # @task
    # def account_email(self):
    #     self.client.get("/accounts/email/")

    # @task
    # def github_login(self):
    #     self.client.get("/accounts/github/login/")

    # @task
    # def google_login(self):
    #     self.client.get("/accounts/google/login/")

    # @task
    # def google_login_by_token(self):
    #     self.client.get("/accounts/google/login/token/")

    # @task
    # def account_inactive(self):
    #     self.client.get("/accounts/inactive/")

    # @task
    # def account_login(self):
    #     self.client.get("/accounts/login/")

    # @task
    # def account_confirm_login_code(self):
    #     self.client.get("/accounts/login/code/confirm/")

    # @task
    # def account_logout(self):
    #     self.client.get("/accounts/logout/")

    # @task
    # def account_change_password(self):
    #     self.client.get("/accounts/password/change/")

    # @task
    # def account_reset_password(self):
    #     self.client.get("/accounts/password/reset/")

    # @task
    # def account_reset_password_done(self):
    #     self.client.get("/accounts/password/reset/done/")

    # # @task
    # # def account_reset_password_from_key(self):
    # #     uidb36 = "sampleuidb36"  # Replace with a real uid
    # #     key = "samplekey"  # Replace with a real key
    # #     self.client.get(f"/accounts/password/reset/key/{uidb36}-{key}/")

    # @task
    # def account_set_password(self):
    #     self.client.get("/accounts/password/set/")

    # @task
    # def account_reauthenticate(self):
    #     self.client.get("/accounts/reauthenticate/")

    # @task
    # def account_signup(self):
    #     self.client.get("/accounts/signup/")

    # @task
    # def student_profile(self):
    #     self.client.get("/accounts/student-profile/")

    # @task
    # def edit_student_profile(self):
    #     self.client.get("/accounts/student-profile/edit/")

    # @task
    # def student_request(self):
    #     self.client.get("/accounts/student-request/")

    # @task
    # def student_request_status(self):
    #     self.client.get("/accounts/student-request/status/")

    # @task
    # def admin_index(self):
    #     self.client.get("/admin/")

    # @task
    # def admin_user_changelist(self):
    #     self.client.get("/admin/auth/user/")

    # @task
    # def admin_user_add(self):
    #     self.client.get("/admin/auth/user/add/")

    # @task
    # def news_category(self):
    #     self.client.get("/admin/news/category/")

    # @task
    # def admin_news_news(self):
    #     self.client.get("/admin/news/news/")

    # @task
    # def admin_socialaccount(self):
    #     self.client.get("/admin/socialaccount/socialaccount/")

    @task
    def contact(self):
        self.client.get("/contact/")

    @task
    def contact_success(self):
        self.client.get("/contact/success/")

    @task
    def dashboard(self):
        self.client.get("/dashboard/")

    @task
    def post_list(self):
        self.client.get("/dashboard/posts/")

    @task
    def news_list(self):
        self.client.get("/news/")

    @task
    def news_detail(self):
        slugs = ['the-football-news-show-1', 'the-best-backpacking-water-filters-of-2025-tested-and-reviewed', 'whats-behind-trumps-u-turn-on-tariffs']  # List of sample slugs, update it with real slugs
        self.client.get(f"/news/{random.choice(slugs)}/")

    @task
    def news_search(self):
        self.client.get("/news/search/")

    @task
    def profiles(self):
        self.client.get("/profiles/")

    @task
    def sitemap(self):
        self.client.get("/sitemap.xml")

    @task
    def robots_txt(self):
        self.client.get("/robots.txt")

    @task
    def static_file(self):
        self.client.get("/static/profile_pictures/default.png")  # Replace with a real static file path
