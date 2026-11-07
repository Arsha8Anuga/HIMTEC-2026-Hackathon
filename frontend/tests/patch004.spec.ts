import { test, expect } from "@playwright/test";
const child = {
  id: "test-child",
  name: "Profil Uji",
  sex: "female",
  birth_date: "2026-01-01",
};
const envelope = (data: unknown) => ({ data, error: null });
// Test-only placeholders, not clinical KPSP wording.
const questionnaire = {
  questionnaire_age_months: 9,
  due: true,
  items: Array.from({ length: 10 }, (_, i) => ({
    item_no: i + 1,
    aspect: "gerak_kasar",
    question: `DUMMY TEST butir ${i + 1}`,
  })),
};
test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/auth/me")) return route.fulfill({ status: 404 });
    return route.fulfill({
      json: envelope(
        path.endsWith("/test-child")
          ? child
          : path.endsWith("/kpsp/next")
            ? questionnaire
            : [],
      ),
    });
  });
});
test("KPSP sends exactly ten boolean answers and shows backend result", async ({
  page,
}) => {
  let sent: any;
  await page.route("**/test-child/kpsp", async (route) => {
    if (route.request().method() === "POST") {
      sent = route.request().postDataJSON();
      await route.fulfill({
        json: envelope({
          id: "k1",
          questionnaire_age_months: 9,
          answered_at: "2026-11-07",
          yes_count: 10,
          result: "sesuai",
        }),
      });
    } else await route.fulfill({ json: envelope([]) });
  });
  await page.goto("/#/children/test-child/kpsp");
  await expect(page.getByRole("button", { name: "Berikutnya" })).toBeDisabled();
  for (let i = 0; i < 10; i++) {
    await page.getByRole("button", { name: "Ya", exact: true }).click();
    if (i < 9) await page.getByRole("button", { name: "Berikutnya" }).click();
  }
  await page.getByRole("button", { name: "Simpan jawaban" }).click();
  await expect(
    page.getByRole("heading", { name: "Hasil skrining", exact: true }),
  ).toBeVisible();
  expect(sent.answers).toHaveLength(10);
  expect(new Set(sent.answers.map((a: any) => a.item_no)).size).toBe(10);
  expect(sent.answers.every((a: any) => a.answer === true)).toBeTruthy();
  await expect(page.locator("#kpsp-result")).toContainText("sesuai");
  await expect(page.locator("#kpsp-result")).toBeFocused();
});
test("KPSP failed submission retains answers and can go back", async ({
  page,
}) => {
  await page.route("**/test-child/kpsp", (route) =>
    route.request().method() === "POST"
      ? route.fulfill({
          status: 503,
          json: {
            data: null,
            error: { message: "Layanan uji belum tersedia" },
          },
        })
      : route.fulfill({ json: envelope([]) }),
  );
  await page.goto("/#/children/test-child/kpsp");
  for (let i = 0; i < 10; i++) {
    await page.getByRole("button", { name: "Tidak", exact: true }).click();
    if (i < 9) await page.getByRole("button", { name: "Berikutnya" }).click();
  }
  await page.getByRole("button", { name: "Simpan jawaban" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Layanan uji belum tersedia",
  );
  await expect(
    page.getByRole("button", { name: "Tidak", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(
    page.getByRole("button", { name: "Coba lagi", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Sebelumnya" }).click();
  await expect(
    page.getByRole("heading", { name: "DUMMY TEST butir 9" }),
  ).toBeFocused();
});
test("duplicate KPSP item numbers cannot be answered or submitted", async ({
  page,
}) => {
  await page.route("**/kpsp/next", (route) =>
    route.fulfill({
      json: envelope({
        ...questionnaire,
        items: questionnaire.items.map((i) => ({ ...i, item_no: 1 })),
      }),
    }),
  );
  await page.goto("/#/children/test-child/kpsp");
  await expect(
    page.getByText(
      "Butir kuesioner dari layanan belum lengkap. Jawaban belum dapat dikirim.",
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Simpan jawaban" }),
  ).toHaveCount(0);
});
test("source field validation is linked to control without losing form", async ({
  page,
}) => {
  await page.route("**/measurements", (route) =>
    route.fulfill({
      status: 422,
      json: {
        data: null,
        error: {
          message: "Validasi uji",
          fields: { source: "Pesan sumber uji" },
        },
      },
    }),
  );
  await page.goto("/#/children/test-child/measurement");
  await page.getByLabel("Berat badan (kg)").fill("8");
  await page.getByRole("button", { name: "Simpan pengukuran" }).click();
  await expect(page.locator("#source-error")).toHaveText("Pesan sumber uji");
  await expect(
    page.getByRole("combobox", { name: /Sumber pengukuran/ }),
  ).toHaveAttribute("aria-invalid", "true");
});
test("A4 report includes identity and expanded reasons in print", async ({
  page,
}) => {
  await page.route("**/status", (route) =>
    route.fulfill({
      json: envelope({
        level: "yellow",
        level_label: "Perlu perhatian",
        reasons: [
          {
            code: "TEST_ONLY",
            level: "yellow",
            title: "Alasan uji",
            message: "Pesan backend untuk pengujian laporan",
            evidence: { from_date: "2026-01-01" },
          },
        ],
      }),
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
          head_circumference_cm: 40,
          source: "posyandu",
        },
      ]),
    }),
  );
  await page.route("**/growth?*", (route) =>
    route.fulfill({
      status: 503,
      json: { data: null, error: { message: "Referensi uji tidak tersedia" } },
    }),
  );
  await page.setViewportSize({ width: 794, height: 1123 });
  await page.goto("/#/children/test-child/report");
  await expect(page.locator(".report-identity")).toContainText("Perempuan");
  await page
    .getByRole("button", { name: "Lanjutkan cetak tanpa kurva" })
    .click();
  await page.emulateMedia({ media: "print" });
  await expect(
    page.getByText("Pesan backend untuk pengujian laporan", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".report-page tbody").first()).toContainText(
    "Posyandu",
  );
  expect(
    await page
      .locator("main")
      .evaluate((el) => el.scrollWidth <= el.clientWidth),
  ).toBeTruthy();
  await page.screenshot({
    path: "test-results/patch004-report-a4.png",
    fullPage: true,
  });
  const pdf = await page.pdf({
    path: "test-results/patch004-report-a4.pdf",
    format: "A4",
    printBackground: true,
  });
  expect(pdf.subarray(0, 4).toString()).toBe("%PDF");
});
test("questionnaire remains available when history endpoint fails", async ({
  page,
}) => {
  await page.route("**/test-child/kpsp", (route) =>
    route.fulfill({
      status: 503,
      json: { data: null, error: { message: "Riwayat uji belum tersedia" } },
    }),
  );
  await page.goto("/#/children/test-child/kpsp");
  await expect(page.getByRole("alert")).toContainText(
    "Riwayat uji belum tersedia",
  );
  await expect(
    page.getByRole("heading", { name: "DUMMY TEST butir 1" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Ya", exact: true }),
  ).toBeEnabled();
});
test("null questionnaire item is handled without rendering invalid questions", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.route("**/kpsp/next", (route) =>
    route.fulfill({
      json: envelope({
        ...questionnaire,
        items: [null, ...questionnaire.items.slice(1)],
      }),
    }),
  );
  await page.goto("/#/children/test-child/kpsp");
  await expect(
    page.getByText(
      "Butir kuesioner dari layanan belum lengkap. Jawaban belum dapat dikirim.",
    ),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
test("summary shows each reason message without opening anything", async ({
  page,
}) => {
  await page.route("**/status", (route) =>
    route.fulfill({
      json: envelope({
        level: "red",
        level_label: "Segera periksakan",
        reasons: [
          {
            code: "TEST_ONLY",
            level: "red",
            title: "Alasan uji",
            message: "Pesan tindakan uji dari backend",
            evidence: { from_date: "2026-01-01" },
          },
        ],
      }),
    }),
  );
  await page.goto("/#/children/test-child");
  await expect(
    page.getByText("Pesan tindakan uji dari backend", { exact: true }),
  ).toBeVisible();
  // Evidence stays collapsible.
  await expect(page.getByText("from_date", { exact: true })).toBeHidden();
});
test("v0.7 KPSP shows the backend review label with the form", async ({
  page,
}) => {
  const label = "LABEL UJI dari backend";
  await page.route("**/kpsp/next", (route) =>
    route.fulfill({
      json: envelope({ ...questionnaire, review_status: "transcription_unreviewed", review_label: label }),
    }),
  );
  await page.goto("/#/children/test-child/kpsp");
  await expect(page.locator("#kpsp-review")).toHaveText(label);
  await expect(page.getByRole("button", { name: "Ya", exact: true })).toBeVisible();
});
test("v0.7 KPSP form unavailable shows only the backend label", async ({
  page,
}) => {
  const label = "TIDAK TERSEDIA UJI dari backend";
  await page.route("**/kpsp/next", (route) =>
    route.fulfill({
      json: envelope({ ...questionnaire, items: [], review_status: "unavailable", review_label: label }),
    }),
  );
  await page.goto("/#/children/test-child/kpsp");
  await expect(page.locator("#kpsp-review")).toHaveText(label);
  await expect(page.getByRole("button", { name: "Ya", exact: true })).toHaveCount(0);
  await expect(page.getByText("Kuesioner belum tersedia.")).toHaveCount(0);
});
