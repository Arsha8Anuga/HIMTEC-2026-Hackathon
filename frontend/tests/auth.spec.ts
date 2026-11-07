import { expect, test, type Page, type Route } from "@playwright/test";

const user = { id: "parent", name: "Nara", email: "nara@example.test", role: "parent" };
const token = "session-test";
const key = "pantau.access_token";
const bearer = "Bearer " + token;

function reply(route: Route, status: number, data: unknown = null, fields?: Record<string, string>) {
  return route.fulfill({ status, json: {
    data, error: status >= 400 ? { message: "Permintaan gagal", fields } : null,
  } });
}
async function otp(page: Page) {
  await page.route("**/api/v1/auth/me", route =>
    route.request().headers().authorization === bearer ? reply(route, 200, user) : reply(route, 401));
  await page.route("**/api/v1/children", route => reply(route, 200, []));
}
async function existingSession(page: Page) {
  await otp(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Masuk" })).toBeFocused();
  await page.evaluate(([k, t]) => sessionStorage.setItem(k, t), [key, token]);
  await page.reload();
  await expect(page.getByRole("button", { name: "Keluar" })).toBeVisible();
}

test("demo 404 menampilkan beranda tanpa login atau Bearer lama", async ({ page }) => {
  await page.addInitScript(([k,t]) => sessionStorage.setItem(k,t), [key,token]);
  await page.route("**/api/v1/auth/me", route => route.fulfill({ status: 404, body: "Not Found" }));
  await page.route("**/api/v1/children", route => {
    expect(route.request().headers().authorization).toBeUndefined();
    return reply(route, 200, []);
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Catatan tumbuh kembang" })).toBeFocused();
  await expect(page.getByRole("heading", { name: "Masuk" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Keluar" })).toHaveCount(0);
});

test("daftar, kirim ulang setelah 60 detik, lalu akses beranda dengan Bearer", async ({ page }) => {
  await otp(page);
  await page.clock.install();
  let sends = 0;
  await page.route("**/auth/register", route => {
    expect(route.request().postDataJSON()).toEqual({ name: user.name, email: user.email });
    return reply(route, 202, { challenge_id: "challenge-" + ++sends, expires_in: 300 });
  });
  await page.route("**/auth/verify", route => {
    expect(route.request().postDataJSON()).toEqual({ challenge_id: "challenge-2", code: "012345" });
    return reply(route, 200, { access_token: token, token_type: "Bearer", expires_in: 86400, user });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Daftar" }).click();
  await expect(page.getByRole("heading", { name: "Daftar" })).toBeFocused();
  await page.getByLabel("Nama").fill(user.name);
  await page.getByLabel("Email").fill(user.email);
  await page.getByRole("button", { name: "Kirim kode" }).click();
  await expect(page.getByRole("heading", { name: "Masukkan kode" })).toBeFocused();
  const resend = page.getByRole("button", { name: /Kirim ulang kode/ });
  await expect(resend).toBeDisabled();
  await page.clock.fastForward(60000);
  await resend.click();
  const code = page.getByLabel("Kode 6 angka");
  await expect(code).toBeEnabled();
  await code.fill("012345");
  const request = page.waitForRequest("**/api/v1/children");
  await page.getByRole("button", { name: "Masuk", exact: true }).click();
  expect((await request).headers().authorization).toBe(bearer);
  await expect(page.getByRole("banner")).toContainText(user.name);
  await page.reload();
  await expect(page.getByRole("button", { name: "Keluar" })).toBeVisible();
});

test("401 pada route bisnis mengakhiri sesi", async ({ page }) => {
  await existingSession(page);
  await page.route("**/api/v1/guides", route => reply(route, 401));
  await page.getByRole("link", { name: /Panduan$/ }).first().click();
  await expect(page.getByRole("heading", { name: "Masuk" })).toBeFocused();
  await expect(page.getByRole("alert")).toContainText("Sesi telah berakhir");
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
});

test("429 menjelaskan kapan dapat meminta kode lagi", async ({ page }) => {
  await otp(page);
  await page.route("**/auth/login", route => {
    expect(route.request().postDataJSON()).toEqual({ email: user.email });
    return reply(route, 429);
  });
  await page.goto("/");
  await page.getByLabel("Email").fill(user.email);
  await page.getByRole("button", { name: "Kirim kode" }).click();
  await expect(page.getByRole("alert")).toContainText("Terlalu banyak permintaan");
  await expect(page.getByRole("button", { name: /Kirim kode/ })).toBeDisabled();
});

test("keluar mengirim Bearer dan menghapus token hingga halaman dimuat ulang", async ({ page }) => {
  await existingSession(page);
  await page.route("**/auth/logout", route => {
    expect(route.request().method()).toBe("POST");
    expect(route.request().headers().authorization).toBe(bearer);
    return reply(route, 200, { logged_out: true });
  });
  await page.getByRole("button", { name: "Keluar" }).click();
  await expect(page.getByRole("heading", { name: "Masuk" })).toBeFocused();
  expect(await page.evaluate(k => sessionStorage.getItem(k), key)).toBeNull();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Masuk" })).toBeFocused();
});

test("login tetap berjalan saat storage diblokir dan kode salah dapat diperbaiki", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "sessionStorage", { get() { throw new Error("Storage diblokir"); } });
  });
  await otp(page);
  await page.route("**/auth/login", route => reply(route, 202, { challenge_id: "login", expires_in: 300 }));
  await page.route("**/auth/verify", route =>
    route.request().postDataJSON().code === "000001"
      ? reply(route, 200, { access_token: token, token_type: "Bearer", expires_in: 86400, user })
      : reply(route, 401));
  await page.goto("/");
  await page.getByLabel("Email").fill(user.email);
  await page.getByRole("button", { name: "Kirim kode" }).click();
  const code = page.getByLabel("Kode 6 angka");
  await code.fill("123456");
  await page.getByRole("button", { name: "Masuk" }).click();
  await expect(code).toHaveAccessibleDescription(/Kode salah/);
  await expect(code).toHaveValue("");
  await code.fill("000001");
  const request = page.waitForRequest("**/api/v1/children");
  await page.getByRole("button", { name: "Masuk" }).click();
  expect((await request).headers().authorization).toBe(bearer);
});

test("422 mengaitkan pesan validasi dengan isian email", async ({ page }) => {
  await otp(page);
  await page.route("**/auth/login", route => reply(route, 422, null, { email: "Periksa alamat email." }));
  await page.goto("/");
  const email = page.getByLabel("Email");
  await email.fill(user.email);
  await page.getByRole("button", { name: "Kirim kode" }).click();
  await expect(email).toHaveAccessibleDescription("Periksa alamat email.");
  await expect(email).toHaveAttribute("aria-invalid", "true");
});
