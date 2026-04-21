# -*- coding: utf-8 -*-
"""
Django Management Command: warm_permission_cache
Warms up the permission cache by preloading commonly accessed permissions
and user data to improve system performance.
"""

import time
import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from apps.core.cache import (
    permission_cache,
    CacheMonitor,
    execute_cache_warming,
    PERMISSION_CACHE_SETTINGS
)


class Command(BaseCommand):
    """
    Management command for warming permission cache
    
    Usage:
        python manage.py warm_permission_cache [options]
    
    Options:
        --force: Force cache warming even if performance is good
        --stats: Show cache statistics after warming
        --clear: Clear cache before warming
        --validate: Validate cache configuration
        --monitor: Show performance monitoring info
    """
    
    help = 'Warm permission cache by preloading commonly accessed permissions and user data'
    
    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cache warming even if performance is already good'
        )
        
        parser.add_argument(
            '--stats',
            action='store_true', 
            help='Show detailed cache statistics after warming'
        )
        
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all permission cache before warming'
        )
        
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validate cache configuration without warming'
        )
        
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Show performance monitoring information'
        )
        
        parser.add_argument(
            '--max-duration',
            type=int,
            default=300,
            help='Maximum warming duration in seconds (default: 300)'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Batch size for cache warming (default: 10)'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        """Main command execution"""
        try:
            # Setup logging level based on verbosity
            if options['verbose']:
                logging.getLogger('apps.core.cache').setLevel(logging.DEBUG)
            
            self.stdout.write("=" * 60)
            self.stdout.write(self.style.SUCCESS("Permission Cache Management"))
            self.stdout.write("=" * 60)
            
            # Validate configuration if requested
            if options['validate']:
                self._validate_configuration()
                return
            
            # Show monitoring info if requested
            if options['monitor']:
                self._show_monitoring_info()
                return
            
            # Get initial cache statistics
            initial_stats = permission_cache.get_cache_stats()
            self._display_cache_stats("Initial Cache Statistics", initial_stats)
            
            # Clear cache if requested
            if options['clear']:
                self._clear_cache()
            
            # Determine if warming is needed
            if not options['force'] and self._should_skip_warming(initial_stats):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Cache performance is already good (hit ratio: {initial_stats['hit_ratio']:.2%}). "
                        "Use --force to warm anyway."
                    )
                )
                return
            
            # Execute cache warming
            self._execute_warming(options)
            
            # Show final statistics if requested
            if options['stats']:
                final_stats = permission_cache.get_cache_stats()
                self._display_cache_stats("Final Cache Statistics", final_stats)
                self._display_performance_improvement(initial_stats, final_stats)
            
            # Check for performance alerts
            self._check_performance_alerts()
            
            self.stdout.write(
                self.style.SUCCESS("Cache warming completed successfully!")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Cache warming failed: {str(e)}")
            )
            raise CommandError(f"Cache warming failed: {str(e)}")
    
    def _validate_configuration(self):
        """Validate cache configuration"""
        self.stdout.write("Validating cache configuration...")
        
        try:
            from tintas_system.settings.cache import validate_cache_configuration
            
            validation_result = validate_cache_configuration()
            
            if validation_result['valid']:
                self.stdout.write(
                    self.style.SUCCESS("✓ Cache configuration is valid")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("✗ Cache configuration has errors:")
                )
                for error in validation_result['errors']:
                    self.stdout.write(f"  - {error}")
            
            if validation_result['warnings']:
                self.stdout.write(
                    self.style.WARNING("Warnings:")
                )
                for warning in validation_result['warnings']:
                    self.stdout.write(f"  - {warning}")
            
            # Test Redis connectivity
            self.stdout.write("\nTesting Redis connectivity...")
            if permission_cache.is_redis_available:
                self.stdout.write(
                    self.style.SUCCESS("✓ Redis is available and responsive")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("✗ Redis is not available - failover to database will be used")
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Configuration validation failed: {str(e)}")
            )
    
    def _show_monitoring_info(self):
        """Show cache monitoring information"""
        self.stdout.write("Cache Performance Monitoring")
        self.stdout.write("-" * 40)
        
        # Get current statistics
        stats = permission_cache.get_cache_stats()
        self._display_cache_stats("Current Performance", stats)
        
        # Performance health check
        health_checks = CacheMonitor.check_performance_thresholds()
        self.stdout.write("\nPerformance Health Checks:")
        
        checks_status = [
            ("Hit Ratio", health_checks['hit_ratio_ok']),
            ("Response Time", health_checks['response_time_ok']),
            ("Error Rate", health_checks['error_rate_ok']),
            ("Redis Available", health_checks['redis_available']),
        ]
        
        for check_name, status in checks_status:
            status_str = "✓ PASS" if status else "✗ FAIL"
            style = self.style.SUCCESS if status else self.style.ERROR
            self.stdout.write(f"  {check_name}: {style(status_str)}")
        
        # Overall health
        overall_health = health_checks['overall_health']
        overall_str = "HEALTHY" if overall_health else "NEEDS ATTENTION"
        overall_style = self.style.SUCCESS if overall_health else self.style.ERROR
        self.stdout.write(f"\nOverall Health: {overall_style(overall_str)}")
        
        # Performance alerts
        alerts = CacheMonitor.generate_performance_alerts()
        if alerts:
            self.stdout.write("\nActive Performance Alerts:")
            for alert in alerts:
                self.stdout.write(f"  - {self.style.WARNING(alert)}")
    
    def _clear_cache(self):
        """Clear permission cache"""
        self.stdout.write("Clearing permission cache...")
        
        try:
            permission_cache.clear_all_cache()
            self.stdout.write(
                self.style.SUCCESS("✓ Cache cleared successfully")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Cache clearing failed: {str(e)}")
            )
            raise
    
    def _should_skip_warming(self, stats):
        """Determine if cache warming should be skipped"""
        # Skip if hit ratio is already very good and cache is responsive
        return (
            stats['hit_ratio'] > 0.95 and 
            stats['avg_response_time'] < 25.0 and
            stats['redis_available']
        )
    
    def _execute_warming(self, options):
        """Execute cache warming process"""
        self.stdout.write("Warming permission cache...")
        
        start_time = time.time()
        
        try:
            # Update cache warming settings from command options
            original_max_duration = PERMISSION_CACHE_SETTINGS.get('WARMING_LIMITS', {}).get('max_duration', 300)
            original_batch_size = PERMISSION_CACHE_SETTINGS.get('WARMING_LIMITS', {}).get('batch_size', 10)
            
            # Temporarily update settings
            if 'WARMING_LIMITS' not in PERMISSION_CACHE_SETTINGS:
                PERMISSION_CACHE_SETTINGS['WARMING_LIMITS'] = {}
            
            PERMISSION_CACHE_SETTINGS['WARMING_LIMITS']['max_duration'] = options['max_duration']
            PERMISSION_CACHE_SETTINGS['WARMING_LIMITS']['batch_size'] = options['batch_size']
            
            # Execute warming
            execute_cache_warming()
            
            # Restore original settings
            PERMISSION_CACHE_SETTINGS['WARMING_LIMITS']['max_duration'] = original_max_duration
            PERMISSION_CACHE_SETTINGS['WARMING_LIMITS']['batch_size'] = original_batch_size
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Cache warming completed in {duration:.2f} seconds"
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Cache warming failed: {str(e)}")
            )
            raise
    
    def _display_cache_stats(self, title, stats):
        """Display cache statistics in formatted output"""
        self.stdout.write(f"\n{title}:")
        self.stdout.write("-" * len(title))
        
        # Format statistics
        formatted_stats = [
            ("Hits", f"{stats['hits']:,}"),
            ("Misses", f"{stats['misses']:,}"),
            ("Hit Ratio", f"{stats['hit_ratio']:.2%}"),
            ("Avg Response Time", f"{stats['avg_response_time']:.2f}ms"),
            ("Errors", f"{stats['errors']:,}"),
            ("Redis Available", "Yes" if stats['redis_available'] else "No"),
        ]
        
        if stats.get('last_updated'):
            formatted_stats.append(("Last Updated", stats['last_updated']))
        
        if stats.get('redis_memory_used'):
            formatted_stats.append(("Redis Memory", stats['redis_memory_used']))
        
        # Display stats in two columns
        for i in range(0, len(formatted_stats), 2):
            left_item = formatted_stats[i]
            right_item = formatted_stats[i + 1] if i + 1 < len(formatted_stats) else ("", "")
            
            self.stdout.write(
                f"  {left_item[0]:<20}: {left_item[1]:<15} "
                f"{right_item[0]:<20}: {right_item[1]}"
            )
    
    def _display_performance_improvement(self, initial_stats, final_stats):
        """Display performance improvement metrics"""
        self.stdout.write("\nPerformance Improvement:")
        self.stdout.write("-" * 25)
        
        # Calculate improvements
        hit_ratio_change = final_stats['hit_ratio'] - initial_stats['hit_ratio']
        response_time_change = final_stats['avg_response_time'] - initial_stats['avg_response_time']
        
        # Hit ratio improvement
        if hit_ratio_change > 0:
            self.stdout.write(
                f"  Hit Ratio: {self.style.SUCCESS(f'+{hit_ratio_change:.2%}')}"
            )
        elif hit_ratio_change < 0:
            self.stdout.write(
                f"  Hit Ratio: {self.style.WARNING(f'{hit_ratio_change:.2%}')}"
            )
        else:
            self.stdout.write("  Hit Ratio: No change")
        
        # Response time improvement
        if response_time_change < 0:
            self.stdout.write(
                f"  Response Time: {self.style.SUCCESS(f'{response_time_change:.2f}ms (faster)')}"
            )
        elif response_time_change > 0:
            self.stdout.write(
                f"  Response Time: {self.style.WARNING(f'+{response_time_change:.2f}ms (slower)')}"
            )
        else:
            self.stdout.write("  Response Time: No significant change")
    
    def _check_performance_alerts(self):
        """Check and display performance alerts"""
        alerts = CacheMonitor.generate_performance_alerts()
        
        if alerts:
            self.stdout.write("\nPerformance Alerts:")
            self.stdout.write("-" * 19)
            
            for alert in alerts:
                if "CRITICAL" in alert:
                    self.stdout.write(f"  {self.style.ERROR(alert)}")
                else:
                    self.stdout.write(f"  {self.style.WARNING(alert)}")
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✓ No performance alerts - cache is performing well")
            )