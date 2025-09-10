# Detector de Movimiento con Temporizador

Aplicación de detección de movimiento y seguimiento de posturas corporales con temporizador integrado, desarrollada con Python, OpenCV y MediaPipe.

## Características

- Detección de movimiento en tiempo real
- Seguimiento de posturas corporales con MediaPipe Pose
- Temporizador configurable con alarma
- Interfaz visual intuitiva
- Controles por teclado

## Requisitos

- Python 3.7 o superior
- OpenCV (cv2)
- MediaPipe
- NumPy
- Tkinter (generalmente incluido con Python)
- Winsound (para la alarma, solo Windows)

## Instalación

1. Clona este repositorio:
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd [NOMBRE_DEL_REPOSITORIO]
   ```

2. Instala las dependencias:
   ```bash
   pip install opencv-python mediapipe numpy
   ```

## Uso

1. Ejecuta el script:
   ```bash
   python detector_de_movimiento.py
   ```

2. Controles:
   - `T`: Configurar el tiempo del temporizador (en minutos)
   - `Espacio`: Iniciar/detener el temporizador
   - `S`: Mostrar líneas del cuerpo
   - `H`: Ocultar líneas del cuerpo
   - `Q` o `ESC`: Salir de la aplicación

3. La aplicación mostrará una ventana con la cámara en tiempo real y superpondrá la detección de postura cuando esté activada.

## Personalización

- Ajusta `umbral_movimiento` en el código para cambiar la sensibilidad de la detección de movimiento.
- Modifica los parámetros de `mp_pose.Pose()` para ajustar el modelo de detección de posturas.

## Notas

- La aplicación está optimizada para Windows debido al uso de `winsound` para la alarma.
- Para usar en otros sistemas operativos, se recomienda reemplazar la función de alarma por una alternativa multiplataforma.

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.
