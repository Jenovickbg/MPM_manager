/**
 * JavaScript pour l'application MPM
 * Gère l'interface utilisateur et les appels API
 */

// État de l'application
let tasks = [];
let currentResults = null;

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    loadTasksFromStorage();
});

/**
 * Initialise les écouteurs d'événements
 */
function initializeEventListeners() {
    // Formulaire d'ajout de tâche
    const taskForm = document.getElementById('taskForm');
    if (taskForm) {
        taskForm.addEventListener('submit', handleAddTask);
    }

    // Bouton de calcul
    const calculateBtn = document.getElementById('calculateBtn');
    if (calculateBtn) {
        calculateBtn.addEventListener('click', handleCalculate);
    }

    // Bouton d'effacement
    const clearBtn = document.getElementById('clearBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', handleClear);
    }

    // Bouton d'export PDF
    const exportPdfBtn = document.getElementById('exportPdfBtn');
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', handleExportPdf);
    }
}

/**
 * Gère l'ajout d'une nouvelle tâche
 */
function handleAddTask(event) {
    event.preventDefault();

    const taskName = document.getElementById('taskName').value.trim();
    const taskDuration = parseFloat(document.getElementById('taskDuration').value);
    const taskPredecessors = document.getElementById('taskPredecessors').value.trim();

    // Validation
    if (!taskName) {
        alert('Veuillez saisir un nom de tâche');
        return;
    }

    if (isNaN(taskDuration) || taskDuration <= 0) {
        alert('Veuillez saisir une durée valide (nombre positif)');
        return;
    }

    // Vérifier si la tâche existe déjà
    if (tasks.some(t => t.name === taskName)) {
        alert('Une tâche avec ce nom existe déjà');
        return;
    }

    // Traiter les antériorités
    let predecessors = [];
    if (taskPredecessors) {
        predecessors = taskPredecessors.split(',')
            .map(p => p.trim())
            .filter(p => p.length > 0);
    }

    // Ajouter la tâche
    const newTask = {
        name: taskName,
        duration: taskDuration,
        predecessors: predecessors
    };

    tasks.push(newTask);
    saveTasksToStorage();
    updateTasksDisplay();
    resetForm();

    // Activer le bouton de calcul
    document.getElementById('calculateBtn').disabled = tasks.length === 0;
}

/**
 * Réinitialise le formulaire
 */
function resetForm() {
    document.getElementById('taskForm').reset();
    document.getElementById('taskName').focus();
}

/**
 * Met à jour l'affichage des tâches
 */
