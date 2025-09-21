"""
Static Files and CDN Configuration for Performance Optimization
"""

import os
from pathlib import Path

from django.conf import settings

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Static files configuration
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Static files directories
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Static file finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

# CDN Configuration
CDN_CONFIG = {
    "development": {
        "base_url": "/static/",
    },
    "staging": {
        "base_url": "https://staging-cdn.yourdomain.com",
        "aws": {
            "bucket": "staging-assets-bucket",
            "cloudfront_distribution_id": "E1A2B3C4D5E6F7",
        },
    },
    "production": {
        "base_url": "https://cdn.yourdomain.com",
        "aws": {
            "bucket": "production-assets-bucket",
            "cloudfront_distribution_id": "E1A2B3C4D5E6F7",
        },
        "cloudflare": {
            "zone_id": "your-zone-id",
            "account_id": "your-account-id",
        },
    },
}

# Static asset optimization settings
STATICFILES_COMPRESS = True
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_CACHE_BACKEND = "default"
COMPRESS_CACHE_KEY_PREFIX = "compress"
COMPRESS_STORAGE = "compressor.storage.GzipCompressorFileStorage"

# CSS compression
COMPRESS_CSS_FILTERS = [
    "compressor.filters.css_default.CssAbsoluteFilter",
    "compressor.filters.cssmin.rCSSMinFilter",
]

# JS compression
COMPRESS_JS_FILTERS = [
    "compressor.filters.jsmin.JSMinFilter",
]

# Precompile additional file types
COMPRESS_PRECOMPILERS = (
    ("text/x-scss", "django_libsass.SassCompiler"),
    ("text/x-sass", "django_libsass.SassCompiler"),
    ("text/less", "django_compressor.preprocessors.LessCompiler"),
)

# Cache settings for static files
STATICFILES_STORAGE = "django.core.files.storage.ManifestStaticFilesStorage"

# Asset versioning
VERSION_FILE = os.path.join(BASE_DIR, "version.txt")
if os.path.exists(VERSION_FILE):
    with open(VERSION_FILE) as f:
        VERSION = f.read().strip()
else:
    VERSION = "1.0.0"

# Asset manifest settings
ASSET_MANIFEST = "asset-manifest.json"
ASSET_VERSION = VERSION

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Thumbnail settings
THUMBNAIL_PROCESSORS = (
    "easy_thumbnails.processors.colorspace",
    "easy_thumbnails.processors.autocrop",
    "easy_thumbnails.processors.scale_and_crop",
    "easy_thumbnails.processors.filters",
)
THUMBNAIL_QUALITY = 85
THUMBNAIL_PROGRESSIVE = True

# Cache headers for static files
if not settings.DEBUG:
    # Add cache headers to static files in production
    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.middleware.cache.UpdateCacheMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.cache.FetchFromCacheMiddleware",
        # ... other middleware
    ]

    # Cache settings
    CACHE_MIDDLEWARE_SECONDS = 31536000  # 1 year
    CACHE_MIDDLEWARE_KEY_PREFIX = "static_"
    CACHE_MIDDLEWARE_ALIAS = "default"
    CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

# AWS S3 settings for static files (if using S3)
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_S3_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN")
AWS_DEFAULT_ACL = "public-read"
AWS_AUTO_CREATE_BUCKET = True
AWS_QUERYSTRING_AUTH = False
AWS_IS_GZIPPED = True
AWS_S3_FILE_OVERWRITE = False
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=31536000, public",
    "ContentDisposition": "inline",
}

# CloudFront settings
CLOUDFRONT_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN")
CLOUDFRONT_KEY_PAIR_ID = os.environ.get("CLOUDFRONT_KEY_PAIR_ID")
CLOUDFRONT_PRIVATE_KEY_PATH = os.environ.get("CLOUDFRONT_PRIVATE_KEY_PATH")

# CloudFlare settings
CLOUDFLARE_EMAIL = os.environ.get("CLOUDFLARE_EMAIL")
CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY")
CLOUDFLARE_ZONE = os.environ.get("CLOUDFLARE_ZONE")

