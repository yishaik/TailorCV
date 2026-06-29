import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach } from 'vitest';

beforeEach(() => {
  window.sessionStorage.setItem('tailorcv_api_key', 'test-api-key');
});

afterEach(() => {
  cleanup();
  window.sessionStorage.clear();
});
