import { describe, expect, it } from "vitest";

import { formatDate, initials, relativeTime, truncate } from "@/lib/utils";

describe("utils", () => {
  it("builds initials from a name", () => {
    expect(initials("Amina Diallo")).toBe("AD");
    expect(initials(undefined)).toBe("AD");
  });

  it("truncates long values with an ellipsis", () => {
    expect(truncate("abcdefghij", 5)).toBe("abcde…");
    expect(truncate("short", 20)).toBe("short");
  });

  it("formats and guards dates", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate("2026-01-15T10:00:00Z")).toContain("2026");
    expect(relativeTime("2020-01-01T00:00:00Z")).not.toBe("—");
  });
});
