"""
Gerador de Relatórios PDF - LexScan IA
Cria relatórios profissionais de documentos e prazos
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from typing import Dict, List
from datetime import datetime
import os

class PDFReportGenerator:
    """Gera relatórios PDF profissionais"""
    
    def __init__(self):
        self.colors = {
            'primary': colors.HexColor('#1e3a5f'),
            'secondary': colors.HexColor('#c9a227'),
            'accent': colors.HexColor('#10b981'),
            'danger': colors.HexColor('#ef4444'),
            'dark': colors.HexColor('#0f172a'),
            'light': colors.HexColor('#f8fafc'),
            'gray': colors.HexColor('#64748b'),
            'white': colors.white,
            'black': colors.black
        }
        
        self.styles = self._create_styles()
    
    def _create_styles(self):
        """Cria estilos personalizados para o PDF"""
        styles = getSampleStyleSheet()
        
        # Título principal
        styles.add(ParagraphStyle(
            name='LexScanTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.colors['primary'],
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo
        styles.add(ParagraphStyle(
            name='LexScanSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=self.colors['secondary'],
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Cabeçalho de seção
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=self.colors['primary'],
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        # Texto normal
        styles.add(ParagraphStyle(
            name='NormalText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.colors['dark'],
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        # Texto de label
        styles.add(ParagraphStyle(
            name='LabelText',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.colors['gray'],
            spaceAfter=2
        ))
        
        # Texto de valor
        styles.add(ParagraphStyle(
            name='ValueText',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.colors['dark'],
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Alerta
        styles.add(ParagraphStyle(
            name='AlertText',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.colors['danger'],
            fontName='Helvetica-Bold'
        ))
        
        # Rodapé
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=self.colors['gray'],
            alignment=TA_CENTER
        ))
        
        return styles
    
    def generate_document_report(self, document: Dict) -> BytesIO:
        """
        Gera relatório PDF de um documento específico
        
        Args:
            document: Dicionário com dados do documento
            
        Returns:
            BytesIO com o PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Cabeçalho
        story.append(Paragraph("⚖️ LexScan IA", self.styles['LexScanTitle']))
        story.append(Paragraph("Relatório de Análise Documental", self.styles['LexScanSubtitle']))
        story.append(Spacer(1, 20))
        
        # Data do relatório
        story.append(Paragraph(
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles['LabelText']
        ))
        story.append(Spacer(1, 20))
        
        # Informações do documento
        story.append(Paragraph("📄 Informações do Documento", self.styles['SectionHeader']))
        
        doc_info = [
            ['Campo', 'Valor'],
            ['Nome do Arquivo', document.get('filename', 'N/A')],
            ['Tipo', document.get('type', 'N/A').replace('_', ' ').title()],
            ['Nº Processo', document.get('process_number', 'N/A')],
            ['Data de Upload', document.get('uploaded_at', 'N/A')[:10] if document.get('uploaded_at') else 'N/A'],
            ['Status', document.get('status', 'N/A').title()],
        ]
        
        doc_table = Table(doc_info, colWidths=[4*cm, 12*cm])
        doc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors['white']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), self.colors['light']),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['gray']),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        story.append(doc_table)
        story.append(Spacer(1, 20))
        
        # Partes do processo
        parties = document.get('parties', {})
        if parties:
            story.append(Paragraph("👥 Partes do Processo", self.styles['SectionHeader']))
            
            parties_data = [['Papel', 'Nome']]
            for role, name in parties.items():
                parties_data.append([
                    role.replace('_', ' ').title(),
                    name[:60] if name else 'N/A'
                ])
            
            parties_table = Table(parties_data, colWidths=[4*cm, 12*cm])
            parties_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['secondary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.colors['white']),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), self.colors['light']),
                ('GRID', (0, 0), (-1, -1), 1, self.colors['gray']),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            
            story.append(parties_table)
            story.append(Spacer(1, 20))
        
        # Prazos
        deadlines = document.get('deadlines', [])
        if deadlines:
            story.append(Paragraph("⏰ Prazos Identificados", self.styles['SectionHeader']))
            
            for i, dl in enumerate(deadlines[:10], 1):  # Limitar a 10 prazos
                urgency = dl.get('urgency', 'medium')
                urgency_color = self.colors['danger'] if urgency == 'high' else self.colors['secondary'] if urgency == 'medium' else self.colors['accent']
                
                deadline_text = f"""
                <b>Prazo {i}:</b> {dl.get('days', 'N/A')} dias<br/>
                <b>Urgência:</b> <font color="#{urgency_color.hexval()[2:]}">{urgency.upper()}</font><br/>
                <b>Contexto:</b> {dl.get('context', 'N/A')[:200]}
                """
                story.append(Paragraph(deadline_text, self.styles['NormalText']))
                story.append(Spacer(1, 10))
        
        # Resumo/Análise
        story.append(PageBreak())
        story.append(Paragraph("📝 Análise e Resumo", self.styles['SectionHeader']))
        
        summary = document.get('summary', '')
        if summary:
            story.append(Paragraph(summary, self.styles['NormalText']))
        else:
            story.append(Paragraph("Nenhum resumo disponível.", self.styles['NormalText']))
        
        story.append(Spacer(1, 20))
        
        # Análise completa
        analysis = document.get('analysis', '')
        if analysis:
            story.append(Paragraph("📊 Análise Detalhada", self.styles['SectionHeader']))
            story.append(Paragraph(analysis[:2000], self.styles['NormalText']))  # Limitar tamanho
        
        # Rodapé
        story.append(Spacer(1, 40))
        story.append(Paragraph(
            "⚖️ LexScan IA - Automação Documental Jurídica | www.lexscan.ai",
            self.styles['Footer']
        ))
        story.append(Paragraph(
            f"Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['Footer']
        ))
        
        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def generate_dashboard_report(self, stats: Dict, documents: List[Dict], deadlines: List[Dict]) -> BytesIO:
        """
        Gera relatório geral do dashboard
        
        Args:
            stats: Estatísticas do dashboard
            documents: Lista de documentos
            deadlines: Lista de prazos
            
        Returns:
            BytesIO com o PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Cabeçalho
        story.append(Paragraph("⚖️ LexScan IA", self.styles['LexScanTitle']))
        story.append(Paragraph("Relatório Geral do Dashboard", self.styles['LexScanSubtitle']))
        story.append(Spacer(1, 20))
        
        # Data
        story.append(Paragraph(
            f"Período: {datetime.now().strftime('%B/%Y')}",
            self.styles['LabelText']
        ))
        story.append(Spacer(1, 30))
        
        # Estatísticas
        story.append(Paragraph("📊 Estatísticas Gerais", self.styles['SectionHeader']))
        
        stats_data = [
            ['Métrica', 'Valor'],
            ['Total de Documentos', str(stats.get('total_documents', 0))],
            ['Total de Prazos', str(stats.get('total_deadlines', 0))],
            ['Prazos Urgentes', str(stats.get('urgent_deadlines', 0))],
        ]
        
        # Tipos de documentos
        doc_types = stats.get('document_types', {})
        for doc_type, count in doc_types.items():
            stats_data.append([
                f"Tipo: {doc_type.replace('_', ' ').title()}",
                str(count)
            ])
        
        stats_table = Table(stats_data, colWidths=[8*cm, 8*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors['white']),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), self.colors['light']),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['gray']),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 30))
        
        # Lista de documentos
        if documents:
            story.append(Paragraph("📄 Documentos Processados", self.styles['SectionHeader']))
            story.append(Spacer(1, 10))
            
            for document_item in documents[:20]:  # Limitar a 20 documentos
                doc_text = f"""
                <b>{document_item.get('filename', 'N/A')}</b><br/>
                Tipo: {document_item.get('type', 'N/A').replace('_', ' ').title()} | 
                Processo: {document_item.get('process_number', 'N/A')} | 
                Prazos: {len(document_item.get('deadlines', []))}
                """
                story.append(Paragraph(doc_text, self.styles['NormalText']))
                story.append(Spacer(1, 8))
        
        # Prazos urgentes
        urgent_deadlines = [d for d in deadlines if d.get('urgency') == 'high']
        if urgent_deadlines:
            story.append(PageBreak())
            story.append(Paragraph("🚨 Prazos Urgentes", self.styles['SectionHeader']))
            story.append(Spacer(1, 10))
            
            for dl in urgent_deadlines[:15]:  # Limitar a 15
                dl_text = f"""
                <font color="#{self.colors['danger'].hexval()[2:]}">
                <b>{dl.get('document_name', 'N/A')}</b><br/>
                Prazo: {dl.get('deadline', {}).get('days', 'N/A')} dias | 
                {dl.get('deadline', {}).get('context', 'N/A')[:100]}
                </font>
                """
                story.append(Paragraph(dl_text, self.styles['NormalText']))
                story.append(Spacer(1, 10))
        
        # Rodapé
        story.append(Spacer(1, 40))
        story.append(Paragraph(
            "⚖️ LexScan IA - Automação Documental Jurídica",
            self.styles['Footer']
        ))
        story.append(Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['Footer']
        ))
        
        doc.build(story)
        buffer.seek(0)
        
        return buffer


# Instância global
pdf_generator = PDFReportGenerator()


if __name__ == "__main__":
    # Teste
    print("=" * 60)
    print("TESTE GERADOR DE PDF")
    print("=" * 60)
    
    # Dados de exemplo
    test_doc = {
        'id': 1,
        'filename': 'Processo_12345.pdf',
        'type': 'peticao_inicial',
        'process_number': '12345-67.2024.8.26.0001',
        'parties': {
            'autor': 'João Silva',
            'reu': 'Empresa ABC Ltda',
            'advogado': 'Dr. Carlos Mendes OAB/SP 123456'
        },
        'deadlines': [
            {'days': '15', 'urgency': 'high', 'context': 'Prazo para contestação'},
            {'days': '30', 'urgency': 'medium', 'context': 'Prazo para recurso'}
        ],
        'values': [{'value': 'R$ 50.000,00', 'context': 'Valor da causa'}],
        'analysis': 'Documento analisado com sucesso.',
        'summary': 'Ação de indenização por danos morais.',
        'court': 'Vara da Justiça Civil de São Paulo',
        'uploaded_at': '2024-01-15T10:30:00',
        'status': 'processed'
    }
    
    try:
        # Gerar relatório de documento
        pdf_buffer = pdf_generator.generate_document_report(test_doc)
        
        # Salvar para teste
        test_file = 'test_report.pdf'
        with open(test_file, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF gerado com sucesso!")
        print(f"📄 Arquivo: {test_file}")
        print(f"📊 Tamanho: {len(pdf_buffer.getvalue())} bytes")
        
        # Limpar
        os.remove(test_file)
        print("🧹 Arquivo de teste removido")
        print("\nSistema de PDF pronto para uso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
