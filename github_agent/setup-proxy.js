#!/usr/bin/env node

/**
 * Automatic Proxy Configuration Script
 * Detects system proxy and configures npm, git, and environment variables
 * Works on Windows, macOS, and Linux
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function exec(command, silent = false) {
  try {
    const output = execSync(command, { encoding: 'utf8', stdio: silent ? 'pipe' : 'inherit' });
    return output ? output.trim() : '';
  } catch (error) {
    if (!silent) {
      log(`Error executing: ${command}`, colors.red);
      log(error.message, colors.red);
    }
    return null;
  }
}

function detectProxy() {
  log('\n🔍 Detecting proxy settings...', colors.cyan);

  let proxy = null;

  // Check environment variables first
  if (process.env.HTTP_PROXY || process.env.http_proxy) {
    proxy = process.env.HTTP_PROXY || process.env.http_proxy;
    log(`Found in environment: ${proxy}`, colors.green);
    return proxy;
  }

  // Platform-specific detection
  if (os.platform() === 'win32') {
    // Windows: Check registry
    try {
      const regQuery = 'reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer';
      const output = exec(regQuery, true);
      if (output && output.includes('ProxyServer')) {
        const match = output.match(/ProxyServer\s+REG_SZ\s+(.+)/);
        if (match) {
          proxy = match[1].trim();
          // Add http:// if not present
          if (!proxy.startsWith('http')) {
            proxy = `http://${proxy}`;
          }
          log(`Found in Windows registry: ${proxy}`, colors.green);
          return proxy;
        }
      }
    } catch (e) {
      // Registry query failed
    }
  } else if (os.platform() === 'darwin') {
    // macOS: Check network settings
    try {
      const output = exec('networksetup -getwebproxy Wi-Fi', true);
      if (output && output.includes('Enabled: Yes')) {
        const serverMatch = output.match(/Server: (.+)/);
        const portMatch = output.match(/Port: (\d+)/);
        if (serverMatch && portMatch) {
          proxy = `http://${serverMatch[1].trim()}:${portMatch[1].trim()}`;
          log(`Found in macOS network settings: ${proxy}`, colors.green);
          return proxy;
        }
      }
    } catch (e) {
      // Network settings query failed
    }
  } else {
    // Linux: Check common environment variables and configs
    const configs = [
      '/etc/environment',
      `${os.homedir()}/.bashrc`,
      `${os.homedir()}/.profile`,
    ];

    for (const configFile of configs) {
      try {
        if (fs.existsSync(configFile)) {
          const content = fs.readFileSync(configFile, 'utf8');
          const match = content.match(/(?:export\s+)?https?_proxy=["']?([^"'\s]+)["']?/i);
          if (match) {
            proxy = match[1];
            log(`Found in ${configFile}: ${proxy}`, colors.green);
            return proxy;
          }
        }
      } catch (e) {
        // Config file read failed
      }
    }
  }

  return proxy;
}

function promptProxy() {
  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    readline.question('\nEnter proxy URL (e.g., http://proxy.company.com:8080): ', (answer) => {
      readline.close();
      resolve(answer.trim());
    });
  });
}

function configureNpm(proxy) {
  log('\n🔧 Configuring npm...', colors.cyan);

  const commands = [
    `npm config set proxy ${proxy}`,
    `npm config set https-proxy ${proxy}`,
    'npm config set strict-ssl false',
    'npm config set registry http://registry.npmjs.org/',
  ];

  for (const cmd of commands) {
    exec(cmd);
  }

  log('✅ npm configured', colors.green);
}

function configureGit(proxy) {
  log('\n🔧 Configuring git...', colors.cyan);

  const commands = [
    `git config --global http.proxy ${proxy}`,
    `git config --global https.proxy ${proxy}`,
    'git config --global http.sslVerify false',
  ];

  for (const cmd of commands) {
    exec(cmd);
  }

  log('✅ git configured', colors.green);
}

function createEnvFile(proxy) {
  log('\n🔧 Creating .env.proxy file...', colors.cyan);

  const envContent = `# Proxy Configuration
HTTP_PROXY=${proxy}
HTTPS_PROXY=${proxy}
NODE_TLS_REJECT_UNAUTHORIZED=0
PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING=1
`;

  fs.writeFileSync('.env.proxy', envContent);
  log('✅ Created .env.proxy', colors.green);
}

function createHelperScripts(proxy) {
  log('\n🔧 Creating helper scripts...', colors.cyan);

  // Create prisma-proxy script
  if (os.platform() === 'win32') {
    const batchContent = `@echo off
set HTTP_PROXY=${proxy}
set HTTPS_PROXY=${proxy}
set NODE_TLS_REJECT_UNAUTHORIZED=0
set PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING=1
npx prisma %*
`;
    fs.writeFileSync('prisma-proxy.bat', batchContent);
    log('✅ Created prisma-proxy.bat', colors.green);
  } else {
    const bashContent = `#!/bin/bash
export HTTP_PROXY=${proxy}
export HTTPS_PROXY=${proxy}
export NODE_TLS_REJECT_UNAUTHORIZED=0
export PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING=1
npx prisma "$@"
`;
    fs.writeFileSync('prisma-proxy.sh', bashContent);
    fs.chmodSync('prisma-proxy.sh', '755');
    log('✅ Created prisma-proxy.sh', colors.green);
  }
}

function showSummary(proxy) {
  log('\n═══════════════════════════════════════════════════', colors.cyan);
  log('✅ Proxy Configuration Complete!', colors.green);
  log('═══════════════════════════════════════════════════', colors.cyan);

  log(`\n📋 Configured proxy: ${proxy}`, colors.yellow);

  log('\n✅ Configured:', colors.green);
  log('  • npm (proxy, https-proxy, strict-ssl)');
  log('  • git (http.proxy, https.proxy, sslVerify)');
  log('  • Created .env.proxy file');
  log('  • Created helper scripts');

  log('\n🚀 Next Steps:', colors.yellow);
  log('\n1. Test npm:');
  log('   npm install');

  log('\n2. Test Prisma:');
  if (os.platform() === 'win32') {
    log('   prisma-proxy.bat generate');
  } else {
    log('   ./prisma-proxy.sh generate');
  }

  log('\n3. Or set environment variables for current session:');
  if (os.platform() === 'win32') {
    log(`   $env:HTTP_PROXY = "${proxy}"`);
    log(`   $env:HTTPS_PROXY = "${proxy}"`);
    log('   $env:NODE_TLS_REJECT_UNAUTHORIZED = "0"');
  } else {
    log(`   export HTTP_PROXY="${proxy}"`);
    log(`   export HTTPS_PROXY="${proxy}"`);
    log('   export NODE_TLS_REJECT_UNAUTHORIZED=0');
  }

  log('\n4. Then run:');
  log('   npm run db:generate');

  log('\n⚠️  Note: SSL verification is disabled for development.', colors.yellow);
  log('   For production, get the corporate root certificate from IT.\n');
}

async function main() {
  log('═══════════════════════════════════════════════════', colors.cyan);
  log('🔧 Automatic Proxy Configuration', colors.cyan);
  log('═══════════════════════════════════════════════════', colors.cyan);

  let proxy = detectProxy();

  if (!proxy) {
    log('❌ Could not auto-detect proxy settings', colors.yellow);
    proxy = await promptProxy();
  }

  if (!proxy) {
    log('❌ No proxy configured. Exiting.', colors.red);
    process.exit(1);
  }

  // Ensure proxy has protocol
  if (!proxy.startsWith('http://') && !proxy.startsWith('https://')) {
    proxy = `http://${proxy}`;
  }

  configureNpm(proxy);
  configureGit(proxy);
  createEnvFile(proxy);
  createHelperScripts(proxy);
  showSummary(proxy);
}

// Run if called directly
if (require.main === module) {
  main().catch((error) => {
    log(`\n❌ Error: ${error.message}`, colors.red);
    process.exit(1);
  });
}

module.exports = { detectProxy, configureNpm, configureGit };
