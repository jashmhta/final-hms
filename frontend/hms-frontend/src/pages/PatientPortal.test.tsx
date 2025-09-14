import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import PatientPortal from "./PatientPortal";

describe("PatientPortal", () => {
  test("renders patient portal with links", () => {
    render(
      <BrowserRouter>
        <PatientPortal />
      </BrowserRouter>,
    );

    expect(screen.getByText("Patient Portal")).toBeInTheDocument();
    expect(screen.getByText("My Appointments")).toBeInTheDocument();
    expect(screen.getByText("Medical Records")).toBeInTheDocument();
    expect(screen.getByText("Prescriptions")).toBeInTheDocument();
    expect(screen.getByText("Billing")).toBeInTheDocument();
    expect(screen.getByText("Messages")).toBeInTheDocument();
    expect(screen.getByText("Profile")).toBeInTheDocument();

    // Check for links
    expect(screen.getByText("View Appointments")).toBeInTheDocument();
    expect(screen.getByText("View Records")).toBeInTheDocument();
    expect(screen.getByText("View Prescriptions")).toBeInTheDocument();
    expect(screen.getByText("View Billing")).toBeInTheDocument();
    expect(screen.getByText("View Messages")).toBeInTheDocument();
    expect(screen.getByText("Edit Profile")).toBeInTheDocument();
  });
});
