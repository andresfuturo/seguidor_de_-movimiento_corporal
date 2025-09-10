import cv2
import mediapipe as mp
import numpy as np
import time
import threading
import winsound
import tkinter as tk
from tkinter import simpledialog

# Variables de control
draw_pose = True
show_text = True
timer_running = False
timer_seconds = 0
timer_start_time = 0
alarm_sounding = False

# Inicializar MediaPipe Pose con configuración mejorada
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    model_complexity=2,  # Usar el modelo más complejo para mejor precisión
    enable_segmentation=True,  # Habilitar segmentación para mejor detección
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Captura de cámara local
cap_cam = cv2.VideoCapture(0)

if not cap_cam.isOpened():
    print("❌ No se pudo abrir la cámara")
    exit()

# Variables para detección de movimiento
prev_gray = None
umbral_movimiento = 50000  # ajusta sensibilidad

def play_alarm():
    global alarm_sounding
    alarm_sounding = True
    for _ in range(5):  # Sonar la alarma 5 veces
        if not timer_running:  # Detener si se detuvo el cronómetro
            break
        winsound.Beep(1000, 500)  # Frecuencia 1000Hz, duración 500ms
        time.sleep(0.5)
    alarm_sounding = False

def start_timer():
    global timer_running, timer_seconds, timer_start_time
    if not timer_running and timer_seconds > 0:
        timer_running = True
        timer_start_time = time.time()
        print(f"Cronómetro iniciado por {timer_seconds} segundos")

def stop_timer():
    global timer_running, alarm_sounding
    timer_running = False
    alarm_sounding = False
    print("Cronómetro detenido")

def set_timer():
    global timer_seconds
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal
    try:
        minutes = simpledialog.askinteger("Configurar Cronómetro", 
                                       "Ingrese los minutos para el cronómetro:", 
                                       minvalue=1, maxvalue=120)
        if minutes is not None:
            timer_seconds = minutes * 60
            return True
    except:
        pass
    return False

while True:
    current_time = time.time()
    ret, frame = cap_cam.read()
    if not ret:
        break

    # ---- Procesamiento con MediaPipe ----
    # Redimensionar la imagen para mejorar el rendimiento
    height, width = frame.shape[:2]
    frame_resized = cv2.resize(frame, (int(width * 0.8), int(height * 0.8)))
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    
    # Procesar con MediaPipe
    results = pose.process(frame_rgb)

    if results.pose_landmarks:
        if draw_pose:
            # Dibujar landmarks con diferentes colores para diferentes partes del cuerpo
            mp_drawing.draw_landmarks(
                frame_resized, 
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
            )
            # Resaltar puntos clave de las piernas
            if results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP.value]:
                cv2.circle(frame_resized, 
                         (int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP.value].x * frame_resized.shape[1]),
                          int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP.value].y * frame_resized.shape[0])),
                          8, (0, 0, 255), -1)
            
            # Añadir más puntos clave según sea necesario
            
    # Volver al tamaño original
    frame = cv2.resize(frame_resized, (width, height))

    # ---- Detección de movimiento ----
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if prev_gray is None:
        prev_gray = gray
    else:
        diff = cv2.absdiff(prev_gray, gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        movimiento = np.sum(thresh)

        # Solo detecta, ya no dibuja nada
        prev_gray = gray

    # Actualizar y mostrar el cronómetro
    if timer_running:
        elapsed = current_time - timer_start_time
        remaining = max(0, timer_seconds - int(elapsed))
        
        if remaining <= 0 and not alarm_sounding:
            # Tiempo terminado, activar alarma
            timer_running = False
            threading.Thread(target=play_alarm, daemon=True).start()
            remaining = 0
        
        # Mostrar tiempo restante
        mins, secs = divmod(remaining, 60)
        timer_text = f'Tiempo: {mins:02d}:{secs:02d}'
        cv2.putText(frame, timer_text, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255) if remaining < 10 else (0, 255, 0), 2)
    
    # Mostrar estado actual en la pantalla
    if show_text:
        status_text = "Lineas: ACTIVADAS" if draw_pose else "Lineas: DESACTIVADAS"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, "S: Mostrar lineas  H: Ocultar lineas", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Q o ESC: Salir", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "T: Configurar tiempo", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Espacio: Iniciar/Detener", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "D: Mostrar/Ocultar texto", (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Mostrar en ventana
    cv2.imshow("Detector Movimiento OBS", frame)
    
    # Control de teclado
    key = cv2.waitKey(1) & 0xFF
    
    # Debug: Mostrar la tecla presionada
    if key != 255:  # 255 significa que no se presionó ninguna tecla
        print(f"Tecla presionada: {chr(key) if key < 256 else 'keycode: ' + str(key)}")
    
    if key in (27, ord('q'), ord('Q')):  # Salir con ESC o Q
        break
    elif key in (ord('s'), ord('S')):  # Mostrar líneas con S
        draw_pose = True
        print("Mostrando líneas del cuerpo")
    elif key in (ord('h'), ord('H')):  # Ocultar líneas con H
        draw_pose = False
        print("Ocultando líneas del cuerpo")
    elif key == ord(' '):  # Espacio: Iniciar/Detener cronómetro
        if timer_seconds > 0:
            if timer_running:
                stop_timer()
            else:
                start_timer()
        else:
            print("Primero configure el tiempo con la tecla 'T'")
    elif key in (ord('t'), ord('T')):  # Configurar tiempo
        if timer_running:
            stop_timer()
        if set_timer():
            print(f"Tiempo configurado a {timer_seconds//60} minutos")
        else:
            print("Configuración de tiempo cancelada")
    elif key in (ord('d'), ord('D')):  # Mostrar/ocultar texto
        show_text = not show_text
        print(f"Texto {'mostrado' if show_text else 'ocultado'}")

cap_cam.release()
cv2.destroyAllWindows()
