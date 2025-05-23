import pygame
import sys
import random
import json
import hashlib # Şifreleri güvenli saklamak için

pygame.init()

# ------------------------------------------------------------------
# EKRAN AYARLARI: Ekran çözünürlüğüyle tam ekran modunda açılıyor.
info = pygame.display.Info()
WINDOW_WIDTH = info.current_w
WINDOW_HEIGHT = info.current_h
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Yılan Oyunu")
clock = pygame.time.Clock()

# ------------------------------------------------------------------
# GLOBAL AYARLAR ve DEĞİŞKENLER
language = "en"         # "tr" veya "en" - Oyunun başlangıç dili İngilizce yapıldı
theme = "black"         # "black" veya "white"
admin_mode = False      # Admin modu: wrap-around ve ölünmezlik (can kontrolü yapılmaz)
extra_lives_count = 0   # Marketten alınan ekstra can; toplam can = 1 + extra_lives_count
extra_growth = False    # Her elma yediğinde yılan 3 blok uzasın (aktifse)
gold = 0                # Oyun içi para birimi
custom_snake_color = None  # Marketten alınan özel yılan rengi; yoksa tema rengine göre.
paradise_unlocked = False  # Ayarlardan "cennet" kodu ile aktif edilecek.
block_size = 20         # Yılan ve elma blok boyutu

# Kullanıcı verileri ve mevcut kullanıcı
USER_DATA_FILE = "users.json"
users = {} # Tüm kullanıcı verilerini tutar
current_user = None # Giriş yapmış kullanıcının verileri

# Power-up durumları (oyun başında sıfırlanır, satın alınma durumu kaydedilir)
# Bu değişkenler artık güçlendirmelerin aktif olup olmadığını ve kalan süre/kullanımını takip edecek.
# Satın alınma durumu current_user['purchased_powerups'] içinde.
ghost_mode_uses = 0
speed_boost_active_duration = 0 # ms
shield_active_duration = 0      # ms
gold_magnet_active_duration = 0 # ms
thorns_active_duration = 0      # Yeni: Diken etkisi süresi (şimdilik kullanılmıyor, ileride farklı bir efekt için kalabilir)

# Güçlendirme tuşları ve bekleme süreleri
POWERUP_KEYS = {
    'ghost_mode': pygame.K_g, # G tuşu
    'speed_boost': pygame.K_h, # H tuşu
    'shield': pygame.K_j, # J tuşu
    'gold_magnet': pygame.K_k # K tuşu
}
POWERUP_COOLDOWNS = { # ms cinsinden bekleme süreleri
    'ghost_mode': 5000,
    'speed_boost': 10000,
    'shield': 10000,
    'gold_magnet': 10000
}
powerup_cooldown_timers = { # Son kullanım zamanı
    'ghost_mode': 0,
    'speed_boost': 0,
    'shield': 0,
    'gold_magnet': 0
}

# Market Sayfaları
market_page = 1
selected_market_item = None # Market'te seçili olan yetenek
market_message = "" # Market'te gösterilecek yetenek açıklaması

# Seviye Konfigürasyonları (Genişletildi)
# Her seviye için farklı arka plan, yılan ve elma renkleri, hız çarpanı ve bir sonraki seviyeye geçiş skoru.
level_configs = {
    1: {'name': 'Forest Path', 'bg_color': (34, 139, 34), 'snake_color_default': (0, 100, 0), 'apple_color': (255, 0, 0), 'speed_multiplier': 1.0, 'score_to_next': 5, 'hazard_type': None},
    2: {'name': 'Desert Sands', 'bg_color': (244, 164, 96), 'snake_color_default': (139, 69, 19), 'apple_color': (255, 140, 0), 'speed_multiplier': 1.1, 'score_to_next': 10, 'hazard_type': None},
    3: {'name': 'Icy Caverns', 'bg_color': (173, 216, 230), 'snake_color_default': (255, 255, 255), 'apple_color': (0, 0, 139), 'speed_multiplier': 1.2, 'score_to_next': 15, 'hazard_type': 'small_static'},
    4: {'name': 'Volcanic Lair', 'bg_color': (139, 0, 0), 'snake_color_default': (0, 0, 0), 'apple_color': (255, 215, 0), 'speed_multiplier': 1.3, 'score_to_next': 20, 'hazard_type': 'small_static'},
    5: {'name': 'Space Odyssey', 'bg_color': (25, 25, 112), 'snake_color_default': (192, 192, 192), 'apple_color': (138, 43, 226), 'speed_multiplier': 1.4, 'score_to_next': 25, 'hazard_type': 'small_moving'},
    6: {'name': 'Deep Ocean', 'bg_color': (0, 0, 100), 'snake_color_default': (0, 200, 200), 'apple_color': (255, 200, 0), 'speed_multiplier': 1.5, 'score_to_next': 30, 'hazard_type': 'small_moving'},
    7: {'name': 'Crystal Caves', 'bg_color': (150, 0, 150), 'snake_color_default': (200, 255, 200), 'apple_color': (0, 255, 255), 'speed_multiplier': 1.6, 'score_to_next': 35, 'hazard_type': 'multiple_static'},
    8: {'name': 'Cyber City', 'bg_color': (0, 0, 0), 'snake_color_default': (50, 255, 50), 'apple_color': (255, 0, 255), 'speed_multiplier': 1.7, 'score_to_next': 40, 'hazard_type': 'multiple_moving'},
    9: {'name': 'Ancient Ruins', 'bg_color': (100, 50, 0), 'snake_color_default': (200, 150, 100), 'apple_color': (255, 255, 0), 'speed_multiplier': 1.8, 'score_to_next': 45, 'hazard_type': 'multiple_moving'},
    10: {'name': 'Dragon\'s Peak', 'bg_color': (50, 0, 0), 'snake_color_default': (255, 50, 50), 'apple_color': (255, 255, 255), 'speed_multiplier': 2.0, 'score_to_next': 50, 'hazard_type': 'boss', 'apples_to_defeat_boss': 5}, # Boss seviyesi
    11: {'name': 'Cloud City', 'bg_color': (135, 206, 235), 'snake_color_default': (255, 255, 255), 'apple_color': (255, 20, 147), 'speed_multiplier': 2.1, 'score_to_next': 55, 'hazard_type': None},
    12: {'name': 'Toxic Swamp', 'bg_color': (85, 107, 47), 'snake_color_default': (124, 252, 0), 'apple_color': (139, 0, 139), 'speed_multiplier': 2.2, 'score_to_next': 60, 'hazard_type': 'small_static'},
    13: {'name': 'Desert Oasis', 'bg_color': (210, 180, 140), 'snake_color_default': (0, 128, 0), 'apple_color': (0, 191, 255), 'speed_multiplier': 2.3, 'score_to_next': 65, 'hazard_type': 'small_moving'},
    14: {'name': 'Frozen Tundra', 'bg_color': (176, 224, 230), 'snake_color_default': (70, 130, 180), 'apple_color': (255, 69, 0), 'speed_multiplier': 2.4, 'score_to_next': 70, 'hazard_type': 'multiple_static'},
    15: {'name': 'Magical Forest', 'bg_color': (200, 60, 0), 'snake_color_default': (255, 255, 255), 'apple_color': (255, 215, 0), 'speed_multiplier': 1.0, 'score_to_next': 75, 'hazard_type': 'boss', 'apples_to_defeat_boss': 10, 'boss_health': 10, 'spiked_apple_color': (150, 0, 0)}, # Son seviye, boss health ve dikenli elma eklendi
    16: {'name': 'Endless Maze', 'bg_color': (50, 50, 50), 'snake_color_default': (0, 255, 0), 'apple_color': (255, 0, 255), 'speed_multiplier': 1.2, 'score_to_next': float('inf'), 'hazard_type': 'maze_walls'}, # Yeni sonsuz labirent modu
    # Dark Mode ve Acceleration Mode için seviye konfigürasyonları doğrudan zorluk modunda ele alınacak.
}
current_level_in_game = 1 # Oyun başladığında mevcut seviye
selected_start_level = 1 # Ayarlardan seçilen başlangıç seviyesi

# Boss hareket değişkenleri
boss_pos = None
boss_direction = (0, 0)
boss_speed = 0.5 # Boss'un hızı (blok cinsinden) - Yavaşlatıldı
boss_size = 60 # Boss boyutu (3 bloktan 60 piksele çıkarıldı)

# Geri sayım değişkenleri
countdown_active = False
countdown_start_time = 0

# Yeni: Dikenli elma ve boss etkileşimi için
normal_apples_eaten_counter = 0 # Dikenli elmanın ne zaman ortaya çıkacağını belirler
spiked_apple_thrown_message_timer = 0 # "Boss Vuruldu!" mesajı için zamanlayıcı
boss_defeated_final_message_timer = 0 # Yeni: Boss yenildiğinde gösterilecek mesaj için zamanlayıcı

# Boss yenildi animasyonu değişkenleri
boss_defeated_animation_active = False
boss_defeated_animation_char_index = 0
boss_defeated_animation_start_time = 0
BOSS_DEFEATED_ANIMATION_DELAY = 50 # ms per character
BOSS_DEFEATED_TOTAL_DISPLAY_TIME = 6000 # Total time for message to display before transition

# ------------------------------------------------------------------
# ÇOK DİLLİ METİNLER
texts = {
    "tr": {
        "welcome": "Hoşgeldiniz, başlamak için herhangi bir tuşa basın",
        "settings": "Ayarlar",
        "language": "Dil",
        "theme": "Tema",
        "turkish": "Türkçe",
        "english": "English",
        "black": "Siyah",
        "white": "Beyaz",
        "difficulty": "Zorluk Seçimi",
        "easy": "Kolay",
        "normal": "Orta",
        "hard": "Zor",
        "paradise": "Cennet Modu",
        "endless_maze": "Sonsuz Labirent", # Yeni eklendi
        "dark_mode": "Karanlık Mod", # Yeni eklendi
        "acceleration_mode": "Hızlanma Modu", # Yeni eklendi
        "game_over": "Kaybettiniz!",
        "game_won": "Kazandınız!", # Yeni eklendi
        "restart": "Yeniden Başla",
        "back": "Geri",
        "admin_on": "Admin Modu (Açık)",
        "admin_off": "Admin Modu (Kapalı)",
        "extra_growth_on": "Ekstra Büyüme (Açık)",
        "extra_growth_off": "Ekstra Büyüme (Kapalı)",
        "lost_life": "Bir can kaybettiniz! Kalan can: {}",
        "market": "Market",
        "buy_extra_life": "Ekstra Can Satın Al (100 gold)",
        "paradise_btn_on": "Cennet Modu (Açık)",
        "paradise_btn_off": "Cennet Modu (Kapalı)",
        "exit": "Çıkış",
        "login": "Giriş Yap",
        "register": "Kayıt Ol",
        "username": "Kullanıcı Adı:",
        "password": "Şifre:",
        "guest_play": "Misafir Olarak Oyna",
        "invalid_credentials": "Geçersiz kullanıcı adı veya şifre!",
        "user_exists": "Bu kullanıcı adı zaten mevcut!",
        "registration_success": "Kayıt başarılı! Lütfen giriş yapın.",
        "high_scores": "Yüksek Skorlar",
        "page": "Sayfa {}",
        "next_page": "Sonraki Sayfa",
        "prev_page": "Önceki Sayfa",
        "ghost_mode": "Hayalet Modu (10 Kullanım)",
        "speed_boost": "Hız Takviyesi (10sn)",
        "shield": "Kalkan (10sn)",
        "gold_magnet": "Altın Mıknatısı (10sn)",
        "purchased": "Satın Alındı",
        "level": "Level: {}",
        "level_up": "LEVEL ATLANDI!",
        "final_level_bonus": "Son Seviye Tamamlandı! +1000 Altın!",
        "activate_powerup": "Aktif Et ({})", # Tuş gösterimi kaldırıldı, açıklama ile birleşecek
        "powerup_cooldown": "{} (Beklemede)",
        "powerup_not_purchased": "Satın alınmadı",
        "powerup_no_uses": "Kullanım kalmadı",
        "quest": "GÖREV: {} elma topla",
        "boss_warning": "DİKKAT! BOSS YAKLAŞIYOR!",
        "boss_defeated": "BOSS YENİLDİ!",
        "boss_active": "BOSS AKTİF!",
        "start_game": "Oyunu Başlat",
        "score": "Skor",
        "lives": "Can",
        "highest_level_reached": "En Yüksek Level",
        "no_high_scores": "Henüz yüksek skor yok!",
        "gold": "Altın",
        "buy_button": "SATIN AL", # Yeni eklendi
        "powerup_desc_ghost_mode": "Duvarlardan ve kendinizden geçmenizi sağlar. {} kullanım.", # Yeni eklendi
        "powerup_desc_speed_boost": "Yılan hızını 10 saniyeliğine artırır.", # Yeni eklendi
        "powerup_desc_shield": "10 saniyeliğine çarpışmalara karşı koruma sağlar.", # Yeni eklendi
        "powerup_desc_gold_magnet": "10 saniyeliğine elmaları size çeker.", # Yeni eklendi
        "countdown_go": "BAŞLA!", # Yeni eklendi
        "level_15_intro_part1": "Demek buraya kadar gelebildin kahraman ama bu senin hayatının bittiği bölüm olucak!", # Yeni eklendi
        "level_15_intro_part2": "(Bossu yenmek için dikenli elmaları ye)", # Yeni eklendi
        "thorns_active": "Dikenler Aktif!", # Bu metin artık kullanılmayacak ama uyumluluk için bırakıldı.
        "boss_hit": "BOSS VURULDU!", # Yeni eklendi
        "boss_end_message": "Demek... buraya kadarmış ha? Beni yenmiş olabilirsin kahraman ama O seni bulmaya gelicek hazır ol :) (Yakında devam edicek)" # Yeni eklendi
    },
    "en": {
        "welcome": "Welcome, press any key to start",
        "settings": "Settings",
        "language": "Language",
        "theme": "Theme",
        "turkish": "Turkish",
        "english": "English",
        "black": "Black",
        "white": "White",
        "difficulty": "Select Difficulty",
        "easy": "Easy",
        "normal": "Normal",
        "hard": "Hard",
        "paradise": "Paradise Mode",
        "endless_maze": "Endless Maze", # Yeni eklendi
        "dark_mode": "Dark Mode", # Yeni eklendi
        "acceleration_mode": "Acceleration Mode", # Yeni eklendi
        "game_over": "You Lost!",
        "game_won": "You Won!", # Yeni eklendi
        "restart": "Restart",
        "back": "Back",
        "admin_on": "Admin Mode (On)",
        "admin_off": "Admin Mode (Off)",
        "extra_growth_on": "Extra Growth (On)",
        "extra_growth_off": "Extra Growth (Off)",
        "lost_life": "You lost a life! Lives left: {}",
        "market": "Market",
        "buy_extra_life": "Buy Extra Life (100 gold)",
        "paradise_btn_on": "Paradise Mode (On)",
        "paradise_btn_off": "Paradise Mode (Off)",
        "exit": "Exit",
        "login": "Login",
        "register": "Register",
        "username": "Username:",
        "password": "Password:",
        "guest_play": "Play as Guest",
        "invalid_credentials": "Invalid username or password!",
        "user_exists": "Username already exists!",
        "registration_success": "Registration successful! Please log in.",
        "high_scores": "High Scores",
        "page": "Page {}",
        "next_page": "Next Page",
        "prev_page": "Previous Page",
        "ghost_mode": "Ghost Mode (10 Uses)",
        "speed_boost": "Speed Boost (10s)",
        "shield": "Shield (10s)",
        "gold_magnet": "Gold Magnet (10s)",
        "purchased": "Purchased",
        "level": "Level: {}",
        "level_up": "LEVEL UP!",
        "final_level_bonus": "Final Level Completed! +1000 Gold!",
        "activate_powerup": "Activate ({})", # Tuş gösterimi kaldırıldı, açıklama ile birleşecek
        "powerup_cooldown": "{} (Cooldown)",
        "powerup_not_purchased": "Not purchased",
        "powerup_no_uses": "No uses left",
        "quest": "QUEST: Collect {} apples",
        "boss_warning": "WARNING! BOSS APPROACHING!",
        "boss_defeated": "BOSS DEFEATED!",
        "boss_active": "BOSS ACTIVE!",
        "start_game": "Start Game",
        "score": "Score",
        "lives": "Lives",
        "highest_level_reached": "Highest Level Reached",
        "no_high_scores": "No high scores yet!",
        "gold": "Gold",
        "buy_button": "BUY", # Yeni eklendi
        "powerup_desc_ghost_mode": "Allows you to pass through walls and yourself. {} uses.", # Yeni eklendi
        "powerup_desc_speed_boost": "Increases snake speed for 10 seconds.", # Yeni eklendi
        "powerup_desc_shield": "Provides collision protection for 10 seconds.", # Yeni eklendi
        "powerup_desc_gold_magnet": "Attracts apples to you for 10 seconds.", # Yeni eklendi
        "countdown_go": "GO!", # Yeni eklendi
        "level_15_intro_part1": "So you've made it this far, hero, but this will be the end of your life!", # Yeni eklendi
        "level_15_intro_part2": "(Eat the spiked apples to defeat the Boss)", # Yeni eklendi
        "thorns_active": "Thorns Active!", # Bu metin artık kullanılmayacak ama uyumluluk için bırakıldı.
        "boss_hit": "BOSS HIT!", # Yeni eklendi
        "boss_end_message": "So... this is it, huh? You may have defeated me, hero, but He will come for you, be ready :) (To be continued soon)" # Yeni eklendi
    }
}

