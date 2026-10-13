"""Build the final three-page PDF report from the corpus and tokenizer results."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
from matplotlib.lines import Line2D

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"


def read_csv(name: str) -> list[dict[str, str]]:
    with (REPORT / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def new_page(pdf: PdfPages, title: str, subtitle: str):
    fig = plt.figure(figsize=(8.27, 11.69), facecolor="white")
    fig.text(0.08, 0.955, title, fontsize=21, weight="bold", color="#17324d")
    fig.text(0.08, 0.925, subtitle, fontsize=9, color="#526579")
    fig.add_artist(Line2D([0.08, 0.92], [0.905, 0.905], transform=fig.transFigure, color="#1d7891", linewidth=1.4))
    return fig


def add_table(fig, data, columns, bbox, font_size=8, col_widths=None):
    ax = fig.add_axes(bbox)
    ax.axis("off")
    table = ax.table(
        cellText=data, colLabels=columns, cellLoc="left", colLoc="left", loc="center", colWidths=col_widths
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, 1.35)
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor("#d8e0e8")
        if row == 0:
            cell.set_facecolor("#17324d")
            cell.set_text_props(color="white", weight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f1f5f8")
    return ax


def build_q1(pdf: PdfPages) -> None:
    stats = json.loads((ROOT / "corpus" / "stats.json").read_text(encoding="utf-8"))
    source_rows = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    fig = new_page(pdf, "Urdu BPE Tokenizer — Final Report", "Q1 | Member A — Corpus collection, cleaning, and preparation")

    totals = stats["_totals"]
    fig.text(
        0.08, 0.865,
        f"Corpus: {sum(stats[n]['final_bytes'] for n in stats if n != '_totals') / 1e6:,.2f} MB cleaned | "
        f"{sum(stats[n]['final_docs'] for n in stats if n != '_totals'):,} documents | "
        f"{totals['unique_words']:,} unique words",
        fontsize=11, weight="bold", color="#1d7891",
    )
    fig.text(
        0.08, 0.825,
        "Member A's Q1 work assembled a multi-source Urdu corpus and produced document-level 98/1/1 "
        "train/validation/test splits (seed 42). The final split contains 1,094.72 MB of UTF-8 text.",
        fontsize=9, wrap=True, color="#263746",
    )

    source_data = []
    for source in source_rows:
        row = stats[source["name"]]
        source_data.append([
            source["name"].replace("_", " "),
            source["genre"].replace("mixed (news, religion, blogs, literature, science, education)", "mixed (multiple domains)"),
            f"{row['final_bytes'] / 1e6:,.2f}",
            f"{row['final_docs']:,}",
        ])
    fig.text(0.08, 0.77, "Source composition", fontsize=12, weight="bold", color="#17324d")
    add_table(
        fig, source_data, ["Source", "Genre", "Cleaned MB", "Documents"],
        [0.08, 0.57, 0.84, 0.18], 7.5, [0.25, 0.39, 0.17, 0.19],
    )
    fig.text(0.08, 0.545, "Self-collected by scraping: 51.02 MB raw / 50.36 MB cleaned across three news sources.", fontsize=8.5)

    fig.text(0.08, 0.505, "Cleaning and split", fontsize=12, weight="bold", color="#17324d")
    fig.text(
        0.08, 0.475,
        "Extract article text and remove URLs/emails; apply Urdu Unicode normalization; filter lines below "
        "50% Urdu-script letters and documents under 100 characters; exact-deduplicate; remove recurring "
        "short boilerplate; split by document and append <|endoftext|>.",
        fontsize=9, wrap=True, color="#263746",
    )
    fig.text(
        0.08, 0.39,
        "Normalization maps Arabic variants to Urdu forms, removes inconsistent harakat/tatweel and "
        "invisible controls, maps Arabic-Indic digits to ASCII, and removes ZWNJ. These choices reduce "
        "spelling fragmentation but mean raw, marked text is outside the training distribution.",
        fontsize=9, wrap=True, color="#263746",
    )
    fig.text(0.08, 0.30, "Q1 evidence and limitations", fontsize=12, weight="bold", color="#17324d")
    fig.text(
        0.08, 0.27,
        "The source register and corpus data card retain unresolved publisher-terms and collection-date "
        "fields for some scraped sources. The raw crawl-evidence directories are not present in this "
        "workspace. These fields/evidence should be completed and checked before redistribution; this "
        "report does not infer missing licence permissions.",
        fontsize=9, wrap=True, color="#263746",
    )
    fig.text(0.08, 0.08, "Source: corpus/DATA_CARD.md, corpus/stats.json, and sources.json.", fontsize=8, color="#526579")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def build_q2(pdf: PdfPages) -> None:
    aggregate = read_csv("q2_test.csv")[0]
    hand = read_csv("q2_hand.csv")
    fig = new_page(pdf, "Q2 | Comparison with GPT-2 and o200k_base", "All 3,093 documents in corpus/test.txt; whitespace-separated words are the denominator")
    fig.text(
        0.08, 0.86,
        f"{int(aggregate['words']):,} words | {int(aggregate['bytes']):,} UTF-8 bytes | "
        f"{aggregate['ours_tpw']} ours vs {aggregate['gpt2_tpw']} GPT-2 vs "
        f"{aggregate['o200k_base_tpw']} o200k_base tokens/word",
        fontsize=10, weight="bold", color="#17324d",
    )
    pct = (1 - float(aggregate["ours_tpw"]) / float(aggregate["o200k_base_tpw"])) * 100
    fig.text(
        0.08, 0.825,
        f"On this test split, ours uses {pct:.1f}% fewer tokens per word than o200k_base and "
        f"{(1 - float(aggregate['ours_tpw']) / float(aggregate['gpt2_tpw'])) * 100:.1f}% fewer than GPT-2. "
        f"Bytes/token: {aggregate['ours_bytes_per_token']} ours, {aggregate['gpt2_bytes_per_token']} GPT-2, "
        f"{aggregate['o200k_base_bytes_per_token']} o200k_base.",
        fontsize=9, color="#263746",
    )

    names = [row["input"] for row in hand]
    positions = list(range(len(hand)))
    width = 0.24
    ax = fig.add_axes([0.1, 0.46, 0.82, 0.30])
    for offset, (key, label, color) in enumerate((
        ("ours_tpw", "ours", "#1d7891"),
        ("gpt2_tpw", "GPT-2", "#e39c37"),
        ("o200k_base_tpw", "o200k_base", "#6d8f66"),
    )):
        ax.bar([p + (offset - 1) * width for p in positions], [float(r[key]) for r in hand], width, label=label, color=color)
    ax.set_xticks(positions)
    ax.set_xticklabels([r["input"] for r in hand], rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("tokens per word")
    ax.set_title("Hand-picked Urdu and mixed-script inputs", loc="left", fontsize=10, color="#17324d")
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False, ncol=3, fontsize=8)

    fig.text(0.08, 0.405, "Hand-input results", fontsize=11, weight="bold", color="#17324d")
    display = []
    for row in hand:
        display.append([
            row["input"],
            row["form"],
            row["ours_tpw"],
            row["gpt2_tpw"],
            row["o200k_base_tpw"],
        ])
    add_table(fig, display, ["Input", "Form", "Ours", "GPT-2", "o200k_base"], [0.08, 0.08, 0.84, 0.30], 7.5)
    fig.text(0.08, 0.045, "Tokenizer comparison uses tiktoken only for GPT-2/o200k_base; our tokenizer uses the trained 50k vocabulary.", fontsize=7.5, color="#526579")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def build_q3(pdf: PdfPages) -> None:
    hand = read_csv("q2_hand.csv")
    stats = {row["input"]: row for row in hand}
    fig = new_page(pdf, "Q3 | Three tokenizer failure cases", "Failure cases are measured on the same hand-picked inputs from report/hand_inputs.json")
    cases = [
        (
            "1. Roman Urdu (Latin-script Urdu)",
            stats["roman_urdu"],
            "Ours needs 45 tokens for 19 whitespace words (2.368 tokens/word), versus 36 for GPT-2 "
            "and 26 for o200k_base. Latin spelling variants are poorly represented in a predominantly "
            "Urdu-script training corpus.",
            "Mitigation: add licensed Roman Urdu/code-switch data or normalize/transliterate it consistently.",
        ),
        (
            "2. Raw Urdu with diacritics",
            stats["diacritics (raw)"],
            "The raw marked sample takes 71 tokens / 14 words (5.071 tokens/word). The normalized form "
            "takes 16 / 14 (1.143 tokens/word). This is expected from the preprocessing policy, but raw "
            "inputs incur severe fragmentation.",
            "Mitigation: apply the documented normalizer at inference, or retrain with marked-text coverage.",
        ),
        (
            "3. Urdu-English code-switching",
            stats["urdu_english"],
            "Ours takes 37 tokens / 24 words (1.542 tokens/word), compared with 26 for o200k_base. "
            "English words fragment (for example, laptop becomes l | ap | top and Python becomes "
            "P | yth | on), even though ours remains much better than GPT-2 on this sample.",
            "Mitigation: include representative code-switch and English technical vocabulary in training.",
        ),
    ]
    section_positions = (0.855, 0.635, 0.415)
    for (heading, row, evidence, mitigation), y in zip(cases, section_positions):
        fig.text(0.08, y, heading, fontsize=12, weight="bold", color="#17324d")
        fig.text(0.10, y - 0.035, evidence, fontsize=8.5, color="#263746", wrap=True)
        fig.text(0.10, y - 0.115, mitigation, fontsize=8, color="#1d7891", wrap=True)
        fig.text(
            0.10, y - 0.16,
            f"Measured ours/GPT-2/o200k_base: {row['ours_tpw']} / {row['gpt2_tpw']} / {row['o200k_base_tpw']} tokens per word.",
            fontsize=7.5, color="#526579",
        )

    fig.text(0.08, 0.18, "Interpretation", fontsize=12, weight="bold", color="#17324d")
    fig.text(
        0.08, 0.145,
        "These are targeted stress cases, not estimates of prevalence in test.txt. The held-out test "
        "average remains 1.170 tokens/word. Results depend on normalization: the raw diacritics row is "
        "intentionally scored without normalization while the standard corpus is normalized.",
        fontsize=9, color="#263746", wrap=True,
    )
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    with PdfPages(REPORT / "report.pdf") as pdf:
        build_q1(pdf)
        build_q2(pdf)
        build_q3(pdf)
    print(f"Wrote {REPORT / 'report.pdf'}")


if __name__ == "__main__":
    main()
