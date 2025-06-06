import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import App from './App';

const server = setupServer(
  http.get('http://localhost:8000/start', () => {
    return HttpResponse.json({ thread_id: 'thread1' });
  }),
  http.post('http://localhost:8000/chat', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ response: `Echo: ${body.message}` });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('App', () => {
  it('sends message and displays response', async () => {
    render(<App />);

    const input = await screen.findByRole('textbox');
    fireEvent.change(input, { target: { value: 'hi' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => screen.getByText('Assistant: Echo: hi'));
  });
});
