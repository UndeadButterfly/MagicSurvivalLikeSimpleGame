import random

def generate_upgrade_options(bullet_count_upgrades, split_upgrades, bullet_speed_upgrades, player_size_upgrades, bullet_damage_upgrades, bullet_type='PIERCE'):
    # 기본 공통 옵션
    pool = [
        {"ids": [3], "text_kor": "[3] 공격 간격 -10%", "text_eng": "[3] Attack Interval -10%"},
        {"ids": [4], "text_kor": "[4] 발사 방향 +1", "text_eng": "[4] Fire Direction +1%"},
        {"ids": [5], "text_kor": "[5] 최대 체력 +10", "text_eng": "[5] Max HP +10"},
        {"ids": [6], "text_kor": "[6] 초당 체력 회복 +1", "text_eng": "[6] HP Regen +1/s"},
        {"ids": [8], "text_kor": "[8] 획득 범위 +10%", "text_eng": "[8] Magnet Radius +10%"},
        {"ids": [10], "text_kor": "[10] 이동 속도 +20%", "text_eng": "[10] Move Speed +20%"},
        {"ids": [12], "text_kor": "[12] 적 이동 속도 -10%", "text_eng": "[12] Enemy Speed -10%"},
    ]

    # 탄종별 관통력(지속시간) 선택지 텍스트 분기
    if bullet_type == 'LASER':
        pool.append({"ids": [1], "text_kor": "[1] 레이저 지속시간 +0.5s", "text_eng": "[1] Laser Duration +0.5s"})
    else:
        pool.append({"ids": [1], "text_kor": "[1] 관통력 +1", "text_eng": "[1] Pierce +1"})

    # 탄종별 발사 개수 선택지 분기
    if bullet_count_upgrades < 5:
        if bullet_type == 'EXPLOSIVE':
            pool.append({"ids": [2], "text_kor": "[2] 폭발탄 발사 개수 +1", "text_eng": "[2] Explosive Bullet Count +1"})
        elif bullet_type == 'LASER':
            pool.append({"ids": [2], "text_kor": "[2] 레이저 줄기 +1", "text_eng": "[2] Laser Beam +1"})
        else:
            pool.append({"ids": [2], "text_kor": "[2] 관통탄 발사 개수 +2", "text_eng": "[2] Pierce Bullet Count +2"})

    if split_upgrades < 4:
        pool.append({"ids": [11], "text_kor": "[11] 적중 시 분열 +1", "text_eng": "[11] Split on Hit +1"})

    if bullet_speed_upgrades < 3:
        pool.append({"ids": [13], "text_kor": "[13] 투사체 속도 +30%", "text_eng": "[13] Bullet Speed +30%"})

    if player_size_upgrades < 2:
        pool.append({"ids": [14], "text_kor": "[14] 캐릭터 크기 -20%", "text_eng": "[14] Player Size -20%"})

    if bullet_damage_upgrades < 4:
        pool.append({"ids": [15], "text_kor": "[15] 투사체 공격력 +1", "text_eng": "[15] Bullet Damage +1"})

    if len(pool) < 3:
        return pool

    return random.sample(pool, 3)