import pandas as pd
import pingouin as pg
from factor_analyzer.factor_analyzer import calculate_kmo, calculate_bartlett_sphericity
from fpdf import FPDF
import warnings
import json
import re
import os

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="factor_analyzer.utils")
warnings.filterwarnings("ignore", category=FutureWarning)

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Statistical Analysis Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, body)
        self.ln(5)

    def add_table(self, data, col_widths):
        self.set_font('Arial', '', 9)
        # Use simple table format
        for row in data:
            for item, width in zip(row, col_widths):
                # Clean up unicode issues
                text = str(item).encode('latin-1', 'replace').decode('latin-1')
                self.cell(width, 8, text, border=1)
            self.ln()
        self.ln(5)

    def add_wrap_table(self, data, col_widths):
        # A bit more complex to handle word wrap
        self.set_font('Arial', '', 9)
        for row in data:
            max_lines = 1
            # Calculate height needed
            for i, item in enumerate(row):
                text = str(item).encode('latin-1', 'replace').decode('latin-1')
                lines = len(self.multi_cell(col_widths[i], 6, text, border=0, split_only=True))
                if lines > max_lines:
                    max_lines = lines
            h = max_lines * 6

            # Print row
            x = self.get_x()
            y = self.get_y()
            for i, item in enumerate(row):
                text = str(item).encode('latin-1', 'replace').decode('latin-1')
                self.multi_cell(col_widths[i], 6, text, border=1)
                self.set_xy(x + sum(col_widths[:i+1]), y)
            self.ln(h)

            # Page break if needed
            if self.get_y() > 260:
                self.add_page()
        self.ln(5)

def extract_meta():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "questionnaire.html")
    with open(file_path, "r", encoding='utf-8') as f:
        html_content = f.read()

    questions = {}
    matches = re.findall(r'\{id:"([^"]+)",\s*text:"([^"]+)"\}', html_content)
    for m in matches:
        questions[m[0]] = m[1].replace('’', "'")

    scale_dict = {}
    parts = re.split(r'"Part \d+: ', html_content)
    for p in parts[1:]:
        title = "Part " + p.split('"', 1)[0]
        scale_match = re.search(r'scale:\[(.*?)\]', p)
        if scale_match:
            scale_raw = scale_match.group(1)
            scale_items = [s.strip('"') for s in scale_raw.split('","')]
            scale_items = [s.replace('"', '') for s in scale_items]
            scale_dict[title] = scale_items

    mapping_dict = {}
    sections = re.findall(r'"(\d[A-E]\.[^"]+)"\s*:\s*\[(.*?)\]', html_content, re.DOTALL)
    for sec_title, sec_content in sections:
        ids = re.findall(r'id:"([^"]+)"', sec_content)
        mapping_dict[sec_title] = ids

    return questions, scale_dict, mapping_dict

def analyze_reliability_validity(df, cols):
    data = df[cols].dropna()
    data = data.apply(pd.to_numeric, errors='coerce').dropna()

    alpha, ci = pg.cronbach_alpha(data=data)
    try:
        kmo_all, kmo_model = calculate_kmo(data)
        chi_square, p_value = calculate_bartlett_sphericity(data)
    except Exception as e:
        kmo_model, chi_square, p_value = 0, 0, 1

    return alpha, ci, kmo_model, chi_square, p_value

