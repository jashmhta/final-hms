import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import axios from "axios";
import AccountingPage from "./AccountingPage";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{component}</QueryClientProvider>
  );
};

describe("AccountingPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders accounting page with journal entries", async () => {
    const mockData = [
      { id: 1, date: "2023-01-01", description: "Test entry 1" },
      { id: 2, date: "2023-01-02", description: "Test entry 2" },
    ];

    mockedAxios.get.mockResolvedValueOnce({ data: mockData });

    renderWithQueryClient(<AccountingPage />);

    await waitFor(() => {
      expect(screen.getByText("Accounting System - Journal Entries")).toBeInTheDocument();
    });

    expect(screen.getByText("Test entry 1")).toBeInTheDocument();
    expect(screen.getByText("Test entry 2")).toBeInTheDocument();
    expect(screen.getByText("Add Entry")).toBeInTheDocument();
  });

  test("opens add entry dialog", async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: [] });

    renderWithQueryClient(<AccountingPage />);

    await waitFor(() => {
      expect(screen.getByText("Add Entry")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /add entry/i }));

    expect(screen.getByRole("heading", { name: /add entry/i })).toBeInTheDocument(); // Dialog title
    expect(screen.getByLabelText("Date")).toBeInTheDocument();
    expect(screen.getByLabelText("Description")).toBeInTheDocument();
  });

  test("adds a new journal entry", async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: [] });
    mockedAxios.post.mockResolvedValueOnce({ data: { id: 3 } });

    renderWithQueryClient(<AccountingPage />);

    await waitFor(() => {
      fireEvent.click(screen.getByText("Add Entry"));
    });

    fireEvent.change(screen.getByLabelText("Date"), { target: { value: "2023-01-03" } });
    fireEvent.change(screen.getByLabelText("Description"), { target: { value: "New entry" } });

    fireEvent.click(screen.getByText("Create"));

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith("/api/erp/journal_entries", {
        date: "2023-01-03",
        description: "New entry",
      });
    });
  });

  test("shows loading state", () => {
    mockedAxios.get.mockImplementationOnce(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<AccountingPage />);

    expect(screen.getByText("Loading Accounting data...")).toBeInTheDocument();
  });
});
