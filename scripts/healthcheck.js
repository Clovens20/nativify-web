#!/usr/bin/env node

/**
 * Health check script for production deployment
 * Usage: node scripts/healthcheck.js
 */

const http = require('http');

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const FRONTEND_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

async function checkHealth(endpoint, name) {
  return new Promise((resolve) => {
    const url = new URL(endpoint);
    const options = {
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname,
      method: 'GET',
      timeout: 5000,
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        if (res.statusCode === 200 || res.statusCode === 503) {
          try {
            const json = JSON.parse(data);
            resolve({
              name,
              status: json.status || (res.statusCode === 200 ? 'healthy' : 'unhealthy'),
              code: res.statusCode,
              details: json,
            });
          } catch {
            resolve({
              name,
              status: res.statusCode === 200 ? 'healthy' : 'unhealthy',
              code: res.statusCode,
            });
          }
        } else {
          resolve({
            name,
            status: 'unhealthy',
            code: res.statusCode,
            error: `HTTP ${res.statusCode}`,
          });
        }
      });
    });

    req.on('error', (error) => {
      resolve({
        name,
        status: 'unhealthy',
        error: error.message,
      });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({
        name,
        status: 'unhealthy',
        error: 'Request timeout',
      });
    });

    req.end();
  });
}

async function main() {
  console.log('🔍 Checking health status...\n');

  const [backend, frontend] = await Promise.all([
    checkHealth(`${BACKEND_URL}/health`, 'Backend API'),
    checkHealth(`${FRONTEND_URL}`, 'Frontend'),
  ]);

  console.log(`Backend API: ${backend.status === 'healthy' ? '✅' : '❌'} ${backend.status}`);
  if (backend.error) {
    console.log(`  Error: ${backend.error}`);
  }
  if (backend.details) {
    console.log(`  Database: ${backend.details.database || 'unknown'}`);
  }

  console.log(`\nFrontend: ${frontend.status === 'healthy' ? '✅' : '❌'} ${frontend.status}`);
  if (frontend.error) {
    console.log(`  Error: ${frontend.error}`);
  }

  const allHealthy = backend.status === 'healthy' && frontend.status === 'healthy';

  console.log(`\n${allHealthy ? '✅ All services are healthy' : '❌ Some services are unhealthy'}`);

  process.exit(allHealthy ? 0 : 1);
}

main().catch((error) => {
  console.error('Health check failed:', error);
  process.exit(1);
});

