import { useRef, useState } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Container,
  Box,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Button,
  Alert,
  AlertTitle,
  CircularProgress,
  LinearProgress,
  AppBar,
  Toolbar,
  IconButton,
} from '@mui/material';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import RefreshIcon from '@mui/icons-material/Refresh';

import {
  JobDescriptionInput,
  CVUploader,
  OptionsPanel,
  ResultsDisplay,
  ExportOptions,
} from './components';
import { tailorCV, tailorCVWithFile, isApiError } from './services/api';
import type { TailorResult, StrictnessLevel, OutputFormat } from './types';

// Dark theme with purple accent
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#7c4dff',
    },
    secondary: {
      main: '#00bcd4',
    },
    background: {
      default: '#0a0a0f',
      paper: '#1e1e2e',
    },
    success: {
      main: '#4caf50',
    },
    warning: {
      main: '#ff9800',
    },
    error: {
      main: '#f44336',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

const steps = ['Input', 'Configure', 'Results'];

function App() {
  // Step state
  const [activeStep, setActiveStep] = useState(0);

  // Input state
  const [jobDescription, setJobDescription] = useState('');
  const [cvText, setCVText] = useState('');
  const [cvFile, setCVFile] = useState<File | null>(null);

  // Options state
  const [generateCoverLetter, setGenerateCoverLetter] = useState(true);
  const [strictnessLevel, setStrictnessLevel] = useState<StrictnessLevel>('moderate');
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('markdown');
  const [userInstructions, setUserInstructions] = useState('');

  // Result state
  const [result, setResult] = useState<TailorResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<{
    title: string;
    message: string;
    details?: string[];
  } | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('');
  const progressTimer = useRef<number | null>(null);

  // Validation
  const isStep1Valid = jobDescription.length >= 50 && (cvFile !== null || cvText.length >= 100);

  const handleNext = () => {
    if (activeStep === 1) {
      handleTailor();
    } else {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setResult(null);
    setError(null);
  };

  const startProgress = () => {
    const stages = [
      { label: 'Extracting job requirements', value: 18 },
      { label: 'Parsing CV content', value: 36 },
      { label: 'Mapping evidence', value: 56 },
      { label: 'Generating tailored CV', value: 74 },
      { label: 'Running quality checks', value: 88 },
      { label: 'Finalizing results', value: 96 },
    ];
    let stageIndex = 0;
    setProgress(stages[0].value);
    setProgressLabel(stages[0].label);
    if (progressTimer.current) {
      window.clearInterval(progressTimer.current);
    }
    progressTimer.current = window.setInterval(() => {
      stageIndex = Math.min(stageIndex + 1, stages.length - 1);
      setProgress(stages[stageIndex].value);
      setProgressLabel(stages[stageIndex].label);
    }, 1200);
  };

  const stopProgress = () => {
    if (progressTimer.current) {
      window.clearInterval(progressTimer.current);
      progressTimer.current = null;
    }
    setProgress(0);
    setProgressLabel('');
  };

  const formatError = (err: unknown) => {
    if (isApiError(err)) {
      const apiError = err.response.data;
      switch (apiError.error) {
        case 'FABRICATION_DETECTED':
          return {
            title: 'Quality check blocked the output',
            message:
              'Potential fabrication was detected. Review your input, lower strictness, or add more evidence.',
            details: apiError.details,
          };
        case 'INVALID_FILE_TYPE':
          return {
            title: 'Unsupported file type',
            message: apiError.message,
          };
        case 'PARSE_FAILURE':
          return {
            title: 'Could not read the file',
            message:
              'Try a different file or paste the CV text directly. The uploaded file may be scanned or protected.',
          };
        case 'EXTRACTION_FAILED':
          return {
            title: 'Extraction failed',
            message: 'The text could not be analyzed. Please try again.',
          };
        case 'PROCESSING_ERROR':
          return {
            title: 'Processing error',
            message: 'The server failed to complete the request. Please retry.',
          };
        default:
          return {
            title: apiError.error || 'Request failed',
            message: apiError.message || 'Please try again.',
            details: apiError.details,
          };
      }
    }

    if (typeof err === 'object' && err !== null && 'response' in err) {
      const response = (err as any).response;
      if (response?.status === 422 && Array.isArray(response?.data?.detail)) {
        const details = response.data.detail.map((item: any) => item.msg);
        return {
          title: 'Invalid input',
          message: 'Please check the required fields and try again.',
          details,
        };
      }
    }

    if (err instanceof Error) {
      return {
        title: 'Unexpected error',
        message: err.message,
      };
    }

    return {
      title: 'Unexpected error',
      message: 'An unexpected error occurred. Please try again.',
    };
  };

  const handleTailor = async () => {
    setLoading(true);
    setError(null);
    startProgress();

    try {
      let tailorResult: TailorResult;
      const trimmedInstructions = userInstructions.trim();

      if (cvFile) {
        tailorResult = await tailorCVWithFile(jobDescription, cvFile, {
          generateCoverLetter,
          strictnessLevel,
          outputFormat,
          userInstructions: trimmedInstructions || undefined,
        });
      } else {
        tailorResult = await tailorCV({
          job_description: jobDescription,
          original_cv: cvText,
          options: {
            generate_cover_letter: generateCoverLetter,
            output_format: outputFormat,
            language: 'en',
            strictness_level: strictnessLevel,
            user_instructions: trimmedInstructions || null,
          },
        });
      }

      setResult(tailorResult);
      setActiveStep(2);
    } catch (err) {
      console.error('Tailoring failed:', err);
      setError(formatError(err));
    } finally {
      setLoading(false);
      stopProgress();
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      {/* App Bar */}
      <AppBar position="static" elevation={0} sx={{ backgroundColor: 'transparent' }}>
        <Toolbar>
          <AutoFixHighIcon sx={{ mr: 2, color: 'primary.main' }} />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>
            AI CV Tailor
          </Typography>
          {activeStep === 2 && (
            <IconButton onClick={handleReset} sx={{ color: 'primary.main' }}>
              <RefreshIcon />
            </IconButton>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Stepper */}
        <Box sx={{ mb: 4 }}>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel
                  sx={{
                    '& .MuiStepLabel-label': { color: 'text.secondary' },
                    '& .MuiStepLabel-label.Mui-active': { color: 'primary.main' },
                    '& .MuiStepLabel-label.Mui-completed': { color: 'success.main' },
                  }}
                >
                  {label}
                </StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            <AlertTitle>{error.title}</AlertTitle>
            {error.message}
            {error.details && error.details.length > 0 && (
              <Box component="ul" sx={{ mt: 1, mb: 0, pl: 3 }}>
                {error.details.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </Box>
            )}
          </Alert>
        )}

        {loading && (
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                {progressLabel || 'Working...'}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                {progress ? `${progress}%` : ''}
              </Typography>
            </Box>
            <LinearProgress
              variant={progress ? 'determinate' : 'indeterminate'}
              value={progress}
              sx={{
                height: 8,
                borderRadius: 6,
                backgroundColor: 'rgba(255,255,255,0.1)',
                '& .MuiLinearProgress-bar': {
                  background: 'linear-gradient(90deg, #7c4dff 0%, #00bcd4 100%)',
                },
              }}
            />
          </Box>
        )}

        {/* Step Content */}
        {activeStep === 0 && (
          <Box>
            <Typography variant="h4" sx={{ color: '#fff', mb: 1, textAlign: 'center' }}>
              Tailor Your CV with AI
            </Typography>
            <Typography
              variant="body1"
              sx={{ color: 'text.secondary', mb: 4, textAlign: 'center' }}
            >
              Paste a job description and upload your CV. Our AI will optimize it for the role.
            </Typography>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
              <JobDescriptionInput
                value={jobDescription}
                onChange={setJobDescription}
                disabled={loading}
              />
              <CVUploader
                cvText={cvText}
                onCVTextChange={setCVText}
                cvFile={cvFile}
                onCVFileChange={setCVFile}
                disabled={loading}
              />
            </Box>
          </Box>
        )}

        {activeStep === 1 && (
          <Box sx={{ maxWidth: 600, mx: 'auto' }}>
            <Typography variant="h4" sx={{ color: '#fff', mb: 1, textAlign: 'center' }}>
              Configure Options
            </Typography>
            <Typography
              variant="body1"
              sx={{ color: 'text.secondary', mb: 4, textAlign: 'center' }}
            >
              Choose how aggressively to tailor your CV
            </Typography>

            <OptionsPanel
              generateCoverLetter={generateCoverLetter}
              onGenerateCoverLetterChange={setGenerateCoverLetter}
              strictnessLevel={strictnessLevel}
              onStrictnessChange={setStrictnessLevel}
              outputFormat={outputFormat}
              onOutputFormatChange={setOutputFormat}
              userInstructions={userInstructions}
              onUserInstructionsChange={setUserInstructions}
              disabled={loading}
            />
          </Box>
        )}

        {activeStep === 2 && result && (
          <Box>
            <Typography variant="h4" sx={{ color: '#fff', mb: 1, textAlign: 'center' }}>
              Your Tailored CV
            </Typography>
            <Typography
              variant="body1"
              sx={{ color: 'text.secondary', mb: 4, textAlign: 'center' }}
            >
              Review the optimized CV and export when ready
            </Typography>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3 }}>
              <ResultsDisplay result={result} />
              <Box>
                <ExportOptions result={result} />
              </Box>
            </Box>
          </Box>
        )}

        {/* Navigation */}
        {activeStep < 2 && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={handleBack}
              disabled={activeStep === 0 || loading}
              sx={{ visibility: activeStep === 0 ? 'hidden' : 'visible' }}
            >
              Back
            </Button>

            <Button
              variant="contained"
              size="large"
              endIcon={
                loading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : activeStep === 1 ? (
                  <AutoFixHighIcon />
                ) : (
                  <ArrowForwardIcon />
                )
              }
              onClick={handleNext}
              disabled={!isStep1Valid || loading}
              sx={{
                px: 4,
                py: 1.5,
                background: 'linear-gradient(45deg, #7c4dff 30%, #b47cff 90%)',
                boxShadow: '0 3px 15px 2px rgba(124, 77, 255, 0.3)',
              }}
            >
              {loading
                ? 'Processing...'
                : activeStep === 1
                  ? 'Tailor My CV'
                  : 'Continue'}
            </Button>
          </Box>
        )}
      </Container>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 3,
          textAlign: 'center',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          mt: 'auto',
        }}
      >
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          AI CV Tailor • Never fabricates, only optimizes
        </Typography>
      </Box>
    </ThemeProvider>
  );
}

export default App;
