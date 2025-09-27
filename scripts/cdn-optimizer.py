#!/usr/bin/env python3
"""
CDN Optimization and Static Asset Compression Utilities
Automated asset optimization, CDN deployment, and cache invalidation
"""

import gzip
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import brotli

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CDNOptimizer:
    """CDN optimization and asset compression utilities"""

    def __init__(self, static_dir: str = None, cdn_config: Dict = None):
        self.static_dir = static_dir or "/var/www/static"
        self.cdn_config = cdn_config or {}
        self.compressed_dir = os.path.join(static_dir, "compressed")
        self.manifest_file = os.path.join(static_dir, "asset-manifest.json")

    def optimize_static_assets(self) -> Dict[str, Any]:
        """Optimize all static assets with compression and caching"""
        results = {
            "optimized_files": 0,
            "total_size_original": 0,
            "total_size_compressed": 0,
            "compression_ratio": 0,
            "files": [],
        }

        # Create compressed directory
        os.makedirs(self.compressed_dir, exist_ok=True)

        # Process each file type
        for ext in ["css", "js", "html", "json", "xml", "svg"]:
            self._process_file_type(ext, results)

        # Process images
        self._optimize_images(results)

        # Generate manifest
        self._generate_asset_manifest(results["files"])

        # Calculate overall compression ratio
        if results["total_size_original"] > 0:
            results["compression_ratio"] = (
                (results["total_size_original"] - results["total_size_compressed"])
                / results["total_size_original"]
            ) * 100

        logger.info(
            f"Optimization complete: {results['optimized_files']} files, "
            f"{results['compression_ratio']:.1f}% compression ratio"
        )

        return results

    def _process_file_type(self, extension: str, results: Dict[str, Any]):
        """Process files of a specific type"""
        pattern = f"**/*.{extension}"
        file_paths = list(Path(self.static_dir).glob(pattern))

        for file_path in file_paths:
            if file_path.is_file() and not file_path.name.startswith("."):
                file_result = self._compress_file(file_path)
                if file_result:
                    results["files"].append(file_result)
                    results["optimized_files"] += 1
                    results["total_size_original"] += file_result["original_size"]
                    results["total_size_compressed"] += file_result["compressed_size"]

    def _compress_file(self, file_path: Path) -> Dict[str, Any]:
        """Compress a single file with multiple algorithms"""
        try:
            with open(file_path, "rb") as f:
                content = f.read()

            original_size = len(content)
            compressed_size = original_size
            best_algorithm = "none"
            compressed_content = content

            # Try gzip compression
            if original_size > 256:  # Only compress files larger than 256 bytes
                gzipped = gzip.compress(content, compresslevel=6)
                if len(gzipped) < compressed_size:
                    compressed_content = gzipped
                    compressed_size = len(gzipped)
                    best_algorithm = "gzip"

            # Try brotli compression
            try:
                brotlied = brotli.compress(content, quality=6)
                if len(brotlied) < compressed_size:
                    compressed_content = brotlied
                    compressed_size = len(brotlied)
                    best_algorithm = "brotli"
            except:
                pass  # brotli not available

            # Create compressed file
            if best_algorithm != "none":
                rel_path = file_path.relative_to(self.static_dir)
                compressed_path = os.path.join(
                    self.compressed_dir, f"{rel_path}.{best_algorithm}"
                )
                os.makedirs(os.path.dirname(compressed_path), exist_ok=True)

                with open(compressed_path, "wb") as f:
                    f.write(compressed_content)

            # Generate hash for cache busting
            file_hash = hashlib.hashlib.sha256(content).hexdigest()[:8]

            return {
                "path": str(file_path.relative_to(self.static_dir)),
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_algorithm": best_algorithm,
                "hash": file_hash,
                "etag": f'"{file_hash}"',
            }

        except Exception as e:
            logger.error(f"Failed to compress {file_path}: {e}")
            return None

    def _optimize_images(self, results: Dict[str, Any]):
        """Optimize images using external tools"""
        image_extensions = ["jpg", "jpeg", "png", "gif", "svg", "webp"]

        for ext in image_extensions:
            pattern = f"**/*.{ext}"
            file_paths = list(Path(self.static_dir).glob(pattern))

            for file_path in file_paths:
                if file_path.is_file() and not file_path.name.startswith("."):
                    image_result = self._optimize_image(file_path)
                    if image_result:
                        results["files"].append(image_result)
                        results["optimized_files"] += 1
                        results["total_size_original"] += image_result["original_size"]
                        results["total_size_compressed"] += image_result[
                            "compressed_size"
                        ]

    def _optimize_image(self, file_path: Path) -> Dict[str, Any]:
        """Optimize a single image"""
        try:
            original_size = file_path.stat().st_size

            # Try to optimize with available tools
            optimized_path = file_path.with_suffix(f".optimized{file_path.suffix}")

            if file_path.suffix.lower() in [".jpg", ".jpeg"]:
                # Optimize JPEG
                subprocess.run(
                    [
                        "jpegoptim",
                        "--max=85",
                        "--strip-all",
                        "--dest=" + str(optimized_path.parent),
                        str(file_path),
                    ],
                    check=False,
                    capture_output=True,
                )
            elif file_path.suffix.lower() == ".png":
                # Optimize PNG
                subprocess.run(
                    [
                        "optipng",
                        "-o7",
                        "-quiet",
                        "-out",
                        str(optimized_path),
                        str(file_path),
                    ],
                    check=False,
                    capture_output=True,
                )
            elif file_path.suffix.lower() == ".svg":
                # Optimize SVG
                subprocess.run(
                    [
                        "svgo",
                        "--input",
                        str(file_path),
                        "--output",
                        str(optimized_path),
                    ],
                    check=False,
                    capture_output=True,
                )

            # Check if optimized file was created and is smaller
            if optimized_path.exists():
                optimized_size = optimized_path.stat().st_size
                if optimized_size < original_size:
                    # Replace original with optimized
                    shutil.move(str(optimized_path), str(file_path))

                    # Generate WebP version
                    webp_path = file_path.with_suffix(".webp")
                    subprocess.run(
                        ["cwebp", "-q", "80", str(file_path), "-o", str(webp_path)],
                        check=False,
                        capture_output=True,
                    )

                    return {
                        "path": str(file_path.relative_to(self.static_dir)),
                        "original_size": original_size,
                        "compressed_size": optimized_size,
                        "compression_algorithm": "image_optimization",
                        "webp_available": webp_path.exists(),
                        "hash": hashlib.hashlib.sha256(
                            file_path.read_bytes()
                        ).hexdigest()[:8],
                    }

        except Exception as e:
            logger.error(f"Failed to optimize image {file_path}: {e}")

        return None

    def _generate_asset_manifest(self, files: List[Dict]):
        """Generate asset manifest for CDN deployment"""
        manifest = {"version": datetime.now().isoformat(), "files": {}}

        for file_info in files:
            file_path = file_info["path"]
            hash_value = file_info["hash"]

            # Add hashed filename
            parts = file_path.rsplit(".", 1)
            if len(parts) == 2:
                hashed_path = f"{parts[0]}.{hash_value}.{parts[1]}"
            else:
                hashed_path = f"{file_path}.{hash_value}"

            manifest["files"][file_path] = {
                "hashed_path": hashed_path,
                "size": file_info["compressed_size"],
                "hash": hash_value,
                "etag": file_info["etag"],
                "compression": file_info["compression_algorithm"],
            }

            # Add compressed version info
            if file_info["compression_algorithm"] != "none":
                compressed_path = f"{hashed_path}.{file_info['compression_algorithm']}"
                manifest["files"][file_path]["compressed"] = compressed_path

        # Save manifest
        with open(self.manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Generated asset manifest with {len(files)} files")

    def deploy_to_cdn(self, provider: str = "aws") -> Dict[str, Any]:
        """Deploy optimized assets to CDN"""
        if not os.path.exists(self.manifest_file):
            logger.error("Asset manifest not found. Run optimize_static_assets first.")
            return {}

        with open(self.manifest_file) as f:
            manifest = json.load(f)

        results = {
            "provider": provider,
            "uploaded_files": 0,
            "invalidated_paths": [],
            "cdn_urls": {},
        }

        if provider == "aws":
            results.update(self._deploy_to_aws_s3(manifest))
        elif provider == "cloudflare":
            results.update(self._deploy_to_cloudflare(manifest))
        else:
            logger.error(f"Unsupported CDN provider: {provider}")

        return results

    def _deploy_to_aws_s3(self, manifest: Dict) -> Dict[str, Any]:
        """Deploy assets to AWS S3 + CloudFront"""
        import boto3
        from botocore.exceptions import ClientError

        s3 = boto3.client("s3")
        cloudfront = boto3.client("cloudfront")

        bucket = self.cdn_config.get("aws_s3_bucket")
        distribution_id = self.cdn_config.get("aws_cloudfront_distribution")

        if not bucket:
            logger.error("AWS S3 bucket not configured")
            return {}

        results = {"uploaded_files": 0, "invalidated_paths": []}

        # Upload files
        for original_path, file_info in manifest["files"].items():
            try:
                # Upload original file with hash
                source_path = os.path.join(self.static_dir, original_path)
                if os.path.exists(source_path):
                    s3_key = file_info["hashed_path"]
                    s3.upload_file(
                        source_path,
                        bucket,
                        s3_key,
                        ExtraArgs={
                            "ContentType": self._get_content_type(original_path),
                            "CacheControl": "public, max-age=31536000, immutable",
                            "Metadata": {
                                "original-path": original_path,
                                "hash": file_info["hash"],
                            },
                        },
                    )
                    results["uploaded_files"] += 1

                # Upload compressed version if available
                if file_info.get("compressed"):
                    compressed_path = os.path.join(
                        self.compressed_dir,
                        f"{original_path}.{file_info['compression_algorithm']}",
                    )
                    if os.path.exists(compressed_path):
                        s3.upload_file(
                            compressed_path,
                            bucket,
                            file_info["compressed"],
                            ExtraArgs={
                                "ContentType": self._get_content_type(original_path),
                                "ContentEncoding": file_info["compression_algorithm"],
                                "CacheControl": "public, max-age=31536000, immutable",
                            },
                        )

            except ClientError as e:
                logger.error(f"Failed to upload {original_path}: {e}")

        # Create CloudFront invalidation
        if distribution_id:
            try:
                invalidation = cloudfront.create_invalidation(
                    DistributionId=distribution_id,
                    InvalidationBatch={
                        "Paths": {
                            "Quantity": len(manifest["files"]),
                            "Items": [
                                f'/{info["hashed_path"]}'
                                for info in manifest["files"].values()
                            ],
                        },
                        "CallerReference": str(datetime.now().timestamp()),
                    },
                )
                results["invalidated_paths"] = list(manifest["files"].keys())
                logger.info(
                    f"Created CloudFront invalidation: {invalidation['Invalidation']['Id']}"
                )
            except ClientError as e:
                logger.error(f"Failed to create CloudFront invalidation: {e}")

        return results

    def _deploy_to_cloudflare(self, manifest: Dict) -> Dict[str, Any]:
        """Deploy assets using Cloudflare R2"""
        # Implementation for Cloudflare R2 deployment
        logger.info("Cloudflare R2 deployment not yet implemented")
        return {}

    def _get_content_type(self, filename: str) -> str:
        """Get content type for file"""
        ext = filename.split(".")[-1].lower()
        content_types = {
            "css": "text/css",
            "js": "application/javascript",
            "html": "text/html",
            "json": "application/json",
            "xml": "application/xml",
            "svg": "image/svg+xml",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp",
            "woff": "font/woff",
            "woff2": "font/woff2",
            "ttf": "font/ttf",
        }
        return content_types.get(ext, "application/octet-stream")

    def generate_cdn_urls(self, base_url: str) -> Dict[str, str]:
        """Generate CDN URLs for all assets"""
        if not os.path.exists(self.manifest_file):
            logger.error("Asset manifest not found")
            return {}

        with open(self.manifest_file) as f:
            manifest = json.load(f)

        urls = {}
        for original_path, file_info in manifest["files"].items():
            urls[original_path] = f"{base_url.rstrip('/')}/{file_info['hashed_path']}"

        return urls

    def invalidate_cache(self, paths: List[str], provider: str = "aws"):
        """Invalidate CDN cache for specific paths"""
        if provider == "aws":
            import boto3

            cloudfront = boto3.client("cloudfront")

            distribution_id = self.cdn_config.get("aws_cloudfront_distribution")
            if distribution_id:
                try:
                    invalidation = cloudfront.create_invalidation(
                        DistributionId=distribution_id,
                        InvalidationBatch={
                            "Paths": {"Quantity": len(paths), "Items": paths},
                            "CallerReference": str(datetime.now().timestamp()),
                        },
                    )
                    logger.info(
                        f"Invalidated {len(paths)} paths: {invalidation['Invalidation']['Id']}"
                    )
                    return invalidation["Invalidation"]["Id"]
                except Exception as e:
                    logger.error(f"Failed to invalidate cache: {e}")

        return None


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="CDN Optimization Tool")
    parser.add_argument("--static-dir", help="Static files directory")
    parser.add_argument(
        "--optimize", action="store_true", help="Optimize static assets"
    )
    parser.add_argument("--deploy", choices=["aws", "cloudflare"], help="Deploy to CDN")
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    # Load configuration
    config = {}
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Initialize optimizer
    optimizer = CDNOptimizer(
        static_dir=args.static_dir, cdn_config=config.get("cdn", {})
    )

    if args.optimize:
        results = optimizer.optimize_static_assets()
        print(f"\nOptimization Results:")
        print(f"Files optimized: {results['optimized_files']}")
        print(f"Original size: {results['total_size_original']:,} bytes")
        print(f"Compressed size: {results['total_size_compressed']:,} bytes")
        print(f"Compression ratio: {results['compression_ratio']:.1f}%")

    if args.deploy:
        results = optimizer.deploy_to_cdn(args.deploy)
        print(f"\nDeployment Results:")
        print(f"Provider: {results['provider']}")
        print(f"Files uploaded: {results['uploaded_files']}")
        if results["invalidated_paths"]:
            print(f"Cache invalidated for {len(results['invalidated_paths'])} paths")


if __name__ == "__main__":
    main()
