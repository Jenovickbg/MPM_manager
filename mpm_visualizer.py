"""
Module de visualisation du réseau MPM
Génère un graphe visuel du réseau MPM avec NetworkX et Matplotlib
"""

import matplotlib
matplotlib.use("Agg")  # Backend non-interactif pour Flask - DOIT être avant tout import matplotlib.pyplot
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import networkx as nx
import os
from datetime import datetime
import math


class MPMVisualizer:
    """
    Classe pour visualiser le réseau MPM sous forme de graphe
    """
    
    def __init__(self, results):
        """
        Initialise le visualiseur avec les résultats MPM
        
        Args:
            results: Dictionnaire contenant les résultats du calcul MPM
        """
        self.results = results
        self.tasks = results['tasks']
        self.dpt = results['dpt']
        self.dpl = results['dpl']
        self.marges = results['marges']
        self.critical_path = set(results['critical_path'])
        self.project_duration = results['project_duration']
        self.graph = nx.DiGraph()
    
    def generate_graph(self, output_dir='static/temp'):
        """
        Génère le graphe MPM et le sauvegarde
        
        Args:
            output_dir: Répertoire de sortie pour l'image
            
        Returns:
            Chemin vers l'image générée
        """
        # Créer le répertoire s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
        
        # Construire le graphe
        self._build_graph()
        
        # Générer la visualisation
        filename = f'mpm_graph_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(output_dir, filename)
        
        self._draw_graph(filepath)
        
        return filepath
    
    def _build_graph(self):
        """
        Construit le graphe NetworkX à partir des tâches avec nœuds Début et Fin
        """
        # Ajouter le nœud Début
        self.graph.add_node('Début', duration=0, dpt=0, dpl=0, marge=0, is_critical=True, is_special=True)
        
        # Ajouter les nœuds (tâches)
        for task in self.tasks:
            task_name = task['name']
            self.graph.add_node(
                task_name,
                duration=float(task['duration']),
                dpt=self.dpt[task_name],
                dpl=self.dpl[task_name],
                marge=self.marges[task_name],
                is_critical=task_name in self.critical_path,
                is_special=False
            )
        
        # Ajouter le nœud Fin
        self.graph.add_node('Fin', duration=0, dpt=self.project_duration, 
                           dpl=self.project_duration, marge=0, is_critical=True, is_special=True)
        
        # Trouver les tâches sans antériorités (connectées à Début)
        tasks_without_pred = []
        tasks_without_succ = []
        
        all_predecessors = set()
        for task in self.tasks:
            predecessors = task.get('predecessors', [])
            if not predecessors:
                tasks_without_pred.append(task['name'])
            all_predecessors.update(predecessors)
        
        # Trouver les tâches sans successeurs (connectées à Fin)
        all_task_names = {task['name'] for task in self.tasks}
        for task in self.tasks:
            task_name = task['name']
            # Vérifier si cette tâche n'est antériorité d'aucune autre
            is_successor = any(task_name in t.get('predecessors', []) for t in self.tasks)
            if not is_successor:
                tasks_without_succ.append(task_name)
        
        # Connecter Début aux tâches sans antériorités
        for task_name in tasks_without_pred:
            is_critical = task_name in self.critical_path
            self.graph.add_edge('Début', task_name, critical=is_critical)
        
        # Ajouter les arêtes (antériorités)
        for task in self.tasks:
            task_name = task['name']
            predecessors = task.get('predecessors', [])
            for pred in predecessors:
                # Vérifier si l'arête est critique
                is_critical_edge = (
                    task_name in self.critical_path and 
                    pred in self.critical_path
                )
                self.graph.add_edge(pred, task_name, critical=is_critical_edge)
        
        # Connecter les tâches sans successeurs à Fin
        for task_name in tasks_without_succ:
            is_critical = task_name in self.critical_path
            self.graph.add_edge(task_name, 'Fin', critical=is_critical)
    
    def _draw_graph(self, filepath):
        """
        Dessine le graphe avec Matplotlib
        
        Args:
            filepath: Chemin où sauvegarder l'image
        """
        # Configuration de la figure avec taille adaptative
        # Calculer la taille nécessaire basée sur le nombre de nœuds
        num_nodes = len(self.graph.nodes())
        num_levels = min(20, int(math.ceil(self.project_duration)) + 2)
        
        # Limiter la taille de la figure pour éviter les images trop grandes
        fig_width = min(20, max(12, num_levels * 1.5))
        fig_height = min(14, max(8, num_nodes * 0.8))
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.axis('off')
        
        # Définir les limites de l'axe pour contrôler la taille
        ax.set_xlim(-1, num_levels * 2.5)
        ax.set_ylim(-num_nodes * 0.8, num_nodes * 0.8)
        
        # Positionnement des nœuds avec un layout hiérarchique de gauche à droite
        pos = self._hierarchical_layout()
        
        # Dessiner les arêtes
        self._draw_edges(ax, pos)
        
        # Dessiner les nœuds
        self._draw_nodes(ax, pos)
        
        # Ajouter une légende
        self._add_legend(ax)
        
        # Titre
        plt.title('Graphe MPM d\'un projet', 
                 fontsize=18, fontweight='bold', pad=20)
        
        # Sauvegarder (sans tight_layout pour éviter le warning)
        try:
            plt.tight_layout()
        except:
            pass  # Ignorer le warning si tight_layout échoue
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', pad_inches=0.2)
        plt.close()
    
    def _hierarchical_layout(self):
        """
        Génère un positionnement hiérarchique des nœuds de gauche à droite basé sur les DPT
        """
        # Normaliser les DPT pour créer des niveaux compacts
        all_dpt_values = [self.dpt[node] for node in self.graph.nodes() if node in self.dpt and node not in ['Début', 'Fin']]
        
        if not all_dpt_values:
            # Cas simple : utiliser un layout basique
            pos = {}
            nodes_list = list(self.graph.nodes())
            for i, node in enumerate(nodes_list):
                pos[node] = (i * 2, 0)
            return pos
        
        min_dpt = min(all_dpt_values) if all_dpt_values else 0
        max_dpt = max(all_dpt_values) if all_dpt_values else self.project_duration
        
        # Créer des niveaux normalisés (max 20 niveaux pour éviter les images trop grandes)
        num_levels = min(20, int(math.ceil(self.project_duration)) + 2)
        level_size = (max_dpt - min_dpt) / max(1, num_levels - 2) if num_levels > 2 else 1
        
        # Calculer les niveaux basés sur les DPT normalisés
        levels = {}
        for node in self.graph.nodes():
            if node == 'Début':
                level = 0
            elif node == 'Fin':
                level = num_levels - 1
            else:
                # Vérifier que le nœud existe dans dpt
                if node in self.dpt:
                    dpt = self.dpt[node]
                    # Normaliser le niveau (entre 1 et num_levels-2)
                    normalized = (dpt - min_dpt) / max(1, level_size) if level_size > 0 else 0
                    level = min(int(normalized) + 1, num_levels - 2)
                else:
                    level = 1  # Niveau par défaut
            
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
        
        # Positionner les nœuds de gauche à droite avec espacement contrôlé
        pos = {}
        max_nodes_per_level = max(len(nodes) for nodes in levels.values()) if levels else 1
        
        # Espacement horizontal réduit pour éviter les images trop grandes
        x_spacing = 2.0  # Espacement entre les niveaux
        y_spacing = 1.5  # Espacement vertical entre nœuds
        
        for level, nodes in sorted(levels.items()):
            x = level * x_spacing
            if len(nodes) == 1:
                pos[nodes[0]] = (x, 0)
            else:
                start_y = -(len(nodes) - 1) * y_spacing / 2
                for i, node in enumerate(nodes):
                    pos[node] = (x, start_y + i * y_spacing)
        
        return pos
    
    def _draw_edges(self, ax, pos):
        """
        Dessine les arêtes du graphe
        """
        # Arêtes critiques (rouge)
        critical_edges = [
            (u, v) for u, v, d in self.graph.edges(data=True) 
            if d.get('critical', False)
        ]
        
        for u, v in critical_edges:
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                  arrowstyle='->', mutation_scale=25,
                                  color='red', linewidth=2.5, zorder=1)
            ax.add_patch(arrow)
        
        # Arêtes non critiques (noir)
        non_critical_edges = [
            (u, v) for u, v, d in self.graph.edges(data=True) 
            if not d.get('critical', False)
        ]
        
        for u, v in non_critical_edges:
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                  arrowstyle='->', mutation_scale=20,
                                  color='black', linewidth=1.5, zorder=1, alpha=0.6)
            ax.add_patch(arrow)
    
    def _draw_nodes(self, ax, pos):
        """
        Dessine les nœuds du graphe avec leurs informations formatées
        """
        for node in self.graph.nodes():
            x, y = pos[node]
            data = self.graph.nodes[node]
            duration = data.get('duration', 0)
            dpt = data.get('dpt', 0)
            dpl = data.get('dpl', 0)
            is_critical = data.get('is_critical', False)
            is_special = data.get('is_special', False)
            
            # Couleur selon le type
            if is_special:
                # Nœuds Début/Fin en violet
                facecolor = '#9b59b6'
                edgecolor = '#6c3483'
            elif is_critical:
                # Nœuds critiques en rouge
                facecolor = '#e74c3c'
                edgecolor = '#c0392b'
            else:
                # Nœuds non critiques en bleu
                facecolor = '#3498db'
                edgecolor = '#2980b9'
            
            # Taille du nœud
            width = 1.2
            height = 0.8
            
            # Dessiner le rectangle
            box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                              boxstyle="round,pad=0.1", 
                              facecolor=facecolor, edgecolor=edgecolor,
                              linewidth=2, zorder=2)
            ax.add_patch(box)
            
            # Texte formaté comme dans le modèle
            if is_special:
                # Pour Début/Fin : juste le nom en haut
                ax.text(x, y + 0.15, node, ha='center', va='center',
                       fontsize=11, fontweight='bold', color='white', zorder=3)
                # Dates en bas
                ax.text(x - 0.4, y - 0.2, f'{dpt:.0f}', ha='left', va='center',
                       fontsize=9, color='white', zorder=3)
                ax.text(x + 0.4, y - 0.2, f'{dpl:.0f}', ha='right', va='center',
                       fontsize=9, color='white', zorder=3)
            else:
                # Nom de la tâche en haut à gauche
                ax.text(x - 0.5, y + 0.25, node, ha='left', va='center',
                       fontsize=10, fontweight='bold', color='white', zorder=3)
                # Durée en haut à droite
                ax.text(x + 0.5, y + 0.25, f'{duration:.0f}', ha='right', va='center',
                       fontsize=9, color='white', zorder=3)
                # DPT en bas à gauche
                ax.text(x - 0.5, y - 0.25, f'{dpt:.0f}', ha='left', va='center',
                       fontsize=9, color='white', zorder=3)
                # DPL en bas à droite
                ax.text(x + 0.5, y - 0.25, f'{dpl:.0f}', ha='right', va='center',
                       fontsize=9, color='white', zorder=3)
    
    def _add_legend(self, ax):
        """
        Ajoute une légende au graphe avec explication des éléments
        """
        # Légende des lignes
        legend_elements = [
            mpatches.Patch(color='red', label='Chemin critique'),
            mpatches.Patch(color='black', label='Relation de dépendance')
        ]
        
        legend1 = ax.legend(handles=legend_elements, loc='upper left', 
                           fontsize=11, framealpha=0.95, title='Légende')
        legend1.get_title().set_fontweight('bold')
        
        # Explication de la structure des nœuds (dans un encadré)
        explanation_text = (
            "Structure d'un nœud :\n"
            "• Nom de la tâche (haut gauche)\n"
            "• Durée (haut droite)\n"
            "• Date au plus tôt (bas gauche)\n"
            "• Date au plus tard (bas droite)"
        )
        
        # Encadré d'explication
        text_box = ax.text(0.98, 0.02, explanation_text, 
                          transform=ax.transAxes,
                          fontsize=9,
                          verticalalignment='bottom',
                          horizontalalignment='right',
                          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                          zorder=10)
