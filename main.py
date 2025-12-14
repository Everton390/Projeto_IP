import os
import pygame
import sys

pygame.init()

largura = 1280
altura = 760

tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption('Caramelo: A Saga do Bolo de Rolo Dourado')

script_dir = os.path.abspath(os.path.dirname(__file__))
spritesheet_path = os.path.join(script_dir, 'assets', 'cachorro_animacao.png')
cachorro_latindo_path = os.path.join(
    script_dir, 'assets', 'cachorro_latindo.png')
cachorro_jpg_path = os.path.join(script_dir, 'assets', 'cachorro.jpeg')
# backgorund
background_path = os.path.join(
    script_dir, 'IMAGENS PROJETO IP', 'BACKGROUND', 'BACKGROUND1.jpg'
)

# Parâmetros de escala/animacao (reduzidos para sprites menores)
# Ajuste estes valores para deixar o sprite ainda menor/grande conforme necessário
max_width, max_height = largura // 10, altura // 8
animation_frames = []
anim_index = 0
last_anim_time = 0
anim_delay = 200  # ms entre frames
# frames específicos para o latido (serão extraídos de `cachorro_latindo.png` se existir)
barking_frames = []
bark_index = 0
bark_last = 0
bark_delay = 120

try:
    if os.path.exists(spritesheet_path):
        sheet = pygame.image.load(spritesheet_path).convert_alpha()
        sheet_w, sheet_h = sheet.get_size()
        cols, rows = 2, 2
        frame_w, frame_h = sheet_w // cols, sheet_h // rows
        for ry in range(rows):
            for cx in range(cols):
                rect = (cx * frame_w, ry * frame_h, frame_w, frame_h)
                frame = sheet.subsurface(rect).copy()
                ow, oh = frame.get_size()
                scale = min(max_width / ow, max_height / oh, 1)
                if scale < 1:
                    frame = pygame.transform.smoothscale(
                        frame, (int(ow * scale), int(oh * scale)))
                animation_frames.append(frame)

        if not animation_frames:
            raise pygame.error('Spritesheet não contém frames válidos')

        imagem_cachorro = animation_frames[0]
    else:
        imagem_cachorro = pygame.image.load(cachorro_jpg_path).convert_alpha()
        orig_w, orig_h = imagem_cachorro.get_size()
        scale = min(max_width / orig_w, max_height / orig_h, 1)
        if scale < 1:
            imagem_cachorro = pygame.transform.smoothscale(
                imagem_cachorro, (int(orig_w * scale), int(orig_h * scale)))
        animation_frames = [imagem_cachorro]

    rect_obj = imagem_cachorro.get_rect()
    # posiciona o sprite no chão (sempre)
    ground_y = altura - 20
    rect_obj.centerx = largura // 2
    rect_obj.bottom = ground_y

    # se houver spritesheet de 'latindo' (anexo), cortamos em frames para usar no latido
    if os.path.exists(cachorro_latindo_path):
        try:
            sheet_b = pygame.image.load(cachorro_latindo_path).convert_alpha()
            sw, sh = sheet_b.get_size()
            # imagem anexa tem 2x2 (4 frames) — ajustar se precisar
            bcols, brows = 2, 2
            bf_w, bf_h = sw // bcols, sh // brows
            for bry in range(brows):
                for bcx in range(bcols):
                    brect = (bcx * bf_w, bry * bf_h, bf_w, bf_h)
                    bframe = sheet_b.subsurface(brect).copy()
                    ow, oh = bframe.get_size()
                    scale = min(max_width / ow, max_height / oh, 1)
                    if scale < 1:
                        bframe = pygame.transform.smoothscale(
                            bframe, (int(ow * scale), int(oh * scale)))
                    barking_frames.append(bframe)
        except pygame.error:
            barking_frames = []

except pygame.error as e:
    print(f"Erro ao carregar imagem: {e}")
    print(
        f"Verifique se os caminhos '{spritesheet_path}' ou '{cachorro_jpg_path}' estão corretos.")
    pygame.quit()
    sys.exit()
#carregando background
background = None
if os.path.exists(background_path):
    background = pygame.image.load(background_path).convert()
    background = pygame.transform.scale(background, (largura,altura))
