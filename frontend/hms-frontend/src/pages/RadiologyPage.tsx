import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import axios from "axios";

interface RadiologyOrder {
  id: number;
  patient_id: number;
  study_type: string;
  priority: string;
}

export default function RadiologyPage() {
  const [orders, setOrders] = useState<RadiologyOrder[]>([]);
  const [form, setForm] = useState({
    patient_id: "",
    study_type: "",
    priority: "ROUTINE",
  });
  const [report, setReport] = useState({ order_id: "", impression: "" });

  const refresh = async () => {
    const r = await axios.get("/api/radiology/orders");
    setOrders(r.data);
  };

  useEffect(() => {
    refresh().catch(() => setOrders([]));
  }, []);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Radiology
      </Typography>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Create Order
        </Typography>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            label="Patient ID"
            value={form.patient_id}
            onChange={(e) => setForm({ ...form, patient_id: e.target.value })}
          />
          <TextField
            label="Study"
            value={form.study_type}
            onChange={(e) => setForm({ ...form, study_type: e.target.value })}
          />
          <TextField
            label="Priority"
            value={form.priority}
            onChange={(e) => setForm({ ...form, priority: e.target.value })}
          />
          <Button
            variant="contained"
            onClick={async () => {
              const created = await axios.post("/api/radiology/orders", {
                ...form,
                patient_id: parseInt(form.patient_id || "0", 10),
              });
              await axios
                .post("/api/audit/events", {
                  service: "radiology",
                  action: "order",
                  resource_type: "order",
                  resource_id: String(created.data.id),
                })
                .catch(() => {});
              await refresh();
            }}
          >
            Create
          </Button>
        </Stack>
      </Paper>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Orders
        </Typography>
        {orders.map((o) => (
          <Box key={o.id} sx={{ mb: 1 }}>
            <Typography>
              #{o.id} - Patient {o.patient_id} - {o.study_type} ({o.priority})
            </Typography>
          </Box>
        ))}
      </Paper>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Submit Report
        </Typography>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            label="Order ID"
            value={report.order_id}
            onChange={(e) => setReport({ ...report, order_id: e.target.value })}
          />
          <TextField
            label="Impression"
            value={report.impression}
            onChange={(e) =>
              setReport({ ...report, impression: e.target.value })
            }
          />
          <Button
            variant="outlined"
            onClick={async () => {
              await axios.post("/api/radiology/report", {
                order_id: parseInt(report.order_id || "0", 10),
                impression: report.impression,
              });
              await axios
                .post("/api/audit/events", {
                  service: "radiology",
                  action: "report",
                  resource_type: "report",
                  resource_id: String(report.order_id),
                })
                .catch(() => {});
              setReport({ order_id: "", impression: "" });
            }}
          >
            Submit
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}
