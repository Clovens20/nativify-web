/**
 * Script Node.js pour synchroniser les utilisateurs
 * Usage: node scripts/sync-users.js [USER_ID]
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: './backend/.env' });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error('❌ Erreur: SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent être définis dans backend/.env');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

async function syncUser(userId) {
  try {
    // Vérifier si l'utilisateur existe dans users
    const { data: existingUser, error: checkError } = await supabase
      .from('users')
      .select('id, email, role')
      .eq('id', userId)
      .single();

    if (existingUser) {
      console.log('✅ L\'utilisateur existe déjà dans la table users:');
      console.log(`   Email: ${existingUser.email}`);
      console.log(`   Role: ${existingUser.role}`);
      return true;
    }

    if (checkError && checkError.code !== 'PGRST116') {
      throw checkError;
    }

    console.log(`⚠️  L'utilisateur ${userId} n'existe pas dans la table users`);
    console.log('💡 Pour créer l\'utilisateur, exécutez le script SQL sync-users.sql dans Supabase SQL Editor');
    
    return false;
  } catch (error) {
    console.error('❌ Erreur:', error.message);
    return false;
  }
}

async function main() {
  const userId = process.argv[2];
  
  if (!userId) {
    console.log('Usage: node scripts/sync-users.js USER_ID');
    console.log('\nExemple:');
    console.log('  node scripts/sync-users.js 6488b320-b39f-411d-849e-4d36a5145f70');
    console.log('\n💡 Pour synchroniser tous les utilisateurs, utilisez le script SQL sync-users.sql');
    process.exit(1);
  }

  console.log(`🔍 Vérification de l'utilisateur: ${userId}\n`);
  
  const success = await syncUser(userId);
  
  if (!success) {
    console.log('\n📝 Instructions pour résoudre le problème:');
    console.log('   1. Allez dans Supabase Dashboard → SQL Editor');
    console.log('   2. Exécutez le script scripts/sync-users.sql');
    console.log('   3. Ou exécutez cette requête SQL:');
    console.log(`\n   INSERT INTO public.users (id, email, name, role, status, created_at)`);
    console.log(`   SELECT id, email, COALESCE(raw_user_meta_data->>'name', email), 'user', 'active', created_at`);
    console.log(`   FROM auth.users WHERE id = '${userId}'`);
    console.log(`   ON CONFLICT (id) DO NOTHING;`);
  }
}

main();

