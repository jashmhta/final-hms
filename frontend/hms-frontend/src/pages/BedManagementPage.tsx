import { useCallback, useEffect, useState } from "react";
import {
  Box,
  Button,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import axios from "axios";

export default function BedsPage() {
  const [hospitalId, setHospitalId] = useState("1");
  const [availability, setAvailability] = useState<{
    total: number;
    available: number;
    occupied: number;
  } | null>(null);
  const [assignForm, setAssignForm] = useState({ patient_id: "", bed_id: "" });
  const fetchAvailability = useCallback(async () => {
    const r = await axios.get(`/api/bed/availability`, {
      params: { hospital_id: hospitalId },
    });
    setAvailability(r.data);
  }, [hospitalId]);
  useEffect(() => {
    fetchAvailability().catch(() => setAvailability(null));
  }, [fetchAvailability]);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Bed Management
      </Typography>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          alignItems="center"
        >
          <TextField
            label="Hospital ID"
            value={hospitalId}
            onChange={(e) => setHospitalId(e.target.value)}
          />
          <Button variant="contained" onClick={fetchAvailability}>
            Refresh
          </Button>
        </Stack>
        <Box sx={{ mt: 2 }}>
          <Typography>Total: {availability?.total ?? "-"}</Typography>
          <Typography>Available: {availability?.available ?? "-"}</Typography>
          <Typography>Occupied: {availability?.occupied ?? "-"}</Typography>
        </Box>
      </Paper>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Assign Bed
        </Typography>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            label="Patient ID"
            value={assignForm.patient_id}
            onChange={(e) =>
              setAssignForm({ ...assignForm, patient_id: e.target.value })
            }
          />
          <TextField
            label="Bed ID"
            value={assignForm.bed_id}
            onChange={(e) =>
              setAssignForm({ ...assignForm, bed_id: e.target.value })
            }
          />
          <Button
            variant="outlined"
            onClick={async () => {
              await axios.post("/api/bed/assign", {
                ...assignForm,
                hospital_id: hospitalId,
              });
              await axios
                .post("/api/audit/events", {
                  service: "bed",
                  action: "assign",
                  resource_type: "bed",
                  resource_id: assignForm.bed_id,
                  detail: `patient=${assignForm.patient_id}`,
                })
                .catch(() => {});
              await fetchAvailability();
            }}
          >
            Assign
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}
