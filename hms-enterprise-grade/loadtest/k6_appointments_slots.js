import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  vus: 50,
  duration: '1m',
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TOKEN = __ENV.TOKEN || '';
const DOCTOR = __ENV.DOCTOR || '1';
const DATE = __ENV.DATE || new Date(Date.now() + 86400000).toISOString().slice(0,10);

export default function () {
  const headers = TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {};
  const res = http.get(`${BASE_URL}/api/appointments/available_slots/?doctor=${DOCTOR}&date=${DATE}`, { headers });
  check(res, {
    'status is 200 or 400 (validation)': (r) => r.status === 200 || r.status === 400,
  });
  sleep(1);
}
