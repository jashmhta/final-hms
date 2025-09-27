#!/usr/bin/env python3
"""
Automated CDN Deployment Script
Deploys optimized static assets to CDN with cache invalidation
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

import boto3
import requests
from botocore.exceptions import ClientError

# Add the backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hms.settings")

try:
    import django

    django.setup()
    from django.conf import settings
    from django.core.cache import cache
except ImportError:
    print("Django not found. Make sure you're in the project directory.")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class CDNDeployer:
    """CDN deployment automation"""

    def __init__(self, environment="production"):
        self.environment = environment
        self.cdn_config = getattr(settings, "CDN_CONFIG", {}).get(environment, {})
        self.manifest_path = os.path.join(settings.STATIC_ROOT, "asset-manifest.json")
        self.manifest = self._load_manifest()
        self.aws_config = self.cdn_config.get("aws", {})

    def _load_manifest(self):
        """Load asset manifest"""
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path) as f:
                return json.load(f)
        return {}

    def deploy_to_s3(self):
        """Deploy assets to AWS S3"""
        logger.info("Deploying assets to S3...")

        if not self.aws_config.get("bucket"):
            logger.error("S3 bucket not configured")
            return False

        try:
            s3 = boto3.client("s3")
            bucket = self.aws_config["bucket"]
            uploaded = 0

            # Upload each asset
            for asset_path, asset_info in self.manifest.get("assets", {}).items():
                source_path = os.path.join(
                    settings.STATIC_ROOT, "optimized", asset_path
                )
                if not os.path.exists(source_path):
                    logger.warning(f"Source file not found: {source_path}")
                    continue

                # Extract key from CDN URL
                cdn_url = asset_info.get("cdn_url", "")
                s3_key = cdn_url.split("/")[-1] if cdn_url else asset_path

                # Determine content type
                content_type = self._get_content_type(asset_path)

                # Upload main file
                s3.upload_file(
                    source_path,
                    bucket,
                    s3_key,
                    ExtraArgs={
                        "ContentType": content_type,
                        "CacheControl": "public, max-age=31536000, immutable",
                        "Metadata": {
                            "environment": self.environment,
                            "version": self.manifest.get("version", "1.0.0"),
                            "hash": asset_info.get("hash", ""),
                        },
                    },
                )
                uploaded += 1

                # Upload gzipped version if available
                gzipped_path = f"{source_path}.gz"
                if os.path.exists(gzipped_path):
                    s3.upload_file(
                        gzipped_path,
                        bucket,
                        f"{s3_key}.gz",
                        ExtraArgs={
                            "ContentType": content_type,
                            "ContentEncoding": "gzip",
                            "CacheControl": "public, max-age=31536000, immutable",
                        },
                    )

            logger.info(f"Successfully uploaded {uploaded} assets to S3")
            return True

        except Exception as e:
            logger.error(f"S3 deployment failed: {e}")
            return False

    def invalidate_cloudfront(self):
        """Create CloudFront cache invalidation"""
        logger.info("Creating CloudFront invalidation...")

        distribution_id = self.aws_config.get("cloudfront_distribution_id")
        if not distribution_id:
            logger.error("CloudFront distribution ID not configured")
            return None

        try:
            cloudfront = boto3.client("cloudfront")

            # Collect paths to invalidate
            paths = []
            for asset_info in self.manifest.get("assets", {}).values():
                cdn_url = asset_info.get("cdn_url", "")
                if cdn_url:
                    paths.append(f'/{cdn_url.split("/")[-1]}')

            if not paths:
                logger.warning("No paths to invalidate")
                return None

            # Create invalidation
            invalidation = cloudfront.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    "Paths": {"Quantity": len(paths), "Items": paths},
                    "CallerReference": f"{self.environment}-{datetime.now().timestamp()}",
                },
            )

            invalidation_id = invalidation["Invalidation"]["Id"]
            logger.info(f"Created CloudFront invalidation: {invalidation_id}")

            # Wait for invalidation to complete (optional)
            if self._wait_for_invalidation(
                cloudfront, distribution_id, invalidation_id
            ):
                logger.info("Cache invalidation completed")
            else:
                logger.warning("Cache invalidation is still in progress")

            return invalidation_id

        except Exception as e:
            logger.error(f"CloudFront invalidation failed: {e}")
            return None

    def _wait_for_invalidation(
        self, cloudfront, distribution_id, invalidation_id, timeout=300
    ):
        """Wait for invalidation to complete"""
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = cloudfront.get_invalidation(
                    DistributionId=distribution_id, Id=invalidation_id
                )

                status = response["Invalidation"]["Status"]
                if status == "Completed":
                    return True
                elif status == "InProgress":
                    time.sleep(10)
                else:
                    logger.error(f"Invalidation failed with status: {status}")
                    return False

            except Exception as e:
                logger.error(f"Error checking invalidation status: {e}")
                return False

        return False

    def deploy_to_cloudflare(self):
        """Deploy assets to Cloudflare"""
        logger.info("Deploying to Cloudflare...")

        zone_id = self.cdn_config.get("cloudflare", {}).get("zone_id")
        account_id = self.cdn_config.get("cloudflare", {}).get("account_id")
        api_key = os.environ.get("CLOUDFLARE_API_KEY")
        email = os.environ.get("CLOUDFLARE_EMAIL")

        if not all([zone_id, api_key, email]):
            logger.error("Cloudflare configuration incomplete")
            return False

        # Implementation would go here
        logger.warning("Cloudflare deployment not yet implemented")
        return False

    def update_dns_records(self):
        """Update DNS records to point to CDN"""
        logger.info("Updating DNS records...")

        # This would integrate with your DNS provider
        # Example: Route53, Cloudflare DNS, etc.
        logger.warning("DNS record updates not yet implemented")

    def run_health_checks(self):
        """Run health checks on deployed assets"""
        logger.info("Running health checks...")

        base_url = self.cdn_config.get("base_url", "")
        success_count = 0
        total_count = 0

        for asset_path, asset_info in self.manifest.get("assets", {}).items():
            if asset_info.get("cdn_url"):
                url = (
                    asset_info["cdn_url"]
                    if asset_info["cdn_url"].startswith("http")
                    else f"{base_url}{asset_info['cdn_url']}"
                )
                total_count += 1

                try:
                    response = requests.head(url, timeout=10)
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        logger.warning(
                            f"Health check failed for {url}: {response.status_code}"
                        )
                except Exception as e:
                    logger.error(f"Health check error for {url}: {e}")

        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        logger.info(
            f"Health check success rate: {success_rate:.1f}% ({success_count}/{total_count})"
        )

        return success_rate >= 95  # 95% success threshold

    def send_deployment_notification(self, success=True, details=None):
        """Send deployment notification"""
        logger.info("Sending deployment notification...")

        if not details:
            details = {}

        notification = {
            "environment": self.environment,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "assets_deployed": len(self.manifest.get("assets", {})),
            "version": self.manifest.get("version", "1.0.0"),
            **details,
        }

        # Send to various channels
        self._send_slack_notification(notification)
        self._send_email_notification(notification)
        self._update_deployment_log(notification)

    def _send_slack_notification(self, notification):
        """Send notification to Slack"""
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        if not webhook_url:
            return

        color = "good" if notification["success"] else "danger"
        message = {
            "text": f"CDN Deployment - {notification['environment']}",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "Status",
                            "value": "Success" if notification["success"] else "Failed",
                            "short": True,
                        },
                        {
                            "title": "Environment",
                            "value": notification["environment"],
                            "short": True,
                        },
                        {
                            "title": "Assets Deployed",
                            "value": str(notification["assets_deployed"]),
                            "short": True,
                        },
                        {
                            "title": "Version",
                            "value": notification["version"],
                            "short": True,
                        },
                        {
                            "title": "Timestamp",
                            "value": notification["timestamp"],
                            "short": False,
                        },
                    ],
                }
            ],
        }

        try:
            requests.post(webhook_url, json=message, timeout=10)
            logger.info("Slack notification sent")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    def _send_email_notification(self, notification):
        """Send email notification"""
        # Implementation would go here
        pass

    def _update_deployment_log(self, notification):
        """Update deployment log"""
        log_path = os.path.join(settings.BASE_DIR, "logs", "cdn_deployments.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        with open(log_path, "a") as f:
            f.write(json.dumps(notification) + "\n")

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


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="CDN Deployment Script")
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        default="production",
        help="Target environment",
    )
    parser.add_argument(
        "--provider", choices=["aws", "cloudflare"], default="aws", help="CDN provider"
    )
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip health checks after deployment",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )

    args = parser.parse_args()

    # Initialize deployer
    deployer = CDNDeployer(args.environment)

    # Deployment process
    success = True
    details = {}

    try:
        if args.dry_run:
            logger.info("DRY RUN MODE - No actual deployment will occur")
            return

        # Deploy to CDN
        if args.provider == "aws":
            if not deployer.deploy_to_s3():
                success = False
                details["error"] = "S3 deployment failed"
            else:
                invalidation_id = deployer.invalidate_cloudfront()
                details["invalidation_id"] = invalidation_id
        elif args.provider == "cloudflare":
            if not deployer.deploy_to_cloudflare():
                success = False
                details["error"] = "Cloudflare deployment failed"

        # Update DNS if successful
        if success:
            deployer.update_dns_records()

        # Run health checks
        if not args.skip_health_check and success:
            health_check_passed = deployer.run_health_checks()
            details["health_check_passed"] = health_check_passed
            if not health_check_passed:
                logger.warning("Some health checks failed")

        # Send notification
        deployer.send_deployment_notification(success, details)

        if success:
            logger.info("CDN deployment completed successfully")
            sys.exit(0)
        else:
            logger.error("CDN deployment failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Deployment failed with exception: {e}")
        deployer.send_deployment_notification(False, {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
