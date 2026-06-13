import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, test, vi } from 'vitest';

import { OptionsPanel } from '../components/OptionsPanel';

describe('OptionsPanel', () => {
  test('renders and accepts real option inputs', async () => {
    const user = userEvent.setup();
    const onNotesChange = vi.fn();

    render(
      <OptionsPanel
        generateCoverLetter
        onGenerateCoverLetterChange={vi.fn()}
        strictnessLevel="moderate"
        onStrictnessChange={vi.fn()}
        outputFormat="markdown"
        onOutputFormatChange={vi.fn()}
        userInstructions=""
        onUserInstructionsChange={onNotesChange}
      />,
    );

    expect(screen.getByText(/Tailoring Approach/i)).toBeInTheDocument();
    expect(screen.getByText(/Aggressive/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /PDF/i })).toBeInTheDocument();

    const notes = screen.getByPlaceholderText(/Add preferences for tone/i);
    await user.type(notes, 'Keep tone formal');
    expect(onNotesChange).toHaveBeenCalled();
  });
});
