import { render, screen, waitFor } from "@testing-library/react";
import axios from "axios";
import AnalyticsPage from "./AnalyticsPage";

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock window.open
const mockOpen = jest.fn();
Object.defineProperty(window, "open", {
  writable: true,
  value: mockOpen,
});

describe("AnalyticsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders analytics page with overview data", async () => {
    const overviewData = {
      patients_count: 150,
      appointments_today: 25,
      revenue_cents: 75000,
    };
    const apptTrendData = [
      { date: "2023-09-01", appointments: 10 },
      { date: "2023-09-02", appointments: 15 },
    ];
    const revTrendData = [
      { date: "2023-09-01", revenue_cents: 50000 },
      { date: "2023-09-02", revenue_cents: 60000 },
    ];

    mockedAxios.get.mockImplementation((url) => {
      if (url === "/api/analytics/overview") {
        return Promise.resolve({ data: overviewData });
      } else if (url === "/api/analytics/appointments_trend?days=14") {
        return Promise.resolve({ data: apptTrendData });
      } else if (url === "/api/analytics/revenue_trend?days=14") {
        return Promise.resolve({ data: revTrendData });
      }
      return Promise.reject(new Error("Unknown URL"));
    });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("Analytics")).toBeInTheDocument();
    });

    expect(screen.getByText("Patients: 150")).toBeInTheDocument();
    expect(screen.getByText("Appointments today: 25")).toBeInTheDocument();
    expect(screen.getByText("Revenue: ₹750.00")).toBeInTheDocument();
    expect(screen.getByText("Appointments (last 14 days)")).toBeInTheDocument();
    expect(screen.getByText("Revenue (₹, last 14 days)")).toBeInTheDocument();
  });

  test("handles API errors gracefully", async () => {
    mockedAxios.get.mockRejectedValue(new Error("API Error"));

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("Analytics")).toBeInTheDocument();
    });

    expect(screen.getByText("Patients: -")).toBeInTheDocument();
    expect(screen.getByText("Appointments today: -")).toBeInTheDocument();
    expect(screen.getByText("Revenue: ₹0.00")).toBeInTheDocument();
  });

  test("export buttons call window.open with correct URLs", async () => {
    mockedAxios.get.mockRejectedValue(new Error("API Error")); // To avoid waiting for data

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("Export Bills CSV")).toBeInTheDocument();
    });

    const csvButton = screen.getByText("Export Bills CSV");
    const xlsxButton = screen.getByText("Export Bills XLSX");
    const xmlButton = screen.getByText("Export Tally XML");

    csvButton.click();
    expect(mockOpen).toHaveBeenCalledWith("/api/accounting/export-bills", "_blank");

    xlsxButton.click();
    expect(mockOpen).toHaveBeenCalledWith("/api/accounting/export-bills-xlsx", "_blank");

    xmlButton.click();
    expect(mockOpen).toHaveBeenCalledWith("/api/accounting/tally-xml", "_blank");
  });
});
