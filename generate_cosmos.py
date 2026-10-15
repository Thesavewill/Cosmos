import os
import math
import base64
import calendar
import random
import requests

# Настройки (при запуске через GitHub Actions подтянутся автоматически)
USERNAME = os.getenv("GITHUB_USER", "Thesavewill")
TOKEN = os.getenv("GH_TOKEN", "ТВОЙ_ТОКЕН_ДЛЯ_ТЕСТОВ")

# Палитра GitHub Dark Mode (для активных дней)
COLORS = {
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353"
}

# Все длительности (орбиты, звезды, кометы) — делители 240 секунд для бесшовного цикла
ORBIT_DURATIONS = [20, 30, 24, 40, 16, 48, 30, 60, 24, 80, 40, 120]

def fetch_github_data():
    query = """
    query($login: String!) {
      user(login: $login) {
        avatarUrl
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"login": USERNAME}},
        headers=headers
    )
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        raise Exception(f"Ошибка GraphQL: {data['errors']}")
    return data["data"]["user"]

def get_avatar_base64(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return base64.b64encode(resp.content).decode("utf-8")

def generate_svg():
    user_data = fetch_github_data()
    avatar_b64 = get_avatar_base64(user_data["avatarUrl"])
    weeks = user_data["contributionsCollection"]["contributionCalendar"]["weeks"]

    days = [day for week in weeks for day in week["contributionDays"]]

    months = {}
    for d in days:
        m_key = d["date"][:7]
        months.setdefault(m_key, []).append(d)
    
    sorted_months = sorted(months.keys(), reverse=True)[:12]

    cx, cy = 400, 400
    base_radius = 85
    radius_step = 24

    svg = [
        '<svg viewBox="0 0 800 800" width="800" height="800" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        '  <clipPath id="space-clip">',
        '    <rect width="800" height="800" rx="16" />',
        '  </clipPath>',
        '  <clipPath id="avatar-clip">',
        f'    <circle cx="{cx}" cy="{cy}" r="50" />',
        '  </clipPath>',
        
        # Градиент глубокого космоса
        '  <radialGradient id="space-bg" cx="50%" cy="50%" r="70%">',
        '    <stop offset="0%" stop-color="#111927" />',
        '    <stop offset="55%" stop-color="#0d1117" />',
        '    <stop offset="100%" stop-color="#06080c" />',
        '  </radialGradient>',
        
        # Изумрудная туманность вокруг планеты в цветах GitHub
        '  <radialGradient id="nebula" cx="50%" cy="50%" r="45%">',
        '    <stop offset="0%" stop-color="#26a641" stop-opacity="0.14" />',
        '    <stop offset="45%" stop-color="#006d32" stop-opacity="0.05" />',
        '    <stop offset="100%" stop-color="#0d1117" stop-opacity="0" />',
        '  </radialGradient>',
        
        # Градиент хвоста кометы
        '  <linearGradient id="comet-tail" x1="0%" y1="0%" x2="100%" y2="0%">',
        '    <stop offset="0%" stop-color="#ffffff" stop-opacity="0" />',
        '    <stop offset="75%" stop-color="#58a6ff" stop-opacity="0.4" />',
        '    <stop offset="100%" stop-color="#ffffff" stop-opacity="0.95" />',
        '  </linearGradient>',
        
        # Свечение для коммитов и ядер комет
        '  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">',
        '    <feGaussianBlur stdDeviation="2.5" result="blur" />',
        '    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>',
        '  </filter>',
        
        # Шаблон самой кометы (летит вдоль оси X, мы будем поворачивать её под разными углами)
        '  <g id="comet">',
        '    <path d="M -140 0 L 0 -1.8 L 0 1.8 Z" fill="url(#comet-tail)" />',
        '    <circle cx="0" cy="0" r="2.2" fill="#ffffff" filter="url(#glow)" />',
        '  </g>',
        '</defs>',
        
        '<style>',
        '  .orbit-line { fill: none; stroke: #21262d; stroke-width: 1; stroke-dasharray: 4 4; opacity: 0.75; }',
        '  .planet-border { fill: none; stroke: #39d353; stroke-width: 2; stroke-opacity: 0.45; }',
        '  .planet-halo { fill: none; stroke: #26a641; stroke-width: 6; stroke-opacity: 0.15; }',
        '  @keyframes spin-cw { 100% { transform: rotate(360deg); } }',
        '  @keyframes spin-ccw { 100% { transform: rotate(-360deg); } }',
        '  @keyframes twinkle { 0%, 100% { opacity: 0.15; } 50% { opacity: 0.95; } }',
        
        # Движение кометы: пролетает экран за первые 18% времени цикла, остальное время ждет в темноте
        '  @keyframes shoot {',
        '    0% { transform: translateX(0px); opacity: 0; }',
        '    2% { opacity: 1; }',
        '    14% { opacity: 1; }',
        '    18% { transform: translateX(1150px); opacity: 0; }',
        '    100% { transform: translateX(1150px); opacity: 0; }',
        '  }',
        
        # Пять асинхронных групп мерцания звезд (делители 240s)
        '  .twinkle-0 { animation: twinkle 3s ease-in-out infinite; }',
        '  .twinkle-1 { animation: twinkle 4s ease-in-out 1s infinite; }',
        '  .twinkle-2 { animation: twinkle 5s ease-in-out 2.5s infinite; }',
        '  .twinkle-3 { animation: twinkle 6s ease-in-out 0.5s infinite; }',
        '  .twinkle-4 { animation: twinkle 8s ease-in-out 3s infinite; }',
        
        # Стили трех комет с разными интервалами (15s, 24s, 40s — делители 240s)
        '  .comet-1 { animation: shoot 15s ease-in infinite; }',
        '  .comet-2 { animation: shoot 24s ease-in 7s infinite; }',
        '  .comet-3 { animation: shoot 40s ease-in 19s infinite; }'
    ]

    # Стили вращения орбит
    for i, duration in enumerate(ORBIT_DURATIONS):
        direction = "spin-cw" if i % 2 == 0 else "spin-ccw"
        svg.append(f'  .orbit-{i} {{ transform-origin: {cx}px {cy}px; animation: {direction} {duration}s linear infinite; }}')

    svg.append('</style>')
    
    # Обрезаем все вылетающие за край элементы по аккуратным скругленным углам
    svg.append('<g clip-path="url(#space-clip)">')
    
    # 1. Фон космоса и туманность
    svg.append('  <rect width="800" height="800" fill="url(#space-bg)" />')
    svg.append('  <circle cx="400" cy="400" r="380" fill="url(#nebula)" />')

    # 2. Звездное небо (фиксируем seed, чтобы позиции звезд были красивыми)
    rng = random.Random(42)
    star_colors = ["#ffffff", "#e6edf3", "#c9d1d9", "#a5d6ff", "#7ee787"]
    svg.append('  <g id="starfield">')
    
    for s in range(130):
        sx = rng.randint(12, 788)
        sy = rng.randint(12, 788)
        # Не рисуем звезды прямо под аватаркой
        if math.hypot(sx - cx, sy - cy) < 62:
            continue
        
        scolor = rng.choice(star_colors)
        if s < 75:
            # Мелкая фоновая космическая пыль
            sr = rng.uniform(0.5, 1.1)
            sop = rng.uniform(0.15, 0.5)
            svg.append(f'    <circle cx="{sx}" cy="{sy}" r="{sr:.1f}" fill="{scolor}" opacity="{sop:.2f}" />')
        elif s < 124:
            # Мерцающие звезды средней яркости
            sr = rng.uniform(1.0, 1.8)
            tw_cls = f"twinkle-{s % 5}"
            svg.append(f'    <circle cx="{sx}" cy="{sy}" r="{sr:.1f}" fill="{scolor}" class="{tw_cls}" />')
        else:
            # 6 крупных путеводных звезд с 4-лучевым оптическим сиянием
            tw_cls = f"twinkle-{s % 5}"
            svg.append(
                f'    <g class="{tw_cls}" transform="translate({sx}, {sy})">'
                f'<path d="M -6 0 L 6 0 M 0 -6 L 0 6" stroke="{scolor}" stroke-width="0.9" opacity="0.6" />'
                f'<circle cx="0" cy="0" r="1.8" fill="#ffffff" filter="url(#glow)" />'
                f'</g>'
            )
    svg.append('  </g>')

    # 3. Пролетающие на фоне кометы под разными углами
    svg.append('  <g transform="translate(-80, 110) rotate(22)"><use href="#comet" class="comet-1" /></g>')
    svg.append('  <g transform="translate(880, 220) rotate(152)"><use href="#comet" class="comet-2" /></g>')
    svg.append('  <g transform="translate(90, -80) rotate(58)"><use href="#comet" class="comet-3" /></g>')

    # 4. Орбиты и точки-коммиты
    for i, m_key in enumerate(sorted_months):
        r = base_radius + i * radius_step
        svg.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" class="orbit-line" />')
        svg.append(f'  <g class="orbit-{i}">')
        
        year, month = map(int, m_key.split("-"))
        total_days = calendar.monthrange(year, month)[1]

        for d in months[m_key]:
            level = d["contributionLevel"]
            if level == "NONE":
                continue

            day_num = int(d["date"].split("-")[2])
            angle = (day_num / total_days) * 2 * math.pi - (math.pi / 2)
            
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            color = COLORS.get(level, "#39d353")
            dot_radius = 4.5 if level in ("FIRST_QUARTILE", "SECOND_QUARTILE") else 6

            svg.append(
                f'    <circle cx="{x:.2f}" cy="{y:.2f}" r="{dot_radius}" '
                f'fill="{color}" filter="url(#glow)">'
                f'<title>{d["date"]}: {d["contributionCount"]} commits</title>'
                f'</circle>'
            )
        svg.append('  </g>')

    # 5. Центральная планета-аватарка с атмосферным свечением
    svg.append(f'  <circle cx="{cx}" cy="{cy}" r="53" class="planet-halo" />')
    svg.append(f'  <image href="data:image/png;base64,{avatar_b64}" x="{cx-50}" y="{cy-50}" height="100" width="100" clip-path="url(#avatar-clip)" />')
    svg.append(f'  <circle cx="{cx}" cy="{cy}" r="50" class="planet-border" />')
    
    svg.append('</g>')
    svg.append('</svg>')

    os.makedirs("dist", exist_ok=True)
    with open("dist/cosmos.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    print("Файл dist/cosmos.svg успешно создан!")

if __name__ == "__main__":
    generate_svg()