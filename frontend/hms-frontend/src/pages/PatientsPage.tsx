import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Container,
  Paper,
  Typography,
  TextField,
  Stack,
  Button,
} from "@mui/material";
import axios from "axios";
import { DataGrid, GridColDef } from "@mui/x-data-grid";

interface Patient {
  id: number;
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
}

export default function PatientsPage() {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<Patient[]>([]);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [hospitalId, setHospitalId] = useState<number | null>(null);

  const columns = useMemo<GridColDef[]>(
    () => [
      { field: "id", headerName: "ID", width: 80 },
      { field: "first_name", headerName: "First Name", flex: 1 },
      { field: "last_name", headerName: "Last Name", flex: 1 },
      { field: "phone", headerName: "Phone", flex: 1 },
      { field: "email", headerName: "Email", flex: 1 },
    ],
    [],
  );

  const fetchPatients = useCallback(async () => {
    const r = await axios.get("/api/patients/", {
      params: q ? { search: q } : {},
    });
    const data = r.data.results || r.data;
    setRows(data);
  }, [q]);

  useEffect(() => {
    const source = axios.CancelToken.source();
    axios
      .get("/api/users/me/", { cancelToken: source.token })
      .then((r) => setHospitalId(r.data.hospital));
    fetchPatients().catch(() => setRows([]));
    return () => source.cancel();
  }, [q, fetchPatients]);

  const createPatient = async () => {
    if (!hospitalId) return;
    await axios.post("/api/patients/", {
      hospital: hospitalId,
      first_name: firstName,
      last_name: lastName,
    });
    setFirstName("");
    setLastName("");
    await fetchPatients();
  };

  return (
    <Container sx={{ my: 3 }}>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Patients
        </Typography>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          sx={{ mb: 2 }}
        >
          <TextField
            label="First Name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
          />
          <TextField
            label="Last Name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
          />
          <Button
            variant="contained"
            onClick={createPatient}
            disabled={!firstName || !lastName || !hospitalId}
          >
            Add
          </Button>
        </Stack>
        <TextField
          label="Search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          fullWidth
          sx={{ mb: 2 }}
        />
        <div style={{ height: 520, width: "100%" }}>
          <DataGrid
            rows={rows}
            columns={columns}
            pageSizeOptions={[10, 25, 50]}
            initialState={{
              pagination: { paginationModel: { page: 0, pageSize: 10 } },
            }}
            disableRowSelectionOnClick
            density="compact"
          />
        </div>
      </Paper>
    </Container>
  );
}
