#!/usr/bin/env node

/**
 * Pre-production verification script
 * Vérifie que toutes les configurations sont correctes avant le déploiement
 */

const fs = require('fs');
const path = require('path');

const errors = [];
const warnings = [];

console.log('🔍 Vérification de la préparation production...\n');

// Vérifier les fichiers .env.example
console.log('📋 Vérification des fichiers de configuration...');
if (!fs.existsSync('.env.example')) {
  errors.push('Fichier .env.example manquant à la racine');
} else {
  console.log('✅ .env.example existe');
}

if (!fs.existsSync('backend/.env.example')) {
  errors.push('Fichier backend/.env.example manquant');
} else {
  console.log('✅ backend/.env.example existe');
}

// Vérifier que .env n'est pas commité
console.log('\n🔐 Vérification de la sécurité...');
if (fs.existsSync('.gitignore')) {
  const gitignore = fs.readFileSync('.gitignore', 'utf8');
  if (!gitignore.includes('.env')) {
    warnings.push('.env devrait être dans .gitignore');
  } else {
    console.log('✅ .env est dans .gitignore');
  }
} else {
  warnings.push('.gitignore manquant');
}

// Vérifier les Dockerfiles
console.log('\n🐳 Vérification Docker...');
if (!fs.existsSync('Dockerfile')) {
  errors.push('Dockerfile manquant');
} else {
  console.log('✅ Dockerfile existe');
}

if (!fs.existsSync('backend/Dockerfile')) {
  errors.push('backend/Dockerfile manquant');
} else {
  console.log('✅ backend/Dockerfile existe');
}

if (!fs.existsSync('docker-compose.yml')) {
  errors.push('docker-compose.yml manquant');
} else {
  console.log('✅ docker-compose.yml existe');
}

// Vérifier next.config.js
console.log('\n⚙️  Vérification de la configuration...');
if (fs.existsSync('next.config.js')) {
  const nextConfig = fs.readFileSync('next.config.js', 'utf8');
  if (!nextConfig.includes('output: \'standalone\'')) {
    warnings.push('next.config.js ne contient pas "output: standalone" (recommandé pour Docker)');
  } else {
    console.log('✅ next.config.js configuré pour Docker');
  }
  
  if (!nextConfig.includes('removeConsole')) {
    warnings.push('next.config.js ne supprime pas les console.log en production');
  } else {
    console.log('✅ console.log sera supprimé en production');
  }
} else {
  errors.push('next.config.js manquant');
}

// Vérifier package.json
console.log('\n📦 Vérification des scripts...');
if (fs.existsSync('package.json')) {
  const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  
  if (!pkg.scripts.build) {
    errors.push('Script "build" manquant dans package.json');
  } else {
    console.log('✅ Script "build" existe');
  }
  
  if (!pkg.scripts.start) {
    errors.push('Script "start" manquant dans package.json');
  } else {
    console.log('✅ Script "start" existe');
  }
  
  if (!pkg.scripts['start:production']) {
    warnings.push('Script "start:production" manquant (recommandé)');
  } else {
    console.log('✅ Script "start:production" existe');
  }
} else {
  errors.push('package.json manquant');
}

// Résumé
console.log('\n' + '='.repeat(50));
console.log('📊 RÉSUMÉ\n');

if (errors.length === 0 && warnings.length === 0) {
  console.log('✅ Tous les checks sont passés ! Le projet est prêt pour la production.\n');
  process.exit(0);
} else {
  if (errors.length > 0) {
    console.log('❌ ERREURS (DOIVENT être corrigées) :\n');
    errors.forEach((error, i) => {
      console.log(`  ${i + 1}. ${error}`);
    });
    console.log('');
  }
  
  if (warnings.length > 0) {
    console.log('⚠️  AVERTISSEMENTS (recommandés) :\n');
    warnings.forEach((warning, i) => {
      console.log(`  ${i + 1}. ${warning}`);
    });
    console.log('');
  }
  
  console.log('⚠️  Corrigez les erreurs avant de déployer en production.\n');
  process.exit(errors.length > 0 ? 1 : 0);
}

