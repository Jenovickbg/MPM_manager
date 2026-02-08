"""
Application Flask pour la génération de réseaux MPM (Méthode des Potentiels Métra)
Projet pédagogique - Recherche Opérationnelle
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from datetime import datetime
from mpm_calculator import MPMCalculator
from mpm_visualizer import MPMVisualizer
from pdf_generator import PDFGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mpm-ro-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'static/temp'

# Créer le dossier temp s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    """Page d'accueil de l'application"""
    return render_template('index.html')


@app.route('/application')
def application():
    """Page principale de l'application MPM"""
    return render_template('application.html')


@app.route('/a-propos')
def about():
    """Page À propos du projet"""
    return render_template('about.html')


@app.route('/api/calculate-mpm', methods=['POST'])
def calculate_mpm():
    """
    API endpoint pour calculer le réseau MPM
    Reçoit les tâches et retourne les résultats calculés
    """
    try:
        data = request.get_json()
        tasks = data.get('tasks', [])
        
        if not tasks:
            return jsonify({'error': 'Aucune tâche fournie'}), 400
        
        # Validation des données
        validation_error = validate_tasks(tasks)
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        # Calcul MPM
        calculator = MPMCalculator(tasks)
        results = calculator.calculate_all()
        
        # Génération du graphe
        visualizer = MPMVisualizer(results)
        graph_path = visualizer.generate_graph()
        
        return jsonify({
            'success': True,
            'results': results,
            'graph_path': graph_path
        })
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erreur détaillée: {error_details}")  # Pour le debug
        return jsonify({'error': f'Erreur lors du calcul: {str(e)}'}), 500


@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    """
    API endpoint pour générer le PDF du réseau MPM
    """
    try:
        data = request.get_json()
        tasks = data.get('tasks', [])
        results = data.get('results', {})
        
        if not tasks or not results:
            return jsonify({'error': 'Données manquantes'}), 400
        
        # Génération du PDF
        pdf_generator = PDFGenerator(tasks, results)
        pdf_path = pdf_generator.generate()
        
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'reseau_mpm_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la génération du PDF: {str(e)}'}), 500


def validate_tasks(tasks):
    """
    Valide les tâches saisies par l'utilisateur
    Retourne None si valide, sinon un message d'erreur
    """
    if not tasks:
        return "Aucune tâche n'a été saisie"
    
    # Vérifier que toutes les tâches ont un nom et une durée
    for i, task in enumerate(tasks):
        if not task.get('name') or not task.get('name').strip():
            return f"La tâche #{i+1} n'a pas de nom"
        
        try:
            duration = float(task.get('duration', 0))
            if duration <= 0:
                return f"La durée de la tâche '{task.get('name')}' doit être positive"
        except (ValueError, TypeError):
            return f"La durée de la tâche '{task.get('name')}' n'est pas valide"
    
    # Vérifier les cycles dans le graphe
    if has_cycle(tasks):
        return "Le graphe contient un cycle. Vérifiez les antériorités."
    
    # Vérifier que les antériorités référencent des tâches existantes
    task_names = {task['name'] for task in tasks}
    for task in tasks:
        predecessors = task.get('predecessors', [])
        for pred in predecessors:
            if pred not in task_names:
                return f"La tâche '{task['name']}' référence une antériorité inexistante: '{pred}'"
    
    return None


def has_cycle(tasks):
    """
    Vérifie si le graphe contient un cycle en utilisant DFS
    """
    # Construire le graphe d'adjacence
    graph = {}
    task_names = {task['name'] for task in tasks}
    
    for task in tasks:
        graph[task['name']] = task.get('predecessors', [])
    
    # DFS pour détecter les cycles
    visited = set()
    rec_stack = set()
    
    def dfs(node):
        if node in rec_stack:
            return True  # Cycle détecté
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.get(node, []):
            if dfs(neighbor):
                return True
        
        rec_stack.remove(node)
        return False
    
    for node in task_names:
        if node not in visited:
            if dfs(node):
                return True
    
    return False


# Configuration pour le développement local
# Sur Render/Heroku, l'application est lancée via Gunicorn (voir Procfile)
if __name__ == '__main__':
    # Détecter si on est en production (variable d'environnement)
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
