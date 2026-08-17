const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'frontend', 'app.js');
let content = fs.readFileSync(filePath, 'utf8');

const apiUrl = process.env.API_URL || 'http://localhost:8000';
content = content.replace(/__API_URL__/g, apiUrl);

fs.writeFileSync(filePath, content, 'utf8');
console.log('Successfully injected API_URL into frontend/app.js');