def calculate_stats(df, questions, scale, mapping):
    results = {}

    for sec_title, ids in mapping.items():
        results[sec_title] = []
        for q_id in ids:
            if q_id not in df.columns:
                continue

            col_data = pd.to_numeric(df[q_id], errors='coerce').dropna()
            if len(col_data) == 0:
                continue

            mean = col_data.mean()
            sd = col_data.std()

            # Count distribution
            counts = col_data.value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
            percents = (counts / len(col_data)) * 100

            q_text = questions.get(q_id, q_id)

            dist_str = " | ".join([f"{int(c)} ({p:.1f}%)" for c, p in zip(counts.values, percents.values)])

            results[sec_title].append({
                "id": q_id,
                "text": q_text,
                "mean": f"{mean:.2f}",
                "sd": f"{sd:.2f}",
                "dist": dist_str
            })

    return results

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "cleaned_dataset.csv")
    df = pd.read_csv(file_path)
    questions, scales, mapping = extract_meta()

    pdf = PDFReport()
    pdf.add_page()

    # 1. Demographics
    pdf.chapter_title("1. Demographic Profile")
    demographics = ["Role", "YearsOfExperience", "FamiliarityWithBIM", "CurrentBIMUsage", "OrganizationType", "Age", "Gender"]
    for demo in demographics:
        if demo in df.columns:
            counts = df[demo].value_counts()
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 6, f"Distribution of {demo}:", 0, 1)
            pdf.set_font('Arial', '', 10)

            table_data = [["Category", "Count", "Percentage"]]
            total = len(df[demo].dropna())
            for idx, count in counts.items():
                pct = (count / total) * 100
                table_data.append([str(idx), str(count), f"{pct:.1f}%"])

            pdf.add_table(table_data, [100, 40, 40])

    pdf.add_page()

    # 2. Validity and Reliability
    pdf.chapter_title("2. Validity and Reliability Analysis")

    sections_meta = [
        ("Advantages", [c for c in df.columns if c.startswith('adv_')]),
        ("Challenges", [c for c in df.columns if c.startswith('chal_')]),
        ("Strategies", [c for c in df.columns if c.startswith('strat_')])
    ]

    val_table = [["Construct", "Items", "Cronbach's Alpha", "KMO", "Bartlett's p-value"]]
    for name, cols in sections_meta:
        if cols:
            alpha, ci, kmo, chi, pval = analyze_reliability_validity(df, cols)
            val_table.append([name, str(len(cols)), f"{alpha:.3f}", f"{kmo:.3f}", f"{pval:.3e}"])

    pdf.add_table(val_table, [40, 30, 40, 40, 40])

    pdf.chapter_body(
        "Interpretation:\n"
        "- Cronbach's Alpha > 0.7 indicates acceptable to excellent internal consistency.\n"
        "- KMO > 0.6 indicates adequate sampling for factor analysis.\n"
        "- Bartlett's p-value < 0.05 indicates variables are significantly correlated."
    )

    pdf.add_page()

    # 3. Descriptive Statistics
    pdf.chapter_title("3. Descriptive Statistics & Tabulation")

    stats_results = calculate_stats(df, questions, scales, mapping)

    for sec_title, items in stats_results.items():
        if not items:
            continue

        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, str(sec_title.encode('latin-1', 'replace').decode('latin-1')), 0, 1)

        pdf.set_font('Arial', 'B', 8)
        header = ["Item", "Mean", "SD", "Dist. (1 to 5)"]
        col_widths = [110, 15, 15, 50]

        pdf.cell(col_widths[0], 6, header[0], 1)
        pdf.cell(col_widths[1], 6, header[1], 1)
        pdf.cell(col_widths[2], 6, header[2], 1)
        pdf.cell(col_widths[3], 6, header[3], 1)
        pdf.ln()

        pdf.set_font('Arial', '', 8)
        for item in items:
            text = str(item['text']).encode('latin-1', 'replace').decode('latin-1')

            # Calculate height for wrapping text
            lines = len(pdf.multi_cell(col_widths[0], 5, text, border=0, split_only=True))
            h = lines * 5

            if pdf.get_y() + h > 270:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 8)
                pdf.cell(col_widths[0], 6, header[0], 1)
                pdf.cell(col_widths[1], 6, header[1], 1)
                pdf.cell(col_widths[2], 6, header[2], 1)
                pdf.cell(col_widths[3], 6, header[3], 1)
                pdf.ln()
                pdf.set_font('Arial', '', 8)

            x = pdf.get_x()
            y = pdf.get_y()

            pdf.multi_cell(col_widths[0], 5, text, 1)

            # Position for next cells
            pdf.set_xy(x + col_widths[0], y)
            pdf.cell(col_widths[1], h, item['mean'], 1, 0, 'C')
            pdf.cell(col_widths[2], h, item['sd'], 1, 0, 'C')

            # Custom wrapping for distribution cell
            pdf.set_xy(x + col_widths[0] + col_widths[1] + col_widths[2], y)
            dist_text = item['dist']
            pdf.multi_cell(col_widths[3], h, dist_text, 1, 'C')

            pdf.set_xy(x, y + h)

        pdf.ln(5)

    output_filename = os.path.join(base_dir, "reports", "Statistical_Analysis_Report.pdf")
    pdf.output(output_filename)
    print("Statistical_Analysis_Report.pdf generated successfully.")

if __name__ == "__main__":
    main()
