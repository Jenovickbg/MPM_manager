"""
Module de génération de PDF pour le réseau MPM
Génère un PDF avec le graphe, le tableau récapitulatif et les informations du projet
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from io import BytesIO


class PDFGenerator:
    """
    Classe pour générer un PDF contenant le réseau MPM et les résultats
    """
    
    def __init__(self, tasks, results):
        """
        Initialise le générateur PDF
        
        Args:
            tasks: Liste des tâches
            results: Dictionnaire contenant les résultats MPM
        """
        self.tasks = tasks
        self.results = results
        self.dpt = results['dpt']
        self.dpl = results['dpl']
        self.marges = results['marges']
        self.critical_path = results['critical_path']
        self.project_duration = results['project_duration']
    
    def generate(self, output_dir='static/temp'):
        """
        Génère le PDF complet
        
        Args:
            output_dir: Répertoire de sortie
            
        Returns:
            Chemin vers le PDF généré
        """
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f'mpm_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        filepath = os.path.join(output_dir, filename)
        
        # Créer le document PDF
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        # Titre
        story.append(Paragraph('Réseau MPM - Rapport de Projet', title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Informations générales
        story.append(Paragraph('Informations du Projet', heading_style))
        info_data = [
            ['Durée totale du projet:', f'{self.project_duration:.2f} unités de temps'],
            ['Nombre de tâches:', str(len(self.tasks))],
            ['Nombre de tâches critiques:', str(len(self.critical_path))],
            ['Chemin critique:', ' → '.join(self.critical_path) if self.critical_path else 'Aucun']
        ]
        info_table = Table(info_data, colWidths=[6*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 1*cm))
        
        # Tableau récapitulatif
        story.append(Paragraph('Tableau Récapitulatif des Tâches', heading_style))
        table_data = [['Tâche', 'Durée', 'DPT', 'DPL', 'Marge', 'Critique']]
        
        # Trier les tâches par DPT
        sorted_tasks = sorted(self.tasks, key=lambda t: self.dpt[t['name']])
        
        for task in sorted_tasks:
            task_name = task['name']
            duration = float(task['duration'])
            dpt = self.dpt[task_name]
            dpl = self.dpl[task_name]
            marge = self.marges[task_name]
            is_critical = 'Oui' if task_name in self.critical_path else 'Non'
            
            table_data.append([
                task_name,
                f'{duration:.2f}',
                f'{dpt:.2f}',
                f'{dpl:.2f}',
                f'{marge:.2f}',
                is_critical
            ])
        
        # Créer le tableau
        summary_table = Table(table_data, colWidths=[3*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
        
        # Style de base
        table_style = [
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            # Lignes de données par défaut
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            # Grille
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        # Ajouter les couleurs pour les tâches critiques
        for i, task in enumerate(sorted_tasks, start=1):
            if task['name'] in self.critical_path:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fee2e2')))
        
        summary_table.setStyle(TableStyle(table_style))
        story.append(summary_table)
        story.append(PageBreak())
        
        # Graphe MPM
        story.append(Paragraph('Réseau MPM - Visualisation', heading_style))
        graph_image = self._generate_graph_image()
        if graph_image:
            story.append(Spacer(1, 0.5*cm))
            story.append(graph_image)
        
        # Construire le PDF
        doc.build(story)
        
        return filepath
    
    
    def _generate_graph_image(self):
        """
        Génère une image du graphe MPM pour le PDF
        """
        try:
            # Construire le graphe
            G = nx.DiGraph()
            
            # Ajouter les nœuds
            for task in self.tasks:
                task_name = task['name']
                G.add_node(
                    task_name,
                    duration=float(task['duration']),
                    dpt=self.dpt[task_name],
                    dpl=self.dpl[task_name],
                    is_critical=task_name in self.critical_path
                )
            
            # Ajouter les arêtes
            for task in self.tasks:
                task_name = task['name']
                predecessors = task.get('predecessors', [])
                for pred in predecessors:
                    is_critical_edge = (
                        task_name in self.critical_path and 
                        pred in self.critical_path
                    )
                    G.add_edge(pred, task_name, critical=is_critical_edge)
            
            # Créer la figure
            fig, ax = plt.subplots(figsize=(14, 8))
            ax.axis('off')
            
            # Positionnement
            pos = nx.spring_layout(G, k=2, iterations=50)
            
            # Dessiner les arêtes
            critical_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('critical', False)]
            non_critical_edges = [(u, v) for u, v, d in G.edges(data=True) if not d.get('critical', False)]
            
            nx.draw_networkx_edges(G, pos, edgelist=critical_edges, edge_color='red', 
                                  width=2, alpha=0.7, arrows=True, arrowsize=15, ax=ax)
            nx.draw_networkx_edges(G, pos, edgelist=non_critical_edges, edge_color='gray', 
                                  width=1, alpha=0.5, arrows=True, arrowsize=12, ax=ax)
            
            # Dessiner les nœuds
            critical_nodes = [n for n in G.nodes() if n in self.critical_path]
            non_critical_nodes = [n for n in G.nodes() if n not in self.critical_path]
            
            nx.draw_networkx_nodes(G, pos, nodelist=critical_nodes, node_color='#ff6b6b',
                                   node_size=1500, node_shape='s', alpha=0.9, ax=ax)
            nx.draw_networkx_nodes(G, pos, nodelist=non_critical_nodes, node_color='#4dabf7',
                                  node_size=1500, node_shape='s', alpha=0.7, ax=ax)
            
            # Labels simplifiés
            labels = {node: f"{node}\n{self.dpt[node]:.1f}|{self.dpl[node]:.1f}" 
                     for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', 
                                   font_color='white', ax=ax)
            
            plt.title('Réseau MPM', fontsize=14, fontweight='bold', pad=10)
            plt.tight_layout()
            
            # Sauvegarder dans un buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            img_buffer.seek(0)
            img = Image(img_buffer, width=16*cm, height=9*cm)
            
            return img
            
        except Exception as e:
            print(f"Erreur lors de la génération du graphe: {e}")
            return None
