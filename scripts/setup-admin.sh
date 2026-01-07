#!/bin/bash
# Script pour promouvoir un utilisateur en admin

EMAIL="$1"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
SECRET="nativiweb_admin_setup_2024"

if [ -z "$EMAIL" ]; then
    echo "❌ Erreur: Email requis"
    echo ""
    echo "Usage:"
    echo "  ./scripts/setup-admin.sh your-email@example.com"
    echo ""
    echo "OU avec curl:"
    echo "  curl -X POST \"$BACKEND_URL/api/admin/setup?email=your-email@example.com&secret=$SECRET\""
    exit 1
fi

echo "🔄 Promotion de $EMAIL en admin..."
echo "📍 URL: $BACKEND_URL/api/admin/setup"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/admin/setup?email=$(echo "$EMAIL" | sed 's/@/%40/g')&secret=$SECRET")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo "✅ SUCCÈS!"
    echo "   $body"
    echo ""
    echo "📝 Instructions:"
    echo "   1. Déconnectez-vous de l'application"
    echo "   2. Reconnectez-vous avec cet email"
    echo "   3. Vous devriez maintenant avoir accès à /admin"
else
    echo "❌ ERREUR (HTTP $http_code):"
    echo "   $body"
    if echo "$body" | grep -q "ECONNREFUSED\|Connection refused"; then
        echo ""
        echo "💡 Le backend n'est pas démarré."
        echo "   Assurez-vous que le backend tourne sur $BACKEND_URL"
    fi
    exit 1
fi

