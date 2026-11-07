export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public fields: Record<string, string> = {},
  ) {
    super(message);
  }
}
export async function api<T = any>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const base = import.meta.env.VITE_API_URL?.replace(/\/$/, "");
  if (!base)
    throw new ApiError(
      "Alamat layanan belum diatur. Isi VITE_API_URL, lalu mulai ulang aplikasi.",
      0,
    );
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(base + path, {
      method,
      signal: controller.signal,
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (response.status === 204) return null as T;
    let result;
    try {
      result = await response.json();
    } catch {
      throw new ApiError(
        "Layanan mengirim respons yang tidak dapat dibaca. Coba lagi.",
        response.status,
      );
    }
    if (
      !result ||
      typeof result !== "object" ||
      !("data" in result) ||
      !("error" in result)
    ) {
      throw new ApiError(
        "Bentuk respons layanan belum sesuai. Hubungi tim pengelola.",
        response.status,
      );
    }
    if (!response.ok || result.error)
      throw new ApiError(
        result.error?.message || "Permintaan belum berhasil.",
        response.status,
        result.error?.fields,
      );
    return result.data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      "Layanan belum dapat dihubungi. Periksa koneksi lalu coba lagi.",
      0,
    );
  } finally {
    clearTimeout(timeout);
  }
}
export const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
export const dateLabel = (value?: string) =>
  value
    ? new Intl.DateTimeFormat("id-ID", { dateStyle: "long" }).format(
        new Date(value + "T00:00:00"),
      )
    : "Belum ada";