function updateTasksDisplay() {
    const container = document.getElementById('tasksContainer');
    
    if (tasks.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">Aucune tâche ajoutée</p>';
        return;
    }

    let html = '<div class="list-group">';
    
    tasks.forEach((task, index) => {
        const predecessorsText = task.predecessors.length > 0 
            ? task.predecessors.join(', ') 
            : 'Aucune';
        
        html += `
            <div class="task-item list-group-item">
                <div class="task-info">
                    <div class="task-name">${task.name}</div>
                    <div class="task-details">
                        Durée: ${task.duration} | Antériorités: ${predecessorsText}
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="removeTask(${index})">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Supprime une tâche
 */
function removeTask(index) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette tâche ?')) {
        tasks.splice(index, 1);
        saveTasksToStorage();
        updateTasksDisplay();
        document.getElementById('calculateBtn').disabled = tasks.length === 0;
        
        // Masquer les résultats si on supprime une tâche
        document.getElementById('resultsSection').style.display = 'none';
        currentResults = null;
    }
}

/**
 * Gère le calcul du réseau MPM
 */
async function handleCalculate() {
    if (tasks.length === 0) {
        alert('Veuillez ajouter au moins une tâche');
        return;
    }

    // Afficher le chargement
    document.getElementById('loadingSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';

    try {
        const response = await fetch('/api/calculate-mpm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ tasks: tasks })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erreur lors du calcul');
        }

        // Afficher les résultats
        currentResults = data.results;
        displayResults(data.results, data.graph_path);

    } catch (error) {
        console.error('Erreur:', error);
        document.getElementById('errorMessage').textContent = error.message;
        document.getElementById('errorSection').style.display = 'block';
    } finally {
        document.getElementById('loadingSection').style.display = 'none';
    }
}

/**
 * Affiche les résultats du calcul
 */
function displayResults(results, graphPath) {
    // Afficher le graphe
    const graphImg = document.getElementById('mpmGraph');
    graphImg.src = '/' + graphPath;
    graphImg.onload = function() {
        document.getElementById('resultsSection').style.display = 'block';
        document.getElementById('resultsSection').classList.add('fade-in');
    };

    // Afficher le tableau récapitulatif
    displaySummaryTable(results);

    // Afficher les informations du projet
    displayProjectInfo(results);
}

/**
 * Affiche le tableau récapitulatif
 */
function displaySummaryTable(results) {
    const tbody = document.getElementById('summaryTableBody');
    tbody.innerHTML = '';

    // Trier les tâches par DPT
    const sortedTasks = [...results.tasks].sort((a, b) => 
        results.dpt[a.name] - results.dpt[b.name]
    );

    sortedTasks.forEach(task => {
        const taskName = task.name;
        const duration = parseFloat(task.duration);
        const dpt = results.dpt[taskName];
        const dpl = results.dpl[taskName];
        const marge = results.marges[taskName];
        const isCritical = results.critical_path.includes(taskName);

        const row = document.createElement('tr');
        if (isCritical) {
            row.classList.add('critical-task');
        }

        row.innerHTML = `
            <td><strong>${taskName}</strong></td>
            <td>${duration.toFixed(2)}</td>
            <td>${dpt.toFixed(2)}</td>
            <td>${dpl.toFixed(2)}</td>
            <td>${marge.toFixed(2)}</td>
            <td>
                ${isCritical 
                    ? '<span class="badge bg-danger">Oui</span>' 
                    : '<span class="badge bg-secondary">Non</span>'}
            </td>
        `;

        tbody.appendChild(row);
    });
}

/**
 * Affiche les informations du projet
 */
function displayProjectInfo(results) {
    document.getElementById('projectDuration').textContent = 
        results.project_duration.toFixed(2) + ' unités de temps';
    
    document.getElementById('criticalCount').textContent = 
        results.critical_path.length + ' tâche(s)';
    
    const criticalPathText = results.critical_path.length > 0
        ? results.critical_path.join(' → ')
        : 'Aucun chemin critique';
    
    document.getElementById('criticalPath').textContent = criticalPathText;
}

/**
 * Gère l'export en PDF
 */
async function handleExportPdf() {
    if (!currentResults || tasks.length === 0) {
        alert('Veuillez d\'abord calculer le réseau MPM');
        return;
    }

    // Afficher un indicateur de chargement
    const btn = document.getElementById('exportPdfBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Génération...';

    try {
        const response = await fetch('/api/generate-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: tasks,
                results: currentResults
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Erreur lors de la génération du PDF');
        }

        // Télécharger le PDF
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reseau_mpm_${new Date().toISOString().slice(0,10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la génération du PDF: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * Efface toutes les tâches
 */
function handleClear() {
    if (tasks.length === 0) {
        return;
    }

    if (confirm('Êtes-vous sûr de vouloir effacer toutes les tâches ?')) {
        tasks = [];
        saveTasksToStorage();
        updateTasksDisplay();
        document.getElementById('calculateBtn').disabled = true;
        document.getElementById('resultsSection').style.display = 'none';
        currentResults = null;
    }
}

/**
 * Sauvegarde les tâches dans le localStorage
 */
function saveTasksToStorage() {
    try {
        localStorage.setItem('mpm_tasks', JSON.stringify(tasks));
    } catch (e) {
        console.warn('Impossible de sauvegarder dans localStorage:', e);
    }
}

/**
 * Charge les tâches depuis le localStorage
 */
function loadTasksFromStorage() {
    try {
        const saved = localStorage.getItem('mpm_tasks');
        if (saved) {
            tasks = JSON.parse(saved);
            updateTasksDisplay();
            document.getElementById('calculateBtn').disabled = tasks.length === 0;
        }
    } catch (e) {
        console.warn('Impossible de charger depuis localStorage:', e);
    }
}
