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

interface AuditEvent {
  id: number;
  service: string;
  action: string;
  resource_type: string;
  resource_id?: number;
  actor_role: string;
  actor_user: string;
  created_at: string;
}

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [service, setService] = useState("");
  const [action, setAction] = useState("");

  const load = useCallback(async () => {
    const params: Record<string, string> = {};
    if (service) params.service = service;
    if (action) params.action = action;
    const r = await axios.get("/api/audit/events", { params });
    setEvents(r.data);
  }, [service, action]);
  useEffect(() => {
    load().catch(() => setEvents([]));
  }, [load]);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Audit Logs
      </Typography>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            label="Service"
            value={service}
            onChange={(e) => setService(e.target.value)}
          />
          <TextField
            label="Action"
            value={action}
            onChange={(e) => setAction(e.target.value)}
          />
          <Button variant="contained" onClick={load}>
            Filter
          </Button>
        </Stack>
      </Paper>
      <Paper sx={{ p: 2 }}>
        {events.map((ev) => (
          <Box key={ev.id} sx={{ mb: 1 }}>
            <Typography>
              #{ev.id} [{ev.service}] {ev.action} {ev.resource_type}/
              {ev.resource_id || "-"} by {ev.actor_role} ({ev.actor_user}) at{" "}
              {ev.created_at}
            </Typography>
          </Box>
        ))}
      </Paper>
    </Box>
  );
}