else:
    print("Background não encontrado", background_path)

clock = pygame.time.Clock()
velocidade_obj = 5
# física do pulo
vel_y = 0.0
gravity = 0.8
jump_speed = -14.0
jumping = False
# índice de frame para pulo (se não houver `jump_frames`, usa um frame de `animation_frames`)
# índice de frame para pulo (se não houver frames de pulo dedicados, usa um frame do spritesheet principal)
jump_frame_index = min(2, max(0, len(animation_frames) - 1))
# estado de latido
barking = False
# direção que o sprite está virado (False = direita, True = esquerda)
facing_left = False
# Plataformas
on_ground = False
plataformas = [
    pygame.Rect(300,660,100,25),
    pygame.Rect(479,560,112,25),
    pygame.Rect(600,530,92,25),
    pygame.Rect(479,460,112,25),
    pygame.Rect(0,330,225,25)
]
# outras flags

# --- Tela de menu inicial ---


def _draw_button(surface, rect, text, font, hover=False):
    color = (200, 160, 60) if not hover else (255, 200, 70)
    pygame.draw.rect(surface, color, rect, border_radius=8)
    txt = font.render(text, True, (10, 10, 10))
    txt_rect = txt.get_rect(center=rect.center)
    surface.blit(txt, txt_rect)


