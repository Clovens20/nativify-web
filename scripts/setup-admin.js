/**
 * Script pour promouvoir un utilisateur en admin
 * 
 * Usage:
 *   node scripts/setup-admin.js your-email@example.com
 * 
 * OU avec curl:
 *   curl -X POST "http://localhost:8000/api/admin/setup?email=your-email@example.com&secret=nativiweb_admin_setup_2024"
 */

const email = process.argv[2];
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const SECRET = 'nativiweb_admin_setup_2024';

if (!email) {
  console.error('❌ Erreur: Email requis');
  console.log('\nUsage:');
  console.log('  node scripts/setup-admin.js your-email@example.com');
  console.log('\nOU avec curl:');
  console.log(`  curl -X POST "${BACKEND_URL}/api/admin/setup?email=your-email@example.com&secret=${SECRET}"`);
  process.exit(1);
}

async function setupAdmin() {
  try {
    const url = `${BACKEND_URL}/api/admin/setup?email=${encodeURIComponent(email)}&secret=${SECRET}`;
    
    console.log(`🔄 Promotion de ${email} en admin...`);
    console.log(`📍 URL: ${url}\n`);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`HTTP ${response.status}: ${error}`);
    }
    
    const result = await response.json();
    console.log('✅ SUCCÈS!');
    console.log(`   ${result.message}\n`);
    console.log('📝 Instructions:');
    console.log('   1. Déconnectez-vous de l\'application');
    console.log('   2. Reconnectez-vous avec cet email');
    console.log('   3. Vous devriez maintenant avoir accès à /admin\n');
    
  } catch (error) {
    console.error('❌ ERREUR:', error.message);
    if (error.message.includes('ECONNREFUSED') || error.message.includes('fetch failed')) {
      console.error('\n💡 Le backend n\'est pas démarré.');
      console.error('   Assurez-vous que le backend tourne sur', BACKEND_URL);
    }
    process.exit(1);
  }
}

setupAdmin();

