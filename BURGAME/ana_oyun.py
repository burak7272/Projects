import sys
import os
import winreg
import pygame
import tkinter as tk
from tkinter import messagebox

# --- 1. DOSYA YOLU AYARI ---
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- 2. TEKİL KURULUM KONTROLÜ (Registry Mekanizması) ---
def tekil_kurulum_kontrol():
    registry_yolu = r"Software\BurGame"
    anahtar_adi = "KurulumTamamlandi"
    try:
        # Anahtarı okumaya çalış
        anahtar = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_yolu, 0, winreg.KEY_READ)
        deger, _ = winreg.QueryValueEx(anahtar, anahtar_adi)
        winreg.CloseKey(anahtar)
        if deger == "1":
            return False  # Zaten kurulu, girişi engelle
    except FileNotFoundError:
        # Eğer anahtar yoksa, bu ilk kurulumdur. Anahtarı oluştur ve 1 yaz.
        anahtar = winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_yolu)
        winreg.SetValueEx(anahtar, anahtar_adi, 0, winreg.REG_SZ, "1")
        winreg.CloseKey(anahtar)
        return True
    return True

# Programı en başta kontrol et (Sunumda bu kısım hayat kurtarır)
if not tekil_kurulum_kontrol():
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Kurulum Hatası", "Ödev Gereği: Bu uygulama bu sisteme yalnızca bir kez kurulabilir!")
    sys.exit()

# --- 3. OYUN BAŞLATMA ---
pygame.init()
GEN, YUK = 800, 600
ekran = pygame.display.set_mode((GEN, YUK))
pygame.display.set_caption("BurGame - Kastamonu Uni OOP Projesi")
clock = pygame.time.Clock()

# --- 4. OOP SINIFLARI ---
class GameObject:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

