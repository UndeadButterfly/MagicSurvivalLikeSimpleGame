import os
import platform
import pygame

pygame.init()
pygame.font.init()

# 화면 설정
GAME_WIDTH = 800
UI_PANEL_WIDTH = 200
SCREEN_WIDTH = GAME_WIDTH + UI_PANEL_WIDTH
SCREEN_HEIGHT = 600

RANKING_FILE = "rankings.txt"

def get_korean_font(size):
    os_name = platform.system()
    try:
        if os_name == "Windows":
            return pygame.font.SysFont("malgungothic", size)
        elif os_name == "Darwin":
            return pygame.font.SysFont("applegothic", size)
        else:
            return pygame.font.SysFont("nanumgothic", size)
    except:
        return pygame.font.SysFont(None, size)

font = get_korean_font(16)
bold_font = get_korean_font(18)
title_font = get_korean_font(32)

def load_rankings():
    ranks = []
    if os.path.exists(RANKING_FILE):
        try:
            with open(RANKING_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 3:
                        ranks.append({
                            "level": int(parts[0]),
                            "kills": int(parts[1]),
                            "time": float(parts[2]),
                            "stats": parts[3] if len(parts) > 3 else ""
                        })
        except Exception as e:
            print(f"랭킹 로드 실패: {e}")
    ranks.sort(key=lambda x: (x["kills"], x["time"]), reverse=True)
    return ranks

def save_rankings(ranks):
    try:
        with open(RANKING_FILE, "w", encoding="utf-8") as f:
            for r in ranks:
                f.write(f"{r['level']},{r['kills']},{r['time']:.2f},{r['stats']}\n")
    except Exception as e:
        print(f"랭킹 저장 실패: {e}")