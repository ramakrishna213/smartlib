import http from 'k6/http';
import { sleep } from 'k6';

export let options = {
  vus: 100,
  duration: '1m',
};

export default function() {
  http.get('https://smartlib-5sm7.onrender.com/login');
  sleep(1);
}