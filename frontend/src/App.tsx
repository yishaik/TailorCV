import { useState, useEffect } from 'react';
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
  CircularProgress,
  AppBar,
  Toolbar,
  IconButton,
  Dialog,
  DialogContent,
  LinearProgress,
} from '@mui/material';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

import {
  JobDescriptionInput,
  CVUploader,
  OptionsPanel,
  ResultsDisplay,
  ExportOptions,
} from './components';
import { tailorCV, tailorCVWithFile, tailorCVWithProgress, isApiError, type ProgressEvent } from './services/api';
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
  const [userNotes, setUserNotes] = useState('');

  // Result state
  const [result, setResult] = useState<TailorResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Progress state - now driven by real backend SSE events
  const [progressStep, setProgressStep] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [totalSteps, setTotalSteps] = useState(6);

  // Progress steps for display (will be updated by SSE)
  const progressSteps = [
    'Analyzing job description...',
    'Extracting CV facts...',
    'Mapping requirements to experience...',
    'Generating tailored CV...',
    'Running quality checks...',
    generateCoverLetter ? 'Generating cover letter...' : 'Finalizing...',
  ];

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

  const handleTailor = async () => {
    setLoading(true);
    setError(null);
    setProgressStep(0);
    setProgressMessage('Starting...');

    try {
      let tailorResult: TailorResult;

      // Handle progress updates from SSE
      const handleProgress = (event: ProgressEvent) => {
        if (event.step !== undefined) {
          setProgressStep(event.step);
        }
        if (event.message) {
          setProgressMessage(event.message);
        }
        if (event.total !== undefined) {
          setTotalSteps(event.total);
        }
      };

      if (cvFile) {
        // File upload doesn't support SSE yet, use regular API with simulated progress
        const simulateProgress = () => {
          let step = 0;
          const messages = progressSteps;
          const interval = setInterval(() => {
            if (step < messages.length) {
              setProgressStep(step + 1);
              setProgressMessage(messages[step]);
              step++;
            }
          }, 3000);
          return () => clearInterval(interval);
        };
        const stopSimulation = simulateProgress();

        try {
          tailorResult = await tailorCVWithFile(jobDescription, cvFile, {
            generateCoverLetter,
            strictnessLevel,
            outputFormat,
            userNotes: userNotes || undefined,
          });
        } finally {
          stopSimulation();
        }
      } else {
        // Use SSE streaming for real-time progress updates
        tailorResult = await tailorCVWithProgress(
          {
            job_description: jobDescription,
            original_cv: cvText,
            options: {
              generate_cover_letter: generateCoverLetter,
              output_format: outputFormat,
              language: 'en',
              strictness_level: strictnessLevel,
              user_notes: userNotes || undefined,
            },
          },
          handleProgress
        );
      }

      setResult(tailorResult);
      setActiveStep(2);
    } catch (err) {
      console.error('Tailoring failed:', err);

      if (isApiError(err)) {
        const apiError = err.response.data;
        setError(`${apiError.error}: ${apiError.message}`);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
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
            {error}
          </Alert>
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
              userNotes={userNotes}
              onUserNotesChange={setUserNotes}
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

      {/* Progress Dialog */}
      <Dialog
        open={loading}
        PaperProps={{
          sx: {
            backgroundColor: 'background.paper',
            backgroundImage: 'linear-gradient(145deg, #1e1e2e 0%, #2a2a3e 100%)',
            borderRadius: 3,
            border: '1px solid rgba(255,255,255,0.1)',
            minWidth: 400,
            p: 2,
          },
        }}
      >
        <DialogContent>
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <AutoFixHighIcon
              sx={{
                fontSize: 48,
                color: 'primary.main',
                mb: 2,
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%': { opacity: 1, transform: 'scale(1)' },
                  '50%': { opacity: 0.7, transform: 'scale(1.1)' },
                  '100%': { opacity: 1, transform: 'scale(1)' },
                },
              }}
            />
            <Typography variant="h6" sx={{ color: '#fff', mb: 3 }}>
              Tailoring Your CV
            </Typography>

            {/* Progress Steps */}
            <Box sx={{ mb: 3 }}>
              {progressSteps.map((step, index) => (
                <Box
                  key={index}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-start',
                    py: 0.75,
                    px: 2,
                    opacity: index + 1 <= progressStep ? 1 : 0.4,
                    transition: 'opacity 0.3s ease',
                  }}
                >
                  {index + 1 < progressStep ? (
                    <CheckCircleIcon
                      sx={{ color: 'success.main', mr: 1.5, fontSize: 20 }}
                    />
                  ) : index + 1 === progressStep ? (
                    <CircularProgress
                      size={18}
                      sx={{ color: 'primary.main', mr: 1.5 }}
                    />
                  ) : (
                    <Box
                      sx={{
                        width: 18,
                        height: 18,
                        borderRadius: '50%',
                        border: '2px solid rgba(255,255,255,0.3)',
                        mr: 1.5,
                      }}
                    />
                  )}
                  <Typography
                    variant="body2"
                    sx={{
                      color: index + 1 <= progressStep ? '#fff' : 'text.secondary',
                      fontWeight: index + 1 === progressStep ? 600 : 400,
                    }}
                  >
                    {step}
                  </Typography>
                </Box>
              ))}
            </Box>

            {/* Overall Progress Bar */}
            <Box sx={{ px: 2 }}>
              <LinearProgress
                variant="determinate"
                value={(progressStep / totalSteps) * 100}
                sx={{
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: 'rgba(255,255,255,0.1)',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 3,
                    background: 'linear-gradient(45deg, #7c4dff 30%, #b47cff 90%)',
                  },
                }}
              />
              <Typography
                variant="caption"
                sx={{ color: 'text.secondary', mt: 1, display: 'block' }}
              >
                This may take 30-60 seconds...
              </Typography>
            </Box>
          </Box>
        </DialogContent>
      </Dialog>
    </ThemeProvider>
  );
}

export default App;
