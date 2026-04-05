"""
Clean Line Bento — 순수 SVG 차트 모음
Plotly 없이 SVG를 직접 생성합니다.
st.markdown(chart_html, unsafe_allow_html=True) 로 렌더링하세요.
"""
from __future__ import annotations


def vbar(
    data: dict,
    width: int = 580,
    height: int = 160,
    color: str = '#FF4B4B',
    muted: str = '#DEE2E6',
) -> str:
    """
    세로 막대 차트 — 24시간 시간대 분포용.
    data: {"0": count, ..., "23": count}
    피크(최댓값) 시간대는 accent 색으로 강조됩니다.
    """
    keys   = list(data.keys())
    values = [int(data.get(k, 0)) for k in keys]
    n      = len(keys)

    if n == 0:
        return _empty_svg(width, 40)

    PAD_L, PAD_R, PAD_T, PAD_B = 32, 8, 12, 24
    cw = width - PAD_L - PAD_R
    ch = height - PAD_T - PAD_B

    max_val = max(values) if any(v > 0 for v in values) else 1
    peak_i  = values.index(max(values))

    gap   = 2
    bar_w = max(1.0, (cw - gap * (n - 1)) / n)

    elems: list[str] = []

    # Y gridlines (3 levels)
    for pct in [0.25, 0.5, 1.0]:
        gy = PAD_T + ch * (1 - pct)
        gv = int(max_val * pct)
        elems.append(
            f'<line x1="{PAD_L}" y1="{gy:.1f}" x2="{width - PAD_R}" y2="{gy:.1f}"'
            f' stroke="#F0F2F6" stroke-width="1"/>'
        )
        elems.append(
            f'<text x="{PAD_L - 3}" y="{gy + 4:.1f}" text-anchor="end"'
            f' font-size="10" fill="#ADB5BD">{gv}</text>'
        )

    # Bars + x-labels
    for i, (k, v) in enumerate(zip(keys, values)):
        bh   = (v / max_val) * ch if max_val > 0 else 0
        bx   = PAD_L + i * (bar_w + gap)
        by   = PAD_T + ch - bh
        fill = color if i == peak_i else muted
        elems.append(
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{max(bh, 0):.1f}"'
            f' fill="{fill}" rx="2"/>'
        )
        # X-label every 3 hours
        try:
            hour = int(k)
        except ValueError:
            hour = i
        if hour % 3 == 0:
            lx = bx + bar_w / 2
            elems.append(
                f'<text x="{lx:.1f}" y="{height - 4}" text-anchor="middle"'
                f' font-size="10" fill="#6C757D">{hour}시</text>'
            )

    return _svg(width, height, elems)


def hbar(
    items: list[tuple],
    width: int = 580,
    color: str = '#FF4B4B',
    bg_color: str = '#F8F9FA',
    label_w: int = 110,
) -> str:
    """
    가로 막대 차트 — 키워드 빈도·갤러리 비교용.
    items: [(label, value), ...] — 상위 항목이 먼저 오는 순서로 전달.
    상위일수록 진한 빨강, 하위일수록 연한 빨강으로 그라데이션.
    """
    items = list(items)
    n     = len(items)

    if n == 0:
        return _empty_svg(width, 40)

    ROW_H            = 28
    PAD_T, PAD_B, PAD_R = 6, 4, 12
    height           = n * ROW_H + PAD_T + PAD_B
    bar_area         = max(10, width - label_w - PAD_R)

    max_val = max(v for _, v in items) if items else 1
    if max_val == 0:
        max_val = 1

    def _bar_color(i: int) -> str:
        """상위 항목일수록 진한 accent 색."""
        t   = i / max(n - 1, 1)          # 0.0 (top) → 1.0 (bottom)
        r   = int(0xFF + (0xFE - 0xFF) * t)   # 255 → 254
        g   = int(0x4B + (0xCD - 0x4B) * t)   # 75  → 205
        b   = int(0x4B + (0xD3 - 0x4B) * t)   # 75  → 211
        return f'#{r:02X}{g:02X}{b:02X}'

    elems: list[str] = []
    for i, (label, val) in enumerate(items):
        y   = PAD_T + i * ROW_H
        bw  = (val / max_val) * bar_area
        short = (label[:14] + '…') if len(label) > 14 else label
        cy  = y + ROW_H * 0.65

        # Label (right-aligned)
        elems.append(
            f'<text x="{label_w - 5}" y="{cy:.1f}" text-anchor="end"'
            f' font-size="12" fill="#495057">{short}</text>'
        )
        # BG bar
        elems.append(
            f'<rect x="{label_w}" y="{y + 5}" width="{bar_area}" height="{ROW_H - 10}"'
            f' fill="{bg_color}" rx="3"/>'
        )
        # Value bar
        if bw > 0:
            elems.append(
                f'<rect x="{label_w}" y="{y + 5}" width="{bw:.1f}" height="{ROW_H - 10}"'
                f' fill="{_bar_color(i)}" rx="3"/>'
            )
        # Value label
        elems.append(
            f'<text x="{label_w + bw + 4:.1f}" y="{cy:.1f}"'
            f' font-size="11" fill="#6C757D">{val}</text>'
        )

    return _svg(width, height, elems)


