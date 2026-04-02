import { test, expect } from '@playwright/test';

/**
 * Serial API tests against a real MongoDB + FastAPI stack.
 * Playwright starts the stack via webServer unless PLAYWRIGHT_SKIP_WEBSERVER is set.
 */
test.describe.configure({ mode: 'serial' });

test.describe('Microblog REST API', () => {
  let createdId: string;

  test('GET /health returns ok', async ({ request }) => {
    const res = await request.get('/health');
    expect(res.ok()).toBeTruthy();
    expect(await res.json()).toEqual({ status: 'ok' });
  });

  test('GET / serves Swagger UI', async ({ request }) => {
    const res = await request.get('/');
    expect(res.ok()).toBeTruthy();
    const body = (await res.text()).toLowerCase();
    expect(body).toMatch(/swagger|openapi/);
  });

  test('GET /openapi.json describes the API', async ({ request }) => {
    const res = await request.get('/openapi.json');
    expect(res.ok()).toBeTruthy();
    const spec = await res.json();
    expect(spec.info?.title).toBe('Microblog API');
    expect(spec.paths).toHaveProperty('/messages');
    expect(spec.paths).toHaveProperty('/messages/{message_id}');
  });

  test('POST /messages creates a message', async ({ request }) => {
    const res = await request.post('/messages', {
      data: {
        author_first_name: 'Playwright',
        author_last_name: 'API',
        author_email: 'pw-api@example.com',
        text: 'Created via Playwright API test.',
      },
    });
    expect(res.status()).toBe(201);
    const body = await res.json();
    expect(body).toMatchObject({
      author_first_name: 'Playwright',
      author_last_name: 'API',
      author_email: 'pw-api@example.com',
      text: 'Created via Playwright API test.',
    });
    expect(body.id).toBeTruthy();
    expect(body.created_at).toBeTruthy();
    expect(body.updated_at).toBeTruthy();
    createdId = body.id;
  });

  test('GET /messages/{id} returns the message', async ({ request }) => {
    const res = await request.get(`/messages/${createdId}`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.id).toBe(createdId);
    expect(body.text).toBe('Created via Playwright API test.');
  });

  test('GET /messages supports sort and pagination', async ({ request }) => {
    const res = await request.get('/messages', {
      params: {
        skip: '0',
        limit: '10',
        sort_by: 'created_at',
        sort_order: 'desc',
      },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toMatchObject({ skip: 0, limit: 10 });
    expect(typeof body.total).toBe('number');
    expect(Array.isArray(body.items)).toBeTruthy();
    expect(body.total).toBeGreaterThanOrEqual(1);
    expect(body.items.some((m: { id: string }) => m.id === createdId)).toBeTruthy();
  });

  test('PATCH /messages/{id} updates fields', async ({ request }) => {
    const res = await request.patch(`/messages/${createdId}`, {
      data: { text: 'Updated by Playwright.' },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.text).toBe('Updated by Playwright.');
    expect(body.id).toBe(createdId);
  });

  test('POST /messages with invalid body returns 422', async ({ request }) => {
    const res = await request.post('/messages', {
      data: {
        author_first_name: '',
        author_last_name: 'X',
        author_email: 'not-an-email',
        text: 'x',
      },
    });
    expect(res.status()).toBe(422);
  });

  test('GET /messages/{id} for unknown id returns 404', async ({ request }) => {
    const res = await request.get('/messages/507f1f77bcf86cd799439011');
    expect(res.status()).toBe(404);
  });

  test('DELETE /messages/{id} removes the message', async ({ request }) => {
    const res = await request.delete(`/messages/${createdId}`);
    expect(res.status()).toBe(204);
  });

  test('GET /messages/{id} after delete returns 404', async ({ request }) => {
    const res = await request.get(`/messages/${createdId}`);
    expect(res.status()).toBe(404);
  });
});