class Player(GameObject):
    def __init__(self):
        super().__init__(GEN//2 - 70, YUK - 70, 140, 50)
        self.image = pygame.image.load(resource_path("resimler/skateboard.png")).convert_alpha()
    def update(self):
        self.rect.centerx = pygame.mouse.get_pos()[0]
        self.rect.clamp_ip(ekran.get_rect())
    def draw(self, surface):
        surface.blit(pygame.transform.scale(self.image, (self.rect.w, self.rect.h)), self.rect)

class Ball(GameObject):
    def __init__(self):
        super().__init__(GEN//2, YUK//2, 22, 22)
        self.image = pygame.image.load(resource_path("resimler/ball.png")).convert_alpha()
        self.speed = [6, -6]
    def update(self):
        self.rect.x += self.speed[0]
        self.rect.y += self.speed[1]
        if self.rect.left <= 0 or self.rect.right >= GEN: self.speed[0] *= -1
        if self.rect.top <= 0: self.speed[1] *= -1
    def draw(self, surface):
        surface.blit(pygame.transform.scale(self.image, (22, 22)), self.rect)

class Brick(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 75, 25)
        self.image = pygame.image.load(resource_path("resimler/block.png")).convert_alpha()
    def draw(self, surface):
        surface.blit(pygame.transform.scale(self.image, (75, 25)), self.rect)

# --- 5. YARDIMCI FONKSİYONLAR ---
def belirgin_yazi(metin, font, renk, x, y):
    sur_outline = font.render(metin, True, (0, 0, 0))
    sur_text = font.render(metin, True, renk)
    for ox, oy in [(-2,-2), (2,-2), (-2,2), (2,2)]:
        ekran.blit(sur_outline, (x - sur_outline.get_width()//2 + ox, y + oy))
    ekran.blit(sur_text, (x - sur_text.get_width()//2, y))

def buton_ciz(metin, x, y, w, h, renk, aktif_renk):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    ustunde = x + w > mouse[0] > x and y + h > mouse[1] > y
    pygame.draw.rect(ekran, aktif_renk if ustunde else renk, (x, y, w, h), border_radius=15)
    font_btn = pygame.font.SysFont("Consolas", 30, bold=True)
    yazi = font_btn.render(metin, True, (255, 255, 255))
    ekran.blit(yazi, (x + (w - yazi.get_width())//2, y + (h - yazi.get_height())//2))
    if ustunde and click[0] == 1:
        pygame.time.delay(200)
        return True
    return False

# --- 6. OYUN KURULUMU ---
background = pygame.image.load(resource_path("resimler/arkaplan.png")).convert()
background = pygame.transform.smoothscale(background, (GEN, YUK))

MENU, OYUN, BITIS = 0, 1, 2
durum = MENU
sonuc_metni = ""
mesaj_timer = 0
aktif_mesaj = ""

def oyunu_baslat():
    global oyuncu, top, bloklar, skor, can, durum, mesaj_timer, aktif_mesaj
    oyuncu = Player(); top = Ball()
    bloklar = [Brick(c * 76 + 20, r * 26 + 60) for r in range(5) for c in range(10)]
    skor, can, mesaj_timer, aktif_mesaj = 0, 3, 0, ""
    durum = OYUN

# --- 7. ANA DÖNGÜ ---
running = True
while running:
    ekran.blit(background, (0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN and durum == OYUN:
            if event.key == pygame.K_k: bloklar.clear() # Hile

    if durum == MENU:
        f_baslik = pygame.font.SysFont("Consolas", 100, bold=True)
        belirgin_yazi("BURGAME", f_baslik, (255, 255, 255), GEN//2, 180)
        if buton_ciz("OYNA", 300, 340, 200, 70, (46, 204, 113), (39, 174, 96)):
            oyunu_baslat()

    elif durum == OYUN:
        oyuncu.update(); top.update()
        if top.rect.colliderect(oyuncu.rect):
            top.speed[1] *= -1; top.rect.bottom = oyuncu.rect.top
        for b in bloklar[:]:
            if top.rect.colliderect(b.rect):
                top.speed[1] *= -1; bloklar.remove(b); skor += 10
                if skor in [100, 200, 300]: 
                    aktif_mesaj = "IYI GIDIYORSUN!" if skor==100 else ("HARIKA!" if skor==200 else "TAM BIR PRO!")
                    mesaj_timer = 120

        if top.rect.top > YUK:
            can -= 1
            if can > 0:
                top.rect.center = (GEN//2, YUK//2); top.speed = [6, -6]; pygame.time.delay(500)
            else:
                sonuc_metni = "KAYBETTİN!"; durum = BITIS
        if len(bloklar) == 0:
            sonuc_metni = "KAZANDIN!"; durum = BITIS

        oyuncu.draw(ekran); top.draw(ekran)
        for b in bloklar: b.draw(ekran)
        f_gui = pygame.font.SysFont("Consolas", 26, bold=True)
        ekran.blit(f_gui.render(f"SKOR: {skor}", True, (255, 255, 255)), (20, 20))
        ekran.blit(f_gui.render(f"CAN: {can}", True, (255, 82, 82)), (20, 55))
        if mesaj_timer > 0:
            f_msg = pygame.font.SysFont("Consolas", 50, bold=True)
            belirgin_yazi(aktif_mesaj, f_msg, (255, 255, 0), GEN//2, YUK//2 + 100)
            mesaj_timer -= 1

    elif durum == BITIS:
        f_bitis = pygame.font.SysFont("Consolas", 90, bold=True)
        belirgin_yazi(sonuc_metni, f_bitis, (46, 204, 113) if "KAZAN" in sonuc_metni else (231, 76, 60), GEN//2, 150)
        f_skor = pygame.font.SysFont("Consolas", 40, bold=True)
        belirgin_yazi(f"Toplam Skor: {skor}", f_skor, (255, 255, 255), GEN//2, 260)
        if buton_ciz("TEKRAR", 240, 360, 150, 60, (52, 152, 219), (41, 128, 185)): oyunu_baslat()
        if buton_ciz("MENÜ", 410, 360, 150, 60, (149, 165, 166), (127, 140, 141)): durum = MENU

    pygame.display.flip(); clock.tick(60)
pygame.quit()