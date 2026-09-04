import math

import pygame
import config
from game import GameState
import ui

pygame.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption("Survivor Game")
clock = pygame.time.Clock()

game = GameState()
current_lang = 'KOR'
lang_button_rect = pygame.Rect(config.GAME_WIDTH - 90, 10, 80, 30)

running = True
while running:
    dt = clock.tick(60) / 1000.0

    # 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if lang_button_rect.collidepoint(event.pos):
                current_lang = 'ENG' if current_lang == 'KOR' else 'KOR'

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not game.is_game_over:
                game.is_game_over = True

            if game.is_game_over:
                if event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_q:
                    running = False

            if not game.is_game_over and not game.is_upgrading:
                if event.key in (pygame.K_1, pygame.K_EXCLAIM):
                    game.bullet_type = 'PIERCE'
                elif event.key in (pygame.K_2, pygame.K_AT):
                    game.bullet_type = 'EXPLOSIVE'
                elif event.key in (pygame.K_3, pygame.K_HASH):
                    game.bullet_type = 'LASER'

            if game.is_upgrading and not game.is_game_over:
                if event.key == pygame.K_UP:
                    game.selected_option_index = (game.selected_option_index - 1) % len(game.upgrade_options)
                elif event.key == pygame.K_DOWN:
                    game.selected_option_index = (game.selected_option_index + 1) % len(game.upgrade_options)
                elif event.key == pygame.K_SPACE:
                    game.apply_upgrade(game.upgrade_options[game.selected_option_index]["ids"])
                    game.is_upgrading = False

    # 로직 업데이트
    game.update(dt)

    # 렌더링
    screen.fill((30, 30, 30))

    # [신규] 레이저 렌더링
    for laser in game.lasers:
        lx, ly = (game.player.centerx, game.player.centery) if not laser["is_sub"] else (laser["x"], laser["y"])
        end_x = lx + math.cos(laser["angle"]) * 800.0
        end_y = ly + math.sin(laser["angle"]) * 800.0

        # 투명도 및 두께 표현
        alpha_ratio = laser["duration"] / laser["max_duration"]
        width = 6 if not laser["is_sub"] else 3
        color = (0, 255, 255) if not laser["is_sub"] else (180, 100, 255) # 본체: 청록색, 분열: 보라색

        pygame.draw.line(screen, color, (lx, ly), (end_x, end_y), width)

    # 무적 상태일 때는 노란색으로 반짝임
    player_color = (255, 255, 0) if (game.invincible_timer > 0 and int(game.invincible_timer * 10) % 2 == 0) else (0, 255, 0)
    pygame.draw.rect(screen, player_color, game.player)

    # 1. 플레이어 렌더링
    player_color = (255, 255, 0) if (game.invincible_timer > 0 and int(game.invincible_timer * 10) % 2 == 0) else (0, 255, 0)
    pygame.draw.rect(screen, player_color, game.player)

    # 2. [신규 추가] 플레이어 상단 체력바 시각화
    ui.draw_player_hp_bar(screen, game.player, game.player_hp, game.max_hp)

    # 적 렌더링 (스페셜 보스는 붉은주황색)
    for e in game.enemies:
        if e["type"] == "SPECIAL_BOSS":
            c = (255, 60, 0)
        elif e["type"] == "BOSS":
            c = (255, 215, 0)
        elif e["type"] == "ELITE":
            c = (160, 32, 240)
        else:
            c = (255, 0, 0)
        pygame.draw.rect(screen, c, e["rect"])

    # 총알 렌더링
    for b in game.bullets:
        c = (255, 80, 80) if game.bullet_type == 'EXPLOSIVE' else (255, 255, 0)
        pygame.draw.rect(screen, c, b["rect"])

    # 체력 포션 렌더링
    for p in game.potions:
        pygame.draw.rect(screen, (0, 191, 255), p["rect"])
        timer_text = config.font.render(f"{int(p['timer'])}s", True, (255, 255, 255))
        screen.blit(timer_text, (p["rect"].x - 2, p["rect"].y - 15))

    # [신규] 무적 흰색 아이템 렌더링 및 타이머 표시
    for inv_item in game.invincibility_items:
        pygame.draw.rect(screen, (255, 255, 255), inv_item["rect"])
        timer_text = config.font.render(f"{int(inv_item['timer'])}s", True, (255, 255, 255))
        screen.blit(timer_text, (inv_item["rect"].x - 2, inv_item["rect"].y - 15))

    # 전리품 렌더링
    for l in game.loot_items:
        r_size = 10 if l["type"] == "SPECIAL_BOSS" else (8 if l["type"] == "BOSS" else 3)
        c_color = (255, 60, 0) if l["type"] == "SPECIAL_BOSS" else ((255, 215, 0) if l["type"] in ("BOSS", "NORMAL") else (255, 105, 180))
        pygame.draw.circle(screen, c_color, (int(l["x"]), int(l["y"])), r_size)

    for exp in game.explosions:
        pygame.draw.circle(screen, (255, 140, 0), (int(exp["x"]), int(exp["y"])), int(exp["radius"]), 2)

    for eff in game.hit_effects:
        pygame.draw.circle(screen, (255, 200, 50), (int(eff["x"]), int(eff["y"])), 2)

    for ring in game.damage_rings:
        pygame.draw.circle(screen, (255, 0, 0), (int(ring["x"]), int(ring["y"])), int(ring["radius"]), 2)

    # UI 출력
    ui.draw_hud(screen, game.play_time, current_lang, game.player_level, game.kill_count, game.kills_for_next_upgrade, lang_button_rect, game.invincible_timer)
    ui.draw_stats_panel(screen, game.rankings, game.get_stats_dict())

    if game.is_upgrading and not game.is_game_over:
        ui.draw_upgrade_popup(screen, game.upgrade_options, game.selected_option_index)

    if game.is_game_over:
        ui.draw_game_over(screen)

    pygame.display.flip()

pygame.quit()