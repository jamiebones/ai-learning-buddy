import subprocess
import os
import sys

def run_migration():
    """Run Alembic migrations to update the database schema."""
    print("Running database migrations...")
    
    try:
        # Get the directory containing this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Change to the backend directory if not already there
        if not os.path.basename(script_dir) == 'backend':
            os.chdir(script_dir)
        
        # Run the migration
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        
        print("Migration output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
            
        print("Migration completed successfully!")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"Migration failed with error code {e.returncode}")
        print("Output:")
        print(e.stdout)
        print("Error:")
        print(e.stderr)
        return e.returncode
    
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(run_migration()) 