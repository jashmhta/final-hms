import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Optimize static assets for CDN deployment"

    def add_arguments(self, parser):
        parser.add_argument(
            "--compress",
            action="store_true",
            help="Compress static assets",
        )
        parser.add_argument(
            "--deploy",
            choices=["aws", "cloudflare"],
            help="Deploy to CDN provider",
        )
        parser.add_argument(
            "--environment",
            choices=["development", "staging", "production"],
            default="production",
            help="Target environment",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually doing it",
        )

    def handle(self, *args, **options):
        self.verbosity = options["verbosity"]
        self.dry_run = options["dry_run"]

        if options["compress"]:
            self.compress_static_assets(options["environment"])

        if options["deploy"]:
            self.deploy_to_cdn(options["deploy"], options["environment"])

        self.stdout.write(self.style.SUCCESS("Asset optimization complete"))

    def compress_static_assets(self, environment):
        """Compress and optimize static assets"""
        self.stdout.write("Compressing static assets...")

        static_root = settings.STATIC_ROOT
        if not static_root:
            self.stderr.write(self.style.ERROR("STATIC_ROOT not configured"))
            return

        # Create optimized directory
        optimized_dir = os.path.join(static_root, "optimized")
        if not os.path.exists(optimized_dir):
            os.makedirs(optimized_dir)

        # Collect static files first
        if not self.dry_run:
            self.stdout.write("Collecting static files...")
            subprocess.run(["python", "manage.py", "collectstatic", "--noinput"], check=True)

        # Process CSS files
        self._process_css_files(static_root, optimized_dir)

        # Process JS files
        self._process_js_files(static_root, optimized_dir)

        # Process images
        self._process_images(static_root, optimized_dir)

        # Create asset manifest
        self._create_asset_manifest(static_root, optimized_dir, environment)

    def _process_css_files(self, static_root, optimized_dir):
        """Process and optimize CSS files"""
        css_dir = os.path.join(optimized_dir, "css")
        os.makedirs(css_dir, exist_ok=True)

        for css_file in Path(static_root).rglob("*.css"):
            if "optimized" in str(css_file):
                continue

            rel_path = css_file.relative_to(static_root)
            self.stdout.write(f"Processing CSS: {rel_path}")

            if not self.dry_run:
                # Minify CSS
                output_file = os.path.join(css_dir, rel_path)
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # Use cssmin or similar tool
                try:
                    subprocess.run(
                        ["cssmin", str(css_file), ">", output_file], shell=True, check=True, capture_output=True
                    )
                except:
                    # Fallback: just copy the file
                    shutil.copy2(css_file, output_file)

                # Create gzipped version
                with open(output_file, "rb") as f:
                    css_content = f.read()
                with open(f"{output_file}.gz", "wb") as f:
                    f.write(self._gzip_content(css_content))

    def _process_js_files(self, static_root, optimized_dir):
        """Process and optimize JavaScript files"""
        js_dir = os.path.join(optimized_dir, "js")
        os.makedirs(js_dir, exist_ok=True)

        for js_file in Path(static_root).rglob("*.js"):
            if "optimized" in str(js_file):
                continue

            rel_path = js_file.relative_to(static_root)
            self.stdout.write(f"Processing JS: {rel_path}")

            if not self.dry_run:
                # Minify JS
                output_file = os.path.join(js_dir, rel_path)
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # Use terser or similar tool
                try:
                    subprocess.run(
                        ["terser", str(js_file), "--compress", "--mangle", "--output", output_file],
                        check=True,
                        capture_output=True,
                    )
                except:
                    # Fallback: just copy the file
                    shutil.copy2(js_file, output_file)

                # Create gzipped version
                with open(output_file, "rb") as f:
                    js_content = f.read()
                with open(f"{output_file}.gz", "wb") as f:
                    f.write(self._gzip_content(js_content))

    def _process_images(self, static_root, optimized_dir):
        """Process and optimize images"""
        images_dir = os.path.join(optimized_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"]

        for ext in image_extensions:
            for image_file in Path(static_root).rglob(f"*{ext}"):
                if "optimized" in str(image_file):
                    continue

                rel_path = image_file.relative_to(static_root)
                self.stdout.write(f"Processing image: {rel_path}")

                if not self.dry_run:
                    output_file = os.path.join(images_dir, rel_path)
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)

                    # Optimize based on file type
                    if ext in [".jpg", ".jpeg"]:
                        self._optimize_jpg(image_file, output_file)
                    elif ext == ".png":
                        self._optimize_png(image_file, output_file)
                    elif ext == ".svg":
                        self._optimize_svg(image_file, output_file)

                    # Create WebP version if supported
                    if ext in [".jpg", ".jpeg", ".png"]:
                        webp_file = output_file.with_suffix(".webp")
                        self._create_webp(image_file, webp_file)

    def _optimize_jpg(self, input_file, output_file):
        """Optimize JPEG image"""
        try:
            subprocess.run(
                ["jpegoptim", "--max=85", "--strip-all", "--dest=" + str(output_file.parent), str(input_file)],
                check=True,
                capture_output=True,
            )
        except:
            shutil.copy2(input_file, output_file)

    def _optimize_png(self, input_file, output_file):
        """Optimize PNG image"""
        try:
            subprocess.run(
                ["optipng", "-o7", "-quiet", "-out", str(output_file), str(input_file)], check=True, capture_output=True
            )
        except:
            shutil.copy2(input_file, output_file)

    def _optimize_svg(self, input_file, output_file):
        """Optimize SVG image"""
        try:
            subprocess.run(
                ["svgo", "--input", str(input_file), "--output", str(output_file)], check=True, capture_output=True
            )
        except:
            shutil.copy2(input_file, output_file)

    def _create_webp(self, input_file, output_file):
        """Create WebP version of image"""
        try:
            subprocess.run(
                ["cwebp", "-q", "80", str(input_file), "-o", str(output_file)], check=True, capture_output=True
            )
        except:
            pass  # WebP conversion failed

    def _gzip_content(self, content):
        """Gzip content"""
        import gzip
        import io

        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as f:
            f.write(content)
        return buf.getvalue()

    def _create_asset_manifest(self, static_root, optimized_dir, environment):
        """Create asset manifest for CDN deployment"""
        manifest = {"environment": environment, "version": self._get_version(), "assets": {}}

        # Scan optimized directory
        for root, dirs, files in os.walk(optimized_dir):
            for file in files:
                if not file.endswith(".gz"):  # Skip compressed versions
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, optimized_dir)

                    # Calculate file hash
                    with open(file_path, "rb") as f:
                        file_hash = self._calculate_hash(f.read())

                    # Generate CDN URL
                    cdn_url = self._generate_cdn_url(rel_path, file_hash, environment)

                    manifest["assets"][rel_path] = {
                        "hash": file_hash,
                        "cdn_url": cdn_url,
                        "size": os.path.getsize(file_path),
                        "gzip_available": os.path.exists(f"{file_path}.gz"),
                    }

        # Save manifest
        manifest_path = os.path.join(static_root, "asset-manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Cache manifest
        cache.set(f"asset_manifest_{environment}", manifest, timeout=86400)

        self.stdout.write(f'Created asset manifest with {len(manifest["assets"])} assets')

    def _calculate_hash(self, content):
        """Calculate file hash for cache busting"""
        import hashlib

        return hashlib.md5(content).hexdigest()[:8]

    def _get_version(self):
        """Get current version"""
        from django.conf import settings

        return getattr(settings, "VERSION", "1.0.0")

    def _generate_cdn_url(self, rel_path, file_hash, environment):
        """Generate CDN URL for asset"""
        from django.conf import settings

        # Get CDN configuration
        cdn_config = getattr(settings, "CDN_CONFIG", {})
        base_url = cdn_config.get(environment, {}).get("base_url")

        if not base_url:
            base_url = getattr(settings, "STATIC_URL", "/static/")

        # Insert hash into filename
        parts = rel_path.rsplit(".", 1)
        if len(parts) == 2:
            hashed_path = f"{parts[0]}.{file_hash}.{parts[1]}"
        else:
            hashed_path = f"{rel_path}.{file_hash}"

        return f"{base_url.rstrip('/')}/{hashed_path}"

    def deploy_to_cdn(self, provider, environment):
        """Deploy assets to CDN provider"""
        self.stdout.write(f"Deploying to {provider} CDN...")

        # Load asset manifest
        manifest_path = os.path.join(settings.STATIC_ROOT, "asset-manifest.json")
        if not os.path.exists(manifest_path):
            self.stderr.write(self.style.ERROR("Asset manifest not found. Run --compress first."))
            return

        with open(manifest_path) as f:
            manifest = json.load(f)

        if provider == "aws":
            self._deploy_to_aws(manifest, environment)
        elif provider == "cloudflare":
            self._deploy_to_cloudflare(manifest, environment)

    def _deploy_to_aws(self, manifest, environment):
        """Deploy to AWS S3 + CloudFront"""
        try:
            import boto3
        except ImportError:
            self.stderr.write(self.style.ERROR("boto3 not installed"))
            return

        from django.conf import settings

        cdn_config = getattr(settings, "CDN_CONFIG", {})
        aws_config = cdn_config.get(environment, {}).get("aws", {})

        bucket = aws_config.get("bucket")
        distribution_id = aws_config.get("cloudfront_distribution_id")

        if not bucket:
            self.stderr.write(self.style.ERROR("AWS S3 bucket not configured"))
            return

        s3 = boto3.client("s3")
        cloudfront = boto3.client("cloudfront")

        # Upload files
        uploaded = 0
        for asset_path, asset_info in manifest["assets"].items():
            if not self.dry_run:
                # Upload optimized asset
                source_path = os.path.join(settings.STATIC_ROOT, "optimized", asset_path)
                if os.path.exists(source_path):
                    s3_key = asset_info["cdn_url"].split("/")[-1]

                    s3.upload_file(
                        source_path,
                        bucket,
                        s3_key,
                        ExtraArgs={
                            "ContentType": self._get_content_type(asset_path),
                            "CacheControl": "public, max-age=31536000, immutable",
                        },
                    )
                    uploaded += 1

                # Upload gzipped version
                gzipped_path = f"{source_path}.gz"
                if os.path.exists(gzipped_path):
                    s3.upload_file(
                        gzipped_path,
                        bucket,
                        f"{s3_key}.gz",
                        ExtraArgs={
                            "ContentType": self._get_content_type(asset_path),
                            "ContentEncoding": "gzip",
                            "CacheControl": "public, max-age=31536000, immutable",
                        },
                    )

        # Create CloudFront invalidation
        if distribution_id and not self.dry_run:
            paths = [f'/{info["cdn_url"].split("/")[-1]}' for info in manifest["assets"].values()]
            invalidation = cloudfront.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    "Paths": {"Quantity": len(paths), "Items": paths},
                    "CallerReference": str(self._get_version()),
                },
            )
            self.stdout.write(f'Created CloudFront invalidation: {invalidation["Invalidation"]["Id"]}')

        self.stdout.write(self.style.SUCCESS(f"Uploaded {uploaded} assets to S3"))

    def _deploy_to_cloudflare(self, manifest, environment):
        """Deploy to Cloudflare R2"""
        self.stdout.write(self.style.WARNING("Cloudflare R2 deployment not yet implemented"))

    def _get_content_type(self, filename):
        """Get content type for file"""
        ext = filename.split(".")[-1].lower()
        content_types = {
            "css": "text/css",
            "js": "application/javascript",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "svg": "image/svg+xml",
            "webp": "image/webp",
            "woff": "font/woff",
            "woff2": "font/woff2",
        }
        return content_types.get(ext, "application/octet-stream")
