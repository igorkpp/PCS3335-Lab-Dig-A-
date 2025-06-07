import serial
import keyboard
import time
import threading
import pygame

PORTA_SERIAL = 'COM7'
BAUDRATE = 9600
TECLAS_VALIDAS = list("abcdefghijklmnopqrstuvwxyz")

# Palavra correta
PALAVRA_CERTA = "JORGE"

# Visualização compartilha letras e status
letras_grid = [["" for _ in range(5)] for _ in range(6)]
status_grid = [["" for _ in range(5)] for _ in range(6)]  # "green", "yellow", "gray", ""
linha, coluna = 0, 0
lock = threading.Lock()
fim_de_jogo = threading.Event()

def transmissor():
    global linha, coluna
    teclas_ativas = set()
    try:
        ser = serial.Serial(PORTA_SERIAL, BAUDRATE, timeout=0)
        print(f"Conectado em {PORTA_SERIAL} a {BAUDRATE} bps")
    except serial.SerialException:
        print("Erro: porta serial não encontrada.")
        return

    print("Pressione teclas para enviar à FPGA (ESC para sair)...")

    while True:
        try:
            if keyboard.is_pressed('enter'):
                ser.write(b'\r')
                print("[ENTER enviado]")
                with lock:
                    if coluna == 5 and linha < 5:
                        linha += 1
                        coluna = 0
                time.sleep(0.2)

            for tecla in TECLAS_VALIDAS:
                if keyboard.is_pressed(tecla):
                    if tecla not in teclas_ativas:
                        teclas_ativas.add(tecla)
                        ser.write(tecla.encode())
                        print(f"[{tecla}] ENVIADO")
                        with lock:
                            if coluna < 5:
                                letras_grid[linha][coluna] = tecla.upper()
                                coluna += 1
                else:
                    if tecla in teclas_ativas:
                        teclas_ativas.remove(tecla)

            if keyboard.is_pressed('backspace'):
                with lock:
                    if coluna > 0:
                        coluna -= 1
                        letras_grid[linha][coluna] = ""
                time.sleep(0.2)

            if keyboard.is_pressed('esc'):
                print("Encerrando...")
                break

            time.sleep(0.01)

        except KeyboardInterrupt:
            break

    ser.close()
    print("Conexão serial encerrada.")

def checa_tentativa(palavra_usuario):
    palavra_usuario = palavra_usuario.upper()
    palavra_certa = PALAVRA_CERTA
    resultado = ["gray"] * 5
    letras_contadas = list(palavra_certa)

    # Primeiro: marca os verdes
    for i in range(5):
        if palavra_usuario[i] == palavra_certa[i]:
            resultado[i] = "green"
            letras_contadas[i] = None  # Consome a letra

    # Depois: marca os amarelos
    for i in range(5):
        if resultado[i] != "green" and palavra_usuario[i] in letras_contadas:
            resultado[i] = "yellow"
            letras_contadas[letras_contadas.index(palavra_usuario[i])] = None

    return resultado

