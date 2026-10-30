import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
afterEach(()=>vi.unstubAllGlobals());
function mockApi(fail=false) {
 vi.stubGlobal("fetch",vi.fn(async (url:string)=>{
  if(url==="/health") return new Response(JSON.stringify({mode:"simulation"}));
  if(fail) return new Response(JSON.stringify({detail:"Service authentication required."}),{status:401});
  return new Response("[]");
 }));
}
it("labels simulation and provides all five reviewers",async()=>{
 mockApi(); render(<App/>);
 await screen.findByText(/Simulation workspace/);
 expect(screen.getAllByText("Evidence examiner").length).toBeGreaterThan(0);
 expect(screen.getByLabelText("Project title")).toBeTruthy();
 expect(screen.getByRole("button",{name:/Generate council report/})).toBeTruthy();
});
it("loads sample evidence without presenting a completed review",async()=>{
 mockApi(); render(<App/>);
 fireEvent.click(screen.getByRole("button",{name:"Load example"}));
 expect((screen.getByLabelText("Project title") as HTMLInputElement).value).toMatch(/Pump/);
 expect(screen.queryByText("Download PDF")).toBeNull();
});
it("surfaces server errors",async()=>{
 mockApi(true); render(<App/>);
 await waitFor(()=>expect(screen.getByRole("alert").textContent).toMatch(/authentication/));
});
it("rejects binary file extensions before submission",async()=>{
 mockApi(); render(<App/>);
 const file = new File(["bad"],"run.exe",{type:"application/octet-stream"});
 fireEvent.change(screen.getByLabelText("Supporting text and source files"),{target:{files:[file]}});
 await waitFor(()=>expect(screen.getByRole("alert").textContent).toMatch(/Unsupported/));
});
