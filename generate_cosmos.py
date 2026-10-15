import os
import math
import base64
import calendar
from datetime import datetime
import requests

# Настройки (при запуске через GitHub Actions подтянутся автоматически)
USERNAME = os.getenv("GITHUB_USER", "Thesavewill")
TOKEN = os.getenv("GH_TOKEN", "ТВОЙ_ТОКЕН_ДЛЯ_ТЕСТОВ")

# Палитра GitHub Dark Mode (только для активных дней)
COLORS = {
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353"
}

# Асинхронные скорости вращения (все числа — делители 240 секунд для идеального цикла)
# Отрицательные значения в коде заставят часть орбит крутиться в обратную сторону для красоты
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

    # Собираем все дни в плоский список
    days = [day for week in weeks for day in week["contributionDays"]]

    # Группируем по месяцам (ключ "YYYY-MM") и берем последние 12 месяцев
    months = {}
    for d in days:
        m_key = d["date"][:7]
        months.setdefault(m_key, []).append(d)
    
    # Сортируем от самого свежего месяца (1-я орбита) к самому старому (12-я орбита)
    sorted_months = sorted(months.keys(), reverse=True)[:12]

    cx, cy = 400, 400
    base_radius = 85
    radius_step = 24

    svg = [
        f'<svg viewBox="0 0 800 800" width="100%" height="800" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        '  <clipPath id="avatar-clip">',
        f'    <circle cx="{cx}" cy="{cy}" r="50" />',
        '  </clipPath>',
        '  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">',
        '    <feGaussianBlur stdDeviation="2.5" result="blur" />',
        '    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>',
        '  </filter>',
        '</defs>',
        '<style>',
        '  .bg { fill: #0d1117; }',
        '  .orbit-line { fill: none; stroke: #21262d; stroke-width: 1; stroke-dasharray: 4 4; }',
        '  .planet-border { fill: none; stroke: #30363d; stroke-width: 3; }',
        '  @keyframes spin-cw { 100% { transform: rotate(360deg); } }',
        '  @keyframes spin-ccw { 100% { transform: rotate(-360deg); } }'
    ]

    # Генерируем стили анимации для каждой из 12 орбит
    for i, duration in enumerate(ORBIT_DURATIONS):
        direction = "spin-cw" if i % 2 == 0 else "spin-ccw" # Чередуем направление вращения
        svg.append(f'  .orbit-{i} {{ transform-origin: {cx}px {cy}px; animation: {direction} {duration}s linear infinite; }}')

    svg.append('</style>')
    svg.append('<rect width="100%" height="100%" rx="16" class="bg" />')

    # Рисуем орбиты и активные дни
    for i, m_key in enumerate(sorted_months):
        r = base_radius + i * radius_step
        # Линия самой орбиты
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" class="orbit-line" />')
        
        # Группа для вращения точек этого месяца
        svg.append(f'<g class="orbit-{i}">')
        
        year, month = map(int, m_key.split("-"))
        total_days = calendar.monthrange(year, month)[1]

        for d in months[m_key]:
            level = d["contributionLevel"]
            # Пропускаем дни без коммитов
            if level == "NONE":
                continue

            day_num = int(d["date"].split("-")[2])
            angle = (day_num / total_days) * 2 * math.pi - (math.pi / 2)
            
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            color = COLORS.get(level, "#39d353")
            
            # Размер точки чуть увеличивается, если коммитов много
            dot_radius = 4.5 if level in ("FIRST_QUARTILE", "SECOND_QUARTILE") else 6

            svg.append(
                f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{dot_radius}" '
                f'fill="{color}" filter="url(#glow)">'
                f'<title>{d["date"]}: {d["contributionCount"]} commits</title>'
                f'</circle>'
            )
        svg.append('</g>')

    # Рисуем центральную планету-аватарку
    svg.append(f'<image href="data:image/png;base64,{avatar_b64}" x="{cx-50}" y="{cy-50}" height="100" width="100" clip-path="url(#avatar-clip)" />')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="50" class="planet-border" />')
    svg.append('</svg>')

    with open("cosmos.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    print("Файл cosmos.svg успешно создан!")

if __name__ == "__main__":
    generate_svg()