import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { describe, expect, test, vi } from 'vitest';

import { JobDescriptionInput } from '../components/JobDescriptionInput';
import { sampleJobDescription } from '../test/sampleData';

describe('JobDescriptionInput', () => {
  test('accepts real job description text and can clear it', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();

    function Wrapper() {
      const [value, setValue] = useState(sampleJobDescription);
      return (
        <JobDescriptionInput
          value={value}
          onChange={(nextValue) => {
            handleChange(nextValue);
            setValue(nextValue);
          }}
        />
      );
    }

    render(<Wrapper />);

    expect(screen.getByDisplayValue(/Senior Backend Engineer/)).toBeInTheDocument();

    const clearButton = screen.getByTestId('ClearIcon').closest('button');
    expect(clearButton).not.toBeNull();
    await user.click(clearButton!);
    expect(handleChange).toHaveBeenCalledWith('');

    const textArea = screen.getByPlaceholderText(/Paste the job description here/i);
    await user.type(textArea, 'Python API role');
    expect(handleChange).toHaveBeenCalledWith('Python API role');
  });
});
