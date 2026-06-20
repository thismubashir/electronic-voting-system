"""
utils/pdf_export.py
Export election results and voter lists to PDF using reportlab.
"""
from __future__ import annotations
from datetime import datetime


def export_results_pdf(results: list, election_type: str, output_path: str) -> bool:
    """
    Generate a PDF report of election results.
    Returns True on success, False on failure.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph,
            Spacer, HRFlowable
        )
        from reportlab.lib.units import cm

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "EVSTitle",
            parent=styles["Title"],
            fontSize=18,
            textColor=colors.HexColor("#01411C"),
            spaceAfter=6,
        )
        sub_style = ParagraphStyle(
            "EVSSub",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#555555"),
            spaceAfter=12,
        )

        elements = []

        # Header
        elements.append(Paragraph(
            "Islamic Republic of Pakistan", title_style))
        elements.append(Paragraph(
            f"Election Commission — {election_type.title()} Assembly Results",
            sub_style))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            sub_style))
        elements.append(HRFlowable(width="100%", thickness=2,
                                    color=colors.HexColor("#01411C")))
        elements.append(Spacer(1, 0.5*cm))

        if not results:
            elements.append(Paragraph("No results available.", styles["Normal"]))
        else:
            # Table data
            headers = ["#", "Candidate", "Party", "Constituency", "Votes", "%"]
            total = sum(r["vote_count"] for r in results)

            data = [headers]
            for i, r in enumerate(results, 1):
                pct = f"{round(r['vote_count']/total*100,1)}%" if total else "0%"
                data.append([
                    str(i),
                    r["candidate_name"],
                    r["party_name"],
                    r["constituency_name"],
                    str(r["vote_count"]),
                    pct,
                ])

            col_widths = [1*cm, 5*cm, 5*cm, 3.5*cm, 1.8*cm, 1.5*cm]
            table = Table(data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#01411C")),
                ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
                ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,0), 10),
                ("ALIGN",       (0,0), (-1,-1), "CENTER"),
                ("ALIGN",       (1,1), (3,-1), "LEFT"),
                ("ROWBACKGROUNDS", (0,1), (-1,-1),
                 [colors.HexColor("#F8FFF8"), colors.white]),
                ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
                ("FONTSIZE",    (0,1), (-1,-1), 9),
                ("TOPPADDING",  (0,0), (-1,-1), 5),
                ("BOTTOMPADDING",(0,0), (-1,-1), 5),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(
                f"Total Votes Cast: {total}", styles["Normal"]))

        doc.build(elements)
        return True

    except ImportError:
        print("[PDF] reportlab not installed. Run: pip install reportlab")
        return False
    except Exception as e:
        print(f"[PDF] Export failed: {e}")
        return False


def export_voters_pdf(voters: list, output_path: str) -> bool:
    """Generate a PDF list of voters."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle,
            Paragraph, Spacer, HRFlowable
        )
        from reportlab.lib.units import cm

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=1.5*cm, leftMargin=1.5*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Voter Registration List", styles["Title"]))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            styles["Normal"]))
        elements.append(HRFlowable(width="100%", thickness=1,
                                    color=colors.HexColor("#333333")))
        elements.append(Spacer(1, 0.4*cm))

        headers = ["#", "CNIC", "Name", "City", "NA", "PP", "Status"]
        data = [headers]
        for i, v in enumerate(voters, 1):
            data.append([
                str(i),
                v.get("cnic",""),
                v.get("full_name",""),
                v.get("city",""),
                v.get("na_name",""),
                v.get("pp_name",""),
                v.get("status","").title(),
            ])

        col_widths = [0.8*cm, 3.8*cm, 3.5*cm, 2.5*cm, 2*cm, 2*cm, 2*cm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#1F3A6E")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1),
             [colors.HexColor("#F0F4FF"), colors.white]),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ]))
        elements.append(table)
        doc.build(elements)
        return True

    except Exception as e:
        print(f"[PDF] Export failed: {e}")
        return False
