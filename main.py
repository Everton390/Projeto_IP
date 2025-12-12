import os
import pygame
import sys

pygame.init()

largura = 1280
altura = 760

tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption('Caramelo: A Saga da Coxinha Dourada')

script_dir = os.path.abspath(os.path.dirname(__file__))
spritesheet_path = os.path.join(script_dir, 'assets', 'cachorro_animacao.png')
cachorro_latindo_path = os.path.join(script_dir, 'assets', 'cachorro_latindo.png')
cachorro_jpg_path = os.path.join(script_dir, 'assets', 'cachorro.jpeg')

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
# outras flags

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
                if not jumping and rect_obj.bottom >= ground_y:
                    vel_y = jump_speed
                    jumping = True

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
    if (teclas[pygame.K_w] or teclas[pygame.K_UP]) and not jumping and rect_obj.bottom >= ground_y:
        vel_y = jump_speed
        jumping = True

    if rect_obj.left < 0:
        rect_obj.left = 0

    if rect_obj.right > largura:
        rect_obj.right = largura

    # aplica gravidade e movimento vertical
    if jumping or rect_obj.bottom < ground_y:
        vel_y += gravity
        rect_obj.y += int(vel_y)

    # limites verticais e aterrissagem
    if rect_obj.top < 0:
        rect_obj.top = 0
        vel_y = 0

    if rect_obj.bottom >= ground_y:
        rect_obj.bottom = ground_y
        vel_y = 0
        jumping = False

    tela.fill((0, 0, 0))

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
