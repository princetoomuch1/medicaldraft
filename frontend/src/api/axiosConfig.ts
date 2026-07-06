import axios from 'axios';

const base = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8001';

axios.defaults.baseURL = base;
axios.defaults.headers.post['Content-Type'] = 'application/json';

export default axios;
