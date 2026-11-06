import {defineConfig} from '@playwright/test';
export default defineConfig({
 testDir:'./e2e',timeout:120000,expect:{timeout:20000},
 use:{baseURL:'http://127.0.0.1:5173',headless:true,viewport:{width:1440,height:1000}},
 webServer:[
  {
   command:'D:/SupplyScope/.venv/Scripts/python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000',
   cwd:'D:/SupplyScope',url:'http://127.0.0.1:8000/api/health',
   reuseExistingServer:true,timeout:60000,
  },
  {
   command:'node node_modules/vite/bin/vite.js --host 127.0.0.1',
   cwd:'D:/SupplyScope/frontend',url:'http://127.0.0.1:5173',
   reuseExistingServer:true,timeout:60000,
  },
 ],
 workers:1,reporter:[['list'],['json',{outputFile:'../reports/ui-tests.json'}]],
});
