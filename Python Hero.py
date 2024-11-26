import moviepy
import os
import time
import pygame
import sys
import configparser
from moviepy.editor import VideoFileClip

#Los archivos para verificar el programa pueden ser descargados desde https://www.enchor.us
#Cualquiera deberia servir mientras el charter no sea Neversoft, Harmonix o Beenox 
#O que el archivo "notes" tenga extension .mid en vez de .chart -> notes.mid x | notes.chart OK
#El archivo debe ser descargado en .zip, ya que a fecha de escribir esto casi ningun programa fuera de CH o YARG es compatible con .sng

# Inicializar Pygame
pygame.init()

# Definir colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)

# Configuración del juego
speed_multiplier = 2
note_speed = 1
TARGET_FPS = 60
offset_ms = 100

# Definir dimensiones de la ventana y carriles
screen_width = 800
screen_height = 600
lane_width = screen_width // 5

# Crear ventana
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Guitar Hero en Python")

# Cargar y reproducir la música
pygame.mixer.music.load("") #acá debe ir la ruta del archivo song.mp3, por ejemplo D:/Clone Hero/Songs/songss/ITZY - SWIPE/song.mp3
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.1)
# Cargar el video
def cargar_video(ruta_video):
    try:
        clip = VideoFileClip(ruta_video)
        return clip
    except Exception as e:
        print(f"Error al cargar el video: {e}")
        return None

config = configparser.ConfigParser()
config.read("D:/Clone Hero/Songs/songss/ITZY - SWIPE/song.ini") #acá debe ir la ruta del archivo song.ini, por ejemplo D:/Clone Hero/Songs/songss/ITZY - SWIPE/song.ini
last_video_time = -1
clock = pygame.time.Clock()
def cargar_superficie_video(tiempo):
    global superficie_video, last_video_time
    frame = clip.get_frame(tiempo)
    frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
    superficie_video = pygame.transform.scale(frame, (screen_width, screen_height))
    last_video_time = tiempo

# Clase para representar una nota
class Note:
    def __init__(self, lane, time=0):
        self.lane = lane
        self.time = time
        self.color = [GREEN, RED, YELLOW, BLUE, ORANGE][lane]
        self.y = -20
        self.rect = pygame.Rect(lane * lane_width + lane_width // 4, self.y, lane_width // 2, 20)

    def move(self, speed):
        self.y += speed
        self.rect.y = self.y

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)

def ticks_to_seconds(ticks, bpm, resolution):
    return (60 / bpm) * (ticks / resolution)

# Cargar el chart y los eventos de sincronización
def load_chart(chart_path, note_speed):
    notes = []
    bpm = 101 # todos estos numeros deben ser cambiados a mano para lograr una mejor sincronización
    resolution = 192  # Resolución del chart, usualmente se encuentra en el archivo .chart
    sync_events = []
    last_time = -1

    with open(chart_path, 'r') as file:
        for line in file:
            if line.startswith("#") or not line.strip() or line.startswith("["):
                continue

            parts = line.strip().split()

            if len(parts) >= 4 and parts[1] == "=" and parts[2] == "N":
                try:
                    lane = int(parts[3]) % 5
                    ticks = int(parts[0])
                    time = ticks_to_seconds(ticks, bpm, resolution)
                    if time != last_time:
                        notes.append(Note(lane, time))
                        last_time = time
                except ValueError:
                    print(f"Error parsing lane or time: {line.strip()}")

            elif len(parts) >= 3 and parts[1] == "=" and (parts[2] == "TS" or parts[2] == "B"):
                offset = int(parts[0])
                event = parts[2]
                value = parts[3]
                sync_events.append((offset, event, value))

    return notes, sync_events, bpm

# Cargar las notas del chart (UNA SOLA VEZ)
chart_path = "" #acá debe ir la ruta del archivo song.ini, por ejemplo D:/Clone Hero/Songs/songss/ITZY - SWIPE/notes.chart
notes, sync_events, bpm = load_chart(chart_path, note_speed)

print(f"Total de notas cargadas: {len(notes)}")

def get_current_time():
    return pygame.mixer.music.get_pos() + offset_ms

# Puntuación y racha de notas
score = 0
streak = 0
multiplier = 1

# Cargar el video
video_path = "" #acá debe ir la ruta del archivo song.ini, por ejemplo D:/Clone Hero/Songs/songss/D:/Clone Hero/Songs/songss/ITZY - SWIPE/video.mp4
clip = VideoFileClip(video_path)
superficie_video = None  # Superficie para mostrar el fotograma del video
desfase_tiempo_video = -1  # Desfase para sincronizar el video con la música

