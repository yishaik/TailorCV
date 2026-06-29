import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { ExportOptions } from '../components/ExportOptions';
import { sampleResult } from '../test/sampleData';
import { generatePdfHtml } from '../utils/pdfExport';

describe('ExportOptions', () => {
  test('renders export controls for a real tailoring result', () => {
    render(<ExportOptions result={sampleResult} />);

    expect(screen.getByText('Export')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Markdown$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Word$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^PDF$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Copy as Markdown/i })).toBeInTheDocument();
  });

  test('escapes generated PDF HTML content', () => {
    const maliciousResult = {
      ...sampleResult,
      tailored_cv: {
        ...sampleResult.tailored_cv,
        header: {
          ...sampleResult.tailored_cv.header,
          name: '<img src=x onerror=alert(1)>',
        },
        summary: '<script>alert(1)</script>',
      },
      cover_letter: {
        ...sampleResult.cover_letter!,
        hook: '<iframe src="https://example.com"></iframe>',
      },
    };

    const html = generatePdfHtml(maliciousResult);

    expect(html).toContain('&lt;img src=x onerror=alert(1)&gt;');
    expect(html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(html).toContain('&lt;iframe src=&quot;https://example.com&quot;&gt;&lt;/iframe&gt;');
    expect(html).not.toContain('<img src=x');
    expect(html).not.toContain('<script>alert(1)</script>');
    expect(html).not.toContain('<iframe src=');
  });
});
