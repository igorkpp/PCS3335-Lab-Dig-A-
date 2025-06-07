import serial
import keyboard
import time

PORTA_SERIAL = 'COM7'
BAUDRATE = 9600

TECLAS_VALIDAS = list("abcdefghijklmnopqrstuvwxyz")

teclas_ativas = set()

# Inicializa conexão serial
try:
    ser = serial.Serial(PORTA_SERIAL, BAUDRATE, timeout=0)
    print(f"Conectado em {PORTA_SERIAL} a {BAUDRATE} bps")
except serial.SerialException:
    print("Erro: porta serial não encontrada.")
    exit()

print("Pressione teclas para enviar à FPGA (ESC para sair)...")

while True:
    try:
        # Envia ENTER como antes
        if keyboard.is_pressed('enter'):
            ser.write(b'\r')
            print("[ENTER enviado]")
            time.sleep(0.2)

        # Verifica todas as teclas válidas
        for tecla in TECLAS_VALIDAS:
            if keyboard.is_pressed(tecla):
                # só dispara no **momento em que** passa a estar pressionada
                if tecla not in teclas_ativas:
                    teclas_ativas.add(tecla)
                    ser.write(tecla.encode())     # envia só "a", sem "+"
                    print(f"[{tecla}] ENVIADO")
            else:
                # quando solta, apenas removemos do set, sem enviar nada
                if tecla in teclas_ativas:
                    teclas_ativas.remove(tecla)

        if keyboard.is_pressed('esc'):
            print("Encerrando...")
            break

        time.sleep(0.01)

    except KeyboardInterrupt:
        break

ser.close()
print("Conexão serial encerrada.")