# ------------------------------------------------------------------
# YARDIMCI FONKSİYON: Metin çizimi
def draw_text(surface, text, size, color, x, y, align="center"): # 'center' varsayılan hizalama
    font = pygame.font.SysFont("Arial", size, bold=True)
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect()

    if align == "center":
        rect.center = (x, y)
    elif align == "topleft":
        rect.topleft = (x, y)
    elif align == "topright":
        rect.topright = (x, y)
    elif align == "midleft":
        rect.midleft = (x, y)
    elif align == "midright":
        rect.midright = (x, y)
    elif align == "bottomleft":
        rect.bottomleft = (x, y)
    elif align == "bottomright":
        rect.bottomright = (x, y)
    
    surface.blit(text_surface, rect)

# YARDIMCI FONKSİYON: Yuvarlak köşeli dikdörtgen çizimi
def draw_rounded_rect(surface, color, rect, radius, border_color=None, border_width=0):
    # Sınır çizimi (varsa)
    if border_color and border_width > 0:
        border_rect = pygame.Rect(rect.x - border_width, rect.y - border_width,
                                  rect.width + 2 * border_width, rect.height + 2 * border_width)
        pygame.draw.rect(surface, border_color, (border_rect.x + radius + border_width, border_rect.y, border_rect.width - 2 * (radius + border_width), border_rect.height))
        pygame.draw.rect(surface, border_color, (border_rect.x, border_rect.y + radius + border_width, border_rect.width, border_rect.height - 2 * (radius + border_width)))
        pygame.draw.circle(surface, border_color, (border_rect.x + radius + border_width, border_rect.y + radius + border_width), radius + border_width)
        pygame.draw.circle(surface, border_color, (border_rect.x + border_rect.width - (radius + border_width), border_rect.y + radius + border_width), radius + border_width)
        pygame.draw.circle(surface, border_color, (border_rect.x + radius + border_width, border_rect.y + border_rect.height - (radius + border_width)), radius + border_width) # Düzeltildi: border_size -> border_width
        pygame.draw.circle(surface, border_color, (border_rect.x + border_rect.width - (radius + border_width), border_rect.y + border_rect.height - (radius + border_width)), radius + border_width)

    # Ana dolu dikdörtgeni çiz
    pygame.draw.rect(surface, color, (rect.x + radius, rect.y, rect.width - 2 * radius, rect.height))
    pygame.draw.rect(surface, color, (rect.x, rect.y + radius, rect.width, rect.height - 2 * radius))
    pygame.draw.circle(surface, color, (rect.x + radius, rect.y + radius), radius)
    pygame.draw.circle(surface, color, (rect.x + rect.width - radius, rect.y + radius), radius)
    pygame.draw.circle(surface, color, (rect.x + radius, rect.y + rect.height - radius), radius)
    pygame.draw.circle(surface, color, (rect.x + rect.width - radius, rect.y + rect.height - radius), radius)

# YARDIMCI FONKSİYON: Metni belirli bir genişliğe göre sarar
def wrap_text(text, font_obj, max_width):
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font_obj.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line)) # Add the last line
    return lines

