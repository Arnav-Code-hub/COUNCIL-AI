import { defineConfig } from "@playwright/test";
import { resolve } from "node:path";
export default defineConfig({
 testDir:"./e2e", workers:1,
 use:{baseURL:"http://127.0.0.1:8090",channel:process.env.PLAYWRIGHT_CHANNEL||undefined},
 webServer:{
  command:'"'+resolve("..", ".venv", process.platform==="win32"?"Scripts/python.exe":"bin/python")+'" -m uvicorn council.main:create_app --factory --app-dir .. --host 127.0.0.1 --port 8090',
  url:"http://127.0.0.1:8090/health",reuseExistingServer:false,
  env:{COUNCIL_DATA_DIR:"../private/browser-test",COUNCIL_MODE:"simulation",COUNCIL_SERVICE_KEY:"",COUNCIL_GEMINI_KEY:""},
 },
});
