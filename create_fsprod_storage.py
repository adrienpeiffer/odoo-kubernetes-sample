#!/usr/bin/env python3
"""
Script to create or update fsprod storage with correct S3 configuration
"""
import os
import sys
import json

# CRITICAL: Clear problematic environment variables BEFORE importing Odoo
# This prevents them from being loaded into serv_config
if 'SERVER_ENV_CONFIG' in os.environ:
    del os.environ['SERVER_ENV_CONFIG']
    print("✅ Cleared SERVER_ENV_CONFIG before Odoo initialization")
if 'SERVER_ENV_CONFIG_SECRET' in os.environ:
    del os.environ['SERVER_ENV_CONFIG_SECRET']
    print("✅ Cleared SERVER_ENV_CONFIG_SECRET before Odoo initialization")

# Add Odoo to Python path
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
from odoo import api, SUPERUSER_ID

def get_s3_config():
    """Get S3 configuration from environment variables"""
    return {
        'endpoint_url': os.environ.get('AWS_S3_ENDPOINT_URL'),
        'key': os.environ.get('AWS_ACCESS_KEY_ID'),
        'secret': os.environ.get('AWS_SECRET_ACCESS_KEY'),
        'use_ssl': 'true',
    }

def get_directory_path():
    """Get directory path from environment"""
    bucket_name = os.environ.get('S3_BUCKET', 'odoo-k8s-space')
    return f"{bucket_name}/attachments"

def build_server_env_defaults(json_options, directory_path):
    """Build server_env_defaults configuration"""
    return {
        'protocol_env_default': 's3',
        'directory_path_env_default': directory_path,
        'options_env_default': json.dumps(json_options),
        'use_as_default_for_attachments_env_default': True,
        'use_filename_obfuscation_env_default': True,
        'eval_options_from_env_env_default': False,
    }

def update_existing_storage(env, cr, json_options, directory_path):
    """Update existing fsprod storage"""
    print("✅ fsprod storage already exists, updating configuration...")
    
    server_env_defaults = build_server_env_defaults(json_options, directory_path)
    
    # Force update using direct database write
    cr.execute("""
        UPDATE fs_storage 
        SET server_env_defaults = %s
        WHERE code = %s
    """, (
        json.dumps(server_env_defaults),
        'fsprod'
    ))
    
    print("✅ fsprod storage updated successfully")
    return env['fs.storage'].search([('code', '=', 'fsprod')])[0]

def create_new_storage(env, json_options, directory_path):
    """Create new fsprod storage"""
    print("Creating fsprod storage...")
    
    server_env_defaults = build_server_env_defaults(json_options, directory_path)
    
    storage_data = {
        'name': 'DigitalOcean Spaces S3 Storage',
        'code': 'fsprod',
        'protocol': 's3',
        'directory_path': directory_path,
        'use_as_default_for_attachments': True,
        'use_filename_obfuscation': True,
        'eval_options_from_env': False,
        'json_options': json_options,
        'server_env_defaults': json.dumps(server_env_defaults),
    }
    
    print(f"Storage data: {storage_data}")
    storage = env['fs.storage'].create(storage_data)
    print("✅ fsprod storage created successfully")
    return storage

def set_attachment_parameters(env):
    """Set system parameters for attachment location"""
    env['ir.config_parameter'].sudo().set_param('ir_attachment.location', 'fs')
    env['ir.config_parameter'].sudo().set_param('ir_attachment.location.fs', 'fsprod')
    env.cr.commit()
    print("✅ Set ir_attachment.location parameters")

def display_storage_details(storage):
    """Display storage configuration details"""
    print(f"\n=== Storage Details ===")
    print(f"Name: {storage.name}")
    print(f"Code: {storage.code}")
    print(f"Protocol: {storage.protocol}")
    print(f"Directory: {storage.directory_path}")
    print(f"Default for attachments: {storage.use_as_default_for_attachments}")
    print(f"Filename obfuscation: {storage.use_filename_obfuscation}")
    print(f"Eval options from env: {storage.eval_options_from_env}")
    print(f"JSON Options: {storage.json_options}")

def display_all_storages(env):
    """Display all available storages for verification"""
    print(f"\n=== Final verification ===")
    all_storages = env['fs.storage'].search([])
    print(f"Total storages: {len(all_storages)}")
    for s in all_storages:
        print(f"  {s.name}: {s.protocol} (code: {s.code}, default: {s.use_as_default_for_attachments})")

def main():
    print("=== Creating/Updating fsprod storage ===")
    
    # Clear problematic environment variables that override server_env_defaults
    print("🧹 Clearing problematic environment variables...")
    if 'SERVER_ENV_CONFIG' in os.environ:
        del os.environ['SERVER_ENV_CONFIG']
        print("✅ Cleared SERVER_ENV_CONFIG")
    if 'SERVER_ENV_CONFIG_SECRET' in os.environ:
        del os.environ['SERVER_ENV_CONFIG_SECRET']
        print("✅ Cleared SERVER_ENV_CONFIG_SECRET")
    
    # Initialize Odoo
    odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'odoo'])
    odoo.service.db._create_empty_database = lambda *args: None
    
    # Get configuration
    json_options = get_s3_config()
    directory_path = get_directory_path()
    
    print(f"✅ Built JSON options from environment: {json_options}")
    print(f"Bucket name: {os.environ.get('S3_BUCKET', 'odoo-k8s-space')}")
    print(f"Directory path: {directory_path}")
    
    # Connect to database
    registry = odoo.registry('odoo')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Clear problematic environment variables again after Odoo initialization
        print("🧹 Clearing problematic environment variables again...")
        if 'SERVER_ENV_CONFIG' in os.environ:
            del os.environ['SERVER_ENV_CONFIG']
            print("✅ Cleared SERVER_ENV_CONFIG")
        if 'SERVER_ENV_CONFIG_SECRET' in os.environ:
            del os.environ['SERVER_ENV_CONFIG_SECRET']
            print("✅ Cleared SERVER_ENV_CONFIG_SECRET")
        
        # Check if fsprod storage already exists
        existing_storage = env['fs.storage'].search([('code', '=', 'fsprod')])
        
        if existing_storage:
            storage = update_existing_storage(env, cr, json_options, directory_path)
        else:
            storage = create_new_storage(env, json_options, directory_path)
        
        # Set system parameters
        set_attachment_parameters(env)
        
        # Clear cache to force recomputation of computed fields
        print("🔄 Clearing cache to force recomputation...")
        env.cache.clear()
        env.invalidate_all()
        
        # Display results
        display_storage_details(storage)
        display_all_storages(env)
        
        # Verify the configuration is correct
        if (storage.directory_path == directory_path and 
            storage.eval_options_from_env == False):
            print(f"\n🎉 SUCCESS! Configuration is now correct!")
            print(f"✅ Directory path: {storage.directory_path}")
            print(f"✅ Eval options from env: {storage.eval_options_from_env}")
        else:
            print(f"\n❌ Configuration still incorrect:")
            print(f"❌ Directory path: {storage.directory_path} (expected: {directory_path})")
            print(f"❌ Eval options from env: {storage.eval_options_from_env} (expected: False)")
        
        print(f"\n✅ fsprod storage configuration completed successfully!")

if __name__ == '__main__':
    main()