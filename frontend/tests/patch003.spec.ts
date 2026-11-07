import { test, expect } from "@playwright/test";
const child = {
  id: "test-child",
  name: "Profil Uji",
  sex: "female",
  birth_date: "2026-01-01",
};
const envelope = (data: unknown) => ({ data, error: null });
// Synthetic protocol fixtures only: these values are not WHO reference data.
const reference = {
  x: [0, 30, 60],
  sd_neg3: [1, 2, 3],
  sd_neg2: [2, 3, 4],
  median: [3, 4, 5],
  sd_pos2: [4, 5, 6],
  sd_pos3: [5, 6, 7],
};
const growth = {
  indicator: "lhfa",
  x_unit: "days",
  reference,
  points: [
    {
      measurement_id: "m",
      measured_at: "2026-02-01",
      x: 31,
      value: 4,
      z: null,
      flagged: false,
    },
  ],
};
test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    return route.fulfill({
      json: envelope(
        path.endsWith("/children")
          ? [child]
          : path.endsWith("/test-child")
            ? child
            : [],
      ),
    });
  });
});
test("home exposes children and due reminders without waiting for all statuses", async ({
  page,
}) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => (release = resolve));
  await page.route("**/status", async (route) => {
    await gate;
    await route.fulfill({
      json: envelope({
        level: "yellow",
        level_label: "Perlu perhatian",
        next_kpsp: { due: true, questionnaire_age_months: 9 },
        reasons: [{ code: "NO_RECENT_FOOD_RECALL" }],
      }),
    });
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Profil Uji" })).toBeVisible();
  await expect(page.getByText("Memuat status…")).toBeVisible();
  release();
  await expect(
    page.getByText("Perlu perhatian", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Skrining perkembangan jatuh tempo"),
  ).toBeVisible();
  await expect(page.getByText("Isi catatan makan kemarin")).toBeVisible();
});
test("late save completion does not navigate away from the new page", async ({
  page,
}) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => (release = resolve));
  await page.route("**/measurements", async (route) => {
    await gate;
    await route.fulfill({ json: envelope({ measurement: { id: "m" } }) });
  });
  await page.goto("/#/children/test-child/measurement");
  await page.getByLabel("Berat badan (kg)").fill("8");
  await page.getByRole("button", { name: "Simpan pengukuran" }).click();
  await page
    .getByRole("link", { name: "Panduan", exact: true })
    .first()
    .click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Panduan untuk keseharian",
  );
  const completed = page.waitForResponse((r) =>
    r.url().endsWith("/measurements"),
  );
  release();
  await completed;
  await expect(page).toHaveURL(/#\/guides$/);
  await expect(page.getByText("Data berhasil disimpan.")).toHaveCount(0);
});
test("chart has keyboard-operable legend and accessible data table", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.route("**/growth?*", (route) =>
    route.fulfill({ json: envelope(growth) }),
  );
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/#/children/test-child/growth");
  await expect(page.locator(".chart svg")).toBeVisible();
  const median = page.getByRole("checkbox", { name: "Median", exact: true });
  await median.focus();
  await page.keyboard.press("Space");
  await expect(median).not.toBeChecked();
  await page.keyboard.press("Space");
  await expect(median).toBeChecked();
  await page
    .getByText("Data pengukuran pada kurva (1)", { exact: true })
    .click();
  await expect(page.locator("tbody")).toContainText("4");
  await expect(page.locator("tbody")).toContainText("Tidak");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  expect(errors).toEqual([]);
  const chartWidth = await page
    .locator(".chart")
    .evaluate((el) => el.clientWidth);
  expect((await page.locator(".chart svg").boundingBox())?.width).toBe(
    chartWidth,
  );
  await page.screenshot({
    path: "test-results/patch003-chart-mobile.png",
    fullPage: true,
  });
  await page.emulateMedia({ media: "print" });
  await expect(page.locator(".chart svg")).toBeVisible();
});
test("malformed reference is rejected without a chart crash", async ({
  page,
}) => {
  await page.route("**/growth?*", (route) =>
    route.fulfill({
      json: envelope({ ...growth, reference: { ...reference, median: [1] } }),
    }),
  );
  await page.goto("/#/children/test-child/growth");
  await expect(page.getByRole("alert")).toContainText(
    "Data kurva dari layanan belum lengkap",
  );
  await expect(page.locator(".chart svg")).toHaveCount(0);
});
test("empty report curve requires explicit confirmation before print", async ({
  page,
}) => {
  await page.route("**/growth?*", (route) =>
    route.fulfill({
      json: envelope({
        ...growth,
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
  const print = page.getByRole("button", { name: "Cetak / simpan PDF" });
  await expect(print).toBeDisabled();
  await expect(
    page.getByText("Kurva belum tersedia: Belum ada data kurva."),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Lanjutkan cetak tanpa kurva" })
    .click();
  await expect(print).toBeEnabled();
});