menu_path = os.path.join(script_dir, 'assets', 'menu.jpeg')
menu_img = None
mrect = None
if os.path.exists(menu_path):
    try:
        menu_img = pygame.image.load(menu_path).convert()
        mw, mh = menu_img.get_size()
        # escala para COBRIR toda a tela (cover) — pode cortar partes da imagem
        scale = max(largura / mw, altura / mh)
        new_w, new_h = int(mw * scale), int(mh * scale)
        if (new_w, new_h) != (mw, mh):
            menu_img = pygame.transform.smoothscale(menu_img, (new_w, new_h))
        mrect = menu_img.get_rect()
        mrect.center = (largura // 2, altura // 2)
    except Exception:
        menu_img = None

font_title = pygame.font.SysFont(None, 72)
font_btn = pygame.font.SysFont(None, 48)
btn_w, btn_h = 220, 64
start_rect = pygame.Rect((0, 0), (btn_w, btn_h))
exit_rect = pygame.Rect((0, 0), (btn_w, btn_h))

menu_clock = pygame.time.Clock()
in_menu = True
while in_menu:
    mx, my = pygame.mouse.get_pos()
    click = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                in_menu = False
                break
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    tela.fill((20, 20, 30))
    if menu_img and mrect:
        # blita a imagem centralizada cobrindo a tela
        tela.blit(menu_img, mrect)
        # posiciona os botões dentro da imagem (cerca de 25% abaixo do centro)
        y_pos = mrect.centery + int(mrect.height * 0.25)
        spacing = 140
        start_rect.center = (largura // 2 - spacing, y_pos)
        exit_rect.center = (largura // 2 + spacing, y_pos)
    else:
        title_surf = font_title.render('CARAMelo', True, (255, 200, 60))
        trect = title_surf.get_rect(center=(largura // 2, altura // 4))
        tela.blit(title_surf, trect)
        # fallback positions when no image
        y_pos = int(altura * 0.65)
        start_rect.center = (largura // 2 - btn_w - 20, y_pos)
        exit_rect.center = (largura // 2 + btn_w + 20, y_pos)

    hover_start = start_rect.collidepoint((mx, my))
    hover_exit = exit_rect.collidepoint((mx, my))
    _draw_button(tela, start_rect, 'Start', font_btn, hover_start)
    _draw_button(tela, exit_rect, 'Exit', font_btn, hover_exit)

    if hover_start and click:
        in_menu = False
        break
    if hover_exit and click:
        pygame.quit()
        sys.exit()

    pygame.display.flip()
    menu_clock.tick(60)

# fim do menu; o laço do jogo começa abaixo
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # outras teclas (padrão)
        if event.type == pygame.KEYDOWN:
            # latir com SPACE (evento único)
            if event.key == pygame.K_SPACE:
                if barking_frames:
                    barking = True
                    bark_index = 0
                    bark_last = pygame.time.get_ticks()
            # pular com W (evento KEYDOWN também inicia imediatamente)
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                if not jumping and on_ground:
                    vel_y = jump_speed
                    jumping = True
                    on_ground = False

    teclas = pygame.key.get_pressed()
    # sem lógica de latido por espaço

    # Movimento horizontal simplificado (Opção A): calculamos dx e aplicamos uma vez
    dx = 0
    if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
        dx = -velocidade_obj
        facing_left = True
    elif teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
        dx = velocidade_obj
        facing_left = False

    rect_obj.x += dx
    moving = (dx != 0)

    # pular com W/UP (tecla segurada também inicia pulo)
    if (teclas[pygame.K_w] or teclas[pygame.K_UP]) and not jumping and on_ground:
        vel_y = jump_speed
        jumping = True
        on_ground = False

    if rect_obj.left < 0:
        rect_obj.left = 0

    if rect_obj.right > largura:
        rect_obj.right = largura

    # aplica gravidade e movimento vertical
    vel_y += gravity
    rect_obj.y += int(vel_y)
    on_ground = False
    # colisão com plataformas
    for p in plataformas:
        if rect_obj.colliderect(p):
            # só pousa se estiver caindo por cima
            if vel_y > 0 and rect_obj.bottom - vel_y <= p.top:
                rect_obj.bottom = p.top
                vel_y = 0
                jumping = False
                on_ground = True
    # limites verticais e aterrissagem
    if rect_obj.top < 0:
        rect_obj.top = 0
        vel_y = 0

    if rect_obj.bottom >= ground_y:
        rect_obj.bottom = ground_y
        vel_y = 0
        jumping = False
        on_ground = True
    if background:
        tela.blit(background, (0, 0))
    else:
        tela.fill((0, 0, 0))

    # desenha as plataformas
    for p in plataformas:
        pygame.draw.rect(tela, (180,180,180), p)

    # Atualiza animação: pulo / movimento / idle
    now = pygame.time.get_ticks()
    # Prioridade visual: se estiver latindo, mostra animação de latido; senão trata pulo/movimento
    if barking:
        # controla avanço dos frames de latido
        if now - bark_last >= bark_delay:
            bark_index += 1
            bark_last = now
        if bark_index >= len(barking_frames):
            barking = False
            bark_index = 0
        else:
            center = rect_obj.center
            base_b = barking_frames[bark_index]
            if facing_left:
                imagem_cachorro = pygame.transform.flip(base_b, True, False)
            else:
                imagem_cachorro = base_b
            rect_obj = imagem_cachorro.get_rect()
            rect_obj.center = center
    elif jumping:
        # mostra o frame de pulo
        if anim_index != jump_frame_index:
            anim_index = jump_frame_index
            center = rect_obj.center
            base = animation_frames[anim_index]
            if facing_left:
                imagem_cachorro = pygame.transform.flip(base, True, False)
            else:
                imagem_cachorro = base
            rect_obj = imagem_cachorro.get_rect()
            rect_obj.center = center
    else:
        if len(animation_frames) > 1 and moving:
            if now - last_anim_time > anim_delay:
                anim_index = (anim_index + 1) % len(animation_frames)
                # preserva o centro ao trocar de frame
                center = rect_obj.center
                base = animation_frames[anim_index]
                if facing_left:
                    imagem_cachorro = pygame.transform.flip(base, True, False)
                else:
                    imagem_cachorro = base
                rect_obj = imagem_cachorro.get_rect()
                rect_obj.center = center
                last_anim_time = now
        else:
            # parado: garante que mostramos o primeiro frame (idle)
            if anim_index != 0 and len(animation_frames) > 0:
                anim_index = 0
                center = rect_obj.center
                base = animation_frames[0]
                if facing_left:
                    imagem_cachorro = pygame.transform.flip(base, True, False)
                else:
                    imagem_cachorro = base
                rect_obj = imagem_cachorro.get_rect()
                rect_obj.center = center

    tela.blit(imagem_cachorro, rect_obj)

    pygame.display.flip()
    clock.tick(60)
