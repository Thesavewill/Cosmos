import os
import math
import base64
import calendar
import random
import requests

# Настройки (при запуске через GitHub Actions подтянутся автоматически)
USERNAME = os.getenv("GITHUB_USER", "Thesavewill")
TOKEN = os.getenv("GH_TOKEN", "ТВОЙ_ТОКЕН_ДЛЯ_ТЕСТОВ")

# Палитра GitHub Dark Mode
COLORS = {
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353"
}

# Все длительности — делители 240 секунд для идеального бесшовного цикла
ORBIT_DURATIONS = [20, 30, 24, 40, 16, 48, 30, 60, 24, 80, 40, 120]

# Параметры 3D-наклона
TILT = 0.38          # Сила наклона к горизонтали (0.38 — выразительный 3D-эллипс)
ROLL_ANGLE = -12     # Легкий диагональный наклон всей оси системы в градусах

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

    width, height = 800, 520
    cx, cy = 400, 260
    base_radius = 85
    radius_step = 24

    svg = [
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        '  <clipPath id="space-clip">',
        f'    <rect width="{width}" height="{height}" rx="16" />',
        '  </clipPath>',
        '  <clipPath id="avatar-clip">',
        f'    <circle cx="{cx}" cy="{cy}" r="50" />',
        '  </clipPath>',
        
        # Разделение пространства на "За планетой" (верхняя половина эллипса) и "Перед планетой" (нижняя)
        '  <clipPath id="back-clip">',
        '    <rect x="-500" y="-500" width="1000" height="500" />',
        '  </clipPath>',
        '  <clipPath id="front-clip">',
        '    <rect x="-500" y="0" width="1000" height="500" />',
        '  </clipPath>',
        
        # Градиент глубокого космоса
        '  <radialGradient id="space-bg" cx="50%" cy="50%" r="70%">',
        '    <stop offset="0%" stop-color="#111927" />',
        '    <stop offset="55%" stop-color="#0d1117" />',
        '    <stop offset="100%" stop-color="#06080c" />',
        '  </radialGradient>',
        
        # Изумрудная 3D-туманность, повторяющая форму наклоненных орбит
        '  <radialGradient id="nebula" cx="50%" cy="50%" r="50%">',
        '    <stop offset="0%" stop-color="#26a641" stop-opacity="0.18" />',
        '    <stop offset="50%" stop-color="#006d32" stop-opacity="0.06" />',
        '    <stop offset="100%" stop-color="#0d1117" stop-opacity="0" />',
        '  </radialGradient>',
        
        # Объемная тень на самой планете для 3D-эффекта сферы
        '  <radialGradient id="planet-3d-shade" cx="35%" cy="30%" r="70%">',
        '    <stop offset="0%" stop-color="#ffffff" stop-opacity="0.12" />',
        '    <stop offset="55%" stop-color="#000000" stop-opacity="0" />',
        '    <stop offset="100%" stop-color="#000000" stop-opacity="0.65" />',
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
        
        '  <g id="comet">',
        '    <path d="M -140 0 L 0 -1.8 L 0 1.8 Z" fill="url(#comet-tail)" />',
        '    <circle cx="0" cy="0" r="2.2" fill="#ffffff" filter="url(#glow)" />',
        '  </g>'
    ]

    # Генерируем эллиптические траектории (пути) для каждой из 12 орбит
    for i in range(len(sorted_months)):
        rx = base_radius + i * radius_step
        ry = rx * TILT
        # Чередуем направление вращения (по часовой и против часовой стрелки)
        sweep = 1 if i % 2 == 0 else 0
        path_d = f"M {rx} 0 A {rx} {ry} 0 1 {sweep} {-rx} 0 A {rx} {ry} 0 1 {sweep} {rx} 0"
        svg.append(f'  <path id="orbit-path-{i}" d="{path_d}" />')

    svg.extend([
        '</defs>',
        '<style>',
        '  .orbit-back { fill: none; stroke: #21262d; stroke-width: 1; stroke-dasharray: 4 4; opacity: 0.45; }',
        '  .orbit-front { fill: none; stroke: #30363d; stroke-width: 1.2; stroke-dasharray: 4 4; opacity: 0.9; }',
        '  .planet-border { fill: none; stroke: #39d353; stroke-width: 2; stroke-opacity: 0.5; }',
        '  .planet-halo { fill: none; stroke: #26a641; stroke-width: 6; stroke-opacity: 0.15; }',
        '  @keyframes twinkle { 0%, 100% { opacity: 0.15; } 50% { opacity: 0.95; } }',
        '  @keyframes shoot {',
        '    0% { transform: translateX(0px); opacity: 0; }',
        '    2% { opacity: 1; }',
        '    14% { opacity: 1; }',
        '    18% { transform: translateX(1150px); opacity: 0; }',
        '    100% { transform: translateX(1150px); opacity: 0; }',
        '  }',
        '  .twinkle-0 { animation: twinkle 3s ease-in-out infinite; }',
        '  .twinkle-1 { animation: twinkle 4s ease-in-out 1s infinite; }',
        '  .twinkle-2 { animation: twinkle 5s ease-in-out 2.5s infinite; }',
        '  .twinkle-3 { animation: twinkle 6s ease-in-out 0.5s infinite; }',
        '  .twinkle-4 { animation: twinkle 8s ease-in-out 3s infinite; }',
        '  .comet-1 { animation: shoot 15s ease-in infinite; }',
        '  .comet-2 { animation: shoot 24s ease-in 7s infinite; }',
        '  .comet-3 { animation: shoot 40s ease-in 19s infinite; }',
        '</style>',
        '<g clip-path="url(#space-clip)">',
        f'  <rect width="{width}" height="{height}" fill="url(#space-bg)" />',
        f'  <ellipse cx="{cx}" cy="{cy}" rx="390" ry="170" transform="rotate({ROLL_ANGLE} {cx} {cy})" fill="url(#nebula)" />'
    ])

    # Звездное небо
    rng = random.Random(42)
    star_colors = ["#ffffff", "#e6edf3", "#c9d1d9", "#a5d6ff", "#7ee787"]
    svg.append('  <g id="starfield">')
    for s in range(120):
        sx = rng.randint(12, width - 12)
        sy = rng.randint(12, height - 12)
        if math.hypot(sx - cx, sy - cy) < 58:
            continue
        scolor = rng.choice(star_colors)
        if s < 70:
            sr = rng.uniform(0.5, 1.1)
            sop = rng.uniform(0.15, 0.5)
            svg.append(f'    <circle cx="{sx}" cy="{sy}" r="{sr:.1f}" fill="{scolor}" opacity="{sop:.2f}" />')
        elif s < 114:
            sr = rng.uniform(1.0, 1.8)
            tw_cls = f"twinkle-{s % 5}"
            svg.append(f'    <circle cx="{sx}" cy="{sy}" r="{sr:.1f}" fill="{scolor}" class="{tw_cls}" />')
        else:
            tw_cls = f"twinkle-{s % 5}"
            svg.append(
                f'    <g class="{tw_cls}" transform="translate({sx}, {sy})">'
                f'<path d="M -6 0 L 6 0 M 0 -6 L 0 6" stroke="{scolor}" stroke-width="0.9" opacity="0.6" />'
                f'<circle cx="0" cy="0" r="1.8" fill="#ffffff" filter="url(#glow)" />'
                f'</g>'
            )
    svg.append('  </g>')

    # Пролетающие кометы
    svg.append('  <g transform="translate(-80, 70) rotate(18)"><use href="#comet" class="comet-1" /></g>')
    svg.append('  <g transform="translate(880, 140) rotate(158)"><use href="#comet" class="comet-2" /></g>')
    svg.append('  <g transform="translate(140, -60) rotate(48)"><use href="#comet" class="comet-3" /></g>')

    # Формируем два 3D-слоя для орбит: задний (за планетой) и передний (перед планетой)
    back_layer = [f'  <g transform="translate({cx}, {cy}) rotate({ROLL_ANGLE})" clip-path="url(#back-clip)">']
    front_layer = [f'  <g transform="translate({cx}, {cy}) rotate({ROLL_ANGLE})" clip-path="url(#front-clip)">']

    for i, m_key in enumerate(sorted_months):
        rx = base_radius + i * radius_step
        ry = rx * TILT
        duration = ORBIT_DURATIONS[i]

        # Задняя дуга орбиты чуть тусклее (эффект глубины), передняя — четче
        back_layer.append(f'    <ellipse cx="0" cy="0" rx="{rx}" ry="{ry}" class="orbit-back" />')
        front_layer.append(f'    <ellipse cx="0" cy="0" rx="{rx}" ry="{ry}" class="orbit-front" />')

        year, month = map(int, m_key.split("-"))
        total_days = calendar.monthrange(year, month)[1]

        for d in months[m_key]:
            level = d["contributionLevel"]
            if level == "NONE":
                continue

            day_num = int(d["date"].split("-")[2])
            frac = day_num / total_days
            # Смещение старта анимации (отрицательный begin ставит точку сразу на нужный день орбиты)
            begin_offset = -frac * duration
            color = COLORS.get(level, "#39d353")
            dot_radius = 4.5 if level in ("FIRST_QUARTILE", "SECOND_QUARTILE") else 6

            dot_svg = (
                f'    <circle r="{dot_radius}" fill="{color}" filter="url(#glow)">'
                f'<title>{d["date"]}: {d["contributionCount"]} commits</title>'
                f'<animateMotion dur="{duration}s" begin="{begin_offset:.2f}s" repeatCount="indefinite">'
                f'<mpath href="#orbit-path-{i}" />'
                f'</animateMotion>'
                f'</circle>'
            )
            back_layer.append(dot_svg)
            front_layer.append(dot_svg)

    back_layer.append('  </g>')
    front_layer.append('  </g>')

    # 1. Сначала рисуем дальнюю половину орбит (проходит ЗА планетой)
    svg.extend(back_layer)

    # 2. В центре рисуем саму планету-аватарку с 3D-светотенью
    svg.append(f'  <circle cx="{cx}" cy="{cy}" r="53" class="planet-halo" />')
    svg.append(f'  <image href="data:image/png;base64,{avatar_b64}" x="{cx-50}" y="{cy-50}" height="100" width="100" clip-path="url(#avatar-clip)" />')
    svg.append(f'  <circle cx="{cx}" cy="{cy}" r="50" fill="url(#planet-3d-shade)" />')
    svg.append(f'  <circle cx="{cx}" cy="{cy}" r="50" class="planet-border" />')

    # 3. Поверх планеты рисуем ближнюю половину орбит (проходит ПЕРЕД планетой)
    svg.extend(front_layer)

    svg.append('</g>')
    svg.append('</svg>')

    os.makedirs("dist", exist_ok=True)
    with open("dist/cosmos.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    print("3D-файл dist/cosmos.svg успешно создан!")

if __name__ == "__main__":
    generate_svg()