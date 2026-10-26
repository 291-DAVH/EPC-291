import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Markdown } from "./markdown";

describe("Markdown", () => {
  it("renders headings, lists, quotes and emphasis without injecting HTML", () => {
    const { container } = render(<Markdown text={"# Title\n\n- one\n- **two**\n\n> quote\n\n<script>alert(1)</script>"} />);
    expect(container.querySelector("h2")?.textContent).toBe("Title");
    expect(container.querySelectorAll("li")).toHaveLength(2);
    expect(container.querySelector("li b")?.textContent).toBe("two");
    expect(container.querySelector("blockquote")?.textContent).toBe("quote");
    expect(container.querySelector("script")).toBeNull();
    expect(container.textContent).toContain("<script>alert(1)</script>");
  });

  it("renders a table with its header row", () => {
    const { container } = render(<Markdown text={"| A | B |\n|---|---|\n| 1 | 2 |"} />);
    expect(Array.from(container.querySelectorAll("th")).map((x) => x.textContent)).toEqual(["A", "B"]);
    expect(Array.from(container.querySelectorAll("td")).map((x) => x.textContent)).toEqual(["1", "2"]);
  });
});
