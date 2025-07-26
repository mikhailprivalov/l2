#!/usr/bin/env python3
"""
Performance monitoring script for L2 MIS system
Analyzes bundle sizes, compression ratios, and provides optimization recommendations
"""

import os
import sys
import json
import gzip
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"


def analyze_webpack_bundles(bundle_dir: str) -> Dict:
    """Analyze webpack bundles and return statistics"""
    bundle_path = Path(bundle_dir)
    if not bundle_path.exists():
        return {"error": f"Bundle directory {bundle_dir} not found"}
    
    stats = {
        "total_files": 0,
        "total_size": 0,
        "js_files": 0,
        "js_size": 0,
        "css_files": 0,
        "css_size": 0,
        "compressed_files": 0,
        "compressed_size": 0,
        "largest_files": [],
        "compression_ratio": 0,
        "chunk_analysis": defaultdict(int)
    }
    
    # Analyze all files
    for file_path in bundle_path.rglob('*'):
        if file_path.is_file():
            size = get_file_size(str(file_path))
            stats["total_files"] += 1
            stats["total_size"] += size
            
            # Categorize by extension
            if file_path.suffix == '.js':
                stats["js_files"] += 1
                stats["js_size"] += size
                stats["largest_files"].append((str(file_path.name), size))
            elif file_path.suffix == '.css':
                stats["css_files"] += 1
                stats["css_size"] += size
            elif file_path.suffix == '.gz':
                stats["compressed_files"] += 1
                stats["compressed_size"] += size
            
            # Analyze chunk patterns
            if any(chunk in file_path.name for chunk in ['chunk-', 'vendors', 'common']):
                chunk_type = 'vendor' if 'vendor' in file_path.name else 'common'
                stats["chunk_analysis"][chunk_type] += size
    
    # Sort largest files
    stats["largest_files"].sort(key=lambda x: x[1], reverse=True)
    stats["largest_files"] = stats["largest_files"][:10]  # Top 10
    
    # Calculate compression ratio
    if stats["total_size"] > 0 and stats["compressed_size"] > 0:
        original_size = stats["total_size"] - stats["compressed_size"]
        if original_size > 0:
            stats["compression_ratio"] = (1 - (stats["compressed_size"] / original_size)) * 100
    
    return stats


def analyze_django_performance() -> Dict:
    """Analyze Django configuration for performance settings"""
    performance_settings = {
        "caching": {"status": "unknown", "recommendations": []},
        "database": {"status": "unknown", "recommendations": []},
        "static_files": {"status": "unknown", "recommendations": []},
        "sessions": {"status": "unknown", "recommendations": []},
        "middleware": {"status": "unknown", "recommendations": []},
    }
    
    settings_file = "laboratory/settings.py"
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check caching configuration
        if "CACHES" in content and "memcached" in content:
            performance_settings["caching"]["status"] = "optimized"
        else:
            performance_settings["caching"]["status"] = "needs_improvement"
            performance_settings["caching"]["recommendations"].append(
                "Configure Memcached for better caching performance"
            )
        
        # Check database optimizations
        if "CONN_MAX_AGE" in content:
            performance_settings["database"]["status"] = "optimized"
        else:
            performance_settings["database"]["status"] = "needs_improvement"
            performance_settings["database"]["recommendations"].append(
                "Add database connection pooling with CONN_MAX_AGE"
            )
        
        # Check static files
        if "ManifestStaticFilesStorage" in content:
            performance_settings["static_files"]["status"] = "optimized"
        else:
            performance_settings["static_files"]["status"] = "needs_improvement"
            performance_settings["static_files"]["recommendations"].append(
                "Use ManifestStaticFilesStorage for better static file handling"
            )
        
        # Check sessions
        if "cached_db" in content:
            performance_settings["sessions"]["status"] = "optimized"
        else:
            performance_settings["sessions"]["status"] = "needs_improvement"
            performance_settings["sessions"]["recommendations"].append(
                "Use cached session backend for better performance"
            )
        
        # Check middleware order
        if "GZipMiddleware" in content:
            performance_settings["middleware"]["status"] = "optimized"
        else:
            performance_settings["middleware"]["status"] = "needs_improvement"
            performance_settings["middleware"]["recommendations"].append(
                "Add GZipMiddleware for response compression"
            )
    
    return performance_settings


