"""
DC-Pickaxe Analytics — 순수 SVG 차트 모음 v4
앰버(#E8A020) 피크 강조, 그레이 기본
"""
from __future__ import annotations


def vbar(
    data: dict,
    width: int = 580,
    height: int = 160,
    color: str = '#E8A020',
    muted: str = '#E2E8F0',
) -> str:
    keys   = list(data.keys())
    values = [int(data.get(k, 0)) for k in keys]
    n      = len(keys)
    if n == 0:
        return _empty(width, 40)

    PAD_L, PAD_R, PAD_T, PAD_B = 32, 8, 10, 24
    cw = width - PAD_L - PAD_R
    ch = height - PAD_T - PAD_B
    max_val = max(values) if any(v > 0 for v in values) else 1
    peak_i  = values.index(max(values))
    gap     = 2
    bar_w   = max(1.0, (cw - gap * (n - 1)) / n)
    elems: list[str] = []

    for pct in [0.25, 0.5, 0.75, 1.0]:
        gy = PAD_T + ch * (1 - pct)
        gv = int(max_val * pct)
        elems.append(
            f'<line x1="{PAD_L}" y1="{gy:.1f}" x2="{width-PAD_R}" y2="{gy:.1f}"'
            f' stroke="#F1F5F9" stroke-width="1"/>'
        )
        if pct in [0.5, 1.0]:
            elems.append(
                f'<text x="{PAD_L-3}" y="{gy+4:.1f}" text-anchor="end"'
                f' font-size="10" fill="#94A3B8">{gv}</text>'
            )

    for i, (k, v) in enumerate(zip(keys, values)):
        bh   = (v / max_val) * ch if max_val > 0 else 0
        bx   = PAD_L + i * (bar_w + gap)
        by   = PAD_T + ch - bh
        fill = color if i == peak_i else muted
        if bh > 4:
            elems.append(
                f'<rect x="{bx:.1f}" y="{by+3:.1f}" width="{bar_w:.1f}"'
                f' height="{max(bh-3,0):.1f}" fill="{fill}"/>'
            )
            r = min(bar_w / 2, 3)
            elems.append(
                f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}"'
                f' height="6" fill="{fill}" rx="{r}"/>'
            )
        else:
            elems.append(
                f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}"'
                f' height="{max(bh,0):.1f}" fill="{fill}" rx="2"/>'
            )
        if i == peak_i and v > 0:
            elems.append(
                f'<text x="{bx+bar_w/2:.1f}" y="{by-3:.1f}" text-anchor="middle"'
                f' font-size="9" font-weight="700" fill="{color}">{v}</text>'
            )
        try:
            hour = int(k)
        except ValueError:
            hour = i
        if hour % 3 == 0:
            lx = bx + bar_w / 2
            elems.append(
                f'<text x="{lx:.1f}" y="{height-4}" text-anchor="middle"'
                f' font-size="10" fill="#94A3B8">{hour}시</text>'
            )
    return _svg(width, height, elems)


def hbar(
    items: list[tuple],
    width: int = 580,
    color: str = '#E8A020',
    bg_color: str = '#F8FAFC',
    label_w: int = 110,
) -> str:
    items = list(items)
    n     = len(items)
    if n == 0:
        return _empty(width, 40)

    ROW_H            = 30
    PAD_T, PAD_B, PAD_R = 6, 4, 16
    height           = n * ROW_H + PAD_T + PAD_B
    bar_area         = max(10, width - label_w - PAD_R)
    max_val          = max(v for _, v in items) if items else 1
    if max_val == 0:
        max_val = 1

    def _c(i: int) -> str:
        t   = i / max(n - 1, 1)
        # amber → slate gradient
        r = int(0xE8 + (0x64 - 0xE8) * t)
        g = int(0xA0 + (0x74 - 0xA0) * t)
        b = int(0x20 + (0x8B - 0x20) * t)
        return f'#{r:02X}{g:02X}{b:02X}'

    elems: list[str] = []
    for i, (label, val) in enumerate(items):
        y     = PAD_T + i * ROW_H
        bw    = (val / max_val) * bar_area
        short = (label[:15] + '…') if len(label) > 15 else label
        cy    = y + ROW_H * 0.63
        elems.append(
            f'<text x="{label_w-6}" y="{cy:.1f}" text-anchor="end"'
            f' font-size="12" fill="#475569">{short}</text>'
        )
        elems.append(
            f'<rect x="{label_w}" y="{y+6}" width="{bar_area}" height="{ROW_H-12}"'
            f' fill="{bg_color}" rx="4"/>'
        )
        if bw > 0:
            elems.append(
                f'<rect x="{label_w}" y="{y+6}" width="{bw:.1f}" height="{ROW_H-12}"'
                f' fill="{_c(i)}" rx="4"/>'
            )
        elems.append(
            f'<text x="{label_w+bw+5:.1f}" y="{cy:.1f}"'
            f' font-size="11" fill="#94A3B8">{val}</text>'
        )
    return _svg(width, height, elems)


