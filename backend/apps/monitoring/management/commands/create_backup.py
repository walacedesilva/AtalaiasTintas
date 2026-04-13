"""
Django management command for creating database backups
User Story 2: Data Integrity and Backup
Task: T043 - Create backup management command
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.monitoring.services import BackupService
from apps.core.models import BackupRecord

User = get_user_model()


class Command(BaseCommand):
    """
    Management command to create database backups
    
    Usage:
        python manage.py create_backup [OPTIONS]
        python manage.py create_backup --type full --user admin
        python manage.py create_backup --type incremental
        python manage.py create_backup --cleanup
    """
    
    help = 'Create database backups and manage backup files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['full', 'incremental', 'manual'],
            default='full',
            help='Type of backup to create (default: full)'
        )
        
        parser.add_argument(
            '--user',
            type=str,
            help='Username of the user initiating the backup'
        )
        
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up expired backup files'
        )
        
        parser.add_argument(
            '--list',
            action='store_true',
            help='List recent backup files'
        )
        
        parser.add_argument(
            '--verify',
            type=str,
            help='Verify backup file integrity by backup ID'
        )
    
    def handle(self, *args, **options):
        backup_service = BackupService()
        
        if options['cleanup']:
            self._cleanup_backups(backup_service)
            return
        
        if options['list']:
            self._list_backups()
            return
        
        if options['verify']:
            self._verify_backup(options['verify'])
            return
        
        # Create backup
        self._create_backup(backup_service, options)
    
    def _create_backup(self, backup_service, options):
        """Create a new backup"""
        backup_type = options['type']
        username = options.get('user')
        
        # Get user if username provided
        initiated_by = None
        if username:
            try:
                initiated_by = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"User '{username}' not found. Creating as automated backup.")
                )
        
        # Map backup type to model constant
        backup_type_map = {
            'full': BackupRecord.TYPE_FULL,
            'incremental': BackupRecord.TYPE_INCREMENTAL,
            'manual': BackupRecord.TYPE_MANUAL
        }
        
        backup_type_const = backup_type_map[backup_type]
        
        self.stdout.write(f"Creating {backup_type} backup...")
        
        try:
            backup_record = backup_service.create_backup(
                backup_type=backup_type_const,
                initiated_by=initiated_by
            )
            
            if backup_record.status == BackupRecord.STATUS_COMPLETED:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Backup created successfully\n"
                        f"  ID: {backup_record.backup_id}\n"
                        f"  File: {backup_record.filename}\n"
                        f"  Size: {self._format_size(backup_record.file_size)}\n"
                        f"  Path: {backup_record.file_path}\n"
                        f"  Checksum: {backup_record.checksum[:16]}...\n"
                        f"  Duration: {backup_record.duration_seconds}s"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Backup failed\n"
                        f"  ID: {backup_record.backup_id}\n"
                        f"  Status: {backup_record.status}\n"
                        f"  Error: {backup_record.error_message}"
                    )
                )
                raise CommandError("Backup creation failed")
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Backup creation failed: {str(e)}")
            )
            raise CommandError("Backup creation failed")
    
    def _cleanup_backups(self, backup_service):
        """Clean up expired backup files"""
        self.stdout.write("Cleaning up expired backups...")
        
        try:
            cleaned_count = backup_service.cleanup_expired_backups()
            
            if cleaned_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Cleaned up {cleaned_count} expired backup files"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING("No expired backups found to clean up")
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Cleanup failed: {str(e)}")
            )
            raise CommandError("Backup cleanup failed")
    
    def _list_backups(self):
        """List recent backup files"""
        self.stdout.write("Recent backup files:")
        self.stdout.write("-" * 80)
        
        try:
            recent_backups = BackupRecord.objects.order_by('-created_at')[:10]
            
            if not recent_backups:
                self.stdout.write(self.style.WARNING("No backup records found"))
                return
            
            for backup in recent_backups:
                status_color = self.style.SUCCESS if backup.status == BackupRecord.STATUS_COMPLETED else self.style.ERROR
                
                self.stdout.write(
                    f"{backup.backup_id[:8]}  "
                    f"{backup.get_backup_type_display():<12}  "
                    f"{status_color(backup.status):<15}  "
                    f"{self._format_size(backup.file_size):<10}  "
                    f"{backup.created_at.strftime('%Y-%m-%d %H:%M:%S')}  "
                    f"{backup.filename}"
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Failed to list backups: {str(e)}")
            )
            raise CommandError("Failed to list backups")
    
    def _verify_backup(self, backup_id):
        """Verify backup file integrity"""
        self.stdout.write(f"Verifying backup {backup_id}...")
        
        try:
            backup_record = BackupRecord.objects.get(backup_id=backup_id)
            
            if not backup_record.is_valid():
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Backup verification failed\n"
                        f"  Status: {backup_record.status}\n"
                        f"  File exists: {backup_record.file_exists()}\n"
                        f"  Checksum valid: {backup_record.verify_checksum()}"
                    )
                )
                raise CommandError("Backup verification failed")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Backup verification successful\n"
                    f"  ID: {backup_record.backup_id}\n"
                    f"  File: {backup_record.filename}\n"
                    f"  Size: {self._format_size(backup_record.file_size)}\n"
                    f"  Created: {backup_record.created_at}\n"
                    f"  Checksum: {backup_record.checksum[:16]}...\n"
                    f"  Status: {backup_record.status}"
                )
            )
        
        except BackupRecord.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"✗ Backup with ID '{backup_id}' not found")
            )
            raise CommandError("Backup not found")
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Backup verification failed: {str(e)}")
            )
            raise CommandError("Backup verification failed")
    
    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if not size_bytes:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"