// Simple script to inject API URL into index.html for Vercel deployment
// This runs at build time to replace the placeholder with the actual Railway URL

const fs = require('fs');
const path = require('path');

const apiUrl = process.env.API_URL || process.env.VITE_API_URL || 'https://your-app.railway.app';

// Handle both cases: running from project root or from frontend directory
// If running from frontend (Vercel with root directory set), use current dir
// Otherwise, go up one level to frontend
let indexPath;
if (fs.existsSync(path.join(process.cwd(), 'index.html'))) {
  // Running from frontend directory
  indexPath = path.join(process.cwd(), 'index.html');
} else if (fs.existsSync(path.join(process.cwd(), 'frontend', 'index.html'))) {
  // Running from project root
  indexPath = path.join(process.cwd(), 'frontend', 'index.html');
} else {
  // Fallback: try relative to script location
  indexPath = path.join(__dirname, '..', 'frontend', 'index.html');
}

if (fs.existsSync(indexPath)) {
  let content = fs.readFileSync(indexPath, 'utf8');
  
  // Replace the placeholder API URL
  content = content.replace(
    /window\.API_URL = window\.API_URL \|\| 'https:\/\/your-app\.railway\.app';/g,
    `window.API_URL = window.API_URL || '${apiUrl}';`
  );
  
  fs.writeFileSync(indexPath, content, 'utf8');
  console.log(`✓ Injected API URL: ${apiUrl}`);
} else {
  console.error('✗ index.html not found');
  process.exit(1);
}

