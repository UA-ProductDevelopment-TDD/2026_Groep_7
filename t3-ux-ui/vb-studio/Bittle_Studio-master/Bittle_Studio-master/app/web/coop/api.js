// HTTP calls to the simulator. Errors carry the server's `detail` text as their message.

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.status = status;  // 0 = the server could not be reached
  }
}

function detailText(data, status) {
  const detail = data && data.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(item => item.msg || JSON.stringify(item)).join('; ');
  if (detail) return JSON.stringify(detail);
  return `The simulator answered HTTP ${status}`;
}

export async function request(path, method = 'GET', body = undefined) {
  const options = { method };
  if (body !== undefined) {
    options.headers = { 'Content-Type': 'application/json' };
    options.body = JSON.stringify(body);  // NaN becomes null, which the server reports as "must be a number"
  }
  let response;
  try {
    response = await fetch(path, options);
  } catch (error) {
    throw new ApiError('Cannot reach the simulator. Is it still running?');
  }
  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    // no JSON body: fall through to the status text
  }
  if (!response.ok) throw new ApiError(detailText(data, response.status), response.status);
  return data;
}

export const get = path => request(path);
export const post = (path, body = {}) => request(path, 'POST', body);
export const put = (path, body) => request(path, 'PUT', body);
