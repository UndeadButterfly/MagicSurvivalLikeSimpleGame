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
    pygame.draw.rect(screen, (0, 255, 0), game.player)

    for e in game.enemies:
        c = (255, 215, 0) if e["type"] == "BOSS" else ((160, 32, 240) if e["type"] == "ELITE" else (255, 0, 0))
        pygame.draw.rect(screen, c, e["rect"])

    for b in game.bullets:
        c = (255, 80, 80) if game.bullet_type == 'EXPLOSIVE' else (255, 255, 0)
        pygame.draw.rect(screen, c, b["rect"])

    # 포션 렌더링 및 제한 시간 표시
    for p in game.potions:
        pygame.draw.rect(screen, (0, 191, 255), p["rect"])
        timer_text = config.font.render(f"{int(p['timer'])}s", True, (255, 255, 255))
        screen.blit(timer_text, (p["rect"].x - 2, p["rect"].y - 15))

    for l in game.loot_items:
        pygame.draw.circle(screen, (255, 215, 0) if l["type"] in ("BOSS", "NORMAL") else (255, 105, 180), (int(l["x"]), int(l["y"])), 8 if l["type"] == "BOSS" else 3)

    for exp in game.explosions:
        pygame.draw.circle(screen, (255, 140, 0), (int(exp["x"]), int(exp["y"])), int(exp["radius"]), 2)

    for eff in game.hit_effects:
        pygame.draw.circle(screen, (255, 200, 50), (int(eff["x"]), int(eff["y"])), 2)

    for ring in game.damage_rings:
        pygame.draw.circle(screen, (255, 0, 0), (int(ring["x"]), int(ring["y"])), int(ring["radius"]), 2)

    # UI 출력
    ui.draw_hud(screen, game.play_time, current_lang, game.player_level, game.kill_count, game.kills_for_next_upgrade, lang_button_rect)
    ui.draw_stats_panel(screen, game.rankings, game.get_stats_dict())

    if game.is_upgrading and not game.is_game_over:
        ui.draw_upgrade_popup(screen, game.upgrade_options, game.selected_option_index)

    if game.is_game_over:
        ui.draw_game_over(screen)

    pygame.display.flip()

pygame.quit()