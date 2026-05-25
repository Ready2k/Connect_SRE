const fs = require('fs');
const path = require('path');

const walk = (dir) => {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    file = path.join(dir, file);
    const stat = fs.statSync(file);
    if (stat && stat.isDirectory()) { 
      results = results.concat(walk(file));
    } else if (file.endsWith('.jsx')) {
      results.push(file);
    }
  });
  return results;
}

const files = walk('./src');
files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  // Remove standalone React import
  content = content.replace(/^import React from 'react';\r?\n/m, '');
  // Remove React from destructuring imports
  content = content.replace(/import React, \{\s*/g, 'import { ');
  // Remove unused lucide-react icons
  content = content.replace(/Settings, /g, '');
  content = content.replace(/AlertTriangle, /g, '');
  fs.writeFileSync(file, content, 'utf8');
});
