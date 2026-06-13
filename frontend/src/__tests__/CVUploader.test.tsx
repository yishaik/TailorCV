import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, test, vi } from 'vitest';

import { CVUploader } from '../components/CVUploader';
import { sampleCvText } from '../test/sampleData';

describe('CVUploader', () => {
  test('accepts a real text file upload', async () => {
    const user = userEvent.setup();
    const onFileChange = vi.fn();

    render(
      <CVUploader
        cvText=""
        onCVTextChange={vi.fn()}
        cvFile={null}
        onCVFileChange={onFileChange}
      />,
    );

    const file = new File([sampleCvText], 'alex-taylor-cv.txt', { type: 'text/plain' });
    const input = document.getElementById('cv-file-input') as HTMLInputElement;
    await user.upload(input, file);

    expect(onFileChange).toHaveBeenCalledWith(file);
  });

  test('accepts pasted CV text in text mode', async () => {
    const onTextChange = vi.fn();

    render(
      <CVUploader
        cvText=""
        onCVTextChange={onTextChange}
        cvFile={null}
        onCVFileChange={vi.fn()}
      />,
    );

    await userEvent.setup().click(screen.getAllByRole('tab', { name: /Paste Text/i })[0]);
    const textArea = screen.getByPlaceholderText(/Paste your CV content here/i);
    fireEvent.change(textArea, { target: { value: sampleCvText } });

    expect(onTextChange).toHaveBeenCalledWith(sampleCvText);
    expect(screen.getAllByText(/characters/i).length).toBeGreaterThan(0);
  });
});
