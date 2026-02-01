from djitellopy import Tello
import matplotlib.pyplot as plt
import numpy as np
import time
import threading

# =======================
# Parámetros de control
# =======================
referencia = 50     # cm
Kp = 3.15          # ganancia proporcional
Ts = 0.05            # periodo de muestreo [s]

# =======================
# Variables globales
# =======================
altura = 0           # altura actual [cm]
u = 0                # velocidad de control
running = True

mediciones = []      # altura relativa
e = []               # error
vector_u = []        # señal de control

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

a0 = tello.get_height()   # referencia inicial
print(f"Altura inicial: {a0} cm")
print(f"Batería inicial: {tello.get_battery()}%")

# =======================
# Lanzar hilo de sensor
# =======================
hilo_altura = threading.Thread(target=leer_altura, daemon=True)
hilo_altura.start()

# =======================
# Configuración gráficas
# =======================
plt.ion()

# Control
fig1, ax1 = plt.subplots()
line_u, = ax1.plot([], [], label="u")
ax1.set_xlabel("Tiempo [s]")
ax1.set_ylabel("u")
ax1.set_ylim(-100, 100)
ax1.grid(True)
ax1.legend()

# Error
fig2, ax2 = plt.subplots()
line_e, = ax2.plot([], [], label="Error")
ax2.set_xlabel("Tiempo [s]")
ax2.set_ylabel("Error [cm]")
ax2.set_ylim(-100, 100)
ax2.grid(True)
ax2.legend()

# Altura
fig3, ax3 = plt.subplots()
line_altura, = ax3.plot([], [], label="Altura")
ax3.set_xlabel("Tiempo [s]")
ax3.set_ylabel("Altura [cm]")
ax3.set_ylim(0, 200)
ax3.grid(True)
ax3.legend()

# =======================
# Bucle principal (CONTROL P)
# =======================
inicio = time.time()

while True:

    now = time.time()

    if now - inicio > 20:
        print("TIEMPO DE VUELO TERMINADO")
        break

    # Altura relativa
    altura_rel = altura - a0
    mediciones.append(altura_rel)

    # Error
    error = referencia - altura_rel
    e.append(error)

    # CONTROL PROPORCIONAL DIGITAL
    u = Kp * error
    u = max(-100, min(100, u))   # saturación
    vector_u.append(u)

    tello.send_rc_control(0, 0, int(u), 0)

    # Tiempo
    t = np.linspace(0, now - inicio, len(mediciones))

    # Actualizar gráficas
    line_u.set_data(t, vector_u)
    ax1.relim()
    ax1.autoscale_view()

    line_e.set_data(t, e)
    ax2.relim()
    ax2.autoscale_view()

    line_altura.set_data(t, mediciones)
    ax3.relim()
    ax3.autoscale_view()

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
