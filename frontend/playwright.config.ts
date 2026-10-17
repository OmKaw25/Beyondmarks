import { defineConfig } from '@playwright/test';
import { loadEnvConfig } from '@next/env';
import path from 'node:path';
loadEnvConfig(path.resolve(__dirname, '..'));
export default defineConfig({testDir:'./tests', timeout:60000, expect:{timeout:15000}, workers:2, use:{baseURL:'http://127.0.0.1:3000',trace:'off'}, webServer:{command:'npm run dev',url:'http://127.0.0.1:3000',reuseExistingServer:!process.env.CI,timeout:120000}});
