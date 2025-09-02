#!/bin/bash

echo "🚄 Raylix Database Seed"
echo "======================="

# Controlla se i file JSON esistono
if [ ! -d "static_data" ]; then
    echo "❌ Cartella static_data non trovata!"
    echo "Crea i file JSON necessari prima di continuare."
    exit 1
fi

echo "🐳 Avvio containers..."
docker-compose up --build

echo ""
echo "✅ Seed completato!"
echo "🔧 Adminer: http://localhost:8080"
echo "📊 PostgreSQL: localhost:5432"