import { render, screen, waitFor } from "@testing-library/react";
import axios from "axios";
import DashboardPage from "./DashboardPage";

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe("DashboardPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders dashboard with overview data", async () => {
    // Mock localStorage
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: jest.fn(() => "mock-token"),
      },
      writable: true,
    });

    // Mock axios.create to return a mocked instance
    const mockGet = jest.fn();
    mockGet.mockResolvedValueOnce({
      data: {
        patients_count: 100,
        appointments_today: 20,
        revenue_cents: 50000,
      },
    });
    mockGet.mockResolvedValueOnce({
      data: [],
    });

    mockedAxios.create = jest.fn().mockReturnValue({
      get: mockGet,
      interceptors: {
        request: {
          use: jest.fn(),
        },
      },
    });

    render(<DashboardPage />);

    // Wait for the API calls to resolve and state to update
    await waitFor(() => {
      expect(
        screen.getByText("Hospital Management Dashboard"),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Total Patients")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("Appointments Today")).toBeInTheDocument();
    expect(screen.getByText("20")).toBeInTheDocument();
    expect(screen.getByText("Revenue")).toBeInTheDocument();
    expect(screen.getByText("₹500.00")).toBeInTheDocument();
  });
});
