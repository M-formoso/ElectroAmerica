import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.core.config import settings
import uuid


def configure_cloudinary():
    """Configura Cloudinary con las credenciales."""
    if not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
        return False

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )
    return True


async def upload_image(file: UploadFile, folder: str = "proyectos") -> dict:
    """
    Sube una imagen a Cloudinary.

    Args:
        file: Archivo a subir
        folder: Carpeta en Cloudinary (proyectos, materiales, equipos, usuarios, etc.)

    Returns:
        dict con url, public_id, thumbnail_url y metadatos
    """
    if not configure_cloudinary():
        raise HTTPException(
            status_code=500,
            detail="Cloudinary no está configurado. Configure las variables de entorno."
        )

    # Validar tipo de archivo
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Use: {', '.join(allowed_types)}"
        )

    # Leer contenido y validar tamaño (máximo 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="El archivo es demasiado grande. Máximo 10MB."
        )

    try:
        # Generar ID único
        public_id = f"electro_america/{folder}/{uuid.uuid4()}"

        # Subir imagen original
        result = cloudinary.uploader.upload(
            contents,
            public_id=public_id,
            resource_type="image",
            transformation=[
                {"quality": "auto:good"},
                {"fetch_format": "auto"}
            ]
        )

        # Generar URL de thumbnail
        thumbnail_url = cloudinary.CloudinaryImage(result["public_id"]).build_url(
            width=300,
            height=300,
            crop="fill",
            quality="auto"
        )

        return {
            "url": result["secure_url"],
            "thumbnail_url": thumbnail_url,
            "public_id": result["public_id"],
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format"),
            "bytes": result.get("bytes"),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al subir imagen: {str(e)}"
        )


async def delete_image(public_id: str) -> bool:
    """
    Elimina una imagen de Cloudinary.

    Args:
        public_id: ID público de la imagen

    Returns:
        True si se eliminó correctamente
    """
    if not configure_cloudinary():
        return False

    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception:
        return False


def get_optimized_url(public_id: str, width: int = None, height: int = None) -> str:
    """
    Genera URL optimizada de una imagen.

    Args:
        public_id: ID de la imagen
        width: Ancho deseado (opcional)
        height: Alto deseado (opcional)

    Returns:
        URL optimizada
    """
    transformations = {"quality": "auto", "fetch_format": "auto"}

    if width:
        transformations["width"] = width
    if height:
        transformations["height"] = height
    if width or height:
        transformations["crop"] = "fill"

    return cloudinary.CloudinaryImage(public_id).build_url(**transformations)
