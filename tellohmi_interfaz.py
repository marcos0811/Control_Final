from djitellopy import Tello
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
import time
import threading

# =======================
# Parámetros iniciales
# =======================
referencia = 50.0     # cm (modificable en HMI)
Kp = 1.20             # ganancia proporcional (modificable)
Ts = 0.05             # periodo de muestreo [s]

# =======================
# Variables globales
# =======================
altura = 0
running = True

mediciones = []
vector_u = []

# =======================
# Hilo lector de altura
# =======================
def leer_altura():
    global altura, running
    while running:
        altura = tello.get_height()
        time.sleep(Ts)

# =======================
# Inicialización Tello
# =======================
tello = Tello()
tello.connect()
tello.streamoff()

tello.takeoff()
time.sleep(2)

a0 = tello.get_height()
print(f"Altura inicial: {a0} cm")
print(f"Batería inicial: {tello.get_battery()}%")

# =======================
# Lanzar hilo
# =======================
hilo_altura = threading.Thread(target=leer_altura, daemon=True)
hilo_altura.start()

# =======================
# INTERFAZ HMI + GRÁFICA
# =======================
plt.ion()

fig, ax = plt.subplots()
plt.subplots_adjust(left=0.1, bottom=0.35)

line_altura, = ax.plot([], [], lw=2)
ax.set_xlabel("Tiempo [s]")
ax.set_ylabel("Altura [cm]")
ax.set_ylim(0, 200)
ax.grid(True)

# --- Sliders ---
ax_ref = plt.axes([0.1, 0.22, 0.8, 0.03])
ax_kp  = plt.axes([0.1, 0.15, 0.8, 0.03])

slider_ref = Slider(ax_ref, "Referencia [cm]", 0, 100, valinit=referencia)
slider_kp  = Slider(ax_kp,  "Kp", 0.0, 3.5, valinit=Kp)

# =======================
# Callbacks HMI
# =======================
def actualizar_ref(val):
    global referencia
    referencia = slider_ref.val

def actualizar_kp(val):
    global Kp
    Kp = slider_kp.val

slider_ref.on_changed(actualizar_ref)
slider_kp.on_changed(actualizar_kp)

# =======================
# Bucle principal
# =======================
inicio = time.time()

while True:
    now = time.time()

    if now - inicio > 30:
        print("TIEMPO DE VUELO TERMINADO")
        break

    altura_rel = altura - a0
    mediciones.append(altura_rel)

    # Control P digital
    error = referencia - altura_rel
    u = Kp * error
    u = max(-100, min(100, u))
    vector_u.append(u)

    tello.send_rc_control(0, 0, int(u), 0)

    # Tiempo
    t = np.linspace(0, now - inicio, len(mediciones))

    # Actualizar gráfica
    line_altura.set_data(t, mediciones)
    ax.relim()
    ax.autoscale_view()

    plt.pause(0.001)

    # Seguridad
    if altura_rel > 150:
        print("ATERRIZAJE DE EMERGENCIA")
        break

# =======================
# Finalización segura
# =======================
running = False
tello.send_rc_control(0, 0, 0, 0)
tello.land()

print(f"Batería final: {tello.get_battery()}%")

plt.ioff()
plt.show()
