"""
Module de génération de PDF pour le réseau MPM
Génère un PDF avec le graphe, le tableau récapitulatif et les informations du projet
"""

import matplotlib
matplotlib.use("Agg")  # Backend non-interactif pour Flask - DOIT être avant tout import matplotlib.pyplot
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
from datetime import datetime
import networkx as nx
from io import BytesIO
import math


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
        Génère une image du graphe MPM pour le PDF avec le même style que le visualiseur principal
        """
        try:
            # Construire le graphe avec nœuds Début et Fin
            G = nx.DiGraph()
            
            # Ajouter le nœud Début
            G.add_node('Début', duration=0, dpt=0, dpl=0, is_critical=True, is_special=True)
            
            # Ajouter les nœuds (tâches)
            for task in self.tasks:
                task_name = task['name']
                G.add_node(
                    task_name,
                    duration=float(task['duration']),
                    dpt=self.dpt[task_name],
                    dpl=self.dpl[task_name],
                    is_critical=task_name in self.critical_path,
                    is_special=False
                )
            
            # Ajouter le nœud Fin
            G.add_node('Fin', duration=0, dpt=self.project_duration, 
                      dpl=self.project_duration, is_critical=True, is_special=True)
            
            # Trouver les tâches sans antériorités et sans successeurs
            tasks_without_pred = []
            tasks_without_succ = []
            
            for task in self.tasks:
                predecessors = task.get('predecessors', [])
                if not predecessors:
                    tasks_without_pred.append(task['name'])
            
            all_task_names = {task['name'] for task in self.tasks}
            for task in self.tasks:
                task_name = task['name']
                is_successor = any(task_name in t.get('predecessors', []) for t in self.tasks)
                if not is_successor:
                    tasks_without_succ.append(task_name)
            
            # Connecter Début aux tâches sans antériorités
            for task_name in tasks_without_pred:
                is_critical = task_name in self.critical_path
                G.add_edge('Début', task_name, critical=is_critical)
            
            # Ajouter les arêtes (antériorités)
            for task in self.tasks:
                task_name = task['name']
                predecessors = task.get('predecessors', [])
                for pred in predecessors:
                    is_critical_edge = (
                        task_name in self.critical_path and 
                        pred in self.critical_path
                    )
                    G.add_edge(pred, task_name, critical=is_critical_edge)
            
            # Connecter les tâches sans successeurs à Fin
            for task_name in tasks_without_succ:
                is_critical = task_name in self.critical_path
                G.add_edge(task_name, 'Fin', critical=is_critical)
            
            # Calculer le layout hiérarchique
            pos = self._hierarchical_layout_pdf(G)
            
            # Créer la figure avec taille adaptative
            num_nodes = len(G.nodes())
            num_levels = min(15, int(math.ceil(self.project_duration)) + 2)
            fig_width = min(16, max(10, num_levels * 1.2))
            fig_height = min(10, max(6, num_nodes * 0.6))
            
            fig, ax = plt.subplots(figsize=(fig_width, fig_height))
            ax.axis('off')
            
            # Définir les limites pour contrôler la taille
            ax.set_xlim(-1, num_levels * 2.2)
            ax.set_ylim(-num_nodes * 0.6, num_nodes * 0.6)
            
            # Dessiner les arêtes
            critical_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('critical', False)]
            non_critical_edges = [(u, v) for u, v, d in G.edges(data=True) if not d.get('critical', False)]
            
            for u, v in critical_edges:
                x1, y1 = pos[u]
                x2, y2 = pos[v]
                arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                      arrowstyle='->', mutation_scale=20,
                                      color='red', linewidth=2, zorder=1)
                ax.add_patch(arrow)
            
            for u, v in non_critical_edges:
                x1, y1 = pos[u]
                x2, y2 = pos[v]
                arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                      arrowstyle='->', mutation_scale=15,
                                      color='black', linewidth=1.2, zorder=1, alpha=0.6)
                ax.add_patch(arrow)
            
            # Dessiner les nœuds avec le même style que le visualiseur principal
            for node in G.nodes():
                x, y = pos[node]
                data = G.nodes[node]
                duration = data.get('duration', 0)
                dpt = data.get('dpt', 0)
                dpl = data.get('dpl', 0)
                is_critical = data.get('is_critical', False)
                is_special = data.get('is_special', False)
                
                # Couleur selon le type
                if is_special:
                    facecolor = '#9b59b6'
                    edgecolor = '#6c3483'
                elif is_critical:
                    facecolor = '#e74c3c'
                    edgecolor = '#c0392b'
                else:
                    facecolor = '#3498db'
                    edgecolor = '#2980b9'
                
                # Taille du nœud (légèrement réduite pour le PDF)
                width = 0.9
                height = 0.6
                
                # Dessiner le rectangle
                box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                                  boxstyle="round,pad=0.08", 
                                  facecolor=facecolor, edgecolor=edgecolor,
                                  linewidth=1.5, zorder=2)
                ax.add_patch(box)
                
                # Texte formaté
                if is_special:
                    ax.text(x, y + 0.1, node, ha='center', va='center',
                           fontsize=9, fontweight='bold', color='white', zorder=3)
                    ax.text(x - 0.3, y - 0.15, f'{dpt:.0f}', ha='left', va='center',
                           fontsize=7, color='white', zorder=3)
                    ax.text(x + 0.3, y - 0.15, f'{dpl:.0f}', ha='right', va='center',
                           fontsize=7, color='white', zorder=3)
                else:
                    ax.text(x - 0.4, y + 0.2, node, ha='left', va='center',
                           fontsize=8, fontweight='bold', color='white', zorder=3)
                    ax.text(x + 0.4, y + 0.2, f'{duration:.0f}', ha='right', va='center',
                           fontsize=7, color='white', zorder=3)
                    ax.text(x - 0.4, y - 0.2, f'{dpt:.0f}', ha='left', va='center',
                           fontsize=7, color='white', zorder=3)
                    ax.text(x + 0.4, y - 0.2, f'{dpl:.0f}', ha='right', va='center',
                           fontsize=7, color='white', zorder=3)
            
            plt.title('Graphe MPM d\'un projet', fontsize=12, fontweight='bold', pad=10)
            
            try:
                plt.tight_layout()
            except:
                pass
            
            # Sauvegarder dans un buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', pad_inches=0.2)
            plt.close()
            
            img_buffer.seek(0)
            img = Image(img_buffer, width=16*cm, height=10*cm)
            
            return img
            
        except Exception as e:
            import traceback
            print(f"Erreur lors de la génération du graphe PDF: {e}")
            print(traceback.format_exc())
            return None
    
    def _hierarchical_layout_pdf(self, G):
        """
        Génère un positionnement hiérarchique pour le PDF (similaire au visualiseur principal)
        """
        # Normaliser les DPT
        all_dpt_values = [G.nodes[node].get('dpt', 0) for node in G.nodes() 
                         if node not in ['Début', 'Fin'] and 'dpt' in G.nodes[node]]
        
        if not all_dpt_values:
            pos = {}
            nodes_list = list(G.nodes())
            for i, node in enumerate(nodes_list):
                pos[node] = (i * 1.5, 0)
            return pos
        
        min_dpt = min(all_dpt_values) if all_dpt_values else 0
        max_dpt = max(all_dpt_values) if all_dpt_values else self.project_duration
        
        num_levels = min(15, int(math.ceil(self.project_duration)) + 2)
        level_size = (max_dpt - min_dpt) / max(1, num_levels - 2) if num_levels > 2 else 1
        
        levels = {}
        for node in G.nodes():
            if node == 'Début':
                level = 0
            elif node == 'Fin':
                level = num_levels - 1
            else:
                if 'dpt' in G.nodes[node]:
                    dpt = G.nodes[node]['dpt']
                    normalized = (dpt - min_dpt) / max(1, level_size) if level_size > 0 else 0
                    level = min(int(normalized) + 1, num_levels - 2)
                else:
                    level = 1
            
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
        
        pos = {}
        x_spacing = 1.5
        y_spacing = 1.0
        
        for level, nodes in sorted(levels.items()):
            x = level * x_spacing
            if len(nodes) == 1:
                pos[nodes[0]] = (x, 0)
            else:
                start_y = -(len(nodes) - 1) * y_spacing / 2
                for i, node in enumerate(nodes):
                    pos[node] = (x, start_y + i * y_spacing)
        
        return pos
