"""
Module de calcul MPM (Méthode des Potentiels Métra)
Calcule les dates au plus tôt, au plus tard, les marges et le chemin critique
"""

from collections import deque


class MPMCalculator:
    """
    Classe pour calculer les paramètres MPM d'un réseau de tâches
    """
    
    def __init__(self, tasks):
        """
        Initialise le calculateur avec les tâches
        
        Args:
            tasks: Liste de dictionnaires contenant:
                - name: nom de la tâche
                - duration: durée de la tâche
                - predecessors: liste des noms des tâches précédentes
        """
        self.tasks = tasks
        self.task_dict = {task['name']: task for task in tasks}
        self.dpt = {}  # Dates au plus tôt
        self.dpl = {}  # Dates au plus tard
        self.marges = {}  # Marges totales
        self.critical_path = []  # Chemin critique
        self.project_duration = 0  # Durée totale du projet
    
    def calculate_all(self):
        """
        Effectue tous les calculs MPM
        
        Returns:
            Dictionnaire contenant tous les résultats
        """
        self._calculate_dpt()
        self._calculate_dpl()
        self._calculate_marges()
        self._find_critical_path()
        
        return {
            'dpt': self.dpt,
            'dpl': self.dpl,
            'marges': self.marges,
            'critical_path': self.critical_path,
            'project_duration': self.project_duration,
            'tasks': self.tasks
        }
    
    def _calculate_dpt(self):
        """
        Calcule les dates au plus tôt (DPT) de chaque tâche
        Utilise un parcours topologique du graphe
        """
        # Construire le graphe d'adjacence (successeurs)
        successors = {task['name']: [] for task in self.tasks}
        in_degree = {task['name']: 0 for task in self.tasks}
        
        for task in self.tasks:
            predecessors = task.get('predecessors', [])
            for pred in predecessors:
                if pred in successors:
                    successors[pred].append(task['name'])
                    in_degree[task['name']] += 1
        
        # Initialiser les DPT à 0
        self.dpt = {task['name']: 0 for task in self.tasks}
        
        # Parcours topologique avec BFS
        queue = deque()
        
        # Trouver les tâches sans antériorités (début du projet)
        for task_name in in_degree:
            if in_degree[task_name] == 0:
                queue.append(task_name)
                self.dpt[task_name] = 0
        
        while queue:
            current = queue.popleft()
            current_dpt = self.dpt[current]
            current_duration = float(self.task_dict[current]['duration'])
            current_finish = current_dpt + current_duration
            
            # Mettre à jour les DPT des successeurs
            for successor in successors[current]:
                # La DPT d'une tâche = max(DPT + durée) de toutes ses antériorités
                if current_finish > self.dpt[successor]:
                    self.dpt[successor] = current_finish
                
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)
        
        # Calculer la durée totale du projet
        # C'est le maximum de (DPT + durée) de toutes les tâches
        self.project_duration = 0
        for task in self.tasks:
            task_finish = self.dpt[task['name']] + float(task['duration'])
            if task_finish > self.project_duration:
                self.project_duration = task_finish
    
    def _calculate_dpl(self):
        """
        Calcule les dates au plus tard (DPL) de chaque tâche
        Utilise une approche itérative depuis les tâches terminales
        """
        # Construire le graphe des successeurs
        successors = {task['name']: [] for task in self.tasks}
        for task in self.tasks:
            for pred in task.get('predecessors', []):
                if pred in successors:
                    successors[pred].append(task['name'])
        
        # Initialiser toutes les DPL à la durée du projet
        self.dpl = {task['name']: self.project_duration for task in self.tasks}
        
        # Itérer jusqu'à convergence
        # Pour chaque tâche: DPL = min(DPL_successeur) - durée_tâche
        # Pour les tâches terminales: DPL = durée_projet - durée_tâche
        changed = True
        max_iterations = len(self.tasks) * 2
        iterations = 0
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            for task in self.tasks:
                task_name = task['name']
                task_duration = float(task['duration'])
                task_successors = successors[task_name]
                
                if len(task_successors) == 0:
                    # Tâche terminale: DPL = durée_projet - durée
                    new_dpl = self.project_duration - task_duration
                else:
                    # DPL = min(DPL_successeur) - durée_tâche
                    # La tâche doit finir avant que ses successeurs ne commencent
                    new_dpl = min(self.dpl[succ] for succ in task_successors) - task_duration
                
                # Mettre à jour si nécessaire
                if abs(new_dpl - self.dpl[task_name]) > 0.001:
                    self.dpl[task_name] = new_dpl
                    changed = True
    
    def _calculate_marges(self):
        """
        Calcule les marges totales de chaque tâche
        Marge = DPL - DPT
        """
        self.marges = {}
        for task_name in self.dpt:
            self.marges[task_name] = self.dpl[task_name] - self.dpt[task_name]
    
    def _find_critical_path(self):
        """
        Identifie le chemin critique
        Le chemin critique est composé des tâches avec marge = 0
        """
        critical_tasks = [
            task_name for task_name, marge in self.marges.items()
            if abs(marge) < 0.001  # Tolérance pour les erreurs d'arrondi
        ]
        
        # Trier les tâches critiques par DPT pour obtenir un ordre logique
        critical_tasks.sort(key=lambda x: self.dpt[x])
        
        self.critical_path = critical_tasks
