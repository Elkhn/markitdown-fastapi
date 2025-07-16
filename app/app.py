import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import JSONResponse, FileResponse
from markitdown import MarkItDown
import uuid
import logging

# Set up basic logging configuration
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MarkItDown API",
    description="Convert various file formats to Markdown using MarkItDown",
    version="1.0.0"
)

# Create necessary directories
UPLOAD_DIR = Path("/app/uploads")
CONVERTED_DIR = Path("/app/converted")
UPLOAD_DIR.mkdir(exist_ok=True)
CONVERTED_DIR.mkdir(exist_ok=True)

# Initialize MarkItDown
md_converter = MarkItDown(enable_plugins=False)

@app.get("/")
def root():
    return {
        "message": "MarkItDown API is running",
        "upload_dir": str(UPLOAD_DIR),
        "converted_dir": str(CONVERTED_DIR),
        "directories_exist": {
            "uploads": UPLOAD_DIR.exists(),
            "converted": CONVERTED_DIR.exists()
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Check if directories are accessible
        upload_writable = os.access(UPLOAD_DIR, os.W_OK)
        converted_writable = os.access(CONVERTED_DIR, os.W_OK)
        
        return {
            "status": "healthy",
            "directories": {
                "upload_dir": {
                    "path": str(UPLOAD_DIR),
                    "exists": UPLOAD_DIR.exists(),
                    "writable": upload_writable
                },
                "converted_dir": {
                    "path": str(CONVERTED_DIR),
                    "exists": CONVERTED_DIR.exists(),
                    "writable": converted_writable
                }
            },
            "user_info": {
                "uid": os.getuid(),
                "gid": os.getgid()
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/convert-by-filename")
def convert_file_by_name(
    file_name: str = Form(...),
    output_filename: Optional[str] = Form(None)
):
    """
    Convert a file from the uploads directory to Markdown and save it in the converted directory.
    
    Args:
        file_name: The name of the file in the uploads directory to convert
        output_filename: Optional custom output filename (without extension)
    
    Returns:
        JSON response with conversion details
    """
    try:
        # Validate file_name
        if not file_name:
            raise HTTPException(status_code=400, detail="No file_name provided")
        
        # Sanitize file_name to prevent directory traversal
        file_name = os.path.basename(file_name)
        
        # Check if file exists in uploads directory
        input_file_path = UPLOAD_DIR / file_name
        
        if not input_file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"File '{file_name}' not found in uploads directory"
            )
        
        if not input_file_path.is_file():
            raise HTTPException(
                status_code=400, 
                detail=f"'{file_name}' is not a valid file"
            )
        
        logger.info(f"Converting file: {file_name}")
        
        # Generate unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        original_name = Path(file_name).stem
        file_extension = Path(file_name).suffix
        
        # Convert file using MarkItDown
        try:
            result = md_converter.convert(str(input_file_path))
            
            if not result or not result.text_content:
                raise HTTPException(
                    status_code=422, 
                    detail=f"Unable to convert file: {file_name}"
                )
            
            logger.info(f"File converted successfully, content length: {len(result.text_content)}")
            
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            raise HTTPException(
                status_code=422, 
                detail=f"Conversion failed: {str(e)}"
            )
        
        # Determine output filename
        if output_filename:
            md_filename = f"{output_filename}.md"
        else:
            md_filename = f"{original_name}_{unique_id}.md"
        
        # Save converted markdown to converted directory
        output_path = CONVERTED_DIR / md_filename
        
        with open(output_path, 'w', encoding='utf-8') as md_file:
            md_file.write(result.text_content)
        
        logger.info(f"Converted file saved: {output_path}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "File converted successfully",
                "original_filename": file_name,
                "converted_filename": md_filename,
                "input_path": str(input_file_path),
                "output_path": str(output_path),
                "file_size": len(result.text_content),
                "metadata": {
                    "original_extension": file_extension,
                    "conversion_id": unique_id
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/convert-by-filename/{file_name}")
def convert_file_by_name_get(
    file_name: str,
    output_filename: Optional[str] = Query(None)
):
    """
    Convert a file from the uploads directory to Markdown using GET method.
    
    Args:
        file_name: The name of the file in the uploads directory to convert
        output_filename: Optional custom output filename (without extension)
    
    Returns:
        JSON response with conversion details
    """
    try:
        # Validate file_name
        if not file_name:
            raise HTTPException(status_code=400, detail="No file_name provided")
        
        # Sanitize file_name to prevent directory traversal
        file_name = os.path.basename(file_name)
        
        # Check if file exists in uploads directory
        input_file_path = UPLOAD_DIR / file_name
        
        if not input_file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"File '{file_name}' not found in uploads directory"
            )
        
        if not input_file_path.is_file():
            raise HTTPException(
                status_code=400, 
                detail=f"'{file_name}' is not a valid file"
            )
        
        logger.info(f"Converting file: {file_name}")
        
        # Generate unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        original_name = Path(file_name).stem
        file_extension = Path(file_name).suffix
        
        # Convert file using MarkItDown
        try:
            result = md_converter.convert(str(input_file_path))
            
            if not result or not result.text_content:
                raise HTTPException(
                    status_code=422, 
                    detail=f"Unable to convert file: {file_name}"
                )
            
            logger.info(f"File converted successfully, content length: {len(result.text_content)}")
            
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            raise HTTPException(
                status_code=422, 
                detail=f"Conversion failed: {str(e)}"
            )
        
        # Determine output filename
        if output_filename:
            md_filename = f"{output_filename}.md"
        else:
            md_filename = f"{original_name}_{unique_id}.md"
        
        # Save converted markdown to converted directory
        output_path = CONVERTED_DIR / md_filename
        
        with open(output_path, 'w', encoding='utf-8') as md_file:
            md_file.write(result.text_content)
        
        logger.info(f"Converted file saved: {output_path}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "File converted successfully",
                "original_filename": file_name,
                "converted_filename": md_filename,
                "input_path": str(input_file_path),
                "output_path": str(output_path),
                "file_size": len(result.text_content),
                "metadata": {
                    "original_extension": file_extension,
                    "conversion_id": unique_id
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the uploads directory for later conversion.
    
    Args:
        file: The file to upload
    
    Returns:
        JSON response with upload details
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Sanitize filename
        filename = os.path.basename(file.filename)
        file_path = UPLOAD_DIR / filename
        
        # Check if file already exists
        if file_path.exists():
            raise HTTPException(
                status_code=409, 
                detail=f"File '{filename}' already exists"
            )
        
        # Save uploaded file
        with open(file_path, 'wb') as f:
            content = file.file.read()
            f.write(content)
        
        logger.info(f"File uploaded: {file_path}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "File uploaded successfully",
                "filename": filename,
                "file_path": str(file_path),
                "file_size": len(content)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/list-uploads")
def list_uploaded_files():
    """List all files in the uploads directory."""
    try:
        files = []
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "convert_url": f"/convert-by-filename/{file_path.name}"
                })
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "files": files,
                "total_files": len(files)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error listing files: {str(e)}"
        )

@app.post("/convert")
def convert_file(
    file: UploadFile = File(...),
    output_filename: Optional[str] = Form(None)
):
    """
    Convert an uploaded file to Markdown and save it in the converted directory.
    
    Args:
        file: The file to convert
        output_filename: Optional custom output filename (without extension)
    
    Returns:
        JSON response with conversion details
    """
    temp_file_path = None
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        logger.info(f"Converting file: {file.filename}")
        
        # Generate unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        original_name = Path(file.filename).stem
        file_extension = Path(file.filename).suffix
        
        # Create temporary file for processing
        temp_file_path = UPLOAD_DIR / f"{unique_id}_{file.filename}"
        
        # Save uploaded file temporarily
        with open(temp_file_path, 'wb') as temp_file:
            content = file.file.read()
            temp_file.write(content)
        
        logger.info(f"Temporary file saved: {temp_file_path}")
        
        # Convert file using MarkItDown
        try:
            result = md_converter.convert(str(temp_file_path))
            
            if not result.text_content:
                raise HTTPException(
                    status_code=422, 
                    detail=f"Unable to convert file: {file.filename}"
                )
            
            logger.info(f"File converted successfully, content length: {len(result.text_content)}")
            
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            raise HTTPException(
                status_code=422, 
                detail=f"Conversion failed: {str(e)}"
            )
        
        # Determine output filename
        if output_filename:
            md_filename = f"{output_filename}.md"
        else:
            md_filename = f"{original_name}_{unique_id}.md"
        
        # Save converted markdown to converted directory
        output_path = CONVERTED_DIR / md_filename
        
        with open(output_path, 'w', encoding='utf-8') as md_file:
            md_file.write(result.text_content)
        
        logger.info(f"Converted file saved: {output_path}")
        
        # Clean up temporary file
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "File converted successfully",
                "original_filename": file.filename,
                "converted_filename": md_filename,
                "output_path": str(output_path),
                "file_size": len(result.text_content),
                "metadata": {
                    "original_extension": file_extension,
                    "conversion_id": unique_id
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        # Clean up on error
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/download/{filename}")
def download_converted_file(filename: str):
    """Download a converted markdown file."""
    file_path = CONVERTED_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='text/markdown'
    )

@app.get("/list-converted")
def list_converted_files():
    """List all converted markdown files."""
    try:
        files = []
        for file_path in CONVERTED_DIR.glob("*.md"):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "download_url": f"/download/{file_path.name}"
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "files": files,
                "total_files": len(files)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error listing files: {str(e)}"
        )

@app.delete("/delete/{filename}")
def delete_converted_file(filename: str):
    """Delete a converted markdown file."""
    file_path = CONVERTED_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"File {filename} deleted successfully"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error deleting file: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)