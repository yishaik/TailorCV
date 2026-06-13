import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { ExportOptions } from '../components/ExportOptions';
import { sampleResult } from '../test/sampleData';

describe('ExportOptions', () => {
  test('renders export controls for a real tailoring result', () => {
    render(<ExportOptions result={sampleResult} />);

    expect(screen.getByText('Export')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Markdown$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Word$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^PDF$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Copy as Markdown/i })).toBeInTheDocument();
  });
});
