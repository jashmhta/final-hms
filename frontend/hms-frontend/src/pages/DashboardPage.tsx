import { useEffect, useState } from "react";
import axios, { AxiosHeaders } from "axios";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function authAxios() {
  const instance = axios.create();
  instance.interceptors.request.use((config) => {
    const token = localStorage.getItem("accessToken");
    const headers = new AxiosHeaders(config.headers);
    if (token) headers.set("Authorization", `Bearer ${token}`);
    config.headers = headers;
    return config;
  });
  return instance;
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<{
    patients_count: number;
    appointments_today: number;
    revenue_cents: number;
  } | null>(null);
  const [hospitals, setHospitals] = useState<
    Array<{ id: number; name: string; code: string }>
  >([]);
  const [estimateItems, setEstimateItems] = useState([
    {
      description: "Consultation",
      quantity: 1,
      unit_price_cents: 5000,
      gst_rate: 0.18,
    },
  ]);
  const [estimate, setEstimate] = useState<{
    subtotal_cents: number;
    gst_cents: number;
    discount_cents: number;
    total_cents: number;
  } | null>(null);

  // Sample data for chart
  const chartData = [
    { name: "Mon", patients: 120 },
    { name: "Tue", patients: 150 },
    { name: "Wed", patients: 180 },
    { name: "Thu", patients: 140 },
    { name: "Fri", patients: 200 },
    { name: "Sat", patients: 90 },
    { name: "Sun", patients: 60 },
  ];

  useEffect(() => {
    const api = authAxios();
    api
      .get("/api/analytics/overview")
      .then((r) => setOverview(r.data))
      .catch(() => setOverview(null));
    api
      .get("/api/hospitals/")
      .then((r) => setHospitals(r.data))
      .catch(() => setHospitals([]));
  }, []);

  return (
    <main className="space-y-6" role="main">
      <h1 className="text-3xl font-bold text-gray-900" id="dashboard-title">
        Hospital Management Dashboard
      </h1>

      {/* Overview Stats */}
      <section
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
        aria-labelledby="dashboard-title"
      >
        <div
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="patients-count"
        >
          <h3
            className="text-lg font-semibold text-gray-700"
            id="patients-count"
          >
            Total Patients
          </h3>
          <p
            className="text-3xl font-bold text-blue-600"
            aria-label={`Total patients: ${overview?.patients_count ?? "Not available"}`}
          >
            {overview?.patients_count ?? "-"}
          </p>
        </div>
        <div
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="appointments-today"
        >
          <h3
            className="text-lg font-semibold text-gray-700"
            id="appointments-today"
          >
            Appointments Today
          </h3>
          <p
            className="text-3xl font-bold text-green-600"
            aria-label={`Appointments today: ${overview?.appointments_today ?? "Not available"}`}
          >
            {overview?.appointments_today ?? "-"}
          </p>
        </div>
        <div
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="revenue"
        >
          <h3 className="text-lg font-semibold text-gray-700" id="revenue">
            Revenue
          </h3>
          <p
            className="text-3xl font-bold text-purple-600"
            aria-label={`Revenue: ₹${((overview?.revenue_cents ?? 0) / 100).toFixed(2)}`}
          >
            ₹{((overview?.revenue_cents ?? 0) / 100).toFixed(2)}
          </p>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Patient Visits Chart */}
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="chart-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="chart-heading">
            Weekly Patient Visits
          </h2>
          <div role="img" aria-label="Bar chart showing weekly patient visits">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="patients" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Hospitals List */}
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="hospitals-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="hospitals-heading">
            Hospitals
          </h2>
          <ul className="space-y-2" role="list">
            {hospitals.map((h) => (
              <li
                key={h.id}
                className="flex justify-between items-center p-3 bg-gray-50 rounded"
                role="listitem"
                aria-label={`Hospital: ${h.name}, Code: ${h.code}`}
              >
                <span className="font-medium">{h.name}</span>
                <span className="text-sm text-gray-500">{h.code}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Quick Price Estimator */}
        <section
          className="bg-white p-6 rounded-lg shadow-md"
          aria-labelledby="estimator-heading"
        >
          <h2 className="text-xl font-semibold mb-4" id="estimator-heading">
            Quick Price Estimator
          </h2>
          <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Description"
                value={estimateItems[0].description}
                onChange={(e) =>
                  setEstimateItems([
                    { ...estimateItems[0], description: e.target.value },
                  ])
                }
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Item description"
              />
              <input
                type="number"
                placeholder="Qty"
                value={estimateItems[0].quantity}
                onChange={(e) =>
                  setEstimateItems([
                    {
                      ...estimateItems[0],
                      quantity: parseInt(e.target.value || "0"),
                    },
                  ])
                }
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Quantity"
                min="0"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <input
                type="number"
                placeholder="Unit Price (₹)"
                value={estimateItems[0].unit_price_cents / 100}
                onChange={(e) =>
                  setEstimateItems([
                    {
                      ...estimateItems[0],
                      unit_price_cents: parseInt(e.target.value || "0") * 100,
                    },
                  ])
                }
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Unit price in rupees"
                min="0"
                step="0.01"
              />
              <button
                type="button"
                onClick={async () => {
                  const r = await axios.post("/api/estimator/estimate", {
                    items: estimateItems,
                    discount_cents: 0,
                  });
                  setEstimate(r.data);
                  try {
                    await axios.post("/api/audit/events", {
                      service: "estimator",
                      action: "estimate",
                      resource_type: "quote",
                      detail: `items=${estimateItems.length}`,
                    });
                  } catch {
                    /* Audit logging failed, but estimate was created */
                  }
                }}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Calculate price estimate"
              >
                Estimate
              </button>
            </div>
            {estimate && (
              <div
                className="mt-4 p-4 bg-gray-50 rounded"
                role="region"
                aria-labelledby="estimate-results"
              >
                <h3 id="estimate-results" className="sr-only">
                  Estimate Results
                </h3>
                <p>Subtotal: ₹{(estimate.subtotal_cents / 100).toFixed(2)}</p>
                <p>GST: ₹{(estimate.gst_cents / 100).toFixed(2)}</p>
                <p className="font-semibold">
                  Total: ₹{(estimate.total_cents / 100).toFixed(2)}
                </p>
              </div>
            )}
          </form>
        </section>
      </div>
    </main>
  );
}
