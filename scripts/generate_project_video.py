"""Create a captioned, slide-style overview video for the RAG defense project.

Run from the repository root with: python scripts/generate_project_video.py
The video is intentionally silent, matching the supplied caption-led reference.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "project_overview.mp4"
WIDTH, HEIGHT = 1280, 720
FPS = 15
SECONDS_PER_SLIDE = 6
BG = "#0b1020"
PANEL = "#121c30"
PANEL2 = "#17243a"
WHITE = "#f4f7fb"
MUTED = "#aab8cc"
CYAN = "#42c8f5"
GREEN = "#5cdda8"
ORANGE = "#ffb45c"
RED = "#ff6f7d"
BLUE = "#7da8ff"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


F_TITLE = font(43, True)
F_SUBTITLE = font(23)
F_SECTION = font(16, True)
F_CARD = font(21, True)
F_BODY = font(17)
F_SMALL = font(14)
F_STAT = font(36, True)
F_CAPTION = font(18, True)


def read_csv(path: Path):
    if not path.exists():
        raise RuntimeError(f"Missing evaluation output {path}; run `make all` first.")
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def read_manifest():
    path = ROOT / "data/attacks/DATASET_MANIFEST.json"
    if not path.exists():
        raise RuntimeError("Missing public dataset manifest; run `make data` first.")
    return json.loads(path.read_text(encoding="utf-8"))


def rounded(draw: ImageDraw.ImageDraw, box, fill, outline=None, radius=16, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_lines(draw, xy, text, f, fill, max_width, spacing=7):
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = f"{line} {word}".strip()
        if draw.textbbox((0, 0), test, font=f)[2] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    x, y = xy
    for row in lines:
        draw.text((x, y), row, font=f, fill=fill)
        y += f.size + spacing
    return y


def base(section: str, subtitle: str, index: int, caption: str):
    im = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(im)
    d.text((70, 30), section.upper(), font=F_SECTION, fill=CYAN)
    d.line((70, 62, WIDTH - 70, 62), fill="#26334a", width=2)
    d.text((70, 82), subtitle, font=F_TITLE, fill=WHITE)
    # Project identity and an understated progress indicator.
    d.text((WIDTH - 290, 35), "RAG POISON DEFENSE  /  PUBLIC DATA STUDY", font=F_SMALL, fill=MUTED)
    rounded(d, (70, 645, WIDTH - 70, 700), "#050912", radius=12)
    d.text((92, 660), caption, font=F_CAPTION, fill=WHITE)
    d.line((70, 627, WIDTH - 70, 627), fill="#26334a", width=2)
    d.line((70, 627, 70 + int((WIDTH - 140) * (index + 1) / 12), 627), fill=CYAN, width=3)
    return im, d


def card(d, box, title, body, accent=CYAN, body_size=F_BODY):
    rounded(d, box, PANEL, outline="#263852", radius=16, width=2)
    x1, y1, x2, _ = box
    d.rounded_rectangle((x1 + 18, y1 + 19, x1 + 24, y1 + 53), radius=3, fill=accent)
    d.text((x1 + 40, y1 + 17), title, font=F_CARD, fill=WHITE)
    text_lines(d, (x1 + 22, y1 + 63), body, body_size, MUTED, x2 - x1 - 44, spacing=6)


def pill(d, xy, label, color=CYAN):
    x, y = xy
    box = d.textbbox((0, 0), label, font=F_SMALL)
    w = box[2] + 28
    rounded(d, (x, y, x + w, y + 32), "#1b2b43", radius=15)
    d.text((x + 14, y + 7), label, font=F_SMALL, fill=color)
    return w


def draw_bar_chart(d, box, labels, values, colors, max_value=1.0, value_labels=None):
    x1, y1, x2, y2 = box
    chart_top, chart_bottom = y1 + 20, y2 - 50
    d.line((x1, chart_bottom, x2, chart_bottom), fill="#4a5c74", width=2)
    for tick in range(5):
        value = max_value * tick / 4
        y = chart_bottom - int((chart_bottom - chart_top) * tick / 4)
        d.line((x1, y, x2, y), fill="#24344a", width=1)
        d.text((x1 - 48, y - 9), f"{value:.0%}", font=F_SMALL, fill=MUTED)
    n = len(values)
    slot = (x2 - x1) / n
    bw = min(65, slot * 0.56)
    for i, value in enumerate(values):
        x = x1 + slot * (i + 0.5)
        top = chart_bottom - int((chart_bottom - chart_top) * value / max_value)
        d.rounded_rectangle((int(x - bw / 2), top, int(x + bw / 2), chart_bottom), radius=7, fill=colors[i])
        txt = value_labels[i] if value_labels else f"{value:.0%}"
        bb = d.textbbox((0, 0), txt, font=F_SMALL)
        d.text((x - (bb[2] - bb[0]) / 2, top - 25), txt, font=F_SMALL, fill=WHITE)
        bb = d.textbbox((0, 0), labels[i], font=F_SMALL)
        d.text((x - (bb[2] - bb[0]) / 2, chart_bottom + 13), labels[i], font=F_SMALL, fill=MUTED)


def make_slides():
    slides = []
    manifest = read_manifest()
    counts = manifest["counts"]
    proxy_rows = read_csv(ROOT / "results/tables/public_simulator_diagnostic.csv")
    scanner_rows = read_csv(ROOT / "results/tables/public_scanner_metrics.csv")
    cost_rows = read_csv(ROOT / "results/tables/public_false_positive_cost.csv")
    clean_utility_rows = read_csv(ROOT / "results/tables/public_clean_utility.csv")
    source_holdout_rows = read_csv(ROOT / "results/tables/public_source_holdout_metrics.csv")
    squad_qa_rows = read_csv(ROOT / "results/tables/public_squad_clean_qa.csv")
    retriever_rows = read_csv(ROOT / "results/tables/public_retriever_selection.csv")
    proxy_by_name = {row["defense"]: float(row["proxy_obedience_rate"]) for row in proxy_rows}
    scanner_by_name = {row["scanner"]: row for row in scanner_rows if row["record_type"] == "overall"}
    cost_by_name = {row["scanner"]: row for row in cost_rows}
    clean_utility_by_name = {row["policy"]: row for row in clean_utility_rows}
    squad_utility = next(row for row in squad_qa_rows if row["policy"] == "No screening")
    selected_retriever = next(row["embedder"] for row in retriever_rows if row["selected"] == "True")
    retriever_labels = {
        "hashing": "feature hashing",
        "tfidf": "word TF-IDF",
        "tfidf_char": "character TF-IDF",
        "bm25": "BM25",
        "hybrid": "hybrid BM25 + word TF-IDF",
    }

    im, d = base("Project overview", "Can retrieved documents hijack an AI answer?", 0,
                 "Public benchmark data. Real-document ingestion. Measured scanner and false-positive trade-offs.")
    d.text((72, 190), "RAG POISON DEFENSE", font=font(20, True), fill=CYAN)
    text_lines(d, (72, 235), "Testing how instructions hidden in public benchmark documents can alter a RAG assistant's response.", F_SUBTITLE, MUTED, 610)
    for i, (num, label, color) in enumerate([(str(len(manifest["dataset_sources"])), "public datasets", CYAN),
                                               (str(counts["attack_examples"]), "attack records", GREEN),
                                               (str(counts["wikipedia_clean"]), "Wikipedia articles", ORANGE)]):
        x = 760 + (i % 2) * 215
        y = 200 + (i // 2) * 150
        rounded(d, (x, y, x + 185, y + 115), PANEL, outline="#263852", radius=18, width=2)
        d.text((x + 20, y + 10), num, font=F_STAT, fill=color)
        d.text((x + 20, y + 69), label, font=F_SMALL, fill=MUTED)
    slides.append(im)

    im, d = base("The problem", "A quick look at retrieval-augmented generation", 1,
                 "RAG gives a model useful context—but retrieved content is not automatically trustworthy.")
    xs = [90, 365, 640, 915]
    nodes = [("Question", "What should the system answer?", BLUE), ("Retrieve", "Find relevant documents", CYAN),
             ("Context", "Mix trusted and untrusted text", ORANGE), ("Answer", "The model responds", GREEN)]
    for i, (title, body, color) in enumerate(nodes):
        rounded(d, (xs[i], 300, xs[i] + 215, 440), PANEL, outline=color, radius=18, width=2)
        d.text((xs[i] + 18, 325), title, font=F_CARD, fill=color)
        text_lines(d, (xs[i] + 18, 370), body, F_SMALL, MUTED, 180, 5)
        if i < 3:
            d.line((xs[i] + 222, 370, xs[i + 1] - 15, 370), fill="#5b6e88", width=3)
            d.polygon([(xs[i + 1] - 15, 370), (xs[i + 1] - 27, 362), (xs[i + 1] - 27, 378)], fill="#5b6e88")
    pill(d, (400, 490), "ATTACK SURFACE: DOCUMENT INGESTION", ORANGE)
    slides.append(im)

    im, d = base("Threat model", "An attacker-controlled document enters the RAG index", 2,
                 "The project uses benchmark-provided attack text; the pipeline treats it as inert document content.")
    card(d, (80, 235, 385, 460), "Poisoned context", "BIPIA provides real benchmark contexts with embedded indirect instructions.", RED)
    card(d, (488, 235, 793, 460), "User question", "BIPIA pairs poisoned context with the original benchmark question.", ORANGE)
    card(d, (896, 235, 1200, 460), "Safety boundary", "No attack text is executed. Tensor Trust access-code values are removed/redacted.", GREEN)
    slides.append(im)

    im, d = base("Study design", "A repeatable public-data evaluation", 3,
                 "The first run downloads the specified public datasets; evaluation and simulated inference run locally.")
    for i, (big, small, color) in enumerate([(f"{counts['wikipedia_clean']:,}", "real Wikipedia articles", CYAN),
                                            (f"{counts['attack_examples']:,}", "public attack records", RED),
                                            (f"{counts['benign_examples']:,}", "public benign records", ORANGE),
                                            (f"{counts['bipia_questions']:,}", "paired BIPIA questions", GREEN)]):
        x = 86 + (i % 2) * 560
        y = 230 + (i // 2) * 165
        rounded(d, (x, y, x + 500, y + 125), PANEL, outline="#263852", radius=18, width=2)
        d.text((x + 28, y + 18), big, font=F_STAT, fill=color)
        d.text((x + 230, y + 47), small, font=F_BODY, fill=MUTED)
    slides.append(im)

    im, d = base("Attack coverage", "Three public prompt-injection benchmarks", 4,
                 "Source-level counts are shown; each benchmark has different tasks and label conventions.")
    groups = [("deepset prompt-injections", f"{counts['attacks_by_source'].get('deepset', 0)} records · labeled attack / benign text", RED),
              ("BIPIA benchmark", f"{counts['attacks_by_source'].get('bipia', 0)} rows · poisoned contexts + paired questions", ORANGE),
              ("Tensor Trust", f"{counts['attacks_by_source'].get('tensor_trust', 0)} rows · human-authored prompt attacks", CYAN)]
    for i, (title, body, color) in enumerate(groups):
        y = 220 + i * 125
        card(d, (130, y, 1150, y + 98), title, body, color)
    slides.append(im)

    im, d = base("Defense design", "Layered defenses in the codebase", 5,
                 "The public benchmark measures D1/D2 scanner quality plus D3 provenance and D4 quarantine policy effects.")
    defenses = [("D1", "Explainable rules", CYAN), ("D2", "TF-IDF classifier", BLUE),
                ("D3", "Signed provenance", GREEN), ("D4", "Quarantine + review", ORANGE),
                ("D5", "Context hierarchy", CYAN), ("D6", "Output canary guard", RED)]
    for i, (tag, label, color) in enumerate(defenses):
        x = 92 + (i % 3) * 385
        y = 225 + (i // 3) * 165
        rounded(d, (x, y, x + 330, y + 115), PANEL, outline="#263852", radius=17, width=2)
        pill(d, (x + 20, y + 20), tag, color)
        text_lines(d, (x + 20, y + 67), label, F_BODY, WHITE, 290, 4)
    slides.append(im)

    im, d = base("Pipeline", "From public sources to measured result", 6,
                 "Fixed seeds and saved result tables make the evaluation inspectable and reproducible.")
    flow = [("Download", "Wikimedia + benchmarks", BLUE),
            ("Retrieve", f"{retriever_labels[selected_retriever]} retrieval", CYAN),
            ("Defend", "scan / quarantine / guard", GREEN), ("Measure", "retrieval + FPR + cost", ORANGE)]
    for i, (head, body, color) in enumerate(flow):
        x = 75 + i * 300
        rounded(d, (x, 285, x + 235, 430), PANEL, outline=color, radius=18, width=2)
        d.text((x + 20, 310), head, font=F_CARD, fill=color)
        text_lines(d, (x + 20, 365), body, F_SMALL, MUTED, 195, 5)
        if i < 3:
            d.line((x + 241, 355, x + 285, 355), fill="#5b6e88", width=3)
            d.polygon([(x + 285, 355), (x + 273, 347), (x + 273, 363)], fill="#5b6e88")
    pill(d, (412, 490), "SEED 42  ·  LOCAL EVALUATION  ·  REPRODUCIBLE", GREEN)
    slides.append(im)

    im, d = base("Simulator diagnostic", "Deterministic proxy behavior is not real-model ASR", 7,
                 "The simulator is programmed to emit benchmark payloads; this is a plumbing diagnostic, not attack success.")
    rounded(d, (105, 205, 1170, 555), PANEL, outline="#263852", radius=18, width=2)
    proxy_names = ["No screening", "D1 rules", "D2 TF-IDF", "D3 provenance", "D4 quarantine"]
    proxy_labels = ["None", "D1", "D2", "D3", "D4"]
    proxy_values = [proxy_by_name[name] for name in proxy_names]
    draw_bar_chart(d, (190, 270, 1080, 500), proxy_labels, proxy_values,
                   ["#8395a7", BLUE, GREEN, ORANGE, "#8854d0"],
                   max_value=max(0.05, max(proxy_values) * 1.35),
                   value_labels=[f"{value:.1%}" for value in proxy_values])
    d.text((200, 220), "Proxy obedience rate on held-out BIPIA questions", font=F_BODY, fill=MUTED)
    slides.append(im)

    im, d = base("Scanner quality", "Recall under a declared 5% dev-FPR ceiling", 8,
                 "Thresholds maximize validation recall subject to the FPR goal; test data remains held out.")
    rounded(d, (105, 205, 1170, 555), PANEL, outline="#263852", radius=18, width=2)
    d.text((200, 220), "Held-out test metrics", font=F_BODY, fill=MUTED)
    metric_fields = ["recall", "fpr"]
    colors = [GREEN, RED]
    slot = 335
    for i, name in enumerate(["D1_rules", "D2_TFIDF"]):
        x = 265 + i * 410
        d.text((x, 272), "Rule scanner" if i == 0 else "TF-IDF classifier", font=F_CARD, fill=WHITE)
        for j, field in enumerate(metric_fields):
            value = float(scanner_by_name[name][field])
            y = 330 + j * 75
            d.text((x, y), "Recall" if field == "recall" else "False-positive rate", font=F_SMALL, fill=MUTED)
            rounded(d, (x + 155, y, x + 155 + int(slot * value), y + 28), colors[j], radius=8)
            d.text((x + 165 + int(slot * value), y + 2), f"{value:.1%}", font=F_SMALL, fill=WHITE)
    slides.append(im)

    im, d = base("Operational trade-offs", "Detection is only part of the decision", 9,
                 "Held-out recall and benign false positives are reported together with confidence intervals.")
    m1, m2 = scanner_by_name["D1_rules"], scanner_by_name["D2_TFIDF"]
    card(d, (92, 245, 565, 475), "D1 · rule scanner",
         f"Recall {float(m1['recall']):.1%}; FPR {float(m1['fpr']):.1%}. Threshold chosen on dev data under the 5% FPR target.", GREEN)
    card(d, (715, 245, 1188, 475), "D2 · TF-IDF classifier",
         f"Recall {float(m2['recall']):.1%}; FPR {float(m2['fpr']):.1%}. Threshold chosen on dev data under the 5% FPR target.", ORANGE)
    d.line((600, 300, 600, 430), fill="#34445c", width=2)
    d.text((585, 300), "VS", font=F_CARD, fill=CYAN)
    slides.append(im)

    im, d = base("False-positive cost", "Review burden is part of defense effectiveness", 10,
                 "Scenario estimates vary review time, labor rate, and legitimate-document blocking loss.")
    c1, c2 = cost_by_name["D1_rules"], cost_by_name["D2_TFIDF"]
    card(d, (95, 230, 610, 490), "D1 · rule scanner",
         f"{float(c1['reviewer_hours_per_10k']):.1f} reviewer hours per 10k clean docs. Modeled cost: {float(c1['expected_cost_per_10k']):,.0f}.", RED)
    card(d, (670, 230, 1185, 490), "D2 · TF-IDF classifier",
         f"{float(c2['reviewer_hours_per_10k']):.1f} reviewer hours per 10k clean docs. Modeled cost: {float(c2['expected_cost_per_10k']):,.0f}.", GREEN)
    slides.append(im)

    im, d = base("Generalization and utility", "Check unseen sources and benign retrieval too", 11,
                 "Source-held-out scores test transfer; clean title queries measure retrieval and simulator extraction diagnostics.")
    clean_utility = clean_utility_by_name["No screening"]
    text_lines(d, (95, 220),
               f"Clean Wikipedia baseline: Recall@5 {float(clean_utility['recall_at_5']):.1%}; extractive token-F1 {float(clean_utility['answer_token_f1_mean']):.3f} (simulator diagnostic).",
               F_BODY, WHITE, 1070, 8)
    text_lines(d, (95, 258),
               f"Crowd-authored SQuAD: paired-context Recall@5 {float(squad_utility['context_recall_at_5']):.1%}; gold-answer evidence@5 {float(squad_utility['answer_evidence_at_5']):.1%}.",
               F_BODY, CYAN, 1070, 8)
    for i, source in enumerate(["bipia", "tensor_trust"]):
        rows = [row for row in source_holdout_rows if row["heldout_attack_source"] == source]
        detail = "  ·  ".join(
            f"{row['scanner']}: recall {float(row['recall']):.1%}, FPR {float(row['fpr']):.1%}"
            for row in rows
        )
        card(d, (100, 305 + i * 118, 1180, 395 + i * 118),
             f"Held-out attack source: {source}", detail, BLUE if i == 0 else ORANGE)
    d.text((105, 557), "SQuAD QA uses real gold answers; simulator EM/F1 is diagnostic only.", font=F_SMALL, fill=MUTED)
    slides.append(im)

    im, d = base("Takeaway", "Build layered defenses—and keep evaluating", 12,
                 "Explore the code, generated figures, CSV tables, and full effectiveness report in the repository.")
    d.text((90, 205), "RAG POISON DEFENSE", font=font(26, True), fill=CYAN)
    text_lines(d, (90, 270), "Use real public benchmarks. Scan untrusted documents. Preserve provenance. Quarantine uncertainty. Keep instructions separate from data.", F_SUBTITLE, WHITE, 630, 12)
    rounded(d, (850, 220, 1160, 450), PANEL, outline="#263852", radius=20, width=2)
    d.text((885, 260), "REPRODUCE", font=F_SECTION, fill=GREEN)
    d.text((885, 310), "python scripts/", font=font(21, True), fill=WHITE)
    d.text((885, 342), "run_public_pipeline.py", font=font(18, True), fill=WHITE)
    d.text((885, 390), "python -m pytest -q", font=font(20, True), fill=CYAN)
    d.text((90, 515), "Public data · no synthetic fallback · transparent limitations", font=F_BODY, fill=MUTED)
    slides.append(im)
    return slides


def main():
    slides = make_slides()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(OUTPUT), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (WIDTH, HEIGHT))
    if not writer.isOpened():
        raise RuntimeError("Could not initialize MP4 video writer (mp4v).")
    for slide in slides:
        array = np.asarray(slide)
        bgr = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
        for local in range(SECONDS_PER_SLIDE * FPS):
            # Tiny push-in movement gives static slides a subtle presentation feel.
            progress = local / max(1, SECONDS_PER_SLIDE * FPS - 1)
            scale = 1.0 + 0.008 * progress
            nw, nh = int(WIDTH * scale), int(HEIGHT * scale)
            enlarged = cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_LINEAR)
            ox, oy = (nw - WIDTH) // 2, (nh - HEIGHT) // 2
            frame = enlarged[oy:oy + HEIGHT, ox:ox + WIDTH]
            writer.write(frame)
    writer.release()
    print(f"Created {OUTPUT} ({len(slides) * SECONDS_PER_SLIDE}s, {WIDTH}x{HEIGHT}, silent captions).")


if __name__ == "__main__":
    main()