def line(
    items: list[tuple],
    width: int = 580,
    height: int = 120,
    color: str = '#FF4B4B',
) -> str:
    """
    라인 차트 — 게시글 수 일별 추이용.
    items: [(date_str, count), ...] 날짜 오름차순 정렬.
    """
    items = list(items)
    n     = len(items)

    if n == 0:
        return _empty_svg(width, 40)
    if n == 1:
        return _empty_svg(width, 40, '데이터 1건 (추이 표시 불가)')

    PAD_L, PAD_R, PAD_T, PAD_B = 36, 8, 12, 24
    cw = width - PAD_L - PAD_R
    ch = height - PAD_T - PAD_B

    vals  = [v for _, v in items]
    max_v = max(vals) if vals else 1
    min_v = min(vals) if vals else 0
    rng   = max_v - min_v or 1

    def _pt(i: int, v: int) -> tuple[float, float]:
        x = PAD_L + i * cw / (n - 1)
        y = PAD_T + ch - (v - min_v) / rng * ch
        return x, y

    pts = [_pt(i, v) for i, (_, v) in enumerate(items)]

    elems: list[str] = []

    # Y gridlines
    for pct in [0.0, 0.5, 1.0]:
        gy = PAD_T + ch * (1 - pct)
        gv = int(min_v + rng * pct)
        elems.append(
            f'<line x1="{PAD_L}" y1="{gy:.1f}" x2="{width - PAD_R}" y2="{gy:.1f}"'
            f' stroke="#F0F2F6" stroke-width="1"/>'
        )
        elems.append(
            f'<text x="{PAD_L - 3}" y="{gy + 4:.1f}" text-anchor="end"'
            f' font-size="10" fill="#ADB5BD">{gv}</text>'
        )

    # Fill area (light)
    fill_pts = (
        f'{PAD_L:.1f},{PAD_T + ch:.1f} '
        + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        + f' {width - PAD_R:.1f},{PAD_T + ch:.1f}'
    )
    elems.append(f'<polygon points="{fill_pts}" fill="{color}" opacity="0.08"/>')

    # Line
    path_d = 'M ' + ' L '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    elems.append(
        f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="2"'
        f' stroke-linejoin="round" stroke-linecap="round"/>'
    )

    # Dots (only for ≤30 points to avoid visual clutter)
    if n <= 30:
        for x, y in pts:
            elems.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3"'
                f' fill="{color}" stroke="white" stroke-width="1.5"/>'
            )

    # X-axis labels (5 evenly spaced)
    step = max(1, n // 5)
    for i in range(0, n, step):
        lbl, _ = items[i]
        x, _   = pts[i]
        short  = lbl[5:10] if len(lbl) >= 10 else lbl   # MM-DD
        elems.append(
            f'<text x="{x:.1f}" y="{height - 4}" text-anchor="middle"'
            f' font-size="10" fill="#6C757D">{short}</text>'
        )

    return _svg(width, height, elems)


# ── Helpers ──────────────────────────────────────────────────────────

def _svg(width: int, height: int, elems: list[str]) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'style="width:100%;max-width:{width}px;display:block;overflow:visible;">'
        + ''.join(elems)
        + '</svg>'
    )


def _empty_svg(width: int, height: int, msg: str = '데이터 없음') -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'style="width:100%;display:block;">'
        f'<text x="50%" y="{height // 2 + 4}" text-anchor="middle"'
        f' font-size="12" fill="#ADB5BD">{msg}</text>'
        f'</svg>'
    )


def wrap(svg: str, title: str = '') -> str:
    """SVG를 lc 카드 div로 감쌉니다."""
    hdr = f'<div class="sec-hdr" style="margin-bottom:8px;">{title}</div>' if title else ''
    return f'<div class="lc" style="padding:14px 16px;">{hdr}{svg}</div>'
