import pygame, requests, json, sys, time
from pygame.locals import *

# Configuration
API_URL = "https://rse-api.com:5002"
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BLACK, WHITE, BLUE, RED = (0, 0, 0), (255, 255, 255), (0, 100, 200), (200, 0, 0)
FONT_SIZE = 24
BUTTON_HEIGHT = 40
TEXT_INPUT_HEIGHT = 35

# Initialize pygame
pygame.init()
font = pygame.font.SysFont('Arial', FONT_SIZE)

# Global variables
AUTH_TOKEN = None
USERNAME = None
current_screen = None

# Utility function for API requests
def api_request(endpoint, method='GET', data=None):
    headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}
    url = f"{API_URL}{endpoint}"
    try:
        response = requests.request(method, url, headers=headers, json=data) if method == 'POST' else requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

# Core UI classes
class InputBox:
    def __init__(self, x, y, w, h, text='', password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.password = password
        self.active = False
        self.render_text()

    def render_text(self):
        display = '*' * len(self.text) if self.password else self.text
        self.txt_surface = font.render(display, True, BLACK)

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == KEYDOWN and self.active:
            if event.key == K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key != K_RETURN:
                self.text += event.unicode
            self.render_text()
            return event.key == K_RETURN
        return False

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, BLUE if self.active else BLACK, self.rect, 2)