# ------------------------------------------------------------------
# KULLANICI YÖNETİMİ (JSON ile)
def load_user_data():
    global users
    try:
        with open(USER_DATA_FILE, 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {} # Dosya yoksa boş sözlük oluştur

def save_user_data():
    global users
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# YARDIMCI FONKSİYON: Rastgele pozisyon üretir, belirli pozisyonları hariç tutar
def random_position(exclude_positions=[]):
    x = random.randint(0, (WINDOW_WIDTH - block_size) // block_size) * block_size
    y = random.randint(0, (WINDOW_HEIGHT - block_size) // block_size) * block_size
    pos = (x, y)
    # exclude_positions listesinde olmayan bir pozisyon bulunana kadar tekrar dene
    while pos in exclude_positions:
        x = random.randint(0, (WINDOW_WIDTH - block_size) // block_size) * block_size
        y = random.randint(0, (WINDOW_HEIGHT - block_size) // block_size) * block_size
        pos = (x, y)
    return pos

# ------------------------------------------------------------------
# GİRİŞ / KAYIT EKRANI
def auth_menu():
    global current_user, users, language, theme, gold, extra_lives_count, custom_snake_color, paradise_unlocked, extra_growth

    username_input = ""
    password_input = ""
    active_input = "username" # "username" veya "password"
    message = ""
    message_timer = 0

    load_user_data()

    running = True
    while running:
        bg_color = (25, 25, 25) if theme == "black" else (240, 240, 240)
        text_color = (255, 255, 255) if theme == "black" else (50, 50, 50)
        screen.fill(bg_color)

        draw_text(screen, texts[language]["login"], 64, text_color, WINDOW_WIDTH // 2, 100)

        # Kullanıcı Adı Giriş Kutusu
        username_label_rect = pygame.Rect(WINDOW_WIDTH // 2 - 250, 200, 200, 50)
        draw_text(screen, texts[language]["username"], 36, text_color, username_label_rect.centerx, username_label_rect.centery, align="center")
        username_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 200, 300, 50)
        draw_rounded_rect(screen, (50, 50, 50), username_rect, 10, border_color=(100, 100, 255) if active_input == "username" else (70, 70, 70), border_width=3)
        draw_text(screen, username_input, 36, (255, 255, 255), username_rect.x + 10, username_rect.centery, align="midleft")

        # Şifre Giriş Kutusu
        password_label_rect = pygame.Rect(WINDOW_WIDTH // 2 - 250, 280, 200, 50)
        draw_text(screen, texts[language]["password"], 36, text_color, password_label_rect.centerx, password_label_rect.centery, align="center")
        password_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 280, 300, 50)
        draw_rounded_rect(screen, (50, 50, 50), password_rect, 10, border_color=(100, 100, 255) if active_input == "password" else (70, 70, 70), border_width=3)
        draw_text(screen, "*" * len(password_input), 36, (255, 255, 255), password_rect.x + 10, password_rect.centery, align="midleft")

        # Giriş Butonu
        login_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 200, 380, 180, 70)
        draw_rounded_rect(screen, (60, 140, 90), login_btn_rect, 15)
        draw_text(screen, texts[language]["login"], 40, (255, 255, 255), login_btn_rect.centerx, login_btn_rect.centery, align="center")

        # Kayıt Ol Butonu
        register_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 + 20, 380, 180, 70)
        draw_rounded_rect(screen, (70, 130, 180), register_btn_rect, 15)
        draw_text(screen, texts[language]["register"], 40, (255, 255, 255), register_btn_rect.centerx, register_btn_rect.centery, align="center")

        # Misafir Olarak Oyna Butonu
        guest_play_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, 480, 300, 70)
        draw_rounded_rect(screen, (150, 150, 150), guest_play_btn_rect, 15)
        draw_text(screen, texts[language]["guest_play"], 40, (0, 0, 0), guest_play_btn_rect.centerx, guest_play_btn_rect.centery, align="center")

        # Mesaj Kutusu
        if message:
            draw_text(screen, message, 36, (255, 255, 0), WINDOW_WIDTH // 2, 600, align="center")
            if pygame.time.get_ticks() - message_timer > 3000: # 3 saniye sonra mesajı sil
                message = ""

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if username_rect.collidepoint(event.pos):
                    active_input = "username"
                elif password_rect.collidepoint(event.pos):
                    active_input = "password"
                elif login_btn_rect.collidepoint(event.pos):
                    hashed_password = hash_password(password_input)
                    if username_input in users and users[username_input]['password'] == hashed_password:
                        current_user = users[username_input].copy() # Kopyasını al
                        current_user['username'] = username_input # Kullanıcı adını ekle
                        # Kullanıcının kaydedilmiş oyun ayarlarını yükle
                        gold = current_user.get('gold', 0)
                        extra_lives_count = current_user.get('extra_lives_count', 0)
                        custom_snake_color = tuple(current_user['custom_snake_color']) if 'custom_snake_color' in current_user and current_user['custom_snake_color'] is not None else None
                        paradise_unlocked = current_user.get('paradise_unlocked', False)
                        extra_growth = current_user.get('extra_growth', False)
                        current_user['highest_level_reached'] = current_user.get('highest_level_reached', 1) # Yeni eklendi
                        return "menu" # Ana menüye geç
                    else:
                        message = texts[language]["invalid_credentials"]
                        message_timer = pygame.time.get_ticks()
                elif register_btn_rect.collidepoint(event.pos):
                    if username_input in users:
                        message = texts[language]["user_exists"]
                        message_timer = pygame.time.get_ticks()
                    elif not username_input or not password_input:
                        message = texts[language]["invalid_credentials"] # Boş bırakılamaz uyarısı
                        message_timer = pygame.time.get_ticks()
                    else:
                        users[username_input] = {
                            'password': hash_password(password_input),
                            'high_score': 0,
                            'gold': 0,
                            'extra_lives_count': 0,
                            'custom_snake_color': None,
                            'paradise_unlocked': False,
                            'extra_growth': False,
                            'highest_level_reached': 1, # Yeni eklendi
                            'purchased_powerups': { # Satın alınan güçlendirmeler
                                'ghost_mode': False,
                                'speed_boost': False,
                                'shield': False,
                                'gold_magnet': False
                            }
                        }
                        save_user_data()
                        message = texts[language]["registration_success"]
                        message_timer = pygame.time.get_ticks()
                        username_input = ""
                        password_input = ""
                elif guest_play_btn_rect.collidepoint(event.pos):
                    current_user = {
                        'username': 'Guest',
                        'high_score': 0,
                        'gold': 0,
                        'extra_lives_count': 0,
                        'custom_snake_color': None,
                        'paradise_unlocked': False,
                        'extra_growth': False,
                        'highest_level_reached': 1, # Yeni eklendi
                        'purchased_powerups': {
                            'ghost_mode': False,
                            'speed_boost': False,
                            'shield': False,
                            'gold_magnet': False
                        }
                    }
                    gold = 0
                    extra_lives_count = 0
                    custom_snake_color = None
                    paradise_unlocked = False
                    extra_growth = False
                    return "menu"

            elif event.type == pygame.KEYDOWN:
                if active_input == "username":
                    if event.key == pygame.K_BACKSPACE:
                        username_input = username_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        active_input = "password"
                    else:
                        username_input += event.unicode
                elif active_input == "password":
                    if event.key == pygame.K_BACKSPACE:
                        password_input = password_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        # Giriş denemesi
                        hashed_password = hash_password(password_input)
                        if username_input in users and users[username_input]['password'] == hashed_password:
                            current_user = users[username_input].copy() # Kopyasını al
                            current_user['username'] = username_input # Kullanıcı adını ekle
                            gold = current_user.get('gold', 0)
                            extra_lives_count = current_user.get('extra_lives_count', 0)
                            custom_snake_color = tuple(current_user['custom_snake_color']) if 'custom_snake_color' in current_user and current_user['custom_snake_color'] is not None else None
                            paradise_unlocked = current_user.get('paradise_unlocked', False)
                            extra_growth = current_user.get('extra_growth', False)
                            current_user['highest_level_reached'] = current_user.get('highest_level_reached', 1) # Yeni eklendi
                            return "menu"
                        else:
                            message = texts[language]["invalid_credentials"]
                            message_timer = pygame.time.get_ticks()
                    else:
                        password_input += event.unicode
        clock.tick(30)

# ------------------------------------------------------------------
# ANA MENÜ
def main_menu():
    global current_user, gold, extra_lives_count, custom_snake_color, paradise_unlocked, extra_growth
    running = True
    while running:
        bg_color = (25, 25, 25) if theme == "black" else (240, 240, 240)
        text_color = (255, 255, 255) if theme == "black" else (50, 50, 50)
        screen.fill(bg_color)

        # Kullanıcı bilgisi
        if current_user:
            draw_text(screen, f"{texts[language]['welcome'].split(',')[0]}, {current_user['username']}!", 48, text_color, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 200, align="center")
            draw_text(screen, f"{texts[language]['score']}: {current_user['high_score']}", 36, text_color, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 150, align="center")
            draw_text(screen, f"{texts[language]['highest_level_reached']}: {current_user.get('highest_level_reached', 1)}", 36, text_color, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 110, align="center")
            draw_text(screen, f"{texts[language]['gold']}: {current_user['gold']}", 36, (255,215,0), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 70, align="center")
        else:
            draw_text(screen, texts[language]["welcome"], 48, text_color, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100, align="center")

        # Oyun Başlat butonu
        start_game_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 40, 300, 80)
        draw_rounded_rect(screen, (60, 140, 90), start_game_rect, 15)
        draw_text(screen, texts[language]["start_game"], 48, (255, 255, 255), start_game_rect.centerx, start_game_rect.centery, align="center")

        # Ayarlar butonu
        settings_rect = pygame.Rect(WINDOW_WIDTH - 240, WINDOW_HEIGHT - 130, 220, 80)
        draw_rounded_rect(screen, (70, 100, 150), settings_rect, 15)
        draw_text(screen, texts[language]["settings"], 42, (255, 255, 255), settings_rect.centerx, settings_rect.centery, align="center")

        # Market butonu
        market_rect = pygame.Rect(20, WINDOW_HEIGHT - 130, 220, 80)
        draw_rounded_rect(screen, (60, 140, 90), market_rect, 15)
        draw_text(screen, texts[language]["market"], 42, (255, 255, 255), market_rect.centerx, market_rect.centery, align="center")

        # Yüksek Skorlar butonu
        high_scores_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 + 80, 300, 80)
        draw_rounded_rect(screen, (100, 100, 180), high_scores_rect, 15)
        draw_text(screen, texts[language]["high_scores"], 42, (255, 255, 255), high_scores_rect.centerx, high_scores_rect.centery, align="center")

        # Çıkış butonu (Ana Menü)
        exit_rect_main_menu = pygame.Rect(20, 20, 150, 60)
        draw_rounded_rect(screen, (180, 50, 50), exit_rect_main_menu, 10)
        draw_text(screen, texts[language]["exit"], 36, (255, 255, 255), exit_rect_main_menu.centerx, exit_rect_main_menu.centery, align="center")

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_game_rect.collidepoint(event.pos):
                    return "difficulty"
                elif settings_rect.collidepoint(event.pos):
                    return "settings"
                elif market_rect.collidepoint(event.pos):
                    return "market"
                elif high_scores_rect.collidepoint(event.pos):
                    return "high_scores"
                elif exit_rect_main_menu.collidepoint(event.pos):
                    pygame.quit(); sys.exit()
        clock.tick(30)

# ------------------------------------------------------------------
# AYARLAR MENÜSÜ
def settings_menu():
    global language, theme, admin_mode, extra_growth, paradise_unlocked, selected_start_level
    secret_code = ""
    admin_btn_visible = False
    paradise_btn_visible = False
    level_select_input_visible = False # Yeni: Seviye seçimi inputunun görünürlüğü
    level_input = str(selected_start_level)
    active_input = None # "level_select"
    message = ""
    message_timer = 0

    running = True
    while running:
        bg_color = (25, 25, 25) if theme == "black" else (240, 240, 240)
        text_color = (255, 255, 255) if theme == "black" else (50, 50, 50)
        screen.fill(bg_color)
        draw_text(screen, texts[language]["settings"], 64, text_color, WINDOW_WIDTH // 2, 80, align="center")

        # Dil Seçimi
        draw_text(screen, texts[language]["language"], 40, text_color, WINDOW_WIDTH // 2, 160, align="center")
        lang_tr = pygame.Rect(WINDOW_WIDTH // 2 - 250, 200, 200, 70)
        lang_en = pygame.Rect(WINDOW_WIDTH // 2 + 50, 200, 200, 70)
        draw_rounded_rect(screen, (70, 130, 180), lang_tr, 10)
        draw_rounded_rect(screen, (70, 130, 180), lang_en, 10)
        draw_text(screen, texts["tr"]["turkish"], 36, (255, 255, 255), lang_tr.centerx, lang_tr.centery, align="center")
        draw_text(screen, texts["en"]["english"], 36, (255, 255, 255), lang_en.centerx, lang_en.centery, align="center")

        # Tema Seçimi
        draw_text(screen, texts[language]["theme"], 40, text_color, WINDOW_WIDTH // 2, 300, align="center")
        theme_black = pygame.Rect(WINDOW_WIDTH // 2 - 250, 340, 200, 70)
        theme_white = pygame.Rect(WINDOW_WIDTH // 2 + 50, 340, 200, 70)
        draw_rounded_rect(screen, (70, 130, 180), theme_black, 10)
        draw_rounded_rect(screen, (70, 130, 180), theme_white, 10)
        draw_text(screen, texts[language]["black"], 36, (255, 255, 255), theme_black.centerx, theme_black.centery, align="center")
        draw_text(screen, texts[language]["white"], 36, (255, 255, 255), theme_white.centerx, theme_white.centery, align="center")

        # Seviye Seçimi (Sadece level_select_input_visible True ise çiz)
        if level_select_input_visible:
            draw_text(screen, texts[language]["level"], 40, text_color, WINDOW_WIDTH // 2 - 150, 450, align="center")
            level_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 450 - 25, 100, 50)
            draw_rounded_rect(screen, (50, 50, 50), level_rect, 10, border_color=(100, 100, 255) if active_input == "level_select" else (70, 70, 70), border_width=3)
            draw_text(screen, level_input, 36, (255, 255, 255), level_rect.centerx, level_rect.centery, align="center")
        else: # Gizli kod girişi için boş bir alan bırak
            level_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 450 - 25, 100, 50) # Konumu koru ama çizme
            pass # Gizli kod girişi için görsel bir eleman çizmeye gerek yok

        # Geri butonu
        back_rect = pygame.Rect(50, WINDOW_HEIGHT - 100, 150, 60)
        draw_rounded_rect(screen, (150, 150, 150), back_rect, 10)
        draw_text(screen, texts[language]["back"], 36, (0, 0, 0), back_rect.centerx, back_rect.centery, align="center")

        # Admin ve Ekstra Büyüme butonları (gizli kod ile görünür)
        admin_rect = pygame.Rect(WINDOW_WIDTH // 2 - 175, 550, 350, 80)
        growth_rect = pygame.Rect(WINDOW_WIDTH // 2 - 175, 650, 350, 80)
        paradise_rect = pygame.Rect(WINDOW_WIDTH // 2 - 175, 750, 350, 80) # Yeri ayarlandı

        if admin_btn_visible:
            draw_rounded_rect(screen, (180, 80, 80), admin_rect, 15)
            admin_text = texts[language]["admin_on"] if admin_mode else texts[language]["admin_off"]
            draw_text(screen, admin_text, 42, (255, 255, 255), admin_rect.centerx, admin_rect.centery, align="center")

            draw_rounded_rect(screen, (80, 80, 180), growth_rect, 15)
            growth_text = texts[language]["extra_growth_on"] if extra_growth else texts[language]["extra_growth_off"]
            draw_text(screen, growth_text, 42, (255, 255, 255), growth_rect.centerx, growth_rect.centery, align="center")

        if paradise_btn_visible:
            draw_rounded_rect(screen, (100, 200, 200), paradise_rect, 15)
            parad_text = texts[language]["paradise_btn_on"] if paradise_unlocked else texts[language]["paradise_btn_off"]
            draw_text(screen, parad_text, 42, (0, 0, 0), paradise_rect.centerx, paradise_rect.centery, align="center")
        
        # Mesaj Kutusu
        if message:
            draw_text(screen, message, 36, (255, 255, 0), WINDOW_WIDTH // 2, WINDOW_HEIGHT - 150, align="center")
            if pygame.time.get_ticks() - message_timer > 3000: # 3 saniye sonra mesajı sil
                message = ""

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if active_input == "level_select":
                    if event.key == pygame.K_BACKSPACE:
                        level_input = level_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        try:
                            level_num = int(level_input)
                            if 1 <= level_num <= len(level_configs):
                                selected_start_level = level_num
                                message = f"Başlangıç seviyesi: {selected_start_level}" if language == "tr" else f"Starting level: {selected_start_level}"
                            else:
                                message = "Geçersiz seviye!" if language == "tr" else "Invalid level!"
                            message_timer = pygame.time.get_ticks()
                        except ValueError:
                            message = "Sayı giriniz!" if language == "tr" else "Enter a number!"
                            message_timer = pygame.time.get_ticks()
                        active_input = None
                    else:
                        if event.unicode.isdigit():
                            level_input += event.unicode
                else: # Gizli kod girişi
                    secret_code += event.unicode.lower()
                    if secret_code.endswith("arda"):
                        admin_btn_visible = True
                    if secret_code.endswith("cennet"):
                        paradise_btn_visible = True
                        if current_user and not current_user['paradise_unlocked']:
                            current_user['paradise_unlocked'] = True
                            save_user_data()
                    if secret_code.endswith("level"): # Yeni: "level" kodu seviye seçimini gösterir
                        level_select_input_visible = True
                        secret_code = "" # Kodu sıfırla ki tekrar tekrar tetiklenmesin
                    if len(secret_code) > 12: # Kodu çok uzun tutmamak için
                        secret_code = secret_code[-12:]
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if lang_tr.collidepoint(pos):
                    language = "tr"
                elif lang_en.collidepoint(pos):
                    language = "en"
                elif theme_black.collidepoint(pos):
                    theme = "black"
                elif theme_white.collidepoint(pos):
                    theme = "white"
                elif back_rect.collidepoint(pos):
                    return "menu"
                # Sadece görünürse tıklanabilir olsun
                if level_select_input_visible and level_rect.collidepoint(pos):
                    active_input = "level_select"
                if admin_btn_visible:
                    if admin_rect.collidepoint(pos):
                        admin_mode = not admin_mode
                    elif growth_rect.collidepoint(pos):
                        extra_growth = not extra_growth
                if paradise_btn_visible:
                    if paradise_rect.collidepoint(pos):
                        paradise_unlocked = True # Sadece açar, kapatmaz.
                        if current_user and not current_user['paradise_unlocked']:
                            current_user['paradise_unlocked'] = True
                            save_user_data()
        clock.tick(30)

# ------------------------------------------------------------------
# MARKET MENÜSÜ
def market_menu():
    global language, theme, gold, custom_snake_color, extra_lives_count, market_page, current_user, selected_market_item, market_message

    color_cost = 15
    powerup_costs = {
        'ghost_mode': 200,
        'speed_boost': 150,
        'shield': 120,
        'gold_magnet': 180
    }

    market_colors = {
        "tr": [("Kırmızı",(255,0,0)), ("Yeşil",(0,255,0)), ("Mavi",(0,0,255)), ("Sarı",(255,255,0)), ("Mor",(128,0,128)), ("Turuncu",(255,165,0)), ("Turkuaz",(64,224,208)), ("Pembe",(255,192,203)), ("Lacivert",(0,0,139)), ("Gri",(128,128,128)), ("Bordo",(128,0,0)), ("Bronz",(205,127,50))],
        "en": [("Red",(255,0,0)), ("Green",(0,255,0)), ("Blue",(0,0,255)), ("Yellow",(255,255,0)), ("Purple",(128,0,128)), ("Orange",(255,165,0)), ("Turquoise",(64,224,208)), ("Pink",(255,192,203)), ("Navy",(0,0,139)), ("Gray",(128,128,128)), ("Maroon",(128,0,0)), ("Bronze",(205,127,50))]
    }
    market_powerups = {
        "tr": [("Hayalet Modu", "ghost_mode"), ("Hız Takviyesi", "speed_boost"), ("Kalkan", "shield"), ("Altın Mıknatısı", "gold_magnet")],
        "en": [("Ghost Mode", "ghost_mode"), ("Speed Boost", "speed_boost"), ("Shield", "shield"), ("Gold Magnet", "gold_magnet")]
    }

    powerup_descriptions = {
        'ghost_mode': texts[language]["powerup_desc_ghost_mode"].format(10),
        'speed_boost': texts[language]["powerup_desc_speed_boost"],
        'shield': texts[language]["powerup_desc_shield"],
        'gold_magnet': texts[language]["powerup_desc_gold_magnet"]
    }

    running = True
    while running:
        bg_color = (25, 25, 25) if theme == "black" else (240, 240, 240)
        text_color = (255, 255, 255) if theme == "black" else (50, 50, 50)
        screen.fill(bg_color)
        draw_text(screen, texts[language]["market"], 64, text_color, WINDOW_WIDTH // 2, 80, align="center")
        draw_text(screen, f"{texts[language]['gold']}: {gold}", 42, (255, 215, 0), 30, 20, align="topleft")

        num_cols = 4; num_rows = 3
        margin_x = 100; margin_y = 150
        gap_x = (WINDOW_WIDTH - 2 * margin_x) // num_cols
        gap_y = 150
        buttons = []

        if market_page == 1: # Renkler sayfası
            current_items = market_colors[language]
            item_type = "color"
        else: # Güçlendirmeler sayfası
            current_items = market_powerups[language]
            item_type = "powerup"

        for index, item_info in enumerate(current_items):
            col = index % num_cols; row = index // num_cols
            btn_rect = pygame.Rect(margin_x + col * gap_x + (gap_x - 200) // 2, margin_y + row * gap_y, 200, 100)
            buttons.append((btn_rect, item_info, item_type))

            item_name = item_info[0]
            item_value = item_info[1] # Renk kodu veya powerup anahtarı

            is_purchased = False
            item_cost = 0
            item_color = (100, 100, 100) # Varsayılan buton rengi

            if item_type == "color":
                item_cost = color_cost
                item_color = item_value
                if current_user and current_user['custom_snake_color'] == list(item_value): # JSON'da liste olarak kaydedildiği için
                    is_purchased = True
            elif item_type == "powerup":
                item_cost = powerup_costs[item_value]
                item_color = (150, 100, 200) # Power-up butonu rengi
                if current_user and current_user['purchased_powerups'].get(item_value, False):
                    is_purchased = True

            draw_rounded_rect(screen, item_color, btn_rect, 10,
                              border_color=(0, 255, 0) if is_purchased else None, border_width=3 if is_purchased else 0)

            text_color_for_button = (255, 255, 255) if sum(item_color[:3]) < 384 else (0, 0, 0)
            draw_text(screen, item_name, 32, text_color_for_button, btn_rect.centerx, btn_rect.centery - 20, align="center")
            if is_purchased:
                draw_text(screen, texts[language]["purchased"], 28, text_color_for_button, btn_rect.centerx, btn_rect.centery + 20, align="center")
            else:
                draw_text(screen, f"{item_cost} {texts[language]['gold']}", 28, text_color_for_button, btn_rect.centerx, btn_rect.centery + 20, align="center")

        # Sayfa değiştirme butonları
        prev_page_rect = pygame.Rect(WINDOW_WIDTH // 2 - 250, WINDOW_HEIGHT - 180, 200, 60)
        next_page_rect = pygame.Rect(WINDOW_WIDTH // 2 + 50, WINDOW_HEIGHT - 180, 200, 60)
        draw_rounded_rect(screen, (100, 100, 100), prev_page_rect, 10)
        draw_rounded_rect(screen, (100, 100, 100), next_page_rect, 10)
        draw_text(screen, texts[language]["prev_page"], 32, (255, 255, 255), prev_page_rect.centerx, prev_page_rect.centery, align="center")
        draw_text(screen, texts[language]["next_page"], 32, (255, 255, 255), next_page_rect.centerx, next_page_rect.centery, align="center")
        draw_text(screen, texts[language]["page"].format(market_page), 32, text_color, WINDOW_WIDTH // 2, WINDOW_HEIGHT - 220, align="center")


        # Ekstra Can butonu
        extra_life_rect = pygame.Rect(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT - 100, 400, 70) # Yeri biraz yukarı alındı
        draw_rounded_rect(screen, (200, 200, 50), extra_life_rect, 15)
        draw_text(screen, texts[language]["buy_extra_life"], 36, (0, 0, 0), extra_life_rect.centerx, extra_life_rect.centery, align="center")

        # Geri butonu
        back_rect = pygame.Rect(WINDOW_WIDTH - 200, WINDOW_HEIGHT - 100, 150, 60)
        draw_rounded_rect(screen, (150, 150, 150), back_rect, 10)
        draw_text(screen, texts[language]["back"], 36, (0, 0, 0), back_rect.centerx, back_rect.centery, align="center")

        # Seçili yetenek açıklaması ve satın alma butonu
        if selected_market_item and selected_market_item[2] == "powerup":
            item_key = selected_market_item[1][1] # (name, key) -> key
            cost = powerup_costs[item_key]
            is_purchased = current_user and current_user['purchased_powerups'].get(item_key, False)

            desc_y = WINDOW_HEIGHT // 2 + 100
            draw_text(screen, powerup_descriptions[item_key], 32, text_color, WINDOW_WIDTH // 2, desc_y, align="center")

            buy_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 100, desc_y + 50, 200, 60)
            if not is_purchased:
                draw_rounded_rect(screen, (60, 140, 90), buy_btn_rect, 10)
                draw_text(screen, texts[language]["buy_button"], 36, (255, 255, 255), buy_btn_rect.centerx, buy_btn_rect.centery, align="center")
            else:
                draw_rounded_rect(screen, (150, 150, 150), buy_btn_rect, 10)
                draw_text(screen, texts[language]["purchased"], 36, (0, 0, 0), buy_btn_rect.centerx, buy_btn_rect.centery, align="center")


        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if back_rect.collidepoint(pos):
                    selected_market_item = None # Menüye dönerken seçimi sıfırla
                    market_message = ""
                    return "menu"
                if extra_life_rect.collidepoint(pos):
                    if current_user and gold >= 100:
                        gold -= 100
                        extra_lives_count += 1
                        current_user['gold'] = gold
                        current_user['extra_lives_count'] = extra_lives_count
                        save_user_data()
                if prev_page_rect.collidepoint(pos):
                    market_page = 1
                    selected_market_item = None # Sayfa değişince seçimi sıfırla
                    market_message = ""
                elif next_page_rect.collidepoint(pos):
                    market_page = 2
                    selected_market_item = None # Sayfa değişince seçimi sıfırla
                    market_message = ""

                # Yetenek butonlarına tıklama
                for btn_rect, item_info, item_type_in_loop in buttons:
                    if btn_rect.collidepoint(pos):
                        if item_type_in_loop == "powerup":
                            selected_market_item = (btn_rect, item_info, item_type_in_loop) # Seçili yeteneği kaydet
                        elif item_type_in_loop == "color": # Renkler direkt satın alınır
                            if current_user and gold >= color_cost:
                                gold -= color_cost
                                custom_snake_color = item_info[1]
                                current_user['gold'] = gold
                                current_user['custom_snake_color'] = list(custom_snake_color) # JSON'a liste olarak kaydet
                                save_user_data()

                # Satın Al butonuna tıklama
                if selected_market_item and selected_market_item[2] == "powerup":
                    buy_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 100 + 50, 200, 60)
                    if buy_btn_rect.collidepoint(pos):
                        item_key = selected_market_item[1][1]
                        cost = powerup_costs[item_key]
                        if current_user and gold >= cost and not current_user['purchased_powerups'].get(item_key, False):
                            gold -= cost
                            current_user['gold'] = gold
                            current_user['purchased_powerups'][item_key] = True
                            save_user_data()
                            selected_market_item = None # Satın alınca seçimi sıfırla
                            market_message = ""
        clock.tick(30)

# ------------------------------------------------------------------
# YÜKSEK SKORLAR MENÜSÜ
def high_scores_menu():
    global users, language, theme
    # Sadece kayıtlı kullanıcıların skorlarını göster
    sorted_users = sorted([user_data for username, user_data in users.items() if user_data.get('high_score', 0) > 0 and user_data.get('username') != 'Guest'], key=lambda x: x.get('high_score', 0), reverse=True)
    running = True
    while running:
        bg_color = (25, 25, 25) if theme == "black" else (240, 240, 240)
        text_color = (255, 255, 255) if theme == "black" else (50, 50, 50)
        screen.fill(bg_color)
        draw_text(screen, texts[language]["high_scores"], 64, text_color, WINDOW_WIDTH // 2, 80, align="center")

        display_y = 150
        if not sorted_users:
            draw_text(screen, texts[language]["no_high_scores"], 36, text_color, WINDOW_WIDTH // 2, display_y + 50, align="center")
        else:
            for i, user_data in enumerate(sorted_users[:10]): # İlk 10 yüksek skoru göster
                username = user_data.get('username', "Unknown User") # Kullanıcı adı yoksa varsayılan
                score = user_data['high_score']
                level = user_data.get('highest_level_reached', 1)
                draw_text(screen, f"{i+1}. {username}: {texts[language]['score']} {score} ({texts[language]['level'].split(':')[0]} {level})", 40, text_color, WINDOW_WIDTH // 2, display_y, align="center")
                display_y += 50

        back_rect = pygame.Rect(50, WINDOW_HEIGHT - 100, 150, 60)
        draw_rounded_rect(screen, (150, 150, 150), back_rect, 10)
        draw_text(screen, texts[language]["back"], 36, (0, 0, 0), back_rect.centerx, back_rect.centery, align="center")

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    return "menu"
        clock.tick(30)

# ------------------------------------------------------------------
# ZORLUK SEÇİM MENÜSÜ
def difficulty_menu():
    global paradise_unlocked
    options = [
        (texts[language]["easy"], "easy"),
        (texts[language]["normal"], "normal"),
        (texts[language]["hard"], "hard"),
        (texts[language]["endless_maze"], "endless_maze"), # Yeni eklendi
        (texts[language]["dark_mode"], "dark_mode"), # Yeni eklendi
        (texts[language]["acceleration_mode"], "acceleration_mode") # Yeni eklendi
    ]
    if paradise_unlocked: options.append((texts[language]["paradise"], "paradise"))
    
    running = True
    while running:
        bg_color = (25, 25, 25) if theme == "black" else (240, 240, 240)
        text_color = (255, 255, 255) if theme == "black" else (50, 50, 50)
        screen.fill(bg_color)
        draw_text(screen, texts[language]["difficulty"], 64, text_color, WINDOW_WIDTH // 2, 80, align="center")
        button_rects = []
        start_y = 180; gap = 100 # Buton aralığı azaltıldı
        btn_width = 400; btn_height = 80 # Buton boyutu azaltıldı
        for i, (btn_text, mode_val) in enumerate(options):
            rect = pygame.Rect(WINDOW_WIDTH // 2 - btn_width // 2, start_y + i * gap, btn_width, btn_height)
            button_rects.append((rect, mode_val))
            draw_rounded_rect(screen, (70, 130, 180), rect, 15)
            draw_text(screen, btn_text, 40, (255, 255, 255), rect.centerx, rect.centery, align="center") # Font boyutu azaltıldı

        # Geri butonu
        back_rect = pygame.Rect(50, WINDOW_HEIGHT - 100, 150, 60)
        draw_rounded_rect(screen, (150, 150, 150), back_rect, 10)
        draw_text(screen, texts[language]["back"], 36, (0, 0, 0), back_rect.centerx, back_rect.centery, align="center")

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, mode_val in button_rects:
                    if rect.collidepoint(event.pos): return mode_val
                if back_rect.collidepoint(event.pos):
                    return "menu"
        clock.tick(30)

# ------------------------------------------------------------------
# OYUN - KLASİK MODU (Easy, Normal, Hard, Endless Maze, Dark Mode, Acceleration Mode)
def game_loop_classic(difficulty):
    global gold, admin_mode, extra_lives_count, extra_growth, custom_snake_color, language, theme, WINDOW_WIDTH, WINDOW_HEIGHT, block_size
    global current_user, users, ghost_mode_uses, speed_boost_active_duration, shield_active_duration, gold_magnet_active_duration, thorns_active_duration, current_level_in_game, selected_start_level
    global boss_pos, boss_direction, boss_speed, powerup_cooldown_timers
    global countdown_active, countdown_start_time, normal_apples_eaten_counter, spiked_apple_thrown_message_timer, boss_defeated_final_message_timer
    global boss_defeated_animation_active, boss_defeated_animation_char_index, boss_defeated_animation_start_time, BOSS_DEFEATED_ANIMATION_DELAY, BOSS_DEFEATED_TOTAL_DISPLAY_TIME

    # Modlara özgü bayraklar
    is_endless_maze = (difficulty == "endless_maze")
    is_dark_mode = (difficulty == "dark_mode")
    is_acceleration_mode = (difficulty == "acceleration_mode")

    if is_endless_maze:
        current_level_in_game = 16 # Sonsuz labirent modu için özel seviye
        snake_speed_base = level_configs[current_level_in_game]['speed_multiplier'] * 10 # Başlangıç hızı
        gold_per_apple = 10
    else:
        current_level_in_game = selected_start_level # Seçilen seviyeden başla
        # Zorluğa göre yılan hızı ve altın miktarı ayarı
        if difficulty == "easy":
            snake_speed_base = 10
            gold_per_apple = 5
        elif difficulty == "normal":
            snake_speed_base = 15
            gold_per_apple = 10
        elif difficulty == "hard":
            snake_speed_base = 20
            gold_per_apple = 15
        elif is_dark_mode: # Karanlık mod için varsayılan hız ve altın
            snake_speed_base = 15
            gold_per_apple = 10
        elif is_acceleration_mode: # Hızlanma modu için varsayılan hız ve altın
            snake_speed_base = 8 # Daha yavaş başla
            gold_per_apple = 10

    snake_speed = snake_speed_base # Hız takviyesi için başlangıç değeri

    snake_initial_x = (WINDOW_WIDTH // 2 // block_size) * block_size
    snake_initial_y = (WINDOW_HEIGHT // 2 // block_size) * block_size
    snake = [(snake_initial_x, snake_initial_y)]

    direction = (block_size, 0)
    growth_counter = 0
    score = 0

    lives = (1 + extra_lives_count) if not admin_mode else float('inf')

    # Tehlike yönetimi (seviye bazlı)
    hazards = []
    maze_walls = [] # Sonsuz labirent için duvarlar
    
    # Apple'ı burada başlatıyoruz.
    apple = random_position(exclude_positions=snake)

    # Sonsuz labirent modu için duvarları oluştur
    if is_endless_maze:
        num_walls = 50 # Rastgele duvar sayısı
        for _ in range(num_walls):
            wall_pos = random_position(exclude_positions=[snake[0], apple])
            # Duvarın boyutunu rastgele yapabiliriz (1x1, 1x2, 2x1, 2x2 vb.)
            wall_width_blocks = random.randint(1, 4)
            wall_height_blocks = random.randint(1, 4)
            
            for wx in range(wall_width_blocks):
                for wy in range(wall_height_blocks):
                    segment_x = wall_pos[0] + wx * block_size
                    segment_y = wall_pos[1] + wy * block_size
                    # Ekran sınırları içinde kalmasını sağla
                    if 0 <= segment_x < WINDOW_WIDTH and 0 <= segment_y < WINDOW_HEIGHT:
                        maze_walls.append((segment_x, segment_y))
        hazards.extend(maze_walls) # Labirent duvarlarını tehlikeler listesine ekle
        # Ensure apple is not on a maze wall initially
        while apple in maze_walls:
            apple = random_position(exclude_positions=snake)

    boss_pos = None
    boss_direction = (0, 0) # Boss'un yönü
    boss_size = 60 # Boss boyutu
    boss_move_timer = 0
    boss_health = level_configs[15]['boss_health'] if current_level_in_game == 15 else 0 # Sadece 15. seviye için boss health
    spiked_apple_pos = None # Dikenli elma pozisyonu

    # Seviye atlama mesajı
    level_up_message_timer = 0
    final_level_bonus_message_timer = 0
    boss_defeated_final_message_timer = 0 # Initialize here

    # Level 15 intro message variables
    level_15_intro_active = False
    if current_level_in_game == 15 and not is_endless_maze and not is_dark_mode and not is_acceleration_mode: # Sadece 15. seviye ve diğer modlar aktif değilse intro göster
        level_15_intro_active = True
        level_15_intro_text_index = 0
        level_15_intro_char_timer = 0
        level_15_intro_delay = 50 # ms per character

    # Geri sayım başlat
    countdown_active = True
    countdown_start_time = pygame.time.get_ticks()

    # Yeni: Dikenli elma sayacı ve mesaj zamanlayıcısı
    normal_apples_eaten_counter = 0
    spiked_apple_thrown_message_timer = 0

    # Boss yenildi animasyonu değişkenleri
    boss_defeated_animation_active = False
    boss_defeated_animation_char_index = 0
    boss_defeated_animation_start_time = 0
    game_outcome = None # "won" or "lost"

    # Hızlanma modu için ek değişkenler
    acceleration_timer = pygame.time.get_ticks()
    acceleration_interval = 5000 # 5 saniyede bir hızlanma
    acceleration_amount = 0.5 # Her hızlanmada artacak miktar

    running_flag = True
    while running_flag:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if not countdown_active and not level_15_intro_active and not boss_defeated_animation_active: # Geri sayım, intro ve boss animasyonu bitmeden hareket etme
                    if event.key == pygame.K_UP and direction != (0, block_size): direction = (0, -block_size)
                    elif event.key == pygame.K_DOWN and direction != (0, -block_size): direction = (0, block_size)
                    elif event.key == pygame.K_LEFT and direction != (block_size, 0): direction = (-block_size, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-block_size, 0): direction = (block_size, 0)
                    
                    # Güçlendirme aktivasyonu (Yeni Eklendi)
                    for p_name, p_key in POWERUP_KEYS.items():
                        if event.key == p_key and current_user and current_user['purchased_powerups'].get(p_name):
                            if current_time >= powerup_cooldown_timers.get(p_name, 0): # Bekleme süresi bitti mi?
                                if p_name == 'ghost_mode' and ghost_mode_uses > 0:
                                    ghost_mode_uses -= 1
                                    powerup_cooldown_timers[p_name] = current_time + POWERUP_COOLDOWNS[p_name]
                                elif p_name == 'speed_boost':
                                    speed_boost_active_duration = 10000 # 10 saniye
                                    powerup_cooldown_timers[p_name] = current_time + POWERUP_COOLDOWNS[p_name]
                                elif p_name == 'shield':
                                    shield_active_duration = 10000 # 10 saniye
                                    powerup_cooldown_timers[p_name] = current_time + POWERUP_COOLDOWNS[p_name]
                                elif p_name == 'gold_magnet':
                                    gold_magnet_active_duration = 10000 # 10 saniye
                                    powerup_cooldown_timers[p_name] = current_time + POWERUP_COOLDOWNS[p_name]

            if event.type == pygame.MOUSEBUTTONDOWN:
                quit_rect_game = pygame.Rect(WINDOW_WIDTH - 170, 20, 150, 60)
                if quit_rect_game.collidepoint(event.pos):
                    # Oyuncunun skorunu ve altınlarını kaydet
                    if current_user:
                        if score > current_user['high_score']:
                            current_user['high_score'] = score
                        current_user['gold'] = gold
                        # Power-up'ları sıfırla (tek kullanımlık)
                        for p_name in current_user['purchased_powerups']:
                            current_user['purchased_powerups'][p_name] = False
                        save_user_data()
                    return "menu", score, gold # Return score and gold

        if countdown_active:
            # Geri sayım süresini hesapla
            time_left = 3000 - (current_time - countdown_start_time)
            countdown_number = max(0, (time_left // 1000) + 1) # 3, 2, 1

            # Arka plan rengini moda göre ayarla
            if is_endless_maze:
                screen.fill(level_configs[16]['bg_color'])
            elif is_dark_mode:
                screen.fill((0, 0, 0)) # Karanlık modda tamamen siyah arka plan
            else:
                screen.fill(level_configs[current_level_in_game]['bg_color'])

            if countdown_number > 0:
                draw_text(screen, str(countdown_number), 150, (255, 255, 255), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, align="center")
            else:
                draw_text(screen, texts[language]["countdown_go"], 150, (0, 255, 0), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, align="center")
                pygame.display.flip()
                pygame.time.wait(500) # "GO!" yazısı biraz kalsın
                countdown_active = False # Geri sayım bitti
                if current_level_in_game == 15 and not is_endless_maze and not is_dark_mode and not is_acceleration_mode: # Eğer son seviyedeyse intro mesajını başlat
                    level_15_intro_active = True
                    level_15_intro_text_index = 0
                    level_15_intro_char_timer = current_time
            
            pygame.display.flip()
            clock.tick(30) # Geri sayım sırasında sabit FPS
            continue # Oyun mantığını atla

        if level_15_intro_active:
            screen.fill(level_configs[current_level_in_game]['bg_color'])
            
            full_text1 = texts[language]["level_15_intro_part1"]
            full_text2 = texts[language]["level_15_intro_part2"]

            font1 = pygame.font.SysFont("Arial", 40, bold=True)
            font2 = pygame.font.SysFont("Arial", 32, bold=True)
            wrapped_lines1 = wrap_text(full_text1, font1, WINDOW_WIDTH - 200) # 100px padding
            wrapped_lines2 = wrap_text(full_text2, font2, WINDOW_WIDTH - 200)

            total_chars_to_type = sum(len(line) for line in wrapped_lines1) + sum(len(line) for line in wrapped_lines2) + len(wrapped_lines1) + len(wrapped_lines2) # +1 for newline/space between lines

            if current_time - level_15_intro_char_timer > level_15_intro_delay:
                if level_15_intro_text_index < total_chars_to_type:
                    level_15_intro_text_index += 1
                    level_15_intro_char_timer = current_time
                else:
                    pygame.time.wait(1000) # Mesajın tamamı biraz kalsın
                    level_15_intro_active = False # Intro bitti

            current_char_count = 0
            # Calculate starting Y to center the block of text
            total_text_height = len(wrapped_lines1) * 40 + len(wrapped_lines2) * 32 + 20 # 20px space between two parts
            start_y_offset = (WINDOW_HEIGHT - total_text_height) // 2

            for i, line in enumerate(wrapped_lines1):
                chars_in_this_line = len(line)
                display_portion = min(chars_in_this_line, max(0, level_15_intro_text_index - current_char_count))
                draw_text(screen, line[:display_portion], 40, (255, 255, 255), WINDOW_WIDTH // 2, start_y_offset + i * 40, align="center")
                current_char_count += chars_in_this_line + 1 # +1 for implied space/newline

            for i, line in enumerate(wrapped_lines2):
                chars_in_this_line = len(line)
                display_portion = min(chars_in_this_line, max(0, level_15_intro_text_index - current_char_count))
                draw_text(screen, line[:display_portion], 32, (255, 255, 0), WINDOW_WIDTH // 2, start_y_offset + len(wrapped_lines1) * 40 + 20 + i * 32, align="center")
                current_char_count += chars_in_this_line + 1

            pygame.display.flip()
            clock.tick(30)
            continue # Oyun mantığını atla


        # Güçlendirme sürelerini güncelle
        if speed_boost_active_duration > 0:
            speed_boost_active_duration -= clock.get_time()
            if speed_boost_active_duration <= 0:
                snake_speed = snake_speed_base * level_configs[current_level_in_game]['speed_multiplier'] # Süre bittiğinde hızı normale döndür
            else:
                snake_speed = (snake_speed_base * level_configs[current_level_in_game]['speed_multiplier']) * 1.5 # Hız takviyesi aktif
        else:
            # Hızlanma modu için hız artışı
            if is_acceleration_mode:
                if current_time - acceleration_timer > acceleration_interval:
                    snake_speed += acceleration_amount
                    acceleration_timer = current_time
                snake_speed = max(snake_speed_base, snake_speed) # Minimum hızı koru
            else:
                snake_speed = snake_speed_base * level_configs[current_level_in_game]['speed_multiplier'] # Hız takviyesi yoksa normal hız

        if shield_active_duration > 0:
            shield_active_duration -= clock.get_time()
            if shield_active_duration <= 0:
                shield_active_duration = 0 # Süre bitti

        if gold_magnet_active_duration > 0:
            gold_magnet_active_duration -= clock.get_time()
            if gold_magnet_active_duration <= 0:
                gold_magnet_active_duration = 0 # Süre bitti
        
        head = snake[0]
        potential_new_head_x = head[0] + direction[0]
        potential_new_head_y = head[1] + direction[1]

        new_head = (potential_new_head_x, potential_new_head_y)

        cols_on_screen = WINDOW_WIDTH // block_size
        rows_on_screen = WINDOW_HEIGHT // block_size

        # Duvar çarpışması ve admin modu sarma
        collision_with_wall = False
        if admin_mode:
            current_col_index = potential_new_head_x // block_size
            current_row_index = potential_new_head_y // block_size
            wrapped_col = current_col_index % cols_on_screen
            wrapped_row = current_row_index % rows_on_screen
            new_head = (wrapped_col * block_size, wrapped_row * block_size)
        else:
            current_col_index = new_head[0] // block_size
            current_row_index = new_head[1] // block_size
            if current_col_index < 0 or current_col_index >= cols_on_screen or \
               current_row_index < 0 or current_row_index >= rows_on_screen:
                collision_with_wall = True

        # Kendine çarpma
        collision_with_self = False
        if new_head in snake:
            collision_with_self = True

        # Tehlike çarpışması (Hard modda ve seviye bazlı)
        collision_with_hazard = False
        for hazard in hazards:
            if new_head == hazard:
                collision_with_hazard = True
                break
        
        # Labirent duvarı çarpışması (Sonsuz Labirent modunda)
        collision_with_maze_wall = False
        if is_endless_maze and new_head in maze_walls:
            collision_with_maze_wall = True

        # Boss çarpışması (Son seviyede)
        collision_with_boss = False
        if current_level_in_game == 15 and boss_pos: # Sadece 15. seviye için boss çarpışması
            boss_rect = pygame.Rect(boss_pos[0], boss_pos[1], boss_size, boss_size)
            snake_head_rect = pygame.Rect(new_head[0], new_head[1], block_size, block_size)
            if boss_rect.colliderect(snake_head_rect): # Boss ile çarpışma kontrolü
                collision_with_boss = True

        # Çarpışma işleme
        if (collision_with_wall or collision_with_self or collision_with_hazard or collision_with_boss or collision_with_maze_wall) and not admin_mode:
            if shield_active_duration > 0: # Kalkan aktifse çarpışmayı engelle
                pass # Can kaybetmez, oyun devam eder
            elif ghost_mode_uses > 0: # Hayalet modu aktifse
                ghost_mode_uses -= 1
                # Yılanı ortaya ışınla
                snake_reset_x = (WINDOW_WIDTH // 2 // block_size) * block_size
                snake_reset_y = (WINDOW_HEIGHT // 2 // block_size) * block_size
                snake = [(snake_reset_x, snake_reset_y)]
                direction = (block_size, 0)
                growth_counter = 0
                apple = random_position(exclude_positions=snake + hazards + maze_walls) # Yeni elma konumunu belirlerken duvarları da hariç tut
                while apple in snake or apple in hazards or apple in maze_walls: apple = random_position(exclude_positions=snake + hazards + maze_walls)
                hazards = [] # Tehlikeleri sıfırla
                boss_pos = None # Boss'u sıfırla
                spiked_apple_pos = None # Dikenli elmayı sıfırla
                continue # Yeni frame'e geç
            elif lives > 1:
                lives -= 1
                waiting = True
                while waiting:
                    screen.fill((25, 25, 25) if theme == "black" else (240, 240, 240))
                    draw_text(screen, texts[language]["lost_life"].format(int(lives)), 64, (255, 50, 50), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, align="center")
                    pygame.display.flip()
                    for ev in pygame.event.get():
                        if ev.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]: waiting = False
                    clock.tick(5)
                snake_reset_x = (WINDOW_WIDTH // 2 // block_size) * block_size
                snake_reset_y = (WINDOW_HEIGHT // 2 // block_size) * block_size
                snake = [(snake_reset_x, snake_reset_y)]
                direction = (block_size, 0); growth_counter = 0
                apple = random_position(exclude_positions=snake + hazards + maze_walls);
                while apple in snake or apple in hazards or apple in maze_walls: apple = random_position(exclude_positions=snake + hazards + maze_walls)
                hazards = [] # Tehlikeleri sıfırla
                boss_pos = None # Boss'u sıfırla
                spiked_apple_pos = None # Dikenli elmayı sıfırla
                continue
            else:
                running_flag = False
                game_outcome = "lost" # Set outcome to lost
                break

        if not running_flag: continue

        snake.insert(0, new_head)

        # Altın Mıknatısı etkisi
        if gold_magnet_active_duration > 0:
            # Elmayı yılana doğru çek (basit bir yaklaşım)
            if apple[0] > new_head[0]: apple = (apple[0] - block_size, apple[1])
            elif apple[0] < new_head[0]: apple = (apple[0] + block_size, apple[1])
            if apple[1] > new_head[1]: apple = (apple[0], apple[1] - block_size)
            elif apple[1] < new_head[1]: apple = (apple[0], apple[1] + block_size)
            
            # Dikenli elmayı da çek (eğer varsa ve boss seviyesinde)
            if current_level_in_game == 15 and spiked_apple_pos:
                if spiked_apple_pos[0] > new_head[0]: spiked_apple_pos = (spiked_apple_pos[0] - block_size, spiked_apple_pos[1])
                elif spiked_apple_pos[0] < new_head[0]: spiked_apple_pos = (spiked_apple_pos[0] + block_size, spiked_apple_pos[1])
                if spiked_apple_pos[1] > new_head[1]: spiked_apple_pos = (spiked_apple_pos[0], spiked_apple_pos[1] - block_size)
                elif spiked_apple_pos[1] < new_head[1]: spiked_apple_pos = (spiked_apple_pos[0], spiked_apple_pos[1] + block_size)


        if new_head == apple:
            score += 1
            gold += gold_per_apple
            growth_counter += (3 if extra_growth else 1)
            apple = random_position(exclude_positions=snake + hazards + maze_walls) # Yeni elma konumunu belirlerken duvarları da hariç tut
            while apple in snake or apple in hazards or apple in maze_walls: apple = random_position(exclude_positions=snake + hazards + maze_walls)

            if not is_endless_maze and not is_dark_mode and not is_acceleration_mode: # Sadece klasik seviyelerde normal elma sayacı
                normal_apples_eaten_counter += 1 # Normal elma sayacını artır

            # Her 2 normal elma yendiğinde dikenli elma ortaya çıksın (sadece boss seviyesinde)
            if current_level_in_game == 15 and normal_apples_eaten_counter % 2 == 0:
                if not spiked_apple_pos: # Eğer zaten bir dikenli elma yoksa
                    spiked_apple_pos = random_position(exclude_positions=snake + hazards + maze_walls)
                    # Yılanın veya boss'un üzerinde doğmamasını sağla
                    while spiked_apple_pos in snake or (boss_pos and pygame.Rect(spiked_apple_pos[0], spiked_apple_pos[1], block_size, block_size).colliderect(pygame.Rect(boss_pos[0], boss_pos[1], boss_size, boss_size))) or spiked_apple_pos in maze_walls:
                        spiked_apple_pos = random_position(exclude_positions=snake + hazards + maze_walls)

            # Seviye atlama kontrolü (Sonsuz labirent modunda devre dışı)
            if not is_endless_maze and not is_dark_mode and not is_acceleration_mode and current_level_in_game < len(level_configs) and score >= level_configs[current_level_in_game]['score_to_next']:
                current_level_in_game += 1
                # En yüksek seviyeyi kaydet
                if current_user and current_level_in_game > current_user.get('highest_level_reached', 1):
                    current_user['highest_level_reached'] = current_level_in_game
                    save_user_data()

                # Yeni seviye için oyun durumunu sıfırla
                snake_initial_x = (WINDOW_WIDTH // 2 // block_size) * block_size
                snake_initial_y = (WINDOW_HEIGHT // 2 // block_size) * block_size
                snake = [(snake_initial_x, snake_initial_y)]
                direction = (block_size, 0)
                growth_counter = 0
                apple = random_position(exclude_positions=snake + hazards + maze_walls)
                while apple in snake or apple in hazards or apple in maze_walls: apple = random_position(exclude_positions=snake + hazards + maze_walls)
                hazards = [] # Tehlikeleri sıfırla
                boss_pos = None # Boss'u sıfırla
                spiked_apple_pos = None # Dikenli elmayı sıfırla
                boss_health = level_configs[15]['boss_health'] if current_level_in_game == 15 else 0 # Sadece 15. seviye için boss health
                normal_apples_eaten_counter = 0 # Yeni seviyede sayacı sıfırla

                level_up_message_timer = current_time + 2000 # 2 saniye mesaj göster
                countdown_active = True # Yeni seviye için geri sayımı başlat
                countdown_start_time = pygame.time.get_ticks()

                # Son seviye bonusu (Eğer son seviye tamamlandıysa, bu level_configs'in son seviyesinden sonraki bir seviyeye geçişi ifade eder)
                if current_level_in_game == len(level_configs) + 1:
                    gold += 1000
                    final_level_bonus_message_timer = current_time + 3000 # 3 saniye mesaj göster
                    if current_user:
                        current_user['gold'] = gold
                        save_user_data()
        elif new_head == spiked_apple_pos and current_level_in_game == 15: # Dikenli elma yendi (sadece boss seviyesinde)
            # Boss'a hasar ver
            boss_health -= 1
            spiked_apple_thrown_message_timer = current_time + 2000 # "Boss Vuruldu!" mesajı için zamanlayıcı
            
            if boss_health <= 0:
                gold += 1000 # Boss'u yenince 1000 altın
                if current_user:
                    current_user['gold'] = gold
                    save_user_data()
                
                # Trigger boss defeated animation
                boss_defeated_animation_active = True
                boss_defeated_animation_start_time = current_time
                boss_defeated_animation_char_index = 0
                boss_defeated_final_message_timer = current_time + BOSS_DEFEATED_TOTAL_DISPLAY_TIME # Total time for message to display before transition
                boss_pos = None # Boss'u haritadan kaldır

            # Dikenli elmayı hemen yeniden oluştur
            spiked_apple_pos = random_position(exclude_positions=snake + hazards + maze_walls)
            # Yılanın veya boss'un üzerinde doğmamasını sağla
            while spiked_apple_pos in snake or (boss_pos and pygame.Rect(spiked_apple_pos[0], spiked_apple_pos[1], block_size, block_size).colliderect(pygame.Rect(boss_pos[0], boss_pos[1], boss_size, boss_size))) or spiked_apple_pos in maze_walls:
                spiked_apple_pos = random_position(exclude_positions=snake + hazards + maze_walls)
        else:
            if growth_counter > 0: growth_counter -= 1
            else: snake.pop()

        # Seviye bazlı tehlike üretimi (Sonsuz labirent modunda devre dışı)
        if not is_endless_maze and not is_dark_mode and not is_acceleration_mode: # Sadece klasik seviyelerde tehlike üretimi
            current_level_hazard_type = level_configs[current_level_in_game]['hazard_type']
            if current_level_hazard_type == 'small_static' and not hazards:
                # Tek sabit tehlike
                h_pos = random_position(exclude_positions=snake + [apple] + maze_walls)
                while h_pos in snake or h_pos == apple or (spiked_apple_pos and h_pos == spiked_apple_pos) or h_pos in maze_walls: h_pos = random_position(exclude_positions=snake + [apple] + maze_walls)
                hazards.append(h_pos)
            elif current_level_hazard_type == 'small_moving' and not hazards:
                # Tek hareketli tehlike (basit hareket)
                h_pos = random_position(exclude_positions=snake + [apple] + maze_walls)
                while h_pos in snake or h_pos == apple or (spiked_apple_pos and h_pos == spiked_apple_pos) or h_pos in maze_walls: h_pos = random_position(exclude_positions=snake + [apple] + maze_walls)
                hazards.append(h_pos)
                # Hareket mantığı: Tehlikeler her frame'de hareket etmez, daha yavaş hareket eder.
                if current_time - (hazards[0][2] if len(hazards[0]) > 2 else 0) > 500: # 0.5 saniyede bir hareket
                    if len(hazards[0]) <= 2: # İlk kez hareket eden tehlike için zaman damgası ekle
                        hazards[0] = (hazards[0][0], hazards[0][1], current_time)
                    
                    # Basit bir yatay/dikey hareket
                    move_x = random.choice([-block_size, 0, block_size])
                    move_y = random.choice([-block_size, 0, block_size])
                    new_h_pos = (hazards[0][0] + move_x, hazards[0][1] + move_y)
                    
                    # Ekran sınırları içinde kalmasını sağla
                    new_h_pos = (max(0, min(new_h_pos[0], WINDOW_WIDTH - block_size)),
                                 max(0, min(new_h_pos[1], WINDOW_HEIGHT - block_size)))
                    
                    hazards[0] = (new_h_pos[0], new_h_pos[1], current_time)
            elif current_level_hazard_type == 'multiple_static' and len(hazards) < 3:
                # Çoklu sabit tehlike
                h_pos = random_position(exclude_positions=snake + [apple] + hazards + maze_walls)
                while h_pos in snake or h_pos == apple or (spiked_apple_pos and h_pos == spiked_apple_pos) or h_pos in hazards or h_pos in maze_walls: h_pos = random_position(exclude_positions=snake + [apple] + hazards + maze_walls)
                hazards.append(h_pos)
            elif current_level_hazard_type == 'multiple_moving' and len(hazards) < 2:
                # Çoklu hareketli tehlike
                h_pos = random_position(exclude_positions=snake + [apple] + hazards + maze_walls)
                while h_pos in snake or h_pos == apple or (spiked_apple_pos and h_pos == spiked_apple_pos) or h_pos in hazards or h_pos in maze_walls: h_pos = random_position(exclude_positions=snake + [apple] + hazards + maze_walls)
                hazards.append((h_pos[0], h_pos[1], current_time)) # (x, y, last_move_time)
                
                for i, h_info in enumerate(hazards):
                    if current_time - h_info[2] > 300: # 0.3 saniyede bir hareket
                        move_x = random.choice([-block_size, 0, block_size])
                        move_y = random.choice([-block_size, 0, block_size])
                        new_h_pos = (h_info[0] + move_x, h_info[1] + move_y)
                        new_h_pos = (max(0, min(new_h_pos[0], WINDOW_WIDTH - block_size)),
                                     max(0, min(new_h_pos[1], WINDOW_HEIGHT - block_size)))
                        hazards[i] = (new_h_pos[0], new_h_pos[1], current_time)
            elif current_level_hazard_type == 'boss' and not boss_pos:
                # Boss tehlikesi (Yeni Eklendi)
                boss_pos = (WINDOW_WIDTH // 2 - boss_size // 2, WINDOW_HEIGHT // 4) # Ekranın üst ortasında
                boss_health = level_configs[current_level_in_game]['boss_health']
                # Dikenli elma artık hemen burada spawn edilmiyor, normal elma sayacına bağlı.
                spiked_apple_pos = None # Boss seviyesi başladığında dikenli elma yok, elma sayacıyla gelecek.


        # Boss hareketi (Sadece boss seviyesinde ve varsa)
        if current_level_in_game == 15 and boss_pos:
            if current_time - boss_move_timer > 50: # Boss'un hareket hızı (daha sık güncellenir)
                # Yılanın başının koordinatları
                snake_head_x, snake_head_y = snake[0]
                # Boss'un merkez koordinatları
                boss_center_x = boss_pos[0] + boss_size // 2
                boss_center_y = boss_pos[1] + boss_size // 2

                dx = snake_head_x - boss_center_x
                dy = snake_head_y - boss_center_y

                distance = (dx**2 + dy**2)**0.5

                if distance > 0:
                    normalized_dx = dx / distance
                    normalized_dy = dy / distance
                    
                    # Yavaşça yılana doğru hareket et
                    move_x = normalized_dx * boss_speed * block_size
                    move_y = normalized_dy * boss_speed * block_size

                    new_boss_x = boss_pos[0] + move_x
                    new_boss_y = boss_pos[1] + move_y

                    # Ekran sınırları içinde kalmasını sağla
                    new_boss_x = max(0, min(new_boss_x, WINDOW_WIDTH - boss_size))
                    new_boss_y = max(0, min(new_boss_y, WINDOW_HEIGHT - boss_size))
                    
                    boss_pos = (new_boss_x, new_boss_y)
                
                boss_move_timer = current_time


        # Mevcut seviye temasına göre renkleri ayarla
        if is_endless_maze:
            bg_color = level_configs[16]['bg_color']
            snake_color_default_for_level = level_configs[16]['snake_color_default']
            apple_color_for_level = level_configs[16]['apple_color']
        elif is_dark_mode:
            bg_color = (0, 0, 0) # Karanlık modda arka plan siyah
            snake_color_default_for_level = (0, 200, 0) # Yeşil yılan
            apple_color_for_level = (255, 0, 0) # Kırmızı elma
        else:
            bg_color = level_configs[current_level_in_game]['bg_color']
            snake_color_default_for_level = level_configs[current_level_in_game]['snake_color_default']
            apple_color_for_level = level_configs[current_level_in_game]['apple_color']

        screen.fill(bg_color)

        # Karanlık modda görünürlük maskesi
        if is_dark_mode:
            visibility_radius = 150 # Görüş alanı yarıçapı
            dark_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            dark_surface.fill((0, 0, 0, 200)) # Yarı saydam siyah
            
            # Yılanın başının etrafındaki alanı temizle
            pygame.draw.circle(dark_surface, (0, 0, 0, 0), snake[0], visibility_radius)
            screen.blit(dark_surface, (0, 0))

        # Elma çizimi
        if not is_dark_mode or (is_dark_mode and ((apple[0] - snake[0][0])**2 + (apple[1] - snake[0][1])**2)**0.5 <= visibility_radius):
            draw_rounded_rect(screen, apple_color_for_level, pygame.Rect(apple[0], apple[1], block_size, block_size), block_size // 4)

        # Dikenli elma çizimi (sadece boss seviyesinde ve varsa)
        if current_level_in_game == 15 and spiked_apple_pos:
            if not is_dark_mode or (is_dark_mode and ((spiked_apple_pos[0] - snake[0][0])**2 + (spiked_apple_pos[1] - snake[0][1])**2)**0.5 <= visibility_radius):
                draw_rounded_rect(screen, level_configs[current_level_in_game]['spiked_apple_color'], pygame.Rect(spiked_apple_pos[0], spiked_apple_pos[1], block_size, block_size), block_size // 4, border_color=(255,255,0), border_width=2)


        # Tehlikeleri çiz (Sonsuz labirent modunda tehlikeler labirent duvarlarıdır)
        for hazard_item in hazards:
            if not is_dark_mode or (is_dark_mode and ((hazard_item[0] - snake[0][0])**2 + (hazard_item[1] - snake[0][1])**2)**0.5 <= visibility_radius):
                if isinstance(hazard_item, tuple) and len(hazard_item) >= 2: # (x, y) veya (x, y, time)
                    draw_rounded_rect(screen, (180, 0, 0), pygame.Rect(hazard_item[0], hazard_item[1], block_size, block_size), block_size // 4)

        # Boss'u çiz (Sadece boss seviyesinde ve varsa)
        if current_level_in_game == 15 and boss_pos:
            if not is_dark_mode or (is_dark_mode and ((boss_pos[0] + boss_size/2 - snake[0][0])**2 + (boss_pos[1] + boss_size/2 - snake[0][1])**2)**0.5 <= visibility_radius):
                draw_rounded_rect(screen, (100, 0, 0), pygame.Rect(boss_pos[0], boss_pos[1], boss_size, boss_size), boss_size // 4, border_color=(255,0,0), border_width=3)
                # Boss Health Bar
                health_bar_width = boss_size * (boss_health / level_configs[current_level_in_game]['boss_health'])
                health_bar_rect = pygame.Rect(boss_pos[0], boss_pos[1] - 20, boss_size, 10)
                draw_rounded_rect(screen, (0, 255, 0), pygame.Rect(health_bar_rect.x, health_bar_rect.y, health_bar_width, health_bar_rect.height), 3)
                draw_rounded_rect(screen, (255, 0, 0), health_bar_rect, 3, border_color=(255,255,255), border_width=1)


        # Yılan çizimi
        snake_color_to_draw = custom_snake_color if custom_snake_color is not None else snake_color_default_for_level
        for i, segment in enumerate(snake):
            if not is_dark_mode or (is_dark_mode and ((segment[0] - snake[0][0])**2 + (segment[1] - snake[0][1])**2)**0.5 <= visibility_radius):
                # Yılanın başını biraz farklı çiz
                if i == 0:
                    draw_rounded_rect(screen, snake_color_to_draw, pygame.Rect(segment[0], segment[1], block_size, block_size), block_size // 4, border_color=(255,255,255), border_width=2)
                else:
                    draw_rounded_rect(screen, snake_color_to_draw, pygame.Rect(segment[0], segment[1], block_size, block_size), block_size // 4)

        # Skor, Can, Altın ve Seviye göstergeleri
        draw_text(screen, f"{texts[language]['score']}: {score}", 36, (0, 200, 0), 20, 20, align="topleft")
        if not admin_mode: draw_text(screen, f"{texts[language]['lives']}: {int(lives)}", 36, (0, 200, 0), 20, 60, align="topleft")
        draw_text(screen, f"{texts[language]['gold']}: {gold}", 36, (255, 215, 0), 20, 100, align="topleft")
        
        # Seviye göstergesi sadece klasik modda
        if not is_endless_maze and not is_dark_mode and not is_acceleration_mode:
            draw_text(screen, texts[language]["level"].format(current_level_in_game), 36, (0, 200, 0), 20, 140, align="topleft")

        # Seviye içi görev göstergesi (Sonsuz labirent modunda devre dışı)
        if not is_endless_maze and not is_dark_mode and not is_acceleration_mode and current_level_in_game <= len(level_configs):
            quest_text = texts[language]["quest"].format(level_configs[current_level_in_game]['score_to_next'])
            draw_text(screen, quest_text, 32, (255, 255, 0), WINDOW_WIDTH // 2, 50, align="center")

        # Boss uyarısı (Sadece boss seviyesinde)
        if current_level_in_game == 15 and boss_pos:
            draw_text(screen, texts[language]["boss_active"], 40, (255, 0, 0), WINDOW_WIDTH // 2, 90, align="center")

        # Boss vuruldu mesajı
        if current_time < spiked_apple_thrown_message_timer:
            draw_text(screen, texts[language]["boss_hit"], 60, (255, 0, 0), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 150, align="center")

        # Güçlendirme durumları ve aktivasyon tuşları
        powerup_display_y = 120
        for p_name, p_key in POWERUP_KEYS.items():
            key_char = pygame.key.name(p_key).upper()
            display_text = ""
            text_color_powerup = (200, 200, 200) # Varsayılan gri

            if current_user and current_user['purchased_powerups'].get(p_name):
                if current_time < powerup_cooldown_timers.get(p_name, 0):
                    remaining_cooldown = (powerup_cooldown_timers[p_name] - current_time) // 1000 + 1
                    display_text = texts[language]["powerup_cooldown"].format(f"{key_char}: {remaining_cooldown}s")
                    text_color_powerup = (255, 100, 0) # Turuncu
                elif p_name == 'ghost_mode' and ghost_mode_uses <= 0:
                    display_text = texts[language]["powerup_no_uses"]
                    text_color_powerup = (150, 150, 150) # Gri
                else:
                    display_text = f"{texts[language][p_name]} ({key_char})" # Tuş gösterimi eklendi
                    text_color_powerup = (0, 255, 0) # Yeşil

                if p_name == 'ghost_mode':
                    display_text = f"{texts[language][p_name].split('(')[0].strip()}: {ghost_mode_uses} {texts[language]['ghost_mode'].split(' ')[-1].replace(')', '')}" # "Hayalet Modu: 10 Kullanım"
                    if ghost_mode_uses > 0 and current_time >= powerup_cooldown_timers.get(p_name, 0):
                        display_text = f"{texts[language][p_name].split('(')[0].strip()} ({key_char}): {ghost_mode_uses} {texts[language]['ghost_mode'].split(' ')[-1].replace(')', '')}"
                        text_color_powerup = (0, 255, 0)
                    elif ghost_mode_uses <= 0:
                        display_text = texts[language]["powerup_no_uses"]
                        text_color_powerup = (150, 150, 150)
            else:
                display_text = texts[language]["powerup_not_purchased"]
                text_color_powerup = (100, 100, 100) # Koyu gri

            draw_text(screen, display_text, 22, text_color_powerup, WINDOW_WIDTH - 20, powerup_display_y, align="topright") # Hizalama düzeltildi, font boyutu küçültüldü
            powerup_display_y += 25 # Satır aralığı azaltıldı

        # Seviye atlama mesajı
        if current_time < level_up_message_timer:
            draw_text(screen, texts[language]["level_up"], 80, (0, 255, 0), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, align="center")

        # Son seviye bonusu mesajı
        if current_time < final_level_bonus_message_timer:
            draw_text(screen, texts[language]["final_level_bonus"], 80, (255, 215, 0), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80, align="center")

        # Boss yenildi animasyonu çizimi
        if boss_defeated_animation_active:
            screen.fill((255, 165, 0)) # Orange background
            full_message = texts[language]["boss_end_message"]
            font_size = 48
            font = pygame.font.SysFont("Arial", font_size, bold=True)
            wrapped_lines = wrap_text(full_message, font, WINDOW_WIDTH - 200) # 100px padding on each side

            total_chars_in_message = sum(len(line) for line in wrapped_lines) + len(wrapped_lines) # +1 for implied space/newline between lines

            if current_time - boss_defeated_animation_start_time > BOSS_DEFEATED_ANIMATION_DELAY:
                if boss_defeated_animation_char_index < total_chars_in_message:
                    boss_defeated_animation_char_index += 1
                    boss_defeated_animation_start_time = current_time
                else:
                    # All characters displayed, wait for the total display time
                    if current_time >= boss_defeated_final_message_timer:
                        running_flag = False # End game loop to transition to game_won_screen
                        game_outcome = "won" # Set outcome to won
            
            current_char_typed = 0
            # Calculate starting Y to center the block of text
            total_text_height = len(wrapped_lines) * font_size + (len(wrapped_lines) - 1) * 10 # Assuming 10px line spacing
            start_y_offset = (WINDOW_HEIGHT - total_text_height) // 2

            for i, line in enumerate(wrapped_lines):
                chars_in_this_line = len(line)
                display_portion = min(chars_in_this_line, max(0, boss_defeated_animation_char_index - current_char_typed))
                draw_text(screen, line[:display_portion], font_size, (255, 255, 255), WINDOW_WIDTH // 2, start_y_offset + i * (font_size + 10), align="center")
                current_char_typed += chars_in_this_line + 1 # +1 for implied space/newline

            pygame.display.flip()
            clock.tick(30)
            continue # Skip normal game drawing and logic


        # Oyun içi çıkış butonu
        quit_rect_game = pygame.Rect(WINDOW_WIDTH - 170, 20, 150, 60)
        draw_rounded_rect(screen, (180, 50, 50), quit_rect_game, 10)
        draw_text(screen, texts[language]["exit"], 36, (255, 255, 255), quit_rect_game.centerx, quit_rect_game.centery, align="center")

        pygame.display.flip()
        clock.tick(snake_speed)

    # Oyun Bitti Ekranı
    if current_user: # Misafir değilse skor ve altın kaydet
        if score > current_user['high_score']:
            current_user['high_score'] = score
        current_user['gold'] = gold
        # Power-up'ları sıfırla (tek kullanımlık)
        for p_name in current_user['purchased_powerups']:
            current_user['purchased_powerups'][p_name] = False
        save_user_data()

    if game_outcome == "won":
        return "game_won_screen", score, gold
    else: # Default or "lost"
        return "game_over_screen", score, gold

# ------------------------------------------------------------------
# OYUN - CENNET MODU (Paradise Mode)
def game_loop_paradise():
    global gold, admin_mode, extra_lives_count, extra_growth, custom_snake_color, language, theme, WINDOW_WIDTH, WINDOW_HEIGHT, block_size
    global current_user, users, ghost_mode_uses, speed_boost_active_duration, shield_active_duration, gold_magnet_active_duration, thorns_active_duration
    global powerup_cooldown_timers
    global countdown_active, countdown_start_time

    # current_level_in_game = 1 # Cennet modunda seviye atlama kaldırıldığı için bu satır kaldırıldı

    # Oyun başlangıcında güçlendirmeleri sıfırla ve satın alınanları etkinleştir
    ghost_mode_uses = 0
    speed_boost_active_duration = 0
    shield_active_duration = 0
    gold_magnet_active_duration = 0
    thorns_active_duration = 0 # Cennet modunda da kullanılmıyor

    if current_user and current_user.get('purchased_powerups'):
        if current_user['purchased_powerups'].get('ghost_mode'):
            ghost_mode_uses = 10 # 10 kullanım
        # Diğer güçlendirmeler tuşa basıldığında aktif olacak, bu yüzden başlangıçta süreleri 0.

    cols = WINDOW_WIDTH // block_size
    rows = WINDOW_HEIGHT // block_size
    apples = {(c, r): True for c in range(cols) for r in range(rows)} # Tüm ekranı elmalarla doldur
    last_refill_time = pygame.time.get_ticks()

    start_col_pixel = (cols // 2) * block_size
    start_row_pixel = (rows // 2) * block_size
    snake = [(start_col_pixel, start_row_pixel)]

    direction = (block_size, 0)
    growth_counter = 0; score = 0
    lives = (1 + extra_lives_count) if not admin_mode else float('inf')
    snake_speed_base = 10 # Cennet modunun hızı sabit tutuldu
    gold_per_apple = 1 # Cennet modunda her elma 1 altın veriyor

    snake_speed = snake_speed_base # Hız takviyesi için başlangıç değeri
    
    # Seviye atlama mesajı
    level_up_message_timer = 0
    final_level_bonus_message_timer = 0

    countdown_active = True
    countdown_start_time = pygame.time.get_ticks()

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if not countdown_active: # Geri sayım bitmeden hareket etme
                    if event.key == pygame.K_UP and direction != (0, block_size): direction = (0, -block_size)
                    elif event.key == pygame.K_DOWN and direction != (0, -block_size): direction = (0, block_size)
                    elif event.key == pygame.K_LEFT and direction != (block_size, 0): direction = (-block_size, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-block_size, 0): direction = (block_size, 0)
                    
                    # Güçlendirme aktivasyonu (Yeni Eklendi)
                    for p_name, p_key in POWERUP_KEYS.items():
                        if event.key == p_key and current_user and current_user['purchased_powerups'].get(p_name):
                            if current_time >= powerup_cooldown_timers.get(p_name, 0): # Bekleme süresi bitti mi?
                                if p_name == 'ghost_mode' and ghost_mode_uses > 0:
                                    ghost_mode_uses -= 1
                                    powerup_cooldown_timers[p_name] = current_time + POWERUP_COOLDOWNS[p_name]
                                elif p_name == 'speed_boost':
                                    speed_boost_active_duration = 10000 # 10 saniye
                                    powerup_cooldown_timers[p_name] = current_time + POWERUP_COOLDOWNS[p_name]
                                elif p_name == 'shield':
                                    shield_active_duration = 10000 # 10 saniye
                                    powerup_cooldown_timers[p_name] = current_time + POWERUP_COOLDOWNS[p_name]
                                elif p_name == 'gold_magnet':
                                    gold_magnet_active_duration = 10000 # 10 saniye
                                    powerup_cooldown_timers[p_name] = current_time + POWERUP_COOLDOWNS[p_name]

            if event.type == pygame.MOUSEBUTTONDOWN:
                quit_rect_game = pygame.Rect(WINDOW_WIDTH - 170, 20, 150, 60)
                if quit_rect_game.collidepoint(event.pos):
                    # Oyuncunun skorunu ve altınlarını kaydet
                    if current_user:
                        if score > current_user['high_score']:
                            current_user['high_score'] = score
                        current_user['gold'] = gold
                        # Power-up'ları sıfırla (tek kullanımlık)
                        for p_name in current_user['purchased_powerups']:
                            current_user['purchased_powerups'][p_name] = False
                        save_user_data()
                    return "menu", score, gold # Return score and gold

        if countdown_active:
            # Geri sayım süresini hesapla
            time_left = 3000 - (current_time - countdown_start_time)
            countdown_number = max(0, (time_left // 1000) + 1) # 3, 2, 1

            screen.fill(level_configs[1]['bg_color']) # Cennet modunda sabit bir arka plan rengi
            if countdown_number > 0:
                draw_text(screen, str(countdown_number), 150, (255, 255, 255), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, align="center")
            else:
                draw_text(screen, texts[language]["countdown_go"], 150, (0, 255, 0), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, align="center")
                pygame.display.flip()
                pygame.time.wait(500)
                countdown_active = False # Geri sayım bitti

            pygame.display.flip()
            clock.tick(30) # Geri sayım sırasında sabit FPS
            continue # Oyun mantığını atla

        # Güçlendirme sürelerini güncelle
        if speed_boost_active_duration > 0:
            speed_boost_active_duration -= clock.get_time()
            if speed_boost_active_duration <= 0:
                snake_speed = snake_speed_base # Süre bittiğinde hızı normale döndür
            else:
                snake_speed = snake_speed_base * 1.5 # Hız takviyesi aktif
        else:
            snake_speed = snake_speed_base # Hız takviyesi yoksa normal hız

        if shield_active_duration > 0:
            shield_active_duration -= clock.get_time()
            if shield_active_duration <= 0:
                shield_active_duration = 0 # Süre bitti

        if gold_magnet_active_duration > 0:
            gold_magnet_active_duration -= clock.get_time()
            if gold_magnet_active_duration <= 0:
                gold_magnet_active_duration = 0 # Süre bitti

        head = snake[0]
        potential_new_head_x = head[0] + direction[0]
        potential_new_head_y = head[1] + direction[1]

        new_head_pixel_final = (potential_new_head_x, potential_new_head_y)

        # Duvar çarpışması ve admin modu sarma
        collision_with_wall = False
        if admin_mode:
            current_col_index = potential_new_head_x // block_size
            current_row_index = potential_new_head_y // block_size
            wrapped_col = current_col_index % cols
            wrapped_row = current_row_index % rows
            new_head_pixel_final = (wrapped_col * block_size, wrapped_row * block_size)
        else:
            new_cell = (new_head_pixel_final[0] // block_size, new_head_pixel_final[1] // block_size)
            if new_cell[0] < 0 or new_cell[0] >= cols or new_cell[1] < 0 or new_cell[1] >= rows:
                collision_with_wall = True

        # Kendine çarpma
        collision_with_self = False
        if new_head_pixel_final in snake:
            collision_with_self = True

        # Çarpışma işleme
        if (collision_with_wall or collision_with_self) and not admin_mode:
            if shield_active_duration > 0: # Kalkan aktifse çarpışmayı engelle
                pass
            elif ghost_mode_uses > 0: # Hayalet modu aktifse
                ghost_mode_uses -= 1
                # Yılanı ortaya ışınla
                snake = [( (cols // 2) * block_size, (rows // 2) * block_size )] # Reset
                direction = (block_size, 0); growth_counter = 0
                continue # Yeni frame'e geç
            elif lives > 1:
                lives -= 1; waiting = True
                while waiting:
                    screen.fill((25, 25, 25) if theme == "black" else (240, 240, 240))
                    draw_text(screen, texts[language]["lost_life"].format(int(lives)), 64, (255, 50, 50), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, align="center")
                    pygame.display.flip()
                    for ev in pygame.event.get():
                        if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN): waiting = False
                    clock.tick(5)
                snake = [( (cols // 2) * block_size, (rows // 2) * block_size )]
                direction = (block_size, 0); growth_counter = 0
                continue
            else: running = False; break

        if not running: continue

        snake.insert(0, new_head_pixel_final)
        new_cell = (new_head_pixel_final[0] // block_size, new_head_pixel_final[1] // block_size)

        # Altın Mıknatısı etkisi
        if gold_magnet_active_duration > 0:
            # Elmayı yılana doğru çek (basit bir yaklaşım)
            for (c_idx, r_idx), exists in list(apples.items()): # apples üzerinde dönerken değiştirmemek için list()
                if exists:
                    apple_pixel_pos = (c_idx * block_size, r_idx * block_size)
                    if apple_pixel_pos[0] > new_head_pixel_final[0]: apple_pixel_pos = (apple_pixel_pos[0] - block_size, apple_pixel_pos[1])
                    elif apple_pixel_pos[0] < new_head_pixel_final[0]: apple_pixel_pos = (apple_pixel_pos[0] + block_size, apple_pixel_pos[1])
                    if apple_pixel_pos[1] > new_head_pixel_final[1]: apple_pixel_pos = (apple_pixel_pos[0], apple_pixel_pos[1] - block_size)
                    elif apple_pixel_pos[1] < new_head_pixel_final[1]: apple_pixel_pos = (apple_pixel_pos[0], apple_pixel_pos[1] + block_size)
                    # Yeni pozisyonu güncelleyelim (basit bir çekim simülasyonu)
                    new_apple_cell = (apple_pixel_pos[0] // block_size, apple_pixel_pos[1] // block_size)
                    if new_apple_cell != (c_idx, r_idx):
                        apples[new_apple_cell] = True
                        apples[(c_idx, r_idx)] = False


        if apples.get(new_cell, False): # Elma yendi mi kontrol et
            score += 1
            gold += gold_per_apple # Cennet modunda 1 altın
            growth_counter += (3 if extra_growth else 1)
            apples[new_cell] = False # Elmayı kaldır

            # Cennet modunda seviye atlama kaldırıldı.

        else:
            if growth_counter > 0: growth_counter -= 1
            else: snake.pop()

        # Elmaların yenilenmesi
        if current_time - last_refill_time >= 3000: # 3 saniyede bir yenile
            for c_idx in range(cols):
                for r_idx in range(rows): apples[(c_idx, r_idx)] = True
            last_refill_time = current_time

        # Cennet modunda sabit tema renkleri
        bg_color = level_configs[1]['bg_color']
        snake_color_default_for_level = level_configs[1]['snake_color_default']
        apple_color_for_level = level_configs[1]['apple_color']

        screen.fill(bg_color)

        # Elmaların çizimi
        for (c_idx, r_idx), exists in apples.items():
            if exists:
                draw_rounded_rect(screen, apple_color_for_level, pygame.Rect(c_idx * block_size, r_idx * block_size, block_size, block_size), block_size // 4)

        # Yılan çizimi
        snake_color_to_draw = custom_snake_color if custom_snake_color is not None else snake_color_default_for_level
        for i, segment in enumerate(snake):
            if i == 0: # Yılanın başı
                draw_rounded_rect(screen, snake_color_to_draw, pygame.Rect(segment[0], segment[1], block_size, block_size), block_size // 4, border_color=(255,255,255), border_width=2)
            else:
                draw_rounded_rect(screen, snake_color_to_draw, pygame.Rect(segment[0], segment[1], block_size, block_size), block_size // 4)

        # Skor, Can, Altın göstergeleri (Seviye göstergesi kaldırıldı)
        draw_text(screen, f"{texts[language]['score']}: {score}", 36, (0, 200, 0), 20, 20, align="topleft")
        if not admin_mode: draw_text(screen, f"{texts[language]['lives']}: {int(lives)}", 36, (0, 200, 0), 20, 60, align="topleft")
        draw_text(screen, f"{texts[language]['gold']}: {gold}", 36, (255, 215, 0), 20, 100, align="topleft")

        # Güçlendirme durumları ve aktivasyon tuşları (Yeni Eklendi)
        powerup_display_y = 120
        for p_name, p_key in POWERUP_KEYS.items():
            key_char = pygame.key.name(p_key).upper()
            display_text = ""
            text_color_powerup = (200, 200, 200) # Varsayılan gri

            if current_user and current_user['purchased_powerups'].get(p_name):
                if current_time < powerup_cooldown_timers.get(p_name, 0):
                    remaining_cooldown = (powerup_cooldown_timers[p_name] - current_time) // 1000 + 1
                    display_text = texts[language]["powerup_cooldown"].format(f"{key_char}: {remaining_cooldown}s")
                    text_color_powerup = (255, 100, 0) # Turuncu
                elif p_name == 'ghost_mode' and ghost_mode_uses <= 0:
                    display_text = texts[language]["powerup_no_uses"]
                    text_color_powerup = (150, 150, 150) # Gri
                else:
                    display_text = f"{texts[language][p_name]} ({key_char})" # Tuş gösterimi eklendi
                    text_color_powerup = (0, 255, 0)

                if p_name == 'ghost_mode':
                    display_text = f"{texts[language][p_name].split('(')[0].strip()}: {ghost_mode_uses} {texts[language]['ghost_mode'].split(' ')[-1].replace(')', '')}"
                    if ghost_mode_uses > 0 and current_time >= powerup_cooldown_timers.get(p_name, 0):
                        display_text = f"{texts[language][p_name].split('(')[0].strip()} ({key_char}): {ghost_mode_uses} {texts[language]['ghost_mode'].split(' ')[-1].replace(')', '')}"
                        text_color_powerup = (0, 255, 0)
                    elif ghost_mode_uses <= 0:
                        display_text = texts[language]["powerup_no_uses"]
                        text_color_powerup = (150, 150, 150)
            else:
                display_text = texts[language]["powerup_not_purchased"]
                text_color_powerup = (100, 100, 100) # Koyu gri

            draw_text(screen, display_text, 22, text_color_powerup, WINDOW_WIDTH - 20, powerup_display_y, align="topright") # Hizalama düzeltildi, font boyutu küçültüldü
            powerup_display_y += 25 # Satır aralığı azaltıldı

        # Oyun içi çıkış butonu
        quit_rect_game = pygame.Rect(WINDOW_WIDTH - 170, 20, 150, 60)
        draw_rounded_rect(screen, (180, 50, 50), quit_rect_game, 10)
        draw_text(screen, texts[language]["exit"], 36, (255, 255, 255), quit_rect_game.centerx, quit_rect_game.centery, align="center")

        pygame.display.flip()
        clock.tick(snake_speed)

    # Oyun Bitti Ekranı
    if current_user: # Misafir değilse skor ve altın kaydet
        if score > current_user['high_score']:
            current_user['high_score'] = score
        current_user['gold'] = gold
        # Power-up'ları sıfırla (tek kullanımlık)
        for p_name in current_user['purchased_powerups']:
            current_user['purchased_powerups'][p_name] = False
        save_user_data()

    return "game_over_screen", score, gold # Yeni "game_over_screen" durumuna geç ve skor/altın gönder

# ------------------------------------------------------------------
# OYUN BİTTİ EKRANI
def game_over_screen(final_score, final_gold): # Skor ve altın argüman olarak alındı
    global language, theme
    bg_color = (25, 25, 25) if theme == "black" else (240, 240, 240)
    text_color = (255, 255, 255) if theme == "black" else (50, 50, 50)

    while True:
        screen.fill(bg_color)
        draw_text(screen, texts[language]["game_over"], 64, (255, 50, 50), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100, align="center")
        draw_text(screen, f"{texts[language]['score']}: {final_score}", 48, text_color, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20, align="center")
        draw_text(screen, f"{texts[language]['gold']}: {final_gold}", 48, (255, 215, 0), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40, align="center")

        restart_rect = pygame.Rect(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 + 100, 400, 100)
        draw_rounded_rect(screen, (100, 100, 100), restart_rect, 15)
        draw_text(screen, texts[language]["restart"], 48, (255, 255, 255), restart_rect.centerx, restart_rect.centery, align="center")
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if event.type == pygame.MOUSEBUTTONDOWN and not restart_rect.collidepoint(event.pos): continue
                return "menu"
        clock.tick(10)

# ------------------------------------------------------------------
# OYUN KAZANILDI EKRANI
def game_won_screen(final_score, final_gold): # Skor ve altın argüman olarak alındı
    global language, theme
    bg_color = (25, 25, 25) if theme == "black" else (240, 240, 240)
    text_color = (255, 255, 255) if theme == "black" else (50, 50, 50)

    while True:
        screen.fill(bg_color)
        draw_text(screen, texts[language]["game_won"], 64, (0, 255, 0), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100, align="center")
        draw_text(screen, f"{texts[language]['score']}: {final_score}", 48, text_color, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20, align="center")
        draw_text(screen, f"{texts[language]['gold']}: {final_gold}", 48, (255, 215, 0), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40, align="center")

        restart_rect = pygame.Rect(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 + 100, 400, 100)
        draw_rounded_rect(screen, (100, 100, 100), restart_rect, 15)
        draw_text(screen, texts[language]["restart"], 48, (255, 255, 255), restart_rect.centerx, restart_rect.centery, align="center")
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if event.type == pygame.MOUSEBUTTONDOWN and not restart_rect.collidepoint(event.pos): continue
                return "menu"
        clock.tick(10)

# ------------------------------------------------------------------
# ANA PROGRAM DÖNGÜSÜ
def main():
    state = "auth" # İlk olarak giriş/kayıt ekranı ile başla
    final_score = 0 # Initialize final_score
    final_gold = 0 # Initialize final_gold
    while True:
        if state == "auth": state = auth_menu()
        elif state == "menu": state = main_menu()
        elif state == "settings": state = settings_menu()
        elif state == "market": state = market_menu()
        elif state == "high_scores": state = high_scores_menu() # Yeni yüksek skorlar menüsü
        elif state == "difficulty": state = difficulty_menu()
        elif state in ["easy", "normal", "hard", "endless_maze", "dark_mode", "acceleration_mode"]: # Yeni modlar eklendi
            state, final_score, final_gold = game_loop_classic(state)
        elif state == "paradise":
            state, final_score, final_gold = game_loop_paradise()
        elif state == "game_over_screen": state = game_over_screen(final_score, final_gold) # Yeni oyun bitti ekranı
        elif state == "game_won_screen": state = game_won_screen(final_score, final_gold) # Yeni oyun kazanıldı ekranı

if __name__ == "__main__":
    main()