def line(
    items: list[tuple],
    width: int = 580,
    height: int = 130,
    color: str = '#E8A020',
    fill_opacity: float = 0.10,
) -> str:
    items = list(items)
    n     = len(items)
    if n == 0:
        return _empty(width, 40)
    if n == 1:
        return _empty(width, 40, '데이터 1건 (추이 표시 불가)')

    PAD_L, PAD_R, PAD_T, PAD_B = 36, 12, 14, 26
    cw = width - PAD_L - PAD_R
    ch = height - PAD_T - PAD_B
    vals  = [v for _, v in items]
    max_v = max(vals) if vals else 1
    min_v = min(vals) if vals else 0
    rng   = max_v - min_v or 1

    def _pt(i, v):
        x = PAD_L + i * cw / (n - 1)
        y = PAD_T + ch - (v - min_v) / rng * ch
        return x, y

    pts   = [_pt(i, v) for i, (_, v) in enumerate(items)]
    elems: list[str] = []

    for pct in [0.0, 0.5, 1.0]:
        gy = PAD_T + ch * (1 - pct)
        gv = int(min_v + rng * pct)
        elems.append(
            f'<line x1="{PAD_L}" y1="{gy:.1f}" x2="{width-PAD_R}" y2="{gy:.1f}"'
            f' stroke="#F1F5F9" stroke-width="1"/>'
        )
        elems.append(
            f'<text x="{PAD_L-3}" y="{gy+4:.1f}" text-anchor="end"'
            f' font-size="10" fill="#94A3B8">{gv}</text>'
        )

    fill_pts = (
        f'{PAD_L:.1f},{PAD_T+ch:.1f} '
        + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        + f' {width-PAD_R:.1f},{PAD_T+ch:.1f}'
    )
    elems.append(
        f'<polygon points="{fill_pts}" fill="{color}" opacity="{fill_opacity}"/>'
    )
    path_d = 'M ' + ' L '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    elems.append(
        f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="2.5"'
        f' stroke-linejoin="round" stroke-linecap="round"/>'
    )
    if n <= 35:
        for x, y in pts:
            elems.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3"'
                f' fill="{color}" stroke="white" stroke-width="2"/>'
            )
    step = max(1, n // 5)
    for i in range(0, n, step):
        lbl, _ = items[i]
        x, _   = pts[i]
        short  = lbl[5:10] if len(lbl) >= 10 else lbl
        elems.append(
            f'<text x="{x:.1f}" y="{height-5}" text-anchor="middle"'
            f' font-size="10" fill="#94A3B8">{short}</text>'
        )
    return _svg(width, height, elems)


def multiline(
    series: list[dict],
    width: int = 700,
    height: int = 220,
) -> str:
    if not series:
        return _empty(width, 40)

    PAD_L, PAD_R, PAD_T, PAD_B = 40, 16, 14, 26
    all_dates = sorted({d for s in series for d, _ in s.get('items', [])})
    n = len(all_dates)
    if n < 2:
        return _empty(width, 40, '날짜 데이터 부족')

    date_idx  = {d: i for i, d in enumerate(all_dates)}
    all_vals  = [v for s in series for _, v in s.get('items', [])]
    max_v     = max(all_vals) if all_vals else 1
    min_v     = 0
    rng       = max_v - min_v or 1
    cw        = width - PAD_L - PAD_R
    ch        = height - PAD_T - PAD_B

    def _pt(date_str, val):
        x = PAD_L + date_idx[date_str] * cw / (n - 1)
        y = PAD_T + ch - (val - min_v) / rng * ch
        return x, y

    elems: list[str] = []
    for pct in [0.0, 0.25, 0.5, 0.75, 1.0]:
        gy = PAD_T + ch * (1 - pct)
        gv = int(min_v + rng * pct)
        elems.append(
            f'<line x1="{PAD_L}" y1="{gy:.1f}" x2="{width-PAD_R}" y2="{gy:.1f}"'
            f' stroke="#F1F5F9" stroke-width="1"/>'
        )
        if pct in [0, 0.5, 1.0]:
            elems.append(
                f'<text x="{PAD_L-3}" y="{gy+4:.1f}" text-anchor="end"'
                f' font-size="10" fill="#94A3B8">{gv}</text>'
            )

    for s in series:
        items = [(d, v) for d, v in s.get('items', []) if d in date_idx]
        if not items:
            continue
        color = s.get('color', '#E8A020')
        pts   = [_pt(d, v) for d, v in items]
        if len(pts) >= 2:
            fill_pts = (
                f'{pts[0][0]:.1f},{PAD_T+ch:.1f} '
                + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
                + f' {pts[-1][0]:.1f},{PAD_T+ch:.1f}'
            )
            elems.append(
                f'<polygon points="{fill_pts}" fill="{color}" opacity="0.07"/>'
            )
        path_d = 'M ' + ' L '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        elems.append(
            f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="2"'
            f' stroke-linejoin="round" stroke-linecap="round"/>'
        )

    step = max(1, n // 6)
    for i in range(0, n, step):
        d = all_dates[i]
        x = PAD_L + i * cw / (n - 1)
        short = d[5:10] if len(d) >= 10 else d
        elems.append(
            f'<text x="{x:.1f}" y="{height-5}" text-anchor="middle"'
            f' font-size="10" fill="#94A3B8">{short}</text>'
        )
    return _svg(width, height, elems)


def _svg(w, h, elems):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'style="width:100%;max-width:{w}px;display:block;overflow:visible;">'
        + ''.join(elems)
        + '</svg>'
    )


def _empty(w, h, msg='데이터 없음'):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'style="width:100%;display:block;">'
        f'<text x="50%" y="{h//2+4}" text-anchor="middle"'
        f' font-size="12" fill="#94A3B8">{msg}</text>'
        f'</svg>'
    )


def wrap(svg: str, title: str = '') -> str:
    hdr = (
        f'<div style="font-size:0.82rem;font-weight:700;color:#0F172A;'
        f'margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #E8A020;'
        f'display:inline-block;">{title}</div>'
    ) if title else ''
    return f'<div class="lc" style="padding:14px 16px;">{hdr}{svg}</div>'
