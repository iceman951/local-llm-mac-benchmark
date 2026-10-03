#!/usr/bin/env python3
"""Render README result figures as static light/dark SVG files.

Reads saved run metadata, task records and Ollama /api/ps observations; never
runs a model or generated code. Reviewed per-task test counts and notes come
from docs/figures/task-notes.json. Output: docs/figures/*-{light,dark}.svg.
"""

import glob
import json
import os
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "figures")

THEMES = {
    "light": {
        "bg": "#f6f7f9", "panel": "#ffffff", "ink": "#12161d", "ink2": "#4b5361",
        "ink3": "#7a8291", "rule": "#dfe3e9", "track": "#e8ebf0", "accent": "#1f4e8c",
        "fail": "#c23434", "fail_bg": "#fbeceb", "s": ["#2a78d6", "#eb6834", "#1baf7a"],
        "dot_before": "#9aa2b0",
    },
    "dark": {
        "bg": "#0d1117", "panel": "#161b22", "ink": "#eef1f5", "ink2": "#b4bbc7",
        "ink3": "#848c99", "rule": "#2b313a", "track": "#262b33", "accent": "#8fb6ec",
        "fail": "#e66767", "fail_bg": "#3a2224", "s": ["#3987e5", "#d95926", "#199e70"],
        "dot_before": "#6b7380",
    },
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"


def fmt(value, digits=0):
    return "{:,.{d}f}".format(value, d=digits)


def load_runs():
    notes_path = os.path.join(OUT, "task-notes.json")
    with open(notes_path) as handle:
        notes = json.load(handle)
    runs = []
    for path in sorted(glob.glob(os.path.join(ROOT, "metadata", "runs", "*.json"))):
        with open(path) as handle:
            meta = json.load(handle)
        result = meta.get("result") or {}
        if result.get("status") != "completed":
            continue
        run_id = meta["run_id"]
        raw = os.path.join(ROOT, "results", "raw", run_id)
        tasks = []
        for task in result["tasks"]:
            record_path = os.path.join(raw, "aider", task["task"], ".aider.results.json")
            completion = None
            if os.path.exists(record_path):
                with open(record_path) as handle:
                    completion = json.load(handle).get("completion_tokens")
            note = notes.get(run_id, {}).get(task["task"], {})
            tasks.append({
                "task": task["task"], "language": task["language"],
                "passed": task["passed"], "duration": task["duration_sec"],
                "completion": completion, **note,
            })
        resident = None
        for ps_path in sorted(glob.glob(os.path.join(raw, "ollama-ps-*.json"))):
            with open(ps_path) as handle:
                for model in json.load(handle).get("models", []):
                    if model.get("digest") == meta["model"]["digest"]:
                        resident = model.get("size_vram")
        details = meta["model"].get("details") or {}
        runs.append({
            "run_id": run_id, "model": meta["model"]["name"],
            "spec": "{} · {} · {:.1f} GB".format(
                details.get("parameter_size", "?"), details.get("quantization_level", "?"),
                meta["model"]["size"] / 1e9),
            "total": result["total_time_sec"], "task_count": result["task_count"],
            "passed": result["passed"], "tasks": tasks,
            "swap_before": meta["observations"]["before"]["swap_used_mb"],
            "swap_peak": result["peak_swap_mb"], "resident": resident,
        })
    return runs


def task_title(task):
    return "{} · {}".format(task["language"].capitalize(), task["task"].rsplit("/", 1)[-1])


def wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        lines.append(line)
    return lines


class Svg:
    def __init__(self, width, height, theme):
        self.w, self.h, self.t, self.parts = width, height, theme, []

    def add(self, fragment):
        self.parts.append(fragment)

    def text(self, x, y, value, size=12, fill=None, weight=400, family=SANS, anchor="start", spacing=None):
        extra = ' letter-spacing="{}"'.format(spacing) if spacing else ""
        self.add('<text x="{:.1f}" y="{:.1f}" font-family="{}" font-size="{}" font-weight="{}" fill="{}" text-anchor="{}"{}>{}</text>'.format(
            x, y, family, size, weight, fill or self.t["ink"], anchor, extra, escape(str(value))))

    def rect(self, x, y, w, h, fill, rx=0, stroke=None):
        stroke_attr = ' stroke="{}" stroke-width="1"'.format(stroke) if stroke else ""
        self.add('<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" rx="{}" fill="{}"{}/>'.format(
            x, y, max(w, 0), h, rx, fill, stroke_attr))

    def line(self, x1, y1, x2, y2, stroke, width=1, dash=None):
        dash_attr = ' stroke-dasharray="{}"'.format(dash) if dash else ""
        self.add('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" stroke="{}" stroke-width="{}"{}/>'.format(
            x1, y1, x2, y2, stroke, width, dash_attr))

    def bar_end(self, x, y, w, h, fill):
        """Bar segment with a 4px rounded data end on the right."""
        r = min(4, w / 2, h / 2)
        self.add('<path d="M{:.1f},{:.1f} h{:.1f} a{r},{r} 0 0 1 {r},{r} v{:.1f} a{r},{r} 0 0 1 -{r},{r} h{:.1f} z" fill="{}"/>'.format(
            x, y, w - r, h - 2 * r, -(w - r), fill, r=r))

    def render(self, title):
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
                '<title>{title}</title>{body}</svg>\n').format(
            w=self.w, h=self.h, title=escape(title), body="".join(self.parts))


