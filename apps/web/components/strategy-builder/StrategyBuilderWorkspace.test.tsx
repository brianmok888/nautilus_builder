import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StrategyBuilderWorkspace } from "./StrategyBuilderWorkspace";

describe("StrategyBuilderWorkspace", () => {
  it("adds a block, selects it, edits params, and updates spec preview", () => {
    render(<StrategyBuilderWorkspace />);

    fireEvent.click(screen.getByRole("button", { name: "Add EMA" }));
    fireEvent.click(screen.getByRole("button", { name: /Select EMA/ }));
    fireEvent.change(screen.getByLabelText("period"), { target: { value: "21" } });

    expect(screen.getByText("Selected block: EMA")).toBeInTheDocument();
    expect(screen.getByText(/"period": 21/)).toBeInTheDocument();
  });
});
