import pygame
import config

def draw_hud(screen, play_time, current_lang, player_level, kill_count, kills_for_next_upgrade, lang_button_rect, invincible_timer=0.0):
    m, s = int(play_time) // 60, int(play_time) % 60
    time_str = f"시간: {m:02d}:{s:02d} | [1]:관통 [2]:폭발 | [ESC]:포기" if current_lang == 'KOR' else f"Time: {m:02d}:{s:02d} | [1]:Pierce [2]:Exp"
    kill_str = f"LV.{player_level} | 처치: {kill_count} (다음: {kills_for_next_upgrade})"
    
    screen.blit(config.bold_font.render(time_str, True, (255, 255, 255)), (10, 10))
    screen.blit(config.bold_font.render(kill_str, True, (255, 255, 255)), (10, 32))

    # [신규] 무적 상태 시간 표시
    if invincible_timer > 0:
        inv_str = f"★ 무적: {invincible_timer:.1f}초"
        screen.blit(config.bold_font.render(inv_str, True, (255, 255, 0)), (10, 54))

    pygame.draw.rect(screen, (70, 70, 70), lang_button_rect)
    screen.blit(config.font.render(f"[{current_lang}]", True, (255, 255, 255)), (lang_button_rect.x + 15, lang_button_rect.y + 4))

def draw_stats_panel(screen, rankings, stats_dict):
    pygame.draw.rect(screen, (20, 20, 25), (config.GAME_WIDTH, 0, config.UI_PANEL_WIDTH, config.SCREEN_HEIGHT))
    screen.blit(config.bold_font.render("랭킹 (Top 5)", True, (255, 215, 0)), (config.GAME_WIDTH + 15, 10))
    
    for idx, r in enumerate(rankings[:5]):
        screen.blit(config.font.render(f"{idx+1}. Lv.{r['level']} | {r['kills']}K", True, (200, 200, 200)), (config.GAME_WIDTH + 10, 32 + idx * 22))

    screen.blit(config.bold_font.render("캐릭터 스탯", True, (100, 200, 255)), (config.GAME_WIDTH + 15, 150))
    
    stats = [
        f"탄종: {stats_dict['bullet_type']}",
        f"체력: {int(stats_dict['player_hp'])}/{stats_dict['max_hp']}",
        f"초당 회복: +{stats_dict['hp_regen']}/s",
        f"이동 속도: {int(stats_dict['move_speed'])}",
        f"캐릭터 크기: {stats_dict['player_w']}x{stats_dict['player_h']}",
        f"공격 간격: {stats_dict['shoot_interval']:.2f}s",
        f"발사 방향: {stats_dict['fire_directions']}방향",
        f"발사 개수: {stats_dict['disp_bc']}개",
        f"관통력: {stats_dict['pierce_count']}",
        f"추가 공격력: +{stats_dict['bonus_damage']}",
        f"적중 분열: +{stats_dict['split_count']}개",
        f"투사체 속도: {int(stats_dict['bullet_speed'])}",
        f"폭발 범위: {int(stats_dict['current_exp_radius'])}",
        f"획득 범위: {int(stats_dict['magnet_radius'])}",
        f"적 속도율: {int(stats_dict['enemy_speed_mult'] * 100)}%"
    ]

    for idx, st in enumerate(stats):
        screen.blit(config.font.render(st, True, (220, 220, 220)), (config.GAME_WIDTH + 12, 175 + idx * 20))

def draw_upgrade_popup(screen, upgrade_options, selected_index):
    overlay = pygame.Surface((config.GAME_WIDTH, config.SCREEN_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    for idx, option in enumerate(upgrade_options):
        c = (255, 255, 0) if idx == selected_index else (255, 255, 255)
        screen.blit(config.font.render(option["text_kor"], True, c), (120, 220 + idx * 60))

def draw_game_over(screen):
    overlay = pygame.Surface((config.GAME_WIDTH, config.SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    screen.blit(config.title_font.render("GAME OVER", True, (255, 50, 50)), (config.GAME_WIDTH // 2 - 120, 200))
    screen.blit(config.bold_font.render("[R] 재시작  |  [Q] 게임 종료", True, (255, 255, 255)), (config.GAME_WIDTH // 2 - 110, 270))

# ui.py 하단 또는 적절한 위치에 추가

def draw_player_hp_bar(screen, player_rect, current_hp, max_hp):
    if max_hp <= 0:
        return
    
    # 체력바 크기 설정
    bar_width = player_rect.width
    bar_height = 5
    bar_x = player_rect.x
    bar_y = player_rect.y - 8  # 플레이어 캐릭터 8픽셀 위

    # 체력 비율 계산 (0 ~ 1)
    hp_ratio = max(0.0, min(1.0, current_hp / max_hp))

    # 배경(빨간색: 손실된 체력) 및 현재 체력(초록색)
    bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    fill_rect = pygame.Rect(bar_x, bar_y, int(bar_width * hp_ratio), bar_height)

    pygame.draw.rect(screen, (200, 0, 0), bg_rect)       # 빨간 배경
    pygame.draw.rect(screen, (0, 220, 0), fill_rect)     # 초록 게이지
    pygame.draw.rect(screen, (0, 0, 0), bg_rect, 1)      # 검은색 테두리