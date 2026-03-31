import json
import urllib.request
import sys

USERNAME = "eeguskiza"
API_URL = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}"

# Dracula color palette for bars (cycles if more years than colors)
BAR_COLORS = [
    ("#ff79c6", "#bd93f9"),  # pink → purple
    ("#8be9fd", "#6272a4"),  # cyan → muted blue
    ("#50fa7b", "#28a745"),  # green → dark green
    ("#ffb86c", "#f1fa8c"),  # orange → yellow
    ("#ff5555", "#ff79c6"),  # red → pink
    ("#bd93f9", "#6272a4"),  # purple → muted blue
]

LABEL_COLORS = ["#bd93f9", "#8be9fd", "#50fa7b", "#ffb86c", "#ff5555", "#bd93f9"]


def fetch_contributions():
    req = urllib.request.Request(API_URL)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())

    yearly = {}
    for day in data["contributions"]:
        year = int(day["date"][:4])
        yearly[year] = yearly.get(year, 0) + day["count"]

    # Remove years with 0 contributions
    yearly = {y: c for y, c in yearly.items() if c > 0}

    return dict(sorted(yearly.items()))


def generate_svg(yearly):
    years = list(yearly.keys())
    values = list(yearly.values())
    n = len(years)
    total = sum(values)
    max_val = max(values)
    # Round up max to nearest 50 for clean axis
    y_max = ((max_val // 50) + 1) * 50

    # Layout
    chart_left = 100
    chart_right = 720
    chart_top = 70
    chart_bottom = 250
    chart_height = chart_bottom - chart_top
    bar_width = min(80, int((chart_right - chart_left - 40) / n) - 20)
    total_bars_width = n * (bar_width + 20) - 20
    start_x = chart_left + (chart_right - chart_left - total_bars_width) // 2

    # Build gradients
    gradients = ""
    for i in range(n):
        ci = i % len(BAR_COLORS)
        c1, c2 = BAR_COLORS[ci]
        gradients += f'''    <linearGradient id="bar{years[i]}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>\n'''

    # Build Y-axis labels
    num_gridlines = 4
    step = y_max / num_gridlines
    y_labels = ""
    grid_lines = ""
    for i in range(num_gridlines + 1):
        val = int(step * i)
        y = chart_bottom - (val / y_max) * chart_height
        y_labels += f'  <text x="90" y="{y + 4:.0f}" text-anchor="end" fill="#6272a4" font-family="\'Segoe UI\', Ubuntu, sans-serif" font-size="12">{val}</text>\n'
        if i > 0:
            grid_lines += f'  <line x1="{chart_left}" y1="{y:.0f}" x2="{chart_right}" y2="{y:.0f}" stroke="#44475a" stroke-width="0.3" stroke-dasharray="4"/>\n'

    # Build bars
    bars = ""
    for i, (year, val) in enumerate(zip(years, values)):
        ci = i % len(LABEL_COLORS)
        bar_h = (val / y_max) * chart_height
        bar_y = chart_bottom - bar_h
        bar_x = start_x + i * (bar_width + 20)
        center_x = bar_x + bar_width / 2
        dur = f"{0.6 + i * 0.1:.1f}s"

        bars += f'''  <rect x="{bar_x}" y="{bar_y:.1f}" width="{bar_width}" height="{bar_h:.1f}" rx="4" fill="url(#bar{year})" filter="url(#glow)">
    <animate attributeName="height" from="0" to="{bar_h:.1f}" dur="{dur}" fill="freeze"/>
    <animate attributeName="y" from="{chart_bottom}" to="{bar_y:.1f}" dur="{dur}" fill="freeze"/>
  </rect>
  <text x="{center_x:.0f}" y="{bar_y - 8:.0f}" text-anchor="middle" fill="#f8f8f2" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="14" font-weight="600">{val}</text>
  <text x="{center_x:.0f}" y="272" text-anchor="middle" fill="{LABEL_COLORS[ci]}" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="13" font-weight="600">{year}</text>
'''

    first_year = years[0]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="320" viewBox="0 0 800 320">
  <defs>
{gradients}    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="800" height="320" rx="16" fill="#282a36"/>
  <rect width="800" height="320" rx="16" fill="none" stroke="#44475a" stroke-width="1"/>

  <!-- Title -->
  <text x="400" y="40" text-anchor="middle" fill="#f8f8f2" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="18" font-weight="600">Contributions by Year</text>

  <!-- Axes -->
  <line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#44475a" stroke-width="0.5"/>
  <line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#44475a" stroke-width="1"/>
{grid_lines}
  <!-- Y-axis labels -->
{y_labels}
  <!-- Bars -->
{bars}
  <!-- Footer -->
  <text x="400" y="300" text-anchor="middle" fill="#6272a4" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="11">Total: {total} contributions since Nov {first_year}</text>
</svg>
'''
    return svg


def main():
    yearly = fetch_contributions()
    svg = generate_svg(yearly)
    with open("assets/contributions-by-year.svg", "w") as f:
        f.write(svg)
    print(f"Generated chart with {len(yearly)} years: {list(yearly.keys())}")


if __name__ == "__main__":
    main()
