import React, { useEffect, useRef, useState } from 'react';
import { Camera, X, RefreshCw, CheckCircle, AlertTriangle, Video, Layers, Check } from 'lucide-react';
import { api } from '../api/client';

interface WebcamModalProps {
  inspectionId: string;
  inspectionNumber: string;
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

const VIEW_TYPES = [
  { value: 'FRONT', label: 'Front Panel' },
  { value: 'BACK', label: 'Back Panel (Declarations)' },
  { value: 'MRP_PANEL', label: 'MRP & Net Qty Close-Up' },
  { value: 'SIDE', label: 'Side Panel' },
  { value: 'TOP', label: 'Top / Cap' },
  { value: 'BOTTOM', label: 'Bottom / Base' }
];

export const WebcamModal: React.FC<WebcamModalProps> = ({
  inspectionId,
  inspectionNumber,
  isOpen,
  onClose,
  onUploadSuccess
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [stream, setStream] = useState<MediaStream | null>(null);
  const [activeViewType, setActiveViewType] = useState<string>('FRONT');
  const [loadingCamera, setLoadingCamera] = useState<boolean>(true);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState<boolean>(false);
  const [flashing, setFlashing] = useState<boolean>(false);
  const [capturedCount, setCapturedCount] = useState<number>(0);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');

  // Start webcam stream
  const startCamera = async (deviceId?: string) => {
    setLoadingCamera(true);
    setCameraError(null);

    // Stop existing stream
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
    }

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera API (navigator.mediaDevices.getUserMedia) is not supported in this browser.');
      }

      // Enumerate available video inputs
      const allDevices = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = allDevices.filter((d) => d.kind === 'videoinput');
      setDevices(videoInputs);

      const constraints: MediaStreamConstraints = {
        audio: false,
        video: deviceId
          ? { deviceId: { exact: deviceId } }
          : {
              facingMode: { ideal: 'environment' },
              width: { ideal: 1920 },
              height: { ideal: 1080 }
            }
      };

      let newStream: MediaStream;
      try {
        newStream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (err: any) {
        // Fallback to basic video constraint if ideal constraints fail
        newStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }

      setStream(newStream);

      if (videoRef.current) {
        videoRef.current.srcObject = newStream;
        await videoRef.current.play();
      }
      setLoadingCamera(false);
    } catch (err: any) {
      setLoadingCamera(false);
      const msg = err.message || String(err);
      if (err.name === 'NotAllowedError' || msg.includes('Permission denied')) {
        setCameraError(
          'Webcam access was denied by your browser. Please click the lock or camera icon in your address bar (or Brave Shields), select "Allow" for Camera, and click "Try Again".'
        );
      } else if (err.name === 'NotFoundError' || msg.includes('DevicesNotFoundError')) {
        setCameraError('No webcam hardware detected on this device. Please connect a webcam or upload image files directly.');
      } else {
        setCameraError(`Failed to access webcam: ${msg}`);
      }
    }
  };

