import pygame
from adafruit_servokit import ServoKit

# --- BEÁLLÍTÁSOK ---
# Ha Adafruit Motor/Servo HAT-et használsz, az általában 16 csatornás
kit = ServoKit(channels=16)

# Kezdő pozíciók (90 fok = középállás)
arm_angle = 90
base_angle = 90

# Milyen gyorsan mozogjon? (Fok / ciklus)
STEP = 2 

pygame.init()
screen = pygame.display.set_mode((300, 200))
pygame.display.set_caption("Szervó Kar Vezérlő")
font = pygame.font.SysFont("Arial", 20)

print("Vezérlés: I/K (Kar fel-le), J/L (Forgás), ESC (Kilépés)")

running = True
clock = pygame.time.Clock()

while running:
    # Események (pl. ablak bezárás)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Billentyűk figyelése
    keys = pygame.key.get_pressed()

    # --- KAR MOZGATÁSA (Channel 1, 2, 3 egyszerre) ---
    if keys[pygame.K_i]:
        arm_angle += STEP
    if keys[pygame.K_k]:
        arm_angle -= STEP

    # --- BÁZIS FORGATÁSA (Channel 0) ---
    if keys[pygame.K_j]:   # Balra (vagy jobbra, bekötéstől függ)
        base_angle += STEP
    if keys[pygame.K_l]:   # Jobbra
        base_angle -= STEP

    # --- HATÁROLÁS (Geci-védelem) ---
    # Ne engedjük 0 alá vagy 180 fölé, mert leég a szervó
    if arm_angle > 180: arm_angle = 180
    if arm_angle < 0: arm_angle = 0
    
    if base_angle > 180: base_angle = 180
    if base_angle < 0: base_angle = 0

    # --- FIZIKAI MOZGATÁS ---
    try:
        # Kar: 1, 2, 3 csatornák
        kit.servo[1].angle = arm_angle
        kit.servo[2].angle = arm_angle
        kit.servo[3].angle = arm_angle
        
        # Bázis: 0 csatorna
        kit.servo[0].angle = base_angle
    except Exception as e:
        print(f"Hiba a motorvezérlésben: {e}")

    # --- KIÍRATÁS A KÉPERNYŐRE ---
    screen.fill((0, 0, 0)) # Fekete háttér
    text_arm = font.render(f"Kar szög (Ch 1-3): {arm_angle}", True, (255, 255, 255))
    text_base = font.render(f"Bázis szög (Ch 0): {base_angle}", True, (255, 255, 255))
    screen.blit(text_arm, (20, 50))
    screen.blit(text_base, (20, 80))
    
    pygame.display.flip()
    
    # Kilépés ESC-re
    if keys[pygame.K_ESCAPE]:
        running = False

    # FPS limit (hogy ne pörögjön túl gyorsan a ciklus és a motor)
    clock.tick(60)

pygame.quit()