# Bucle principal del juego
running = True
paused = False
paused_time = 0
paused_streak, paused_multiplier = 0, 1
clock = pygame.time.Clock()
start_time = time.time()

def draw_game_state():
    # Dibujar los carriles y los marcadores de cada carril
    for i, color in enumerate([GREEN, RED, YELLOW, BLUE, ORANGE]):
        pygame.draw.rect(screen, color, (i * lane_width, screen_height - 50, lane_width, 20))
        pygame.draw.circle(screen, color, (i * lane_width + lane_width // 2, screen_height - 40), 20)

    # Dibujar las notas
    for note in notes:
        note.move(note_speed * speed_multiplier)
        note.draw(screen)

    # Mostrar la puntuación, racha y multiplicador en la pantalla
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    streak_text = font.render(f"Streak: {streak}", True, WHITE)
    multiplier_text = font.render(f"Multiplier: x{multiplier}", True, WHITE)
    screen.blit(score_text, (10, 10))
    screen.blit(streak_text, (10, 50))
    screen.blit(multiplier_text, (10, 90))

def show_countdown():
    font = pygame.font.Font(None, 74)
    for i in range(3, 0, -1):
        draw_game_state()
        countdown_text = font.render(str(i), True, WHITE)
        text_rect = countdown_text.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(countdown_text, text_rect)
        pygame.display.flip()
        time.sleep(1)

def calculate_multiplier(streak):
    if streak >= 24:
        return 4
    elif streak >= 16:
        return 3
    elif streak >= 8:
        return 2
    else:
        return 1

config = configparser.ConfigParser()
config.read("D:/Clone Hero/Songs/songss/ITZY - SWIPE/song.ini") #acá debe ir la ruta del archivo song.ini, por ejemplo D:/Clone Hero/Songs/songss/ITZY - SWIPE/song.ini
offset = int(config.get("Song", "offset", fallback=0))
video_delay = int(config.get("Song", "VideoLeadIn", fallback=0))

# Mostrar la cuenta regresiva antes de comenzar el juego
start_time = time.time() - offset / 1000
#show_countdown()

while running:
    current_time = get_current_time()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN and not paused:
            if event.key == pygame.K_ESCAPE:
                paused = not paused
                if not paused:
                    paused_time += (time.time() - start_time - paused_time) * 1000
                    start_time = time.time()
                    streak, multiplier = paused_streak, paused_multiplier
                else:
                    paused_time = current_time
                    paused_streak, paused_multiplier = streak, multiplier

            else:
                hit_note = False
                for i, note in enumerate(notes):
                    if note.y > screen_height - 150 and note.y < screen_height - 30:
                        if (note.lane == 0 and event.key == pygame.K_d) or \
                                (note.lane == 1 and event.key == pygame.K_f) or \
                                (note.lane == 2 and event.key == pygame.K_j) or \
                                (note.lane == 3 and event.key == pygame.K_k) or \
                                (note.lane == 4 and event.key == pygame.K_l):
                            del notes[i]
                            streak += 1
                            multiplier = calculate_multiplier(streak)
                            score += 10 * multiplier
                            hit_note = True
                            break
                if not hit_note:
                    streak = 0
                    multiplier = 1

    if not paused:

         # Calcular el tiempo del video en base al tiempo actual de la música
        video_time = max(0, current_time / 1010 + desfase_tiempo_video)
        video_frame = int(video_time * clip.fps)  # Calcular el número de fotograma

        # Cargar el siguiente fotograma solo si el tiempo ha avanzado lo suficiente
        if video_frame > last_video_time:
            cargar_superficie_video(video_time)


        for offset, event, value in sync_events[:]:
            if current_time >= offset:
                if event == "B":
                    bpm = int(value)
                elif event == "TS":
                    pass
                sync_events.remove((offset, event, value))

        for i, note in enumerate(notes):
            note.y = -20 + (current_time - note.time * 1000) * note_speed
    screen.fill(BLACK)
    if superficie_video:
        screen.blit(superficie_video, (0, 0))  # Dibujar el fotograma del video
    else:
        print("Error: Superficie de video no cargada.")  # Mensaje de error si hay problemas
    draw_game_state()  # Dibujar elementos del juego (notas, carriles, etc.) 
    # Dibujar el estado del juego

    draw_game_state()
    pygame.display.flip()

    # Controlar la tasa de fotogramas
    clock.tick(TARGET_FPS)

pygame.quit()
sys.exit()