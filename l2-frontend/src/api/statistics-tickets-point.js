import { generator } from './http-common';

export default generator({
  getTicketsTypes: {
    method: 'get',
    url: 'statistics-tickets/types',
    onReject: {
      visit: [], result: [], cause: [], outcome: [], exclude: [],
    },
  },
  sendTicket: {
    url: 'statistics-tickets/send',
    onReject: { pk: false },
  },
  loadTickets: {
    url: 'statistics-tickets/get',
    onReject: { data: [] },
  },
  invalidateTicket: {
    url: 'statistics-tickets/invalidate',
    onReject: { ok: false, message: 'Ошибка запроса' },
  },
});