class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback

    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)
        txt = font.render(self.text, True, WHITE)
        screen.blit(txt, (self.rect.x + (self.rect.w - txt.get_width()) // 2,
                          self.rect.y + (self.rect.h - txt.get_height()) // 2))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()

class Screen:
    def __init__(self, title):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(title)
        self.title = title
        self.buttons = []
        self.input_boxes = []
        self.message = ""
        self.next_screen = None

    def set_next_screen(self, screen):
        self.next_screen = screen

    def draw(self):
        self.screen.fill(WHITE)
        title = font.render(self.title, True, BLACK)
        self.screen.blit(title, (20, 20))
        if AUTH_TOKEN:
            self.screen.blit(font.render(f"Logged in as: {USERNAME}", True, BLACK), (SCREEN_WIDTH - 200, 20))
        for box in self.input_boxes:
            box.draw(self.screen)
        for btn in self.buttons:
            btn.draw(self.screen)
        if self.message:
            self.screen.blit(font.render(self.message, True, RED), (20, SCREEN_HEIGHT - 40))

    def add_button(self, x, y, w, h, text, callback):
        btn = Button(x, y, w, h, text, callback)
        self.buttons.append(btn)
        return btn

    def add_input_box(self, x, y, w, h, text='', password=False):
        box = InputBox(x, y, w, h, text, password)
        self.input_boxes.append(box)
        return box

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                for box in self.input_boxes:
                    if box.handle_event(event):
                        self.handle_enter()
                for btn in self.buttons:
                    btn.handle_event(event)
            if self.next_screen:
                running = False
            self.draw()
            pygame.display.flip()
        return self.next_screen

    def handle_enter(self):
        pass

# Screen implementations
class WelcomeScreen(Screen):
    def __init__(self):
        super().__init__("RSE Demand Client - Welcome")
        self.add_button(300, 200, 150, BUTTON_HEIGHT, "Login", lambda: self.set_next_screen(LoginScreen()))
        self.add_button(300, 250, 150, BUTTON_HEIGHT, "Register", lambda: self.set_next_screen(RegisterScreen()))

class LoginScreen(Screen):
    def __init__(self):
        super().__init__("RSE - Login")
        self.user = self.add_input_box(200, 100, 200, TEXT_INPUT_HEIGHT)
        self.pwd = self.add_input_box(200, 150, 200, TEXT_INPUT_HEIGHT, password=True)
        self.add_button(200, 200, 150, BUTTON_HEIGHT, "Login", self.login)

    def login(self):
        global AUTH_TOKEN, USERNAME
        resp = api_request('/login', 'POST', {"username": self.user.text, "password": self.pwd.text})
        if "access_token" in resp:
            AUTH_TOKEN = resp["access_token"]
            USERNAME = self.user.text
            self.set_next_screen(MainMenu())

class RegisterScreen(Screen):
    def __init__(self):
        super().__init__("RSE - Register")
        self.user = self.add_input_box(200, 100, 200, TEXT_INPUT_HEIGHT)
        self.pwd = self.add_input_box(200, 150, 200, TEXT_INPUT_HEIGHT, password=True)
        self.add_button(200, 200, 150, BUTTON_HEIGHT, "Register", self.register)

    def register(self):
        api_request('/register', 'POST', {"username": self.user.text, "password": self.pwd.text})
        self.set_next_screen(LoginScreen())

class MainMenu(Screen):
    def __init__(self):
        super().__init__("RSE Demand Client - Main Menu")
        actions = [
            ("Submit Bid", SubmitBidScreen), ("Cancel Bid", CancelBidScreen), ("Account Info", AccountScreen),
            ("Nearby", NearbyScreen), ("Sign Job", SignJobScreen), ("Send Message", SendMessageScreen),
            ("View Messages", ViewMessagesScreen), ("Post Bulletin", PostBulletinScreen),
            ("View Bulletins", ViewBulletinsScreen), ("Ping Server", PingScreen)
        ]
        for i, (text, screen) in enumerate(actions):
            self.add_button(50, 70 + i * 50, 200, BUTTON_HEIGHT, text, lambda s=screen: self.set_next_screen(s()))
        self.add_button(SCREEN_WIDTH - 200, 50, 150, BUTTON_HEIGHT, "Logout", self.logout)

    def logout(self):
        global AUTH_TOKEN, USERNAME
        AUTH_TOKEN = None
        USERNAME = None
        self.set_next_screen(WelcomeScreen())

class SubmitBidScreen(Screen):
    def __init__(self):
        super().__init__("RSE - Submit Bid")
        self.service = self.add_input_box(200, 100, 300, TEXT_INPUT_HEIGHT)
        self.lat = self.add_input_box(200, 150, 100, TEXT_INPUT_HEIGHT, "40.7128")
        self.lon = self.add_input_box(350, 150, 100, TEXT_INPUT_HEIGHT, "-74.0060")
        self.price = self.add_input_box(200, 200, 100, TEXT_INPUT_HEIGHT)
        self.end_time = self.add_input_box(200, 250, 100, TEXT_INPUT_HEIGHT, str(int(time.time()) + 3600))
        self.add_button(200, 300, 150, BUTTON_HEIGHT, "Submit", self.submit)

    def submit(self):
        data = {"service": self.service.text, "lat": float(self.lat.text), "lon": float(self.lon.text),
                "price": float(self.price.text), "end_time": int(self.end_time.text)}
        api_request('/submit_bid', 'POST', data)
        self.set_next_screen(MainMenu())

class CancelBidScreen(Screen):
    def __init__(self):
        super().__init__("RSE - Cancel Bid")
        self.bid_id = self.add_input_box(200, 100, 200, TEXT_INPUT_HEIGHT)
        self.add_button(200, 150, 150, BUTTON_HEIGHT, "Cancel", self.cancel)

    def cancel(self):
        api_request('/cancel_bid', 'POST', {"bid_id": self.bid_id.text})
        self.set_next_screen(MainMenu())

class AccountScreen(Screen):
    def __init__(self):
        super().__init__("RSE - Account Info")
        self.add_button(200, 100, 150, BUTTON_HEIGHT, "Fetch", self.fetch)
        self.add_button(200, 150, 150, BUTTON_HEIGHT, "Back", lambda: self.set_next_screen(MainMenu()))

    def fetch(self):
        self.message = str(api_request('/account'))

class NearbyScreen(Screen):
    def __init__(self):
        super().__init__("RSE - Nearby")
        self.lat = self.add_input_box(200, 100, 100, TEXT_INPUT_HEIGHT, "40.7128")
        self.lon = self.add_input_box(350, 100, 100, TEXT_INPUT_HEIGHT, "-74.0060")
        self.add_button(200, 150, 150, BUTTON_HEIGHT, "Search", self.search)
        self.add_button(200, 200, 150, BUTTON_HEIGHT, "Back", lambda: self.set_next_screen(MainMenu()))

    def search(self):
        data = {"lat": float(self.lat.text), "lon": float(self.lon.text)}
        self.message = str(api_request('/nearby', 'POST', data))

class SignJobScreen(Screen):
    def __init__(self):
        super().__init__("RSE - Sign Job")
        self.job_id = self.add_input_box(200, 100, 200, TEXT_INPUT_HEIGHT)
        self.add_button(200, 150, 150, BUTTON_HEIGHT, "Sign", self.sign)

    def sign(self):
        api_request('/sign_job', 'POST', {"job_id": self.job_id.text, "star_rating": 5})
        self.set_next_screen(MainMenu())

class SendMessageScreen(Screen):
    def __init__(self):
        super().__init__("RSE - Send Message")
        self.recipient = self.add_input_box(200, 100, 200, TEXT_INPUT_HEIGHT)
        self.message = self.add_input_box(200, 150, 200, TEXT_INPUT_HEIGHT)
        self.add_button(200, 200, 150, BUTTON_HEIGHT, "Send", self.send)

    def send(self):
        api_request('/chat', 'POST', {"recipient": self.recipient.text, "message": self.message.text})
        self.set_next_screen(MainMenu())

class ViewMessagesScreen(Screen):
    def __init__(self):
        super().__init__("RSE - View Messages")
        self.add_button(200, 100, 150, BUTTON_HEIGHT, "Fetch", self.fetch)
        self.add_button(200, 150, 150, BUTTON_HEIGHT, "Back", lambda: self.set_next_screen(MainMenu()))

    def fetch(self):
        self.message = str(api_request('/chat'))

class PostBulletinScreen(Screen):
    def __init__(self):
        super().__init__("RSE - Post Bulletin")
        self.title = self.add_input_box(200, 100, 200, TEXT_INPUT_HEIGHT)
        self.content = self.add_input_box(200, 150, 200, TEXT_INPUT_HEIGHT)
        self.add_button(200, 200, 150, BUTTON_HEIGHT, "Post", self.post)

    def post(self):
        api_request('/bulletin', 'POST', {"title": self.title.text, "content": self.content.text, "category": "general"})
        self.set_next_screen(MainMenu())

class ViewBulletinsScreen(Screen):
    def __init__(self):
        super().__init__("RSE - View Bulletins")
        self.add_button(200, 100, 150, BUTTON_HEIGHT, "Fetch", self.fetch)
        self.add_button(200, 150, 150, BUTTON_HEIGHT, "Back", lambda: self.set_next_screen(MainMenu()))

    def fetch(self):
        self.message = str(api_request('/bulletin'))

class PingScreen(Screen):
    def __init__(self):
        super().__init__("RSE - Ping")
        self.add_button(200, 100, 150, BUTTON_HEIGHT, "Ping", self.ping)
        self.add_button(200, 150, 150, BUTTON_HEIGHT, "Back", lambda: self.set_next_screen(MainMenu()))

    def ping(self):
        self.message = str(api_request('/ping'))

# Main function
def main():
    global current_screen
    current_screen = WelcomeScreen()
    while True:
        current_screen = current_screen.run()

if __name__ == "__main__":
    main()
