import { test, expect } from "@playwright/test";
const child = {
  id: "test-child",
  name: "Profil Uji",
  sex: "female",
  birth_date: "2026-01-01",
};
const envelope = (data: unknown) => ({ data, error: null });
test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const data = path.endsWith("/children")
      ? [child]
      : path.endsWith("/test-child")
        ? child
        : [];
    await route.fulfill({ json: envelope(data) });
  });
});
test("measurement sends numbers and null optional values", async ({ page }) => {
  let sent: any;
  await page.route("**/measurements", async (route) => {
    sent = route.request().postDataJSON();
    await route.fulfill({ json: envelope({ measurement: { id: "m" } }) });
  });
  await page.goto("/#/children/test-child/measurement");
  await page.getByLabel("Berat badan (kg)").fill("8.25");
  await page.getByLabel("Panjang / tinggi badan (cm)").fill("70.1");
  await page.getByLabel("Panjang / tinggi badan (cm)").clear();
  await page.getByRole("button", { name: "Simpan pengukuran" }).click();
  await expect.poll(() => sent?.weight_kg).toBe(8.25);
  expect(sent.length_height_cm).toBeNull();
  expect(sent.position).toBeNull();
  expect(sent.head_circumference_cm).toBeNull();
});
test("422 keeps values and exposes backend inline error", async ({ page }) => {
  await page.route("**/measurements", (route) =>
    route.fulfill({
      status: 422,
      json: {
        data: null,
        error: {
          code: "VALIDATION_ERROR",
          message: "Periksa pengukuran",
          fields: { weight_kg: "Pesan validasi uji" },
        },
      },
    }),
  );
  await page.goto("/#/children/test-child/measurement");
  await page.getByLabel("Berat badan (kg)").fill("8");
  await page.getByRole("button", { name: "Simpan pengukuran" }).click();
  await expect(page.getByRole("alert")).toContainText("Periksa pengukuran");
  await expect(page.getByLabel("Berat badan (kg)")).toHaveValue("8");
  await expect(page.locator("#weight_kg-error")).toHaveText(
    "Pesan validasi uji",
  );
});
test("report retains measurements and PB/U chart if status fails", async ({
  page,
}) => {
  await page.route("**/status", (route) =>
    route.fulfill({
      status: 503,
      json: { data: null, error: { message: "Evaluasi uji tidak tersedia" } },
    }),
  );
  await page.route("**/measurements", (route) =>
    route.fulfill({
      json: envelope([
        {
          id: "m",
          measured_at: "2026-11-01",
          weight_kg: 8,
          length_height_cm: 70,
        },
      ]),
    }),
  );
  await page.route("**/growth?*", (route) =>
    route.fulfill({
      json: envelope({
        indicator: "lhfa",
        x_unit: "days",
        points: [],
        reference: {
          x: [],
          sd_neg3: [],
          sd_neg2: [],
          median: [],
          sd_pos2: [],
          sd_pos3: [],
        },
      }),
    }),
  );
  await page.goto("/#/children/test-child/report");
  await expect(page.locator("tbody")).toContainText("8");
  await expect(page.locator(".chart svg")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Cetak / simpan PDF" }),
  ).toBeEnabled();
});
for (const width of [360, 768, 1440])
  test(`responsive layout ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/#/new");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      "Tambahkan profil anak",
    );
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: `test-results/frontend-${width}.png`,
      fullPage: true,
    });
  });
test("old response cannot replace a new child page", async ({ page }) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => (release = resolve));
  await page.route("**/children/slow", async (route) => {
    await gate;
    await route.fulfill({
      json: envelope({ ...child, id: "slow", name: "Profil Lama" }),
    });
  });
  await page.goto("/#/children/slow");
  await page.evaluate(() => {
    location.hash = "/children/test-child/measurement";
  });
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Catat pengukuran",
  );
  release();
  await expect(page.locator(".eyebrow").first()).toContainText("Profil Uji");
});
test("food counts are numbers and blank optional milk stays null", async ({
  page,
}) => {
  let sent: any;
  await page.route("**/food-recalls", async (route) => {
    if (route.request().method() === "POST") {
      sent = route.request().postDataJSON();
      await route.fulfill({
        status: 503,
        json: {
          data: null,
          error: {
            message: "Catatan sudah tersimpan. Evaluasi tidak tersedia.",
          },
        },
      });
    } else await route.fulfill({ json: envelope([]) });
  });
  await page.goto("/#/children/test-child/food");
  await page.getByLabel("Jumlah makan padat / lunak").fill("3");
  await page.getByLabel("Jumlah minum susu selain ASI (opsional)").fill("2");
  await page.getByLabel("Jumlah minum susu selain ASI (opsional)").clear();
  await page.getByRole("button", { name: "Simpan catatan makan" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Catatan sudah tersimpan",
  );
  expect(sent.meal_count).toBe(3);
  expect(sent.milk_feed_count).toBeNull();
  await expect(page.getByLabel("Jumlah makan padat / lunak")).toHaveValue("3");
});
test("delete requires confirmation and cancel keeps record", async ({
  page,
}) => {
  let deleted = false;
  await page.route("**/measurements", (route) =>
    route.fulfill({
      json: envelope([{ id: "m", measured_at: "2026-11-01", weight_kg: 8 }]),
    }),
  );
  await page.route("**/measurements/m", async (route) => {
    deleted = true;
    await route.fulfill({ json: envelope(null) });
  });
  await page.goto("/#/children/test-child/history");
  await page.getByRole("button", { name: /Hapus pengukuran/ }).click();
  await expect(page.getByRole("alertdialog")).toBeVisible();
  await page.getByRole("button", { name: "Batal", exact: true }).click();
  expect(deleted).toBe(false);
  await expect(page.getByRole("alertdialog")).not.toBeVisible();
});
test("guide filters use existing API query", async ({ page }) => {
  let query = "";
  await page.route("**/guides*", async (route) => {
    query = new URL(route.request().url()).search;
    await route.fulfill({ json: envelope([]) });
  });
  await page.goto("/#/guides");
  await page.getByLabel("Kategori").selectOption("mpasi");
  await page.getByLabel("Umur (bulan)", { exact: true }).fill("9");
  await page.getByRole("button", { name: "Terapkan" }).click();
  await expect.poll(() => query).toBe("?category=mpasi&age_months=9");
});
