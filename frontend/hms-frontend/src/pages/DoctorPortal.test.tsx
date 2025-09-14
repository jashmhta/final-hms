import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import DoctorPortal from "./DoctorPortal";

describe("DoctorPortal", () => {
  test("renders doctor portal with links", () => {
    render(
      <BrowserRouter>
        <DoctorPortal />
      </BrowserRouter>,
    );

    expect(screen.getByText("Doctor Portal")).toBeInTheDocument();
    expect(screen.getByText("My Patients")).toBeInTheDocument();
    expect(screen.getByText("Appointments")).toBeInTheDocument();
    expect(screen.getByText("Prescriptions")).toBeInTheDocument();
    expect(screen.getByText("Lab Results")).toBeInTheDocument();
    expect(screen.getByText("Messages")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();

    // Check for links
    expect(screen.getByText("View Patients")).toBeInTheDocument();
    expect(screen.getByText("Manage Appointments")).toBeInTheDocument();
    expect(screen.getByText("Manage Prescriptions")).toBeInTheDocument();
    expect(screen.getByText("View Results")).toBeInTheDocument();
    expect(screen.getByText("View Messages")).toBeInTheDocument();
    expect(screen.getByText("View Reports")).toBeInTheDocument();
  });
});
