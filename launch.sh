#!/bin/bash

# Script de lancement pour les agents du language-teacher
# Utilisation: ./launch.sh <agent_type> [--help]

# Variables d'environnement
export MISTRAL_API_KEY="eBeRjFyEQSDuBOfBjywibb7a08LvnEbg"
# Ajoutez ici d'autres variables d'environnement si nécessaire

# Fonction d'aide
show_help() {
    echo "Usage: $0 <agent_type> [--help]"
    echo ""
    echo "Agent types:"
    echo "  dialogue      - Lance l'agent de dialogue"
    echo "  coordinator   - Lance l'agent coordinateur"
    echo "  exercises     - Lance l'agent d'exercices"
    echo "  planner       - Lance l'agent planificateur"
    echo ""
    echo "Options:"
    echo "  --help        - Affiche cette aide"
    echo ""
    echo "Variables d'environnement définies:"
    echo "  MISTRAL_API_KEY - Clé API pour Mistral"
}

# Vérifier les arguments
if [ $# -eq 0 ] || [ "$1" == "--help" ]; then
    show_help
    exit 0
fi

AGENT_TYPE=$1

# Définir le fichier Python à lancer en fonction du type d'agent
case $AGENT_TYPE in
    dialogue)
        AGENT_FILE="src/agents/dialogue_agent.py"
        ;;
    coordinator)
        AGENT_FILE="src/agents/coordinator_agent.py"
        ;;
    exercises)
        AGENT_FILE="src/agents/exercises_agent.py"
        ;;
    planner)
        AGENT_FILE="src/agents/planner_agent.py"
        ;;
    *)
        echo "Erreur: Type d'agent inconnu '$AGENT_TYPE'"
        echo ""
        show_help
        exit 1
        ;;
esac

# Vérifier si le fichier existe
if [ ! -f "$AGENT_FILE" ]; then
    echo "Erreur: Fichier $AGENT_FILE introuvable"
    exit 1
fi

# Lancer l'agent
echo "Lancement de l'agent $AGENT_TYPE..."
python3 $AGENT_FILE