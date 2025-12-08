import os
import subprocess
import sys
import hashlib

def calculate_sha256(file_path):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_onnx_model():
    """Download nomic-embed-text-v1.5 INT8 ONNX model if not present and verify SHA256."""
    
    # Define paths and expected SHA256
    onnx_dir = "onnx"
    model_path = os.path.join(onnx_dir, "model_int8.onnx")
    EXPECTED_SHA256 = "b4342336debaea79de872370664b0aaeb67dea4605513d00ee236ea871a81f27"
    
    # Check if model already exists and verify hash
    if os.path.exists(model_path):
        print(f"🔍 Verifying existing model: {model_path}")
        actual_hash = calculate_sha256(model_path)
        
        if actual_hash == EXPECTED_SHA256:
            print(f"✅ SHA256 matches! ({actual_hash})")
            return model_path
        else:
            print(f"❌ SHA256 mismatch!")
            print(f"   Expected: {EXPECTED_SHA256}")
            print(f"   Got:      {actual_hash}")
            print("🔄 Redownloading...")
            os.remove(model_path)
    
    # Create onnx directory if it doesn't exist
    os.makedirs(onnx_dir, exist_ok=True)
    print(f"📁 Created directory: {onnx_dir}")
    
    # Download URL
    url = "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5/resolve/main/onnx/model_int8.onnx"
    
    print("⬇️  Downloading model...")
    
    try:
        # Use platform-appropriate download method
        if sys.platform == "win32":
            cmd = [
                "powershell", "-Command",
                f'Invoke-WebRequest -Uri "{url}" -OutFile "{model_path}"'
            ]
        else:
            cmd = ["curl", "-L", url, "-o", model_path]
        
        # Run download command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Download complete!")
        
        # Verify SHA256 after download
        print("🔍 Verifying SHA256...")
        actual_hash = calculate_sha256(model_path)
        
        if actual_hash == EXPECTED_SHA256:
            print(f"✅ SHA256 VERIFIED! ({actual_hash})")
            print(f"📍 Saved to: {model_path}")
            return model_path
        else:
            print(f"❌ SHA256 VERIFICATION FAILED!")
            print(f"   Expected: {EXPECTED_SHA256}")
            print(f"   Got:      {actual_hash}")
            os.remove(model_path)
            print("❌ Corrupted download. Try manual download.")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ curl/powershell not found.")
        sys.exit(1)

if __name__ == "__main__":
    model_path = ensure_onnx_model()
    print(f"\n🎉 Ready to use: {model_path}")
