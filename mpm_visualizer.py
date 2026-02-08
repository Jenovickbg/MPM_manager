"""
Module de visualisation du réseau MPM
Génère un graphe visuel du réseau MPM avec NetworkX et Matplotlib
"""

import matplotlib
matplotlib.use("Agg")  # Backend non-interactif pour Flask - DOIT être avant tout import matplotlib.pyplot
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import os
from datetime import datetime


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
        Construit le graphe NetworkX à partir des tâches
        """
        # Ajouter les nœuds (tâches)
        for task in self.tasks:
            task_name = task['name']
            self.graph.add_node(
                task_name,
                duration=float(task['duration']),
                dpt=self.dpt[task_name],
                dpl=self.dpl[task_name],
                marge=self.marges[task_name],
                is_critical=task_name in self.critical_path
            )
        
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
    
    def _draw_graph(self, filepath):
        """
        Dessine le graphe avec Matplotlib
        
        Args:
            filepath: Chemin où sauvegarder l'image
        """
        # Configuration de la figure
        plt.figure(figsize=(16, 10))
        plt.axis('off')
        
        # Positionnement des nœuds avec un layout hiérarchique
        pos = self._hierarchical_layout()
        
        # Dessiner les arêtes
        self._draw_edges(pos)
        
        # Dessiner les nœuds
        self._draw_nodes(pos)
        
        # Ajouter une légende
        self._add_legend()
        
        # Titre
        plt.title('Réseau MPM - Méthode des Potentiels Métra', 
                 fontsize=16, fontweight='bold', pad=20)
        
        # Sauvegarder
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
    
    def _hierarchical_layout(self):
        """
        Génère un positionnement hiérarchique des nœuds basé sur les DPT
        """
        # Grouper les tâches par niveau (basé sur DPT)
        levels = {}
        for task_name in self.graph.nodes():
            dpt = self.dpt[task_name]
            level = int(dpt)  # Niveau approximatif basé sur DPT
            if level not in levels:
                levels[level] = []
            levels[level].append(task_name)
        
        # Positionner les nœuds
        pos = {}
        max_nodes_per_level = max(len(nodes) for nodes in levels.values()) if levels else 1
        
        for level, nodes in sorted(levels.items()):
            y = -level * 2  # Espacement vertical
            x_spacing = max(3, 12 / max(len(nodes), 1))
            start_x = -(len(nodes) - 1) * x_spacing / 2
            
            for i, node in enumerate(nodes):
                pos[node] = (start_x + i * x_spacing, y)
        
        # Ajuster avec spring layout pour améliorer la lisibilité
        pos = nx.spring_layout(self.graph, pos=pos, k=2, iterations=50)
        
        return pos
    
    def _draw_edges(self, pos):
        """
        Dessine les arêtes du graphe
        """
        # Arêtes critiques (rouge)
        critical_edges = [
            (u, v) for u, v, d in self.graph.edges(data=True) 
            if d.get('critical', False)
        ]
        nx.draw_networkx_edges(
            self.graph, pos, 
            edgelist=critical_edges,
            edge_color='red',
            width=3,
            alpha=0.7,
            arrows=True,
            arrowsize=20,
            arrowstyle='->',
            connectionstyle='arc3,rad=0.1'
        )
        
        # Arêtes non critiques (gris)
        non_critical_edges = [
            (u, v) for u, v, d in self.graph.edges(data=True) 
            if not d.get('critical', False)
        ]
        nx.draw_networkx_edges(
            self.graph, pos,
            edgelist=non_critical_edges,
            edge_color='gray',
            width=1.5,
            alpha=0.5,
            arrows=True,
            arrowsize=15,
            arrowstyle='->',
            connectionstyle='arc3,rad=0.1'
        )
    
    def _draw_nodes(self, pos):
        """
        Dessine les nœuds du graphe avec leurs informations
        """
        # Nœuds critiques (rouge)
        critical_nodes = [n for n in self.graph.nodes() if n in self.critical_path]
        nx.draw_networkx_nodes(
            self.graph, pos,
            nodelist=critical_nodes,
            node_color='#ff6b6b',
            node_size=2000,
            node_shape='s',
            alpha=0.9,
            edgecolors='darkred',
            linewidths=2
        )
        
        # Nœuds non critiques (bleu)
        non_critical_nodes = [n for n in self.graph.nodes() if n not in self.critical_path]
        nx.draw_networkx_nodes(
            self.graph, pos,
            nodelist=non_critical_nodes,
            node_color='#4dabf7',
            node_size=2000,
            node_shape='s',
            alpha=0.7,
            edgecolors='darkblue',
            linewidths=2
        )
        
        # Labels des nœuds avec informations MPM
        labels = {}
        for node in self.graph.nodes():
            data = self.graph.nodes[node]
            duration = data['duration']
            dpt = data['dpt']
            dpl = data['dpl']
            marge = data['marge']
            
            # Format du label
            label = f"{node}\nDurée: {duration}\nDPT: {dpt:.1f} | DPL: {dpl:.1f}\nMarge: {marge:.1f}"
            labels[node] = label
        
        nx.draw_networkx_labels(
            self.graph, pos, labels,
            font_size=8,
            font_weight='bold',
            font_color='white'
        )
    
    def _add_legend(self):
        """
        Ajoute une légende au graphe
        """
        critical_patch = mpatches.Patch(color='#ff6b6b', label='Tâche critique')
        non_critical_patch = mpatches.Patch(color='#4dabf7', label='Tâche non critique')
        
        plt.legend(
            handles=[critical_patch, non_critical_patch],
            loc='upper right',
            fontsize=10,
            framealpha=0.9
        )
