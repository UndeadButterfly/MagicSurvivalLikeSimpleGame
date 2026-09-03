import random

def get_base_upgrades(bullet_count_upgrades, split_upgrades, bullet_speed_upgrades):
    upgrades = [
        {"id": 1, "text_kor": "관통력 +1", "text_eng": "Pierce +1"},
        {"id": 3, "text_kor": "공격 간격 -10%", "text_eng": "Cooldown -10%"},
        {"id": 4, "text_kor": "공격 방향 +1", "text_eng": "Direction +1"},
        {"id": 5, "text_kor": "최대 체력 +10", "text_eng": "Max HP +10"},
        {"id": 6, "text_kor": "초당 체력회복 +1", "text_eng": "HP Regen +1"},
        {"id": 8, "text_kor": "전리품 획득 범위 +10%", "text_eng": "Magnet Range +10%"},
        {"id": 10, "text_kor": "이동속도 +20% (최대 500)", "text_eng": "Move Speed +20% (Max 500)"},
        {"id": 12, "text_kor": "적 이동속도 -10%", "text_eng": "Enemy Speed -10%"}
    ]

    if bullet_count_upgrades < 5:
        upgrades.append({"id": 2, "text_kor": f"개수 +2 ({bullet_count_upgrades}/5)", "text_eng": f"Bullet Count +2 ({bullet_count_upgrades}/5)"})

    if split_upgrades < 4:
        upgrades.append({"id": 11, "text_kor": f"적중 시 분열 +1 ({split_upgrades}/4)", "text_eng": f"Bullet Split +1 ({split_upgrades}/4)"})

    if bullet_speed_upgrades < 3:
        upgrades.append({"id": 13, "text_kor": f"투사체 속도 +30% ({bullet_speed_upgrades}/3)", "text_eng": f"Bullet Speed +30% ({bullet_speed_upgrades}/3)"})

    return upgrades

def generate_upgrade_options(bullet_count_upgrades, split_upgrades, bullet_speed_upgrades):
    avail = get_base_upgrades(bullet_count_upgrades, split_upgrades, bullet_speed_upgrades)
    options = []
    for _ in range(min(3, len(avail))):
        if random.random() < 0.30 and len(avail) >= 2:
            sampled = random.sample(avail, 2)
            for item in sampled:
                if item in avail:
                    avail.remove(item)
            options.append({
                "is_dual": True,
                "ids": [sampled[0]["id"], sampled[1]["id"]],
                "text_kor": f"[세트] {sampled[0]['text_kor']} + {sampled[1]['text_kor']}",
                "text_eng": f"[SET] {sampled[0]['text_eng']} + {sampled[1]['text_eng']}"
            })
        else:
            item = random.choice(avail)
            avail.remove(item)
            options.append({
                "is_dual": False,
                "ids": [item["id"]],
                "text_kor": item["text_kor"],
                "text_eng": item["text_eng"]
            })
    return options