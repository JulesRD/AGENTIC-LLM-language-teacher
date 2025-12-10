import ollama

# Le client se connecte à son port local 11434, qui est tunnelisé vers le serveur
client = ollama.Client(host='http://localhost:11434') 

model_name = "qwen3:4b" # Assurez-vous que ce modèle est installé sur votre serveur

try:
    response = client.generate(
        model=model_name,
        prompt="Quelle est la capitale de la France ?",
    )
    print(response['response'])

except Exception as e:
    print(f"Erreur lors de l'appel à Ollama. Vérifiez que le tunnel SSH est actif. Erreur: {e}")