def matrix_svg(runs, t):
    width, pad, model_w, row_h, head_h, top = 960, 24, 200, 104, 34, 96
    task_names = [task_title(task) for task in runs[0]["tasks"]]
    col_w = (width - 2 * pad - model_w) / len(task_names)
    height = top + head_h + row_h * len(runs) + 20
    svg = Svg(width, height, t)
    svg.rect(0.5, 0.5, width - 1, height - 1, t["panel"], rx=8, stroke=t["rule"])

    all_zero = all(run["passed"] == 0 for run in runs)
    task_count = runs[0]["task_count"]
    svg.text(pad, 62, "{}/{}".format(0 if all_zero else "–", task_count), size=44, weight=700)
    svg.text(pad + 96, 44, "Every model passed 0 of {} tasks".format(task_count) if all_zero else "Task outcomes", size=18, weight=600)
    svg.text(pad + 96, 68, "A task passes only when its whole test suite passes. Bars show unit tests passed in the final attempt.", size=12.5, fill=t["ink2"])
    svg.line(pad, top - 8, width - pad, top - 8, t["ink"], 2)

    y_head = top + 14
    svg.text(pad, y_head, "MODEL", size=10.5, fill=t["ink3"], family=MONO, spacing=0.8)
    for i, name in enumerate(task_names):
        x = pad + model_w + i * col_w + 12
        svg.rect(x, y_head - 9, 9, 9, t["s"][i % 3], rx=2)
        svg.text(x + 15, y_head, name.upper(), size=10.5, fill=t["ink3"], family=MONO, spacing=0.8)

    for r, run in enumerate(runs):
        y0 = top + head_h + r * row_h
        svg.line(pad, y0, width - pad, y0, t["rule"])
        svg.text(pad, y0 + 30, run["model"], size=14, weight=600, family=MONO)
        svg.text(pad, y0 + 50, run["spec"], size=11.5, fill=t["ink3"])
        svg.text(pad, y0 + 70, "run {} s".format(fmt(run["total"])), size=11.5, fill=t["ink3"], family=MONO)
        for i, task in enumerate(run["tasks"]):
            x = pad + model_w + i * col_w + 12
            inner = col_w - 28
            ok = task["passed"]
            chip_fill = t["fail_bg"] if not ok else t["track"]
            chip_ink = t["fail"] if not ok else t["ink"]
            svg.rect(x, y0 + 16, 58, 19, chip_fill, rx=4)
            svg.text(x + 29, y0 + 29.5, "✕ FAIL" if not ok else "✓ PASS", size=10.5, weight=700, fill=chip_ink, anchor="middle")
            svg.text(x + inner, y0 + 29.5, "{} s".format(fmt(task["duration"], 1)), size=11, fill=t["ink3"], family=MONO, anchor="end")
            passed, total = task.get("tests_passed"), task.get("tests_total")
            if passed is not None and total:
                svg.text(x, y0 + 56, "{}/{} tests".format(passed, total), size=12.5, weight=600)
                bx, bw = x + 92, inner - 92
                svg.rect(bx, y0 + 49, bw, 6, t["track"], rx=3)
                if passed:
                    svg.rect(bx, y0 + 49, bw * passed / total, 6, t["ink2"], rx=3)
            elif task.get("label"):
                svg.text(x, y0 + 56, task["label"], size=12.5, weight=600)
            for j, line in enumerate(wrap(task.get("note", ""), 40)[:2]):
                svg.text(x, y0 + 77 + j * 15, line, size=11.5, fill=t["ink2"])
    return svg.render("Per-task outcomes")


