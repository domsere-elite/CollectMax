import sys
import traceback

print("Testing if backend modules can be imported...")
print()

try:
    print("1. Importing app.core.auth...")
    import app.core.auth
    print("   ✓ Success")
except Exception as e:
    print(f"   ✗ Error: {e}")
    traceback.print_exc()

try:
    print("2. Importing app.routers.operations...")
    import app.routers.operations
    print("   ✓ Success")
except Exception as e:
    print(f"   ✗ Error: {e}")
    traceback.print_exc()

try:
    print("3. Importing app.main...")
    import app.main
    print("   ✓ Success")
except Exception as e:
    print(f"   ✗ Error: {e}")
    traceback.print_exc()

print()
print("If all imports succeeded, the code is syntactically correct.")
print("The backend server should reload automatically.")
