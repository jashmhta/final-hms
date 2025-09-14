import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import {
  Container, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody,
  Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField
} from '@mui/material';

interface Account {
  id: number;
  code: string;
  name: string;
  type: string;
}

interface FormData {
  code: string;
  name: string;
  type: string;
}

const ERPPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['chart_of_accounts'],
    queryFn: async () => (await axios.get('/api/erp/chart_of_accounts')).data
  });

  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState<FormData>({ code: '', name: '', type: '' });
  const [editId, setEditId] = useState<number | null>(null);

  const mutation = useMutation({
    mutationFn: async (payload: FormData) => {
      if (editId) {
        return (await axios.put(`/api/erp/chart_of_accounts/${editId}`, payload)).data;
      }
      return (await axios.post('/api/erp/chart_of_accounts', payload)).data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chart_of_accounts'] });
      handleClose();
    }
  });

  const handleOpen = (record?: Account) => {
    if (record) {
      setFormData({ code: record.code, name: record.name, type: record.type });
      setEditId(record.id);
    } else {
      setFormData({ code: '', name: '', type: '' });
      setEditId(null);
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setFormData({ code: '', name: '', type: '' });
    setEditId(null);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = () => {
    mutation.mutate(formData);
  };

  if (isLoading) return <Typography>Loading ERP data...</Typography>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>ERP Module - Chart of Accounts</Typography>
      <Button variant="contained" color="primary" onClick={() => handleOpen()} sx={{ mb: 2 }}>Add Account</Button>
      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Code</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
           <TableBody>
             {data?.map((acc: Account) => (
               <TableRow key={acc.id}>
                 <TableCell>{acc.code}</TableCell>
                 <TableCell>{acc.name}</TableCell>
                 <TableCell>{acc.type}</TableCell>
                 <TableCell>
                   <Button size="small" onClick={() => handleOpen(acc)}>Edit</Button>
                 </TableCell>
               </TableRow>
             ))}
           </TableBody>
        </Table>
      </Paper>

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle>{editId ? 'Edit Account' : 'Add Account'}</DialogTitle>
        <DialogContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
            <TextField fullWidth label="Code" name="code" value={formData.code} onChange={handleChange} />
            <TextField fullWidth label="Name" name="name" value={formData.name} onChange={handleChange} />
            <TextField fullWidth label="Type" name="type" value={formData.type} onChange={handleChange} />
          </div>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button variant="contained" onClick={handleSubmit}>{editId ? 'Update' : 'Create'}</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ERPPage;
