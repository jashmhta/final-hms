try:
    from .biometric_manager import BiometricManager
    from .device_adapters import (
        FingerprintAdapter,
        FacialRecognitionAdapter,
        IrisScannerAdapter,
        PalmVeinAdapter,
    )
    from .verification_engine import BiometricVerificationEngine
    BIOMETRIC_AVAILABLE = True
    __all__ = [
        "BiometricManager",
        "FingerprintAdapter",
        "FacialRecognitionAdapter",
        "IrisScannerAdapter",
        "PalmVeinAdapter",
        "BiometricVerificationEngine",
    ]
except ImportError as e:
    BIOMETRIC_AVAILABLE = False
    print(f"Biometric integration features disabled: {e}")
    __all__ = ["BIOMETRIC_AVAILABLE"]