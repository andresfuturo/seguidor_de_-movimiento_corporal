import cv2
import mediapipe as mp
import numpy as np
import time
import threading
import winsound
import tkinter as tk
from tkinter import simpledialog, messagebox
import requests
from requests.auth import HTTPBasicAuth
from queue import Queue
from threading import Thread

# Variables de control
draw_pose = True
show_text = True
timer_running = False
timer_seconds = 0
timer_start_time = 0
alarm_sounding = False

# Configuración de la cámara
CAMERA_TYPE = "pc"  # "pc" o "phone"
PHONE_IP = "192.168.20.111:4747"  # IP y puerto del celular
frame_queue = Queue(maxsize=1)
stop_thread = False

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

def setup_pc_camera():
    """Configura la cámara web del PC"""
    print("🔍 Configurando cámara del PC...")
    
    # Listar todas las cámaras disponibles
    index = 0
    arr = []
    while index < 3:  # Revisar las primeras 3 cámaras
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.read()[0]:
            arr.append(index)
            cap.release()
        index += 1
    
    print(f"Cámaras disponibles: {arr}")
    
    # Intentar con la cámara 1 primero (índice 1)
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    
    # Si no se pudo abrir, intentar con la cámara 0
    if not cap.isOpened() or not cap.read()[0]:
        print("No se pudo abrir la cámara 1, intentando con la cámara 0...")
        cap.release()
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened() or not cap.read()[0]:
        print("❌ No se pudo abrir ninguna cámara del PC")
        return None
    
    # Configurar resolución
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print(f"✅ Cámara del PC configurada correctamente (índice {1 if cap.isOpened() else 0})")
    return cap

def phone_stream_worker():
    """Hilo para capturar el stream del celular"""
    global stop_thread, frame_queue
    url = f'http://{PHONE_IP}/video'
    bytes_data = bytes()
    
    while not stop_thread:
        try:
            with requests.get(url, stream=True, timeout=5) as response:
                for chunk in response.iter_content(chunk_size=1024):
                    if stop_thread:
                        break
                    if chunk:
                        bytes_data += chunk
                        a = bytes_data.find(b'\xff\xd8')
                        b = bytes_data.find(b'\xff\xd9')
                        
                        if a != -1 and b != -1:
                            jpg = bytes_data[a:b+2]
                            bytes_data = bytes_data[b+2:]
                            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                if frame_queue.full():
                                    frame_queue.get()
                                frame_queue.put(frame)
        except Exception as e:
            print(f"Error en el stream del celular: {e}")
            time.sleep(1)

def setup_phone_camera():
    """Configura la cámara del celular"""
    global stop_thread
    print(f"📱 Intentando conectar al celular en {PHONE_IP}...")
    
    # Iniciar el hilo para el stream del celular
    stop_thread = False
    stream_thread = Thread(target=phone_stream_worker, daemon=True)
    stream_thread.start()
    
    # Esperar a que llegue el primer frame
    start_time = time.time()
    while frame_queue.empty():
        if time.time() - start_time > 10:  # Timeout de 10 segundos
            stop_thread = True
            stream_thread.join(timeout=1)
            print("❌ No se pudo conectar con el celular")
            return None
        time.sleep(0.1)
    
    print("✅ Conexión exitosa con el celular")
    return "phone"  # Retornamos un marcador ya que no usamos cap_cam para el celular

def select_camera():
    """Muestra un diálogo para seleccionar la cámara"""
    root = tk.Tk()
    root.withdraw()
    
    # Crear un diálogo personalizado
    choice = simpledialog.askstring(
        "Seleccionar Cámara",
        "Seleccione la cámara a utilizar:\n\n"
        "1: Usar cámara del celular (vía WiFi)\n"
        "2: Usar cámara web del PC\n\n"
        "Ingrese 1 o 2:"
    )
    
    if choice == '1':
        return setup_phone_camera()
    elif choice == '2':
        return setup_pc_camera()
    else:
        messagebox.showerror("Error", "Opción no válida. Saliendo del programa.")
        return None

# Seleccionar y configurar la cámara
camera = select_camera()
if camera is None:
    print("No se pudo inicializar ninguna cámara")
    exit()

# Inicializar según el tipo de cámara
if camera == "phone":
    cap_cam = None  # No usamos cap_cam para el teléfono
else:
    cap_cam = camera

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
    
    # Obtener frame según la cámara seleccionada
    if camera == "phone":
        if frame_queue.empty():
            continue
        frame = frame_queue.get()
        ret = True
    else:
        ret, frame = cap_cam.read()
        if not ret:
            print("Error al capturar frame de la cámara del PC")
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
    elapsed = current_time - timer_start_time if timer_running else 0
    remaining = max(0, timer_seconds - int(elapsed))
    
    if timer_running and remaining <= 0 and not alarm_sounding:
        # Tiempo terminado, activar alarma
        timer_running = False
        threading.Thread(target=play_alarm, daemon=True).start()
        remaining = 0
    
    # Mostrar tiempo restante (siempre visible)
    mins, secs = divmod(remaining, 60)
    timer_text = f'Tiempo: {mins:02d}:{secs:02d}'
    
    # Cambiar color del texto según el estado
    if remaining == 0:
        color = (0, 255, 255)  # Amarillo cuando el tiempo terminó
    elif remaining < 10:
        color = (0, 0, 255)    # Rojo cuando quedan menos de 10 segundos
    else:
        color = (0, 255, 0)    # Verde cuando hay tiempo suficiente
    
    cv2.putText(frame, timer_text, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    
    # Mostrar estado actual en la pantalla (el resto del texto)
    if show_text:
        status_text = "Lineas: ACTIVADAS" if draw_pose else "Lineas: DESACTIVADAS"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, "S: Mostrar lineas  H: Ocultar lineas", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Q o ESC: Salir", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "T: Configurar tiempo", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Espacio: Iniciar/Detener", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "D: Mostrar/Ocultar texto", (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Mostrar en ventana
    window_title = "Detector Movimiento - Cámara del " + ("Celular" if camera == "phone" else "PC")
    cv2.imshow(window_title, frame)
    
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

# Liberar recursos
if camera != "phone" and cap_cam is not None:
    cap_cam.release()

# Detener el hilo del stream del celular
stop_thread = True
cv2.destroyAllWindows()
