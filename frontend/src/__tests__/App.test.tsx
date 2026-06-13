import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, test } from 'vitest';

import App from '../App';
import { sampleCvText, sampleJobDescription } from '../test/sampleData';

describe('App', () => {
  test('moves from input step to configure step with real input text', async () => {
    const user = userEvent.setup();

    render(<App />);

    const jobTextArea = screen.getByPlaceholderText(/Paste the job description here/i);
    fireEvent.change(jobTextArea, { target: { value: sampleJobDescription } });

    await user.click(screen.getByRole('tab', { name: /Paste Text/i }));
    const cvTextArea = screen.getByPlaceholderText(/Paste your CV content here/i);
    fireEvent.change(cvTextArea, { target: { value: sampleCvText } });

    await user.click(screen.getByRole('button', { name: /Continue/i }));
    expect(screen.getByText(/Configure Options/i)).toBeInTheDocument();
  });
});
