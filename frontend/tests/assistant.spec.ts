import { test, expect } from "@playwright/test";
const child = { id: "test-child", name: "Profil Uji", sex: "female", birth_date: "2026-01-01" };
const status = { level: "yellow", level_label: "Perlu perhatian", reasons: [], next_kpsp: null, latest: null, diet: null };
const envelope = (data: unknown) => ({ data, error: null });
function routes(page: any, enabled: boolean) {
  return page.route("**/api/v1/**", (route: any) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/auth/me")) return route.fulfill({ status: 404 });
    if (path.endsWith("/assistant") && route.request().method() === "GET")
      return route.fulfill({ json: envelope({ enabled }) });
    if (path.endsWith("/test-child")) return route.fulfill({ json: envelope(child) });
    if (path.endsWith("/status")) return route.fulfill({ json: envelope(status) });
    return route.fulfill({ json: envelope([]) });
  });
}
test("assistant is absent when the backend says disabled", async ({ page }) => {
  await routes(page, false);
  await page.goto("/#/children/test-child");
  await expect(page.getByText("Perlu perhatian").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Tanya asisten" })).toHaveCount(0);
});
test("assistant sends question with history and shows backend reply", async ({ page }) => {
  await routes(page, true);
  const bodies: any[] = [];
  await page.route("**/test-child/assistant", (route) => {
    bodies.push(route.request().postDataJSON());
    return route.fulfill({ json: envelope({ reply: `JAWABAN UJI ${bodies.length}`, grounded: true }) });
  });
  await page.goto("/#/children/test-child");
  await page.getByRole("button", { name: "Jelaskan status anak saya" }).click();
  await expect(page.getByText("JAWABAN UJI 1")).toBeVisible();
  await page.getByLabel("Pertanyaan untuk asisten").fill("Pertanyaan kedua");
  await page.getByLabel("Pertanyaan untuk asisten").press("Enter");
  await expect(page.getByText("JAWABAN UJI 2")).toBeVisible();
  expect(bodies[0]).toEqual({ message: "Jelaskan status anak saya", history: [] });
  expect(bodies[1].history).toEqual([
    { role: "user", content: "Jelaskan status anak saya" },
    { role: "assistant", content: "JAWABAN UJI 1" },
  ]);
});
test("assistant failure keeps the question and shows a quiet note", async ({ page }) => {
  await routes(page, true);
  await page.route("**/test-child/assistant", (route) =>
    route.fulfill({ status: 503, json: { data: null, error: { code: "LLM_UNAVAILABLE", message: "x", fields: null } } }),
  );
  await page.goto("/#/children/test-child");
  await page.getByLabel("Pertanyaan untuk asisten").fill("Halo");
  await page.getByRole("button", { name: "Kirim" }).click();
  await expect(page.getByText("Asisten sementara tidak tersedia. Coba lagi nanti.")).toBeVisible();
  await expect(page.getByLabel("Pertanyaan untuk asisten")).toHaveValue("Halo");
});