def visualizacao():
    import pygame, sys
    pygame.init()
    COLS, ROWS = 5, 6

    # --- Tela & fundo ---------------------------------------------------------
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    width, height = screen.get_size()
    centerx = width // 2

    bg_img = pygame.image.load("fundo.png").convert()
    bg_img = pygame.transform.scale(bg_img, (width, height))

    # --- Grid -----------------------------------------------------------------
    grid_w  = int(width * 0.55)
    grid_h  = int(height * 0.46)
    grid_x  = (width - grid_w) // 2
    grid_y  = int(height * 0.22)
    gap_x   = int(grid_w * 0.025)
    gap_y   = int(grid_h * 0.04)
    box_w   = int((grid_w - gap_x * (COLS - 1)) / COLS)
    box_h   = int((grid_h - gap_y * (ROWS - 1)) / ROWS)
    radius  = 5

    # --- Cores ----------------------------------------------------------------
    BG            = (218, 232, 252)
    BOX_BORDA     = (65, 60, 65)
    TXT           = (40, 35, 35)
    SUB           = (80, 80, 80)
    GREEN         = (88, 174, 79)
    YELLOW        = (240, 196, 68)
    GRAY_FUTURO   = (170, 175, 185)
    GRAY_LINHA    = (213, 214, 218)
    GRAY_LETRA    = (200, 202, 206)
    GRAY_NAOUTIL  = (196, 200, 205)
    WHITE         = (255, 255, 255)

    # --- Fontes ---------------------------------------------------------------
    ft  = lambda h, b=False: pygame.font.SysFont("Arial", int(height * h), bold=b)
    f_title, f_sub  = ft(0.052, True), ft(0.032)
    f_grid          = pygame.font.SysFont("Arial", int(box_h * .60), bold=True)
    f_footer        = ft(0.036)
    f_footer_sub    = ft(0.027)
    f_btn           = ft(0.030, True)

    # --- Botão fechar ---------------------------------------------------------
    BTN_W, BTN_H = int(width * 0.05), int(height * 0.05)
    btn_rect      = pygame.Rect(width - BTN_W - 20, 20, BTN_W, BTN_H)

    tentativa_encerrada = [False] * ROWS
    acertou  = False            # palavra correta já acertada?
    verde_on = False            # flag-mostra todos verdes

    running = True
    while running:
        # Fundo
        screen.blit(bg_img, (0, 0))

        # Título e subtítulo
        screen.blit(f_title.render("PROJETO DE LABORATÓRIO DIGITAL A", True, TXT),
                    f_title.render("PROJETO DE LABORATÓRIO DIGITAL A", True, TXT).get_rect(center=(centerx, int(height * 0.06))))
        screen.blit(f_sub.render("HardWordle", True, SUB),
                    f_sub.render("HardWordle", True, SUB).get_rect(center=(centerx, int(height * 0.105))))

        # Botão fechar
        pygame.draw.rect(screen, (255, 80, 80), btn_rect, border_radius=8)
        screen.blit(f_btn.render("X", True, WHITE),
                    f_btn.render("X", True, WHITE).get_rect(center=btn_rect.center))

        # --- GRID -------------------------------------------------------------
        with lock:
            linha_atual = next((r for r in range(ROWS)
                                if not all(letras_grid[r][c] for c in range(COLS)) and not tentativa_encerrada[r]),
                               None)

            for r in range(ROWS):
                for c in range(COLS):
                    x = grid_x + c * (box_w + gap_x)
                    y = grid_y + r * (box_h + gap_y)

                    # cor
                    if verde_on:
                        cor = GREEN
                    else:
                        st = status_grid[r][c]
                        if   st == "green":   cor = GREEN
                        elif st == "yellow":  cor = YELLOW
                        elif st == "gray":    cor = GRAY_LETRA if r == linha_atual else GRAY_NAOUTIL
                        elif r == linha_atual: cor = GRAY_LINHA
                        elif not any(letras_grid[r]): cor = GRAY_FUTURO
                        else: cor = BOX_BORDA

                    pygame.draw.rect(screen, cor, (x, y, box_w, box_h), 0, border_radius=radius)
                    pygame.draw.rect(screen, BOX_BORDA, (x, y, box_w, box_h), 2, border_radius=radius)

                    if letras_grid[r][c]:
                        letra = f_grid.render(letras_grid[r][c], True, TXT)
                        screen.blit(letra, letra.get_rect(center=(x + box_w//2, y + box_h//2)))

        # Rodapés
        screen.blit(f_footer.render("GRUPO: B3 e B4", True, TXT),
                    f_footer.render("GRUPO: B3 e B4", True, TXT).get_rect(center=(centerx, height - int(height * 0.14))))
        screen.blit(f_footer_sub.render("Gustavo, Igor, José e Hideki", True, SUB),
                    f_footer_sub.render("Gustavo, Igor, José e Hideki", True, SUB).get_rect(center=(centerx, height - int(height * 0.11))))

        pygame.display.flip()

        # --- Lógica do jogo (somente visual) ----------------------------------
        with lock:
            for r in range(ROWS):
                if tentativa_encerrada[r]:
                    continue
                if all(letras_grid[r][c] for c in range(COLS)):
                    palavra = "".join(letras_grid[r]).upper()
                    resultado = checa_tentativa(palavra)
                    for c in range(COLS):
                        status_grid[r][c] = resultado[c]
                    tentativa_encerrada[r] = True

                    if palavra == PALAVRA_CERTA:   # “JORGE”
                        acertou  = True
                        verde_on = True             # pinta tudo de verde

            # Fecha apenas se 6 tentativas feitas e NÃO acertou
            if all(tentativa_encerrada) and not acertou:
                running = False

        # Eventos
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and btn_rect.collidepoint(e.pos):
                running = False

        pygame.time.wait(10)

    pygame.quit()
    fim_de_jogo.set()

if __name__ == "__main__":
    t1 = threading.Thread(target=transmissor, daemon=True)
    t2 = threading.Thread(target=visualizacao, daemon=True)
    t1.start()
    t2.start()
    fim_de_jogo.wait()  # Aguarda visualização encerrar