  useEffect(() => {
    if (isOpen) {
      startCamera();
      setCapturedCount(0);
    } else {
      // Cleanup stream when modal closes
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
        setStream(null);
      }
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
      }
    };
  }, [isOpen]);

  const handleDeviceChange = (deviceId: string) => {
    setSelectedDeviceId(deviceId);
    startCamera(deviceId);
  };

  const captureFrame = async () => {
    if (!videoRef.current || isCapturing) return;

    const video = videoRef.current;
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      alert('Camera feed is still initializing. Please wait a moment.');
      return;
    }

    setIsCapturing(true);
    setFlashing(true);
    setTimeout(() => setFlashing(false), 150);

    try {
      const canvas = canvasRef.current || document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) throw new Error('Canvas 2D context unavailable');

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const blob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob(resolve, 'image/jpeg', 0.95);
      });

      if (!blob) throw new Error('Failed to generate image blob from video frame');

      const fileName = `${activeViewType.toLowerCase()}_webcam_${Date.now()}.jpg`;
      const file = new File([blob], fileName, { type: 'image/jpeg' });

      // Upload to backend
      await api.uploadImage(inspectionId, file, activeViewType);

      setCapturedCount((prev) => prev + 1);
      onUploadSuccess();

      // Auto-advance to next view type for smooth multi-shot inspection
      const currentIndex = VIEW_TYPES.findIndex((v) => v.value === activeViewType);
      if (currentIndex !== -1 && currentIndex < VIEW_TYPES.length - 1) {
        setActiveViewType(VIEW_TYPES[currentIndex + 1].value);
      }
    } catch (err: any) {
      alert(`Capture & upload failed: ${err.message}`);
    } finally {
      setIsCapturing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: 16
    }}>
      <div style={{
        background: '#0F172A',
        color: '#FFFFFF',
        borderRadius: 16,
        width: '100%',
        maxWidth: 720,
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6)',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(30, 41, 59, 0.6)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 34,
              height: 34,
              borderRadius: 8,
              background: '#2563EB',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Camera size={18} color="#FFFFFF" />
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>Live Legal Metrology Webcam Scanner</div>
              <div style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.6)' }}>
                Case: {inspectionNumber} {capturedCount > 0 && `• ${capturedCount} panels captured`}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'rgba(255, 255, 255, 0.7)',
              cursor: 'pointer',
              padding: 6,
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Viewfinder Body */}
        <div style={{ position: 'relative', background: '#000000', minHeight: 380, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {/* Video Stream */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              width: '100%',
              maxHeight: 440,
              objectFit: 'contain',
              display: loadingCamera || cameraError ? 'none' : 'block'
            }}
          />

          <canvas ref={canvasRef} style={{ display: 'none' }} />

          {/* Flash Effect */}
          {flashing && (
            <div style={{
              position: 'absolute',
              inset: 0,
              background: '#FFFFFF',
              opacity: 0.9,
              pointerEvents: 'none',
              transition: 'opacity 0.15s ease-out'
            }} />
          )}

          {/* Alignment Reticle HUD */}
          {!loadingCamera && !cameraError && (
            <div style={{
              position: 'absolute',
              inset: 24,
              border: '2px solid rgba(37, 99, 235, 0.75)',
              borderRadius: 12,
              pointerEvents: 'none',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              padding: 12
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{
                  background: 'rgba(0, 0, 0, 0.75)',
                  padding: '4px 10px',
                  borderRadius: 6,
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#FBBF24',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6
                }}>
                  <Layers size={12} />
                  TARGET: {VIEW_TYPES.find((v) => v.value === activeViewType)?.label || activeViewType}
                </span>
                <span style={{
                  background: 'rgba(16, 185, 129, 0.25)',
                  border: '1px solid #10B981',
                  color: '#10B981',
                  padding: '3px 8px',
                  borderRadius: 6,
                  fontSize: 10,
                  fontWeight: 700
                }}>
                  LIVE FEED
                </span>
              </div>

              <div style={{
                textAlign: 'center',
                background: 'rgba(0, 0, 0, 0.7)',
                padding: '6px 12px',
                borderRadius: 6,
                fontSize: 11,
                color: 'rgba(255, 255, 255, 0.85)',
                alignSelf: 'center'
              }}>
                Align commodity packaging inside frame. Ensure statutory declarations & MRP are legible.
              </div>
            </div>
          )}

          {/* Loading Indicator */}
          {loadingCamera && !cameraError && (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <RefreshCw size={36} className="spin" style={{ animation: 'spin 1s linear infinite', color: '#3B82F6', marginBottom: 12 }} />
              <div style={{ fontSize: 14, fontWeight: 500 }}>Connecting to system webcam...</div>
              <div style={{ fontSize: 11, color: 'rgba(255, 255, 255, 0.6)', marginTop: 4 }}>
                Please allow camera access in your browser prompt if requested.
              </div>
            </div>
          )}

          {/* Camera Error / Permission Banner */}
          {cameraError && (
            <div style={{
              padding: 32,
              textAlign: 'center',
              maxWidth: 480
            }}>
              <AlertTriangle size={44} color="#EF4444" style={{ marginBottom: 14 }} />
              <div style={{ fontSize: 16, fontWeight: 600, color: '#F87171', marginBottom: 8 }}>
                Camera Access Blocked
              </div>
              <div style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.8)', lineHeight: 1.5, marginBottom: 20 }}>
                {cameraError}
              </div>
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                <button
                  onClick={() => startCamera(selectedDeviceId)}
                  style={{
                    background: '#2563EB',
                    color: '#FFFFFF',
                    border: 'none',
                    padding: '8px 18px',
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6
                  }}
                >
                  <RefreshCw size={14} />
                  Try Again
                </button>
                <button
                  onClick={onClose}
                  style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    color: '#FFFFFF',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    padding: '8px 18px',
                    borderRadius: 8,
                    fontSize: 13,
                    cursor: 'pointer'
                  }}
                >
                  Use File Upload Instead
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer Controls */}
        <div style={{
          padding: '16px 20px',
          background: 'rgba(15, 23, 42, 0.95)',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          flexDirection: 'column',
          gap: 14
        }}>
          {/* Top Control Bar: Panel selector & Camera Switch */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.7)' }}>View Panel:</span>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {VIEW_TYPES.map((type) => (
                  <button
                    key={type.value}
                    onClick={() => setActiveViewType(type.value)}
                    style={{
                      background: activeViewType === type.value ? '#2563EB' : 'rgba(255, 255, 255, 0.08)',
                      color: '#FFFFFF',
                      border: activeViewType === type.value ? '1px solid #3B82F6' : '1px solid rgba(255, 255, 255, 0.15)',
                      padding: '4px 10px',
                      borderRadius: 6,
                      fontSize: 11,
                      fontWeight: activeViewType === type.value ? 600 : 400,
                      cursor: 'pointer'
                    }}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            {devices.length > 1 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Video size={14} color="rgba(255, 255, 255, 0.6)" />
                <select
                  value={selectedDeviceId}
                  onChange={(e) => handleDeviceChange(e.target.value)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    color: '#FFFFFF',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: 6,
                    padding: '4px 8px',
                    fontSize: 11
                  }}
                >
                  <option value="">Default Camera</option>
                  {devices.map((d, i) => (
                    <option key={d.deviceId || i} value={d.deviceId}>
                      {d.label || `Camera ${i + 1}`}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Shutter Button Row */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.6)' }}>
              {capturedCount > 0 ? (
                <span style={{ color: '#10B981', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <CheckCircle size={14} /> {capturedCount} evidence image(s) saved & uploaded
                </span>
              ) : (
                'Position packaging label and snap photo'
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <button
                onClick={captureFrame}
                disabled={loadingCamera || !!cameraError || isCapturing}
                style={{
                  background: isCapturing ? '#1D4ED8' : '#2563EB',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: 10,
                  padding: '10px 24px',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: (loadingCamera || !!cameraError || isCapturing) ? 'not-allowed' : 'pointer',
                  opacity: (loadingCamera || !!cameraError || isCapturing) ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  boxShadow: '0 4px 14px rgba(37, 99, 235, 0.4)'
                }}
              >
                <Camera size={16} />
                {isCapturing ? 'Uploading & Preprocessing...' : `Snap & Upload ${activeViewType}`}
              </button>

              <button
                onClick={onClose}
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: '#FFFFFF',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: 10,
                  padding: '10px 18px',
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: 'pointer'
                }}
              >
                {capturedCount > 0 ? 'Done' : 'Cancel'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