def check_gunicorn_config() -> Dict:
    """Check Gunicorn configuration for performance"""
    config = {"status": "unknown", "recommendations": []}
    
    gunicorn_file = "gunicorn.conf.py"
    if os.path.exists(gunicorn_file):
        with open(gunicorn_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        optimizations = 0
        total_checks = 6
        
        if "worker_class = 'gevent'" in content:
            optimizations += 1
        else:
            config["recommendations"].append("Use gevent worker class for better async performance")
        
        if "max_requests" in content:
            optimizations += 1
        else:
            config["recommendations"].append("Set max_requests to prevent memory leaks")
        
        if "preload_app = True" in content:
            optimizations += 1
        else:
            config["recommendations"].append("Enable preload_app for faster worker startup")
        
        if "worker_tmp_dir" in content:
            optimizations += 1
        else:
            config["recommendations"].append("Set worker_tmp_dir to /dev/shm for RAM-based temp files")
        
        if "keepalive" in content:
            optimizations += 1
        else:
            config["recommendations"].append("Configure keepalive for connection reuse")
        
        if "worker_connections" in content:
            optimizations += 1
        else:
            config["recommendations"].append("Set worker_connections for concurrent handling")
        
        config["score"] = f"{optimizations}/{total_checks}"
        config["status"] = "optimized" if optimizations >= 4 else "needs_improvement"
    else:
        config["recommendations"].append("Create optimized gunicorn.conf.py configuration")
    
    return config


def generate_performance_report() -> str:
    """Generate comprehensive performance report"""
    report = []
    report.append("=" * 60)
    report.append("L2 MIS PERFORMANCE ANALYSIS REPORT")
    report.append("=" * 60)
    report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Bundle analysis
    report.append("1. WEBPACK BUNDLE ANALYSIS")
    report.append("-" * 30)
    bundle_stats = analyze_webpack_bundles("assets/webpack_bundles")
    
    if "error" in bundle_stats:
        report.append(f"Error: {bundle_stats['error']}")
    else:
        report.append(f"Total files: {bundle_stats['total_files']}")
        report.append(f"Total size: {format_size(bundle_stats['total_size'])}")
        report.append(f"JavaScript files: {bundle_stats['js_files']} ({format_size(bundle_stats['js_size'])})")
        report.append(f"CSS files: {bundle_stats['css_files']} ({format_size(bundle_stats['css_size'])})")
        report.append(f"Compressed files: {bundle_stats['compressed_files']} ({format_size(bundle_stats['compressed_size'])})")
        
        if bundle_stats["largest_files"]:
            report.append("\nLargest JavaScript files:")
            for name, size in bundle_stats["largest_files"][:5]:
                report.append(f"  - {name}: {format_size(size)}")
        
        report.append(f"\nChunk analysis:")
        for chunk_type, size in bundle_stats["chunk_analysis"].items():
            report.append(f"  - {chunk_type}: {format_size(size)}")
    
    report.append("")
    
    # Django performance analysis
    report.append("2. DJANGO CONFIGURATION ANALYSIS")
    report.append("-" * 30)
    django_stats = analyze_django_performance()
    
    for category, info in django_stats.items():
        status_icon = "✓" if info["status"] == "optimized" else "⚠" if info["status"] == "needs_improvement" else "?"
        report.append(f"{status_icon} {category.title()}: {info['status']}")
        for rec in info["recommendations"]:
            report.append(f"    → {rec}")
    
    report.append("")
    
    # Gunicorn configuration
    report.append("3. GUNICORN CONFIGURATION ANALYSIS")
    report.append("-" * 30)
    gunicorn_stats = check_gunicorn_config()
    
    status_icon = "✓" if gunicorn_stats["status"] == "optimized" else "⚠"
    report.append(f"{status_icon} Configuration: {gunicorn_stats['status']}")
    if "score" in gunicorn_stats:
        report.append(f"  Optimization score: {gunicorn_stats['score']}")
    
    for rec in gunicorn_stats["recommendations"]:
        report.append(f"    → {rec}")
    
    report.append("")
    
    # Performance recommendations
    report.append("4. PERFORMANCE OPTIMIZATION SUMMARY")
    report.append("-" * 30)
    
    improvements = []
    
    # Bundle size recommendations
    if not bundle_stats.get("error") and bundle_stats["js_size"] > 10 * 1024 * 1024:  # > 10MB
        improvements.append("Consider further code splitting for large JavaScript bundles")
    
    if bundle_stats.get("compressed_files", 0) == 0:
        improvements.append("Enable gzip compression for static files")
    
    # Django recommendations
    django_issues = sum(1 for info in django_stats.values() if info["status"] == "needs_improvement")
    if django_issues > 0:
        improvements.append(f"Address {django_issues} Django configuration issues")
    
    # General recommendations
    improvements.extend([
        "Implement CDN for static asset delivery",
        "Add database query optimization and indexing",
        "Set up monitoring with tools like New Relic or Datadog",
        "Configure HTTP/2 for improved performance",
        "Implement service worker for offline functionality",
        "Add performance budgets to CI/CD pipeline"
    ])
    
    for i, improvement in enumerate(improvements, 1):
        report.append(f"{i}. {improvement}")
    
    report.append("")
    report.append("=" * 60)
    report.append("For detailed optimization guides, see:")
    report.append("- Django performance: https://docs.djangoproject.com/en/stable/topics/performance/")
    report.append("- Webpack optimization: https://webpack.js.org/guides/optimization/")
    report.append("- Gunicorn tuning: https://docs.gunicorn.org/en/stable/settings.html")
    report.append("=" * 60)
    
    return "\n".join(report)


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # JSON output for programmatic use
        data = {
            "bundles": analyze_webpack_bundles("assets/webpack_bundles"),
            "django": analyze_django_performance(),
            "gunicorn": check_gunicorn_config(),
            "timestamp": time.time()
        }
        print(json.dumps(data, indent=2))
    else:
        # Human-readable report
        report = generate_performance_report()
        print(report)
        
        # Save to file
        with open("performance_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nReport saved to: performance_report.txt")


if __name__ == "__main__":
    main()