def panel_frame(svg, x, y, w, h, title, t):
    svg.rect(x + 0.5, y + 0.5, w - 1, h - 1, t["panel"], rx=8, stroke=t["rule"])
    svg.text(x + 18, y + 28, title, size=14, weight=600)


def legend(svg, x, y, items, t):
    for label, kind, color in items:
        if kind == "swatch":
            svg.rect(x, y - 9, 10, 10, color, rx=2)
        elif kind == "dash":
            svg.line(x, y - 4, x + 12, y - 4, color, 1.5, "4 3")
        elif kind == "ring":
            svg.add('<circle cx="{:.1f}" cy="{:.1f}" r="4" fill="{}" stroke="{}" stroke-width="2"/>'.format(x + 5, y - 4, t["panel"], color))
        else:
            svg.add('<circle cx="{:.1f}" cy="{:.1f}" r="5" fill="{}"/>'.format(x + 5, y - 4, color))
        svg.text(x + 16, y, label, size=11.5, fill=t["ink2"])
        x += 24 + len(label) * 6.6


def axis(svg, x0, y0, plot_w, rows, row_h, max_v, ticks, tick_fmt, t):
    bottom = y0 + rows * row_h
    for tick in ticks:
        tx = x0 + tick / max_v * plot_w
        svg.line(tx, y0, tx, bottom, t["rule"])
        svg.text(tx, bottom + 15, tick_fmt(tick), size=10.5, fill=t["ink3"], family=MONO, anchor="middle")
    return lambda v: x0 + v / max_v * plot_w


def measurements_svg(runs, t):
    width, gap, pw, ph = 960, 16, 472, 236
    height = ph * 2 + gap
    svg = Svg(width, height, t)
    label_w, right, row_h, bar_h = 132, 58, 30, 14
    task_names = [task_title(task).split(" · ")[0] for task in runs[0]["tasks"]]
    swatches = [(name, "swatch", t["s"][i % 3]) for i, name in enumerate(task_names)]

    def rows_top(py):
        return py + 64

    def model_labels(px, py):
        for r, run in enumerate(runs):
            svg.text(px + label_w, rows_top(py) + r * row_h + row_h / 2 + 4, run["model"], size=11.5, family=MONO, anchor="end")

    def stacked(px, py, title, key, max_v, ticks, tick_fmt, total_fmt, caption):
        panel_frame(svg, px, py, pw, ph, title, t)
        legend(svg, px + 18, py + 50, swatches, t)
        x0 = px + label_w + 10
        scale = axis(svg, x0, rows_top(py), pw - label_w - 10 - right, len(runs), row_h, max_v, ticks, tick_fmt, t)
        model_labels(px - 0, py)
        for r, run in enumerate(runs):
            y = rows_top(py) + r * row_h + (row_h - bar_h) / 2
            acc = 0
            values = [task[key] or 0 for task in run["tasks"]]
            for i, value in enumerate(values):
                xa, xb = scale(acc), scale(acc + value)
                last = i == len(values) - 1
                if last:
                    svg.bar_end(xa, y, max(xb - xa, 1), bar_h, t["s"][i % 3])
                else:
                    svg.rect(xa, y, max(xb - xa - 2, 1), bar_h, t["s"][i % 3])
                acc += value
            svg.text(scale(acc) + 6, y + bar_h / 2 + 4, total_fmt(acc), size=11, fill=t["ink2"], family=MONO)
        svg.text(px + 18, py + ph - 14, caption, size=11, fill=t["ink3"])

    stacked(0, 0, "Wall time per task", "duration", 1600, [0, 400, 800, 1200, 1600],
            lambda v: fmt(v), lambda v: "{} s".format(fmt(v)),
            "Bar end = sum of task times. The 14B run swapped heavily; not a clean speed figure.")
    stacked(pw + gap, 0, "Completion tokens (both attempts)", "completion", 25000, [0, 5000, 10000, 15000, 20000, 25000],
            lambda v: "0" if v == 0 else "{}k".format(v // 1000), lambda v: "{:.1f}k".format(v / 1000),
            "ornith:9b spent most tokens thinking; its Python and Go answers were empty.")

    # Swap dumbbell
    px, py = 0, ph + gap
    panel_frame(svg, px, py, pw, ph, "Host swap: before run → peak", t)
    legend(svg, px + 18, py + 50, [("Before", "ring", t["dot_before"]), ("Peak during run", "dot", t["ink"])], t)
    x0 = px + label_w + 10
    scale = axis(svg, x0, rows_top(py), pw - label_w - 10 - right, len(runs), row_h, 10000,
                 [0, 2500, 5000, 7500, 10000], lambda v: "0" if v == 0 else fmt(v), t)
    model_labels(px, py)
    for r, run in enumerate(runs):
        cy = rows_top(py) + r * row_h + row_h / 2
        a, b = scale(run["swap_before"]), scale(run["swap_peak"])
        if b - a > 1:
            svg.line(a, cy, b, cy, t["ink2"], 2)
        svg.add('<circle cx="{:.1f}" cy="{:.1f}" r="5" fill="{}" stroke="{}" stroke-width="2"/>'.format(b, cy, t["ink"], t["panel"]))
        svg.add('<circle cx="{:.1f}" cy="{:.1f}" r="4.5" fill="{}" stroke="{}" stroke-width="2"/>'.format(a, cy, t["panel"], t["dot_before"]))
        delta = run["swap_peak"] - run["swap_before"]
        label = "+{} MiB".format(fmt(delta)) if delta > 0.5 else "±0"
        if max(a, b) + 11 + len(label) * 6.7 > px + pw - 8:
            svg.text(min(a, b) - 11, cy + 4, label, size=11, fill=t["ink2"], family=MONO, anchor="end")
        else:
            svg.text(max(a, b) + 11, cy + 4, label, size=11, fill=t["ink2"], family=MONO)
    svg.text(px + 18, py + ph - 14, "MiB, whole host. Background apps stayed open; 14B swap was still present for ornith.", size=11, fill=t["ink3"])

    # Resident size
    px = pw + gap
    panel_frame(svg, px, py, pw, ph, "Model resident size (GPU)", t)
    legend(svg, px + 18, py + 50, [("Ollama /api/ps, context 8192", "swatch", t["accent"]), ("Docker VM 8.3 GB", "dash", t["ink3"])], t)
    x0 = px + label_w + 10
    scale = axis(svg, x0, rows_top(py), pw - label_w - 10 - right, len(runs), row_h, 12,
                 [0, 3, 6, 9, 12], lambda v: "{} GB".format(v), t)
    vx = scale(8.32)
    svg.line(vx, rows_top(py) - 4, vx, rows_top(py) + len(runs) * row_h, t["ink3"], 1.5, "4 3")
    model_labels(px, py)
    for r, run in enumerate(runs):
        y = rows_top(py) + r * row_h + (row_h - bar_h) / 2
        if run["resident"]:
            gb = run["resident"] / 1e9
            svg.bar_end(x0, y, scale(gb) - x0, bar_h, t["accent"])
            svg.text(scale(gb) + 6, y + bar_h / 2 + 4, "{:.2f}".format(gb), size=11, fill=t["ink2"], family=MONO)
        else:
            svg.text(x0 + 4, y + bar_h / 2 + 4, "not recorded", size=11, fill=t["ink3"])
    svg.text(px + 18, py + ph - 14, "All models ran 100% on GPU. The Docker VM shares the same 24 GiB.", size=11, fill=t["ink3"])
    return svg.render("Time, tokens and memory")


def main():
    runs = load_runs()
    if not runs:
        sys.exit("No completed runs found in metadata/runs/")
    os.makedirs(OUT, exist_ok=True)
    for name, theme in THEMES.items():
        for stem, render in (("outcomes", matrix_svg), ("measurements", measurements_svg)):
            path = os.path.join(OUT, "{}-{}.svg".format(stem, name))
            with open(path, "w") as handle:
                handle.write(render(runs, theme))
            print("Wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
