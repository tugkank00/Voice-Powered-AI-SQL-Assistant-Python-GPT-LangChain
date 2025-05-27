from io import BytesIO
from typing import Protocol
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus.tables import TableStyle
from datetime import datetime
import logging

from app.exceptions.domain import ReportGenerationException
from app.services.base.protocols import ReportGeneratorProtocol

class PDFReportService(ReportGeneratorProtocol):
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.logger = logging.getLogger(__name__)

    def _create_styles(self):
        styles = {
            "title": ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1,
                textColor=colors.HexColor('#2563eb')
            ),
            "timestamp": ParagraphStyle(
                'Timestamp',
                parent=self.styles['Normal'],
                fontSize=10,
                alignment=1,
                textColor=colors.grey
            ),
            "heading2": ParagraphStyle(
                'Heading2Style',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceAfter=10,
                textColor=colors.HexColor('#1f2937')
            ),
            "sql_code": ParagraphStyle(
                'SQLCode',
                parent=self.styles['Code'],
                fontSize=9,
                fontName='Courier',
                backgroundColor=colors.HexColor('#f8f9fa'),
                borderColor=colors.HexColor('#e9ecef'),
                borderWidth=1,
                leftIndent=10,
                rightIndent=10,
                spaceBefore=5,
                spaceAfter=5
            ),
            "summary": ParagraphStyle(
                'Summary',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.grey
            ),
        }
        return styles

    def _add_title_and_timestamp(self, elements, styles):
        elements.append(Paragraph("AI SQL Assistant Report", styles["title"]))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"Generated on: {timestamp}", styles["timestamp"]))
        elements.append(Spacer(1, 20))

    def _add_question(self, elements, styles, query_result):
        if query_result.question:
            elements.append(Paragraph("Question:", styles["heading2"]))
            elements.append(Paragraph(query_result.question, self.styles['Normal']))
            elements.append(Spacer(1, 15))

    def _add_sql(self, elements, styles, query_result):
        if query_result.sql:
            elements.append(Paragraph("Generated SQL:", styles["heading2"]))
            elements.append(Paragraph(query_result.sql, styles["sql_code"]))
            elements.append(Spacer(1, 20))

    def _format_table_data(self, query_result, max_rows=50):
        table_data = [query_result.headers]
        rows_to_show = query_result.rows[:max_rows]
        for row in rows_to_show:
            formatted_row = [
                "" if value is None else (str(value)[:47] + "..." if len(str(value)) > 50 else str(value))
                for value in row
            ]
            table_data.append(formatted_row)
        return table_data

    def _create_table(self, table_data):
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        return table

    def _add_results(self, elements, styles, query_result):
        if query_result.headers and query_result.rows:
            elements.append(Paragraph("Query Results:", styles["heading2"]))
            table_data = self._format_table_data(query_result)
            table = self._create_table(table_data)
            elements.append(table)
            
            elements.append(Spacer(1, 20))
            total_rows = len(query_result.rows)
            summary_text = f"Total records: {total_rows}"
            if total_rows > 50:
                summary_text += " (showing first 50 rows)"
            if query_result.execution_time_ms:
                summary_text += f" | Execution time: {query_result.execution_time_ms}ms"
            elements.append(Paragraph(summary_text, styles["summary"]))
        else:
            elements.append(Paragraph("No results to display", self.styles['Normal']))

    def generate_pdf(self, query_result):
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    rightMargin=72, leftMargin=72,
                                    topMargin=72, bottomMargin=18)
            elements = []
            
            styles = self._create_styles()  
            self._add_title_and_timestamp(elements, styles)
            self._add_question(elements, styles, query_result)
            self._add_sql(elements, styles, query_result)
            self._add_results(elements, styles, query_result)
            
            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            self.logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            self.logger.error(f"PDF generation error: {e}", exc_info=True)
            raise ReportGenerationException(
                report_type="PDF",
                original_exception=e,
                details={
                    "error_type": type(e).__name__,
                    "has_data": bool(query_result.rows if hasattr(query_result, 'rows') else False)
                }
            )
