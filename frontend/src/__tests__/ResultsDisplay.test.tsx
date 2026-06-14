import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, test } from 'vitest';

import { ResultsDisplay } from '../components/ResultsDisplay';
import { sampleResult } from '../test/sampleData';

describe('ResultsDisplay', () => {
  test('renders real result data across tabs', async () => {
    const user = userEvent.setup();

    render(<ResultsDisplay result={sampleResult} onChange={() => {}} />);

    expect(screen.getByText(/Match Score/i)).toBeInTheDocument();
    expect(screen.getByText(/Alex Taylor/i)).toBeInTheDocument();

    await user.click(screen.getByRole('tab', { name: /Cover Letter/i }));
    expect(screen.getByText(/I am applying for the Senior Backend Engineer role/i)).toBeInTheDocument();

    await user.click(screen.getByRole('tab', { name: /Analysis/i }));
    expect(screen.getByText(/ATS Keyword Coverage/i)).toBeInTheDocument();

    await user.click(screen.getByRole('tab', { name: /Changes/i }));
    expect(screen.getByText(/All Changes/i)).toBeInTheDocument();
  });
});