# Static asset optimization settings
OPTIMIZE_IMAGES = True
OPTIMIZE_CSS = True
OPTIMIZE_JS = True
WEBP_SUPPORT = True
LAZY_LOADING = True

# Performance settings for static files
STATICFILES_STORAGE_CACHING = {
    "enabled": True,
    "timeout": 31536000,  # 1 year
    "key_prefix": "staticfiles_",
}

# Bundle versioning
BUNDLE_VERSION = VERSION
BUNDLE_VERSION_HASH = True

# Preconnect to CDN domains
PRECONNECT_DOMAINS = [
    "https://cdn.yourdomain.com",
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com",
]

# Prefetch critical resources
PREFETCH_RESOURCES = [
    "/static/css/main.css",
    "/static/js/main.js",
]

# DNS prefetch for external domains
DNS_PREFETCH_DOMAINS = [
    "//fonts.googleapis.com",
    "//fonts.gstatic.com",
    "//www.google-analytics.com",
]

# Resource hints
RESOURCE_HINTS = {
    "preconnect": PRECONNECT_DOMAINS,
    "prefetch": PREFETCH_RESOURCES,
    "dns-prefetch": DNS_PREFETCH_DOMAINS,
}

# Static file server settings
STATIC_SERVER = {
    "enabled": not settings.DEBUG,
    "gzip": True,
    "brotli": True,
    "cache_control": "public, max-age=31536000, immutable",
    "etag": True,
    "last_modified": True,
}

# Asset integrity settings
INTEGRITY_CHECK = True
INTEGRITY_ALGORITHM = "sha384"

# Service worker settings for PWA
SERVICE_WORKER = {
    "enabled": True,
    "cache_name": "hms-assets-v1",
    "cache_version": VERSION,
    "precached_files": [
        "/offline/",
        "/static/css/main.css",
        "/static/js/main.js",
    ],
}

# Critical CSS inlining
CRITICAL_CSS = {
    "enabled": True,
    "max_size": 14400,  # 14KB
    "files": [
        "css/critical.css",
    ],
}

# Font optimization
FONT_OPTIMIZATION = {
    "preload": True,
    "display_swap": True,
    "subset": True,
    "formats": ["woff2", "woff"],
}

# Image optimization
IMAGE_OPTIMIZATION = {
    "quality": 85,
    "progressive": True,
    "webp": True,
    "avif": True,
    "lazy_loading": True,
    "placeholder": True,
    "responsive": True,
}

# CSS optimization
CSS_OPTIMIZATION = {
    "minify": True,
    "autoprefixer": True,
    "purge": True,
    "critical": True,
    "inline": True,
}

# JavaScript optimization
JS_OPTIMIZATION = {
    "minify": True,
    "bundle": True,
    "tree_shaking": True,
    "code_splitting": True,
    "lazy_loading": True,
}

# Cache busting settings
CACHE_BUSTING = {
    "enabled": True,
    "method": "hash",  # 'hash' or 'version'
    "hash_length": 8,
    "exclude_patterns": [
        "*.hot-update.js",
        "*.map",
    ],
}

# Static file serving middleware
if settings.DEBUG:
    MIDDLEWARE += [
        "django.contrib.staticfiles.finders.FileSystemFinder",
    ]
else:
    # Use WhiteNoise for production static file serving
    MIDDLEWARE += [
        "whitenoise.middleware.WhiteNoiseMiddleware",
    ]
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = True
    WHITENOISE_MAX_AGE = 31536000
    WHITENOISE_IMMUTABLE_FILE_TEST = r"\.[a-f0-9]{8}\."
    WHITENOISE_INDEX_FILE = True
    WHITENOISE_ALLOW_ALL_ORIGINS = True

# Static file security
STATIC_FILE_SECURITY = {
    "x_frame_options": "SAMEORIGIN",
    "x_content_type_options": "nosniff",
    "x_xss_protection": "1; mode=block",
    "referrer_policy": "strict-origin-when-cross-origin",
}

# Asset pipeline settings
ASSET_PIPELINE = {
    "enabled": True,
    "manifest": True,
    "versioning": True,
    "compression": True,
    "fingerprinting": True,
}
