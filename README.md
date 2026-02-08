# Application MPM - Méthode des Potentiels Métra

Application web Flask pour la génération automatique de réseaux MPM (Méthode des Potentiels Métra) dans le cadre du cours de Recherche Opérationnelle.

## 📋 Description

Cette application permet de :
- Saisir des tâches avec leurs durées et antériorités
- Calculer automatiquement les dates au plus tôt (DPT) et au plus tard (DPL)
- Identifier les marges et le chemin critique
- Visualiser graphiquement le réseau MPM
- Exporter les résultats en PDF

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner ou télécharger le projet**

2. **Créer un environnement virtuel (recommandé)**

```bash
python -m venv venv
```

3. **Activer l'environnement virtuel**

Sur Windows :
```bash
venv\Scripts\activate
```

Sur Linux/Mac :
```bash
source venv/bin/activate
```

4. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

## ▶️ Exécution

1. **Démarrer l'application Flask**

```bash
python app.py
```

2. **Accéder à l'application**

Ouvrez votre navigateur et allez à l'adresse :
```
http://localhost:5000
```

## 📁 Structure du Projet

```
RO/
├── app.py                 # Application Flask principale
├── mpm_calculator.py      # Module de calcul MPM
├── mpm_visualizer.py      # Module de visualisation du graphe
├── pdf_generator.py       # Module de génération PDF
├── requirements.txt       # Dépendances Python
├── README.md             # Ce fichier
├── templates/            # Templates HTML
│   ├── index.html        # Page d'accueil
│   ├── application.html  # Page principale de l'application
│   └── about.html        # Page À propos
└── static/               # Fichiers statiques
    ├── css/
    │   └── style.css     # Styles CSS
    ├── js/
    │   └── app.js        # JavaScript de l'application
    └── temp/             # Fichiers temporaires (graphes, PDFs)
```

## 🎯 Utilisation

### Saisie des tâches

1. Accédez à la page "Application"
2. Saisissez le nom de la tâche (ex: A, B, Tâche 1)
3. Saisissez la durée (nombre positif)
4. Saisissez les tâches précédentes (antériorités) séparées par des virgules (ex: A,B)
5. Cliquez sur "Ajouter la tâche"
6. Répétez pour toutes les tâches

### Calcul du réseau MPM

1. Une fois toutes les tâches ajoutées, cliquez sur "Calculer le réseau MPM"
2. Le graphe MPM s'affiche avec :
   - Les tâches critiques en rouge
   - Les dates au plus tôt et au plus tard pour chaque tâche
   - Les marges
3. Un tableau récapitulatif affiche toutes les informations
4. Les informations du projet (durée totale, chemin critique) sont affichées

### Export PDF

1. Après le calcul, cliquez sur "Exporter en PDF"
2. Le PDF contient :
   - Le réseau MPM visualisé
   - Le tableau récapitulatif complet
   - Les informations du projet

## 🔧 Technologies Utilisées

- **Backend** : Python 3, Flask
- **Calculs** : Algorithmes MPM personnalisés
- **Visualisation** : NetworkX, Matplotlib
- **PDF** : ReportLab
- **Frontend** : HTML5, CSS3, JavaScript, Bootstrap 5

## 📚 Concepts MPM

### Dates au plus tôt (DPT)
Date de début au plus tôt d'une tâche, calculée en fonction de la fin au plus tôt de toutes ses antériorités.

### Dates au plus tard (DPL)
Date de début au plus tard d'une tâche, calculée en fonction de la fin au plus tard de tous ses successeurs.

### Marge
Différence entre DPL et DPT. Une marge de 0 indique que la tâche est critique.

### Chemin critique
Séquence de tâches avec marge nulle. Toute augmentation de la durée d'une tâche critique augmente la durée totale du projet.

## ⚠️ Validation

L'application valide automatiquement :
- La présence de toutes les données requises
- L'absence de cycles dans le graphe
- La cohérence des antériorités (références à des tâches existantes)
- La validité des durées (nombres positifs)

## 🐛 Dépannage

### Erreur "Module not found"
Assurez-vous d'avoir installé toutes les dépendances :
```bash
pip install -r requirements.txt
```

### Erreur de port déjà utilisé
Changez le port dans `app.py` :
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Problème de génération de graphe
Vérifiez que le dossier `static/temp` existe et est accessible en écriture.

## 📝 Notes

- Les fichiers temporaires (graphes, PDFs) sont stockés dans `static/temp/`
- Les tâches sont sauvegardées automatiquement dans le localStorage du navigateur
- Le graphe est généré avec une résolution de 300 DPI pour une qualité optimale

## 👥 Équipe

Projet réalisé dans le cadre du cours de Recherche Opérationnelle.

## 📄 Licence

Ce projet est à usage pédagogique.

---

**Bon travail avec votre projet MPM !** 🎓
