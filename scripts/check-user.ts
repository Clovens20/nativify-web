/**
 * Script pour vérifier si un utilisateur existe dans auth.users et public.users
 * Usage: npx ts-node scripts/check-user.ts <user_id>
 */

import { createClient } from '@supabase/supabase-js'
import * as dotenv from 'dotenv'
import * as path from 'path'

dotenv.config({ path: path.join(__dirname, '..', '.env.local') })

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('❌ Erreur: NEXT_PUBLIC_SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent être définis dans .env.local')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseServiceKey)

async function checkUser(userId: string) {
  console.log(`\n🔍 Vérification de l'utilisateur: ${userId}\n`)

  try {
    // 1. Vérifier dans auth.users
    const { data: authUser, error: authError } = await supabase.auth.admin.getUserById(userId)
    
    if (authError) {
      console.error('❌ Erreur lors de la récupération dans auth.users:', authError.message)
      return
    }

    if (!authUser || !authUser.user) {
      console.log('❌ Utilisateur non trouvé dans auth.users')
      return
    }

    console.log('✅ Utilisateur trouvé dans auth.users:')
    console.log(`   - Email: ${authUser.user.email}`)
    console.log(`   - Créé le: ${authUser.user.created_at}`)
    console.log(`   - Métadonnées:`, authUser.user.user_metadata)

    // 2. Vérifier dans public.users
    const { data: publicUser, error: publicError } = await supabase
      .from('users')
      .select('*')
      .eq('id', userId)
      .single()

    if (publicError && publicError.code !== 'PGRST116') {
      console.error('❌ Erreur lors de la récupération dans public.users:', publicError.message)
      return
    }

    if (!publicUser) {
      console.log('\n⚠️  Utilisateur NON trouvé dans public.users')
      console.log('   → Il faut synchroniser cet utilisateur!')
      
      // Proposer de le créer
      const readline = require('readline').createInterface({
        input: process.stdin,
        output: process.stdout
      })

      readline.question('\n❓ Voulez-vous créer cet utilisateur dans public.users? (o/n): ', async (answer: string) => {
        if (answer.toLowerCase() === 'o' || answer.toLowerCase() === 'oui') {
          await syncUser(userId, authUser.user)
        }
        readline.close()
      })
    } else {
      console.log('\n✅ Utilisateur trouvé dans public.users:')
      console.log(`   - Email: ${publicUser.email}`)
      console.log(`   - Nom: ${publicUser.name}`)
      console.log(`   - Rôle: ${publicUser.role}`)
      console.log(`   - Statut: ${publicUser.status}`)
    }

  } catch (error: any) {
    console.error('❌ Erreur inattendue:', error.message)
  }
}

async function syncUser(userId: string, authUser: any) {
  try {
    const userData = {
      id: userId,
      email: authUser.email || '',
      name: authUser.user_metadata?.name || authUser.email?.split('@')[0] || 'User',
      role: 'user',
      status: 'active',
      created_at: authUser.created_at || new Date().toISOString()
    }

    const { data, error } = await supabase
      .from('users')
      .upsert(userData, { onConflict: 'id' })
      .select()

    if (error) {
      console.error('❌ Erreur lors de la synchronisation:', error.message)
    } else {
      console.log('\n✅ Utilisateur synchronisé avec succès dans public.users!')
      console.log('   Données:', data[0])
    }
  } catch (error: any) {
    console.error('❌ Erreur lors de la synchronisation:', error.message)
  }
}

const userId = process.argv[2]

if (!userId) {
  console.error('❌ Erreur: ID utilisateur requis')
  console.log('\nUsage: npx ts-node scripts/check-user.ts <user_id>')
  process.exit(1)
}

checkUser(